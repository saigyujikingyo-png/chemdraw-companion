# Portable lifecycle decisions. This file must not initialize or reconnect COM.
function Write-LifecycleJson {
    param([Parameter(Mandatory)][string]$Path,[Parameter(Mandatory)]$Value,[switch]$NoOverwrite)
    $temporary=$Path+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 100))
    $stream=[IO.FileStream]::new($temporary,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
    # Publication is one rename. A reader never treats partially written bytes as a receipt.
    [IO.File]::Move($temporary,$Path,!$NoOverwrite)
}

function Get-LifecycleProcessState {
    param([hashtable]$Binding,[scriptblock]$ObserveProcess)
    if($null -eq $Binding -or !$Binding.ContainsKey('pid') -or !$Binding.ContainsKey('start_utc') -or !$Binding.ContainsKey('executable') -or
       [string]::IsNullOrWhiteSpace([string]$Binding.start_utc) -or [string]::IsNullOrWhiteSpace([string]$Binding.executable)){
        return @{state='unknown';reason='Complete process creation and executable identity is unavailable.'}
    }
    try{
        $observation=& $ObserveProcess $Binding
        if($null -eq $observation -or !$observation.ContainsKey('state')){throw 'Process observation has no state.'}
        if($observation.state -eq 'absent'){return @{state='absent'}}
        if($observation.state -ne 'present'){throw 'Process identity is unavailable.'}
        foreach($key in @('pid','start_utc','executable')){if(!$observation.ContainsKey($key)){throw 'Process observation is incomplete.'}}
        $expected=[IO.Path]::GetFullPath([string]$Binding.executable)
        $observed=[IO.Path]::GetFullPath([string]$observation.executable)
        if($observation.pid -ne $Binding.pid -or $observation.start_utc -cne $Binding.start_utc -or
           ![StringComparer]::OrdinalIgnoreCase.Equals($expected,$observed)){
            return @{state='identity_changed';reason='PID, creation identity or executable changed; the current process is not owned.'}
        }
        return @{state='exact'}
    }catch{return @{state='unknown';reason=$_.Exception.Message}}
}

function Wait-OwnedProcessExit {
    param([hashtable]$Binding,[scriptblock]$ObserveProcess,
          [ValidateRange(0,10000)][int]$TimeoutMilliseconds=1500,[ValidateRange(1,1000)][int]$PollMilliseconds=50,
          [scriptblock]$NowMilliseconds={[Environment]::TickCount64},[scriptblock]$Pause={param($Milliseconds)Start-Sleep -Milliseconds $Milliseconds})
    $deadline=(& $NowMilliseconds)+$TimeoutMilliseconds;$polls=0
    while($true){
        $observed=Get-LifecycleProcessState -Binding $Binding -ObserveProcess $ObserveProcess;$polls++
        $remaining=$deadline-(& $NowMilliseconds)
        if($observed.state -ne 'exact' -or $remaining -le 0){
            return @{process_state=$observed.state;observed_process_exit=($observed.state -eq 'absent');
                timed_out=($observed.state -eq 'exact');polls=$polls;observed_at=[DateTime]::UtcNow.ToString('o')}
        }
        [void](& $Pause ([int][Math]::Min($PollMilliseconds,$remaining)))
    }
}

function Get-LifecycleApplicationScope {
    param([hashtable]$Context,[scriptblock]$ObserveApplication,[bool]$ExpectDocument)
    try{
        $scope=& $ObserveApplication
        foreach($key in @('retained_application','application_pid','document_count','retained_document_matches')){
            if($null -eq $scope -or !$scope.ContainsKey($key)){throw 'Native application scope is incomplete.'}
        }
        if(!$scope.retained_application -or $scope.application_pid -ne $Context.binding.pid){throw 'Retained native application identity is not proven.'}
        if($ExpectDocument){
            if($scope.document_count -ne 1 -or !$scope.retained_document_matches -or !$scope.ContainsKey('hwnd') -or
               !$Context.binding.ContainsKey('hwnd') -or $scope.hwnd -ne $Context.binding.hwnd){
                throw 'Retained native document or window scope is not proven.'
            }
        }elseif($scope.document_count -ne 0){throw 'The retained application is not empty; no Quit is authorized.'}
        return @{ok=$true}
    }catch{return @{ok=$false;reason=$_.Exception.Message}}
}

function Invoke-OwnedLifecycleCleanup {
    param([Parameter(Mandatory)][hashtable]$Context,[Parameter(Mandatory)][scriptblock]$ObserveProcess,
          [Parameter(Mandatory)][scriptblock]$ObserveApplication,[Parameter(Mandatory)][scriptblock]$CloseDocument,
          [Parameter(Mandatory)][scriptblock]$QuitApplication,[switch]$Detach,[switch]$Preserve,
          [ValidateRange(0,10000)][int]$TimeoutMilliseconds=1500,[ValidateRange(1,1000)][int]$PollMilliseconds=50,
          [scriptblock]$NowMilliseconds={[Environment]::TickCount64},[scriptblock]$Pause={param($Milliseconds)Start-Sleep -Milliseconds $Milliseconds})
    $receipt=@{result_version='owned-lifecycle/0.1';context_id=$Context.context_id;generation=$Context.generation;operation_id=$Context.operation_id;
        observed_at=[DateTime]::UtcNow.ToString('o');session_state='unknown';process_state='unknown';owned_binding=$Context.binding;
        document_id=$(if($Context.ContainsKey('document_id')){$Context.document_id}else{$null});
        revision=$(if($Context.ContainsKey('revision')){$Context.revision}else{$null});
        saved_revision_verified=$Context.saved_revision_verified;
        creation_attempted=$Context.creation_attempted;application_created=$Context.application_created;ownership_verified=$false;
        document_close_attempted=$false;document_close_returned=$false;application_quit_attempted=$false;application_quit_returned=$false;
        observed_process_exit=$false;ownership_transferred_to_user=$false;preserved=$true;errors=@()}
    if(!$Context.creation_attempted){$receipt.session_state='not_created';$receipt.preserved=$false;return $receipt}
    if(!$Context.application_created){$receipt.errors+=,'Application creation may have happened; no retained application is available.';return $receipt}
    $process=Get-LifecycleProcessState -Binding $Context.binding -ObserveProcess $ObserveProcess
    $receipt.process_state=$process.state
    if($process.state -eq 'absent'){
        $receipt.observed_process_exit=$true;$receipt.session_state='closed';$receipt.preserved=$false;return $receipt
    }
    if($process.state -ne 'exact'){$receipt.errors+=,$process.reason;return $receipt}
    if($Preserve){$receipt.errors+=,'Preservation was requested; no close or Quit was attempted.';return $receipt}
    $scope=Get-LifecycleApplicationScope -Context $Context -ObserveApplication $ObserveApplication -ExpectDocument $Context.document_present
    if(!$scope.ok){$receipt.errors+=,$scope.reason;return $receipt}
    $receipt.ownership_verified=$true
    if($Detach){
        if(!$Context.document_present -or !$Context.saved_revision_verified){$receipt.errors+=,'Detach requires the exact verified saved document revision.';return $receipt}
        $receipt.session_state='detached';$receipt.ownership_transferred_to_user=$true;return $receipt
    }
    if($Context.document_present){
        # Check the process again after the native scope observation, before Close.
        $process=Get-LifecycleProcessState -Binding $Context.binding -ObserveProcess $ObserveProcess
        $receipt.process_state=$process.state
        if($process.state -ne 'exact'){$receipt.errors+=,'Process identity changed before document Close.';return $receipt}
        $receipt.document_close_attempted=$true
        try{[void](& $CloseDocument);$receipt.document_close_returned=$true}catch{$receipt.errors+=,$_.Exception.Message;return $receipt}
    }
    $process=Get-LifecycleProcessState -Binding $Context.binding -ObserveProcess $ObserveProcess
    $receipt.process_state=$process.state
    if($process.state -eq 'absent'){
        $receipt.observed_process_exit=$true;$receipt.session_state='closed';$receipt.preserved=$false;return $receipt
    }
    if($process.state -ne 'exact'){$receipt.errors+=,'Process identity changed before application Quit.';return $receipt}
    # Close returning is not permission to quit a remaining or unrelated document.
    $scope=Get-LifecycleApplicationScope -Context $Context -ObserveApplication $ObserveApplication -ExpectDocument $false
    if(!$scope.ok){$receipt.errors+=,$scope.reason;return $receipt}
    $process=Get-LifecycleProcessState -Binding $Context.binding -ObserveProcess $ObserveProcess
    $receipt.process_state=$process.state
    if($process.state -ne 'exact'){$receipt.errors+=,'Process identity changed after empty-application verification.';return $receipt}
    $receipt.application_quit_attempted=$true
    try{[void](& $QuitApplication);$receipt.application_quit_returned=$true}catch{$receipt.errors+=,$_.Exception.Message}
    # Even an exception from Quit is followed only by observation, never replay.
    $exit=Wait-OwnedProcessExit -Binding $Context.binding -ObserveProcess $ObserveProcess -TimeoutMilliseconds $TimeoutMilliseconds -PollMilliseconds $PollMilliseconds -NowMilliseconds $NowMilliseconds -Pause $Pause
    $receipt.process_state=$exit.process_state;$receipt.observed_process_exit=$exit.observed_process_exit;$receipt.exit_observation=$exit
    if($exit.observed_process_exit){$receipt.session_state='closed';$receipt.preserved=$false}
    elseif($exit.process_state -eq 'exact'){$receipt.session_state='ending'}
    return $receipt
}
