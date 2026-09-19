param([Parameter(Mandatory)][string]$SessionDirectory,[Parameter(Mandatory)][string]$PythonExe)
# Bounded, hidden, local STA owner. No listener, service registration or GUI automation.
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'lifecycle-owned.ps1')
$run=[IO.Path]::GetFullPath($SessionDirectory)
[void][IO.Directory]::CreateDirectory($run)
$init=$null;$currentRequest=$null;$sessionId=$null;$operationId=$null;$generation=$null
$revision=0;$documentId=$null;$app=$null;$doc=$null;$binding=$null;$activeContext=$null
$last=$null;$poisoned=$false;$stop=$false;$observationsComplete=$false;$bindingCurrent=$false
$keepOpen=$false;$preserveOnExit=$false;$lastSavedDocumentId=$null;$lastSavedRevision=-1
$artifacts=@{};$ownedContexts=[Collections.Generic.List[hashtable]]::new()
$born=[DateTime]::UtcNow;$lastActivity=$born
$sourceFiles=@('native-edit-loop.ps1','native_edit_loop.py','NativeChemDraw.cs','native-common.ps1','lifecycle-owned.ps1','lifecycle_controller.py')
$sourceHashes=@{}
# Source-only lifecycle repair exception. There is deliberately no environment,
# command-line or request option that enables native execution in this preview.
$nativeExecutionAllowed=$false
function Json-Write($path,$value){Write-LifecycleJson -Path $path -Value $value}
function Record($stage,$detail){
    $entry=@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;generation=$generation;operation_id=$operationId;detail=$detail}
    [IO.File]::AppendAllText((Join-Path $run 'events.jsonl'),($entry|ConvertTo-Json -Depth 100 -Compress)+"`n",[Text.UTF8Encoding]::new($false))
}
function Exception-Detail($record){
    $chain=@();$exception=$record.Exception
    while($null -ne $exception){
        $chain+=,@{type=$exception.GetType().FullName;message=$exception.Message;hresult=('0x{0:X8}' -f $exception.HResult);source=$exception.Source}
        $exception=$exception.InnerException
    }
    return @{type=$record.Exception.GetType().FullName;message=$record.Exception.Message;chain=$chain;fully_qualified_error_id=$record.FullyQualifiedErrorId;script_stack=$record.ScriptStackTrace}
}
function Is-CanonicalUuid($value){
    $parsed=[guid]::Empty
    return $value -is [string] -and [guid]::TryParseExact($value,'D',[ref]$parsed) -and $parsed.ToString() -ceq $value
}
function Current-Readiness {
    $state=if($poisoned){'unknown'}elseif($bindingCurrent -and $observationsComplete -and !$stop){'ready'}else{'not_ready'}
    return @{state=$state;document_bound=$bindingCurrent;observations_complete=$observationsComplete}
}
function Write-WorkerStatus($state,$detail=$null){
    Json-Write (Join-Path $run 'worker-status.json') @{worker_pid=$PID;worker_started_utc=$born.ToString('o');generation=$generation;
        operation_id=$operationId;session_id=$sessionId;state=$state;native_execution_enabled=$nativeExecutionAllowed;readiness=(Current-Readiness);detail=$detail;observed_at=[DateTime]::UtcNow.ToString('o')}
}
function Hash($path){return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Helper([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments){
    & $PythonExe (Join-Path $PSScriptRoot 'native_edit_loop.py') --internal @Arguments
    if($LASTEXITCODE -ne 0){throw 'Deterministic snapshot/check helper failed; see worker.log.'}
    return Get-Content -LiteralPath $Arguments[-1] -Raw|ConvertFrom-Json -AsHashtable
}
function Observe-OwnedProcess($bound){
    try{$process=Get-Process -Id $bound.pid -ErrorAction Stop}catch{
        if($_.FullyQualifiedErrorId -like 'NoProcessFoundForGivenId*'){return @{state='absent'}}
        throw
    }
    return @{state='present';pid=$process.Id;start_utc=$process.StartTime.ToUniversalTime().ToString('o');executable=$process.Path}
}
function Assert-Binding($application,$document,$bound){
    $identity=Get-LifecycleProcessState -Binding $bound -ObserveProcess ${function:Observe-OwnedProcess}
    if($identity.state -ne 'exact' -or [int][NativeChemDraw]::ApplicationProcess($application) -ne $bound.pid -or
       [long]$application.MainWindow -ne $bound.hwnd -or $application.Documents.Count -ne 1 -or
       ![NativeChemDraw]::SameIdentity($application.ActiveDocument,$document)){
        throw 'PID/start/executable/HWND/document identity guard failed.'
    }
}
function Start-Owned {
    # Retain the attempt before New-Object: Open or binding failure must not lose
    # the application reference or be mistaken for proof that nothing was made.
    $context=@{context_id=[guid]::NewGuid().ToString();generation=$generation;operation_id=$operationId;
        creation_attempted=$false;application_created=$false;application=$null;binding=$null;document=$null;document_present=$false;
        document_id=$null;revision=0;fingerprint=$null;saved_revision_verified=$false;cleanup=$null}
    $ownedContexts.Add($context)
    $prior=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|ForEach-Object {@{pid=$_.Id;start_utc=$_.StartTime.ToUniversalTime().ToString('o');hwnd=[long]$_.MainWindowHandle;executable=$_.Path}})
    Record 'owned_application_creation_intent' @{context_id=$context.context_id;executable=$exe;preexisting=$prior}
    $context.creation_attempted=$true
    $application=New-Object -ComObject ChemDraw_x64.Application
    $context.application=$application;$context.application_created=$true
    Record 'owned_application_created' @{context_id=$context.context_id}
    $fresh=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Where-Object {$_.Id -notin @($prior|ForEach-Object {$_.pid}) -and $_.Path -eq $exe})
    $nativePid=[int][NativeChemDraw]::ApplicationProcess($application)
    if($application.Documents.Count -ne 0 -or $fresh.Count -ne 1 -or $fresh[0].Id -ne $nativePid){
        throw 'Fresh owned application could not be established. Ambiguous applications are preserved.'
    }
    $bound=@{pid=$nativePid;start_utc=$fresh[0].StartTime.ToUniversalTime().ToString('o');executable=[IO.Path]::GetFullPath($fresh[0].Path);
        hwnd=[long]$application.MainWindow;initial_documents=0;preexisting=$prior}
    $context.binding=$bound
    Record 'owned_process_bound' @{context_id=$context.context_id;binding=$bound}
    return $context
}
function Close-OwnedContext($context,[bool]$detach=$false,[bool]$preserve=$false){
    # Cleanup has one effect attempt. A later caller receives its retained receipt,
    # including an ending/unknown result; it does not issue another Close or Quit.
    if($null -ne $context.cleanup){return $context.cleanup}
    $scope={
        $application=$context.application;$document=$context.document
        $count=$application.Documents.Count
        return @{retained_application=($context.application_created -and $null -ne $application);
            application_pid=[int][NativeChemDraw]::ApplicationProcess($application);hwnd=[long]$application.MainWindow;
            document_count=$count;retained_document_matches=($null -ne $document -and $count -eq 1 -and [NativeChemDraw]::SameIdentity($application.ActiveDocument,$document))}
    }
    $close={
        Assert-Binding $context.application $context.document $context.binding
        if($null -ne $context.fingerprint){
            $final=Capture (Join-Path $run ('evidence/'+$context.context_id+'-final-before-close')) $context.application $context.document $context.binding $context.document_id $context.revision
            if($final.fingerprint -cne $context.fingerprint){throw 'External change before Close; document preserved.'}
        }
        Assert-Binding $context.application $context.document $context.binding
        Record 'owned_document_close_intent' @{context_id=$context.context_id;binding=$context.binding;document_id=$context.document_id;revision=$context.revision}
        [void][NativeChemDraw]::Close($context.document)
    }
    $quit={
        Record 'owned_application_quit_intent' @{context_id=$context.context_id;binding=$context.binding}
        ([ChemDraw.IChemDrawApplication]$context.application).Quit()
    }
    $receipt=Invoke-OwnedLifecycleCleanup -Context $context -ObserveProcess ${function:Observe-OwnedProcess} -ObserveApplication $scope -CloseDocument $close -QuitApplication $quit -Detach:$detach -Preserve:$preserve
    $context.cleanup=$receipt
    [void][IO.Directory]::CreateDirectory((Join-Path $run 'lifecycle'))
    Write-LifecycleJson -Path (Join-Path $run ('lifecycle/'+$context.context_id+'.json')) -Value $receipt -NoOverwrite
    Record 'owned_cleanup_receipt' $receipt
    return $receipt
}
function Save-Native($path,$mime){
    Assert-Binding $app $doc $binding
    Record 'save_intent' @{path=$path;mime=$mime;document_id=$documentId;revision=$revision}
    $saved=[NativeChemDraw]::Save($doc,$path,$mime,200)
    Record 'save_return' $saved
    if(!$saved.Exists -or $saved.Bytes -le 0){throw 'Native save did not produce bytes.'}
    Assert-Binding $app $doc $binding
    return @{path=$path;sha256=(Hash $path);bytes=$saved.Bytes;producer='ChemDraw Document.SaveAs'}
}
function Capture([string]$base,$readApp=$app,$readDoc=$doc,$readBinding=$binding,$readDocId=$documentId,$readRevision=$revision){
    Assert-Binding $readApp $readDoc $readBinding
    $data=[NativeChemDraw]::Data($readDoc,'text/xml')
    if($data -is [byte[]]){$xml=[Text.Encoding]::UTF8.GetString($data)}else{$xml=[string]$data}
    if($xml -notmatch '<CDXML[\s>]'){throw 'Native Data(text/xml) did not return a full CDXML document.'}
    [IO.File]::WriteAllText(($base+'.cdxml'),$xml,[Text.UTF8Encoding]::new($false))
    $caps=@(foreach($c in $readDoc.Captions){
        $bounds=$c.Bounds
        @{id=[int]$c.ID;text=[string]$c.Text;anchor=@([double]$c.Position.X,[double]$c.Position.Y);
          bounds=@([double]$bounds.Left,[double]$bounds.Top,[double]$bounds.Right,[double]$bounds.Bottom);
          family=[string]$c.Family;size=[double]$c.Size;face=[int]$c.Face;angle=[double]$c.Angle;
          styles=@($c.Styles|ForEach-Object {@{family=[string]$_.Family;size=[double]$_.Size;face=[int]$_.Face}})}
    })
    $arrows=@(foreach($a in $readDoc.Arrows){@{id=[int]$a.ID;start=@([double]$a.Start.X,[double]$a.Start.Y);end=@([double]$a.End.X,[double]$a.End.Y)}})
    $raw=@{session_id=$sessionId;document_id=$readDocId;revision=$readRevision;binding=$readBinding;
        document_full_name=[string]$readDoc.FullName;bond_length=[double]$readDoc.Settings.BondLength;
        captions=$caps;arrows=$arrows;atom_ids=@($readDoc.Atoms|ForEach-Object {[int]$_.ID});bond_ids=@($readDoc.Bonds|ForEach-Object {[int]$_.ID});
        counts=@{atoms=$readDoc.Atoms.Count;bonds=$readDoc.Bonds.Count;captions=$readDoc.Captions.Count;arrows=$readDoc.Arrows.Count;splines=$readDoc.Splines.Count;symbols=$readDoc.Symbols.Count}}
    Json-Write ($base+'.native.json') $raw
    return Helper @('snapshot',$base,($base+'.snapshot.json'))
}
function Observe([string]$prefix,$movingTarget=$null,$motionPath=$null,[bool]$initialExport=$false){
    $base=Join-Path $run ('evidence/'+$prefix)
    $snap=Capture $base
    $png=Save-Native ($base+'.png') 'image/png'
    $after=Capture ($base+'-after-render')
    $compareArgs=@('compare',($base+'.snapshot.json'),($base+'-after-render.snapshot.json'))
    if($initialExport){$compareArgs=@('compare-initial-export',($base+'.snapshot.json'),($base+'-after-render.snapshot.json'))}
    elseif($null -ne $motionPath){$compareArgs=@('compare-movement-export',($base+'.snapshot.json'),($base+'-after-render.snapshot.json'),$motionPath)}
    elseif($null -ne $movingTarget){$compareArgs+=,[string]$movingTarget}
    $compareArgs+=,($base+'-render-check.json')
    $comparison=Helper -Arguments $compareArgs
    $preview=Helper @('preview',$png.path,($base+'-preview.json'))
    $after.preview=$preview;$after.snapshot_file=$base+'-after-render.snapshot.json'
    $after.export_check=$comparison
    Json-Write $after.snapshot_file $after
    $script:last=$after
    if(!$comparison.ok){$script:poisoned=$true;throw 'Native PNG export changed full object state; session frozen.'}
    $script:bindingCurrent=$true;$script:observationsComplete=$true
    if($null -ne $activeContext){$activeContext.fingerprint=$after.fingerprint;$activeContext.document_id=$documentId;$activeContext.revision=$revision}
    return $after
}
function Write-Response($request,$response){
    if($null -eq $request -or !$request.ContainsKey('request_id') -or !(Is-CanonicalUuid $request.request_id)){throw 'No safe request identity for reply publication.'}
    $response.request_id=$request.request_id;$response.session_id=$sessionId
    $response.operation_id=if($request.ContainsKey('operation_id')){$request.operation_id}else{$operationId}
    $response.generation=if($request.ContainsKey('generation')){$request.generation}else{$generation}
    $response.action=if($request.ContainsKey('action')){$request.action}else{$null}
    $response.document_id=$documentId;$response.revision=$revision
    $response.session_poisoned=$poisoned;$response.readiness=Current-Readiness
    $response.tool_source_hashes=$sourceHashes
    if($null -ne $last){$response.observation=$last}
    [void][IO.Directory]::CreateDirectory((Join-Path $run 'replies'))
    $path=Join-Path $run ('replies/'+$request.request_id+'.json')
    Write-LifecycleJson -Path $path -Value $response -NoOverwrite
    Record 'action_response' @{request_id=$request.request_id;operation_id=$response.operation_id;action=$response.action;ok=$response.ok;revision=$revision;poisoned=$poisoned}
    Write-WorkerStatus $(if($stop){'ending'}else{$response.readiness.state})
}
function Check-Source {
    if((Hash $init.source) -cne $init.source_sha256 -or (Hash $init.copy) -cne $init.source_sha256){throw 'Original/copy hash changed outside this session.'}
}
try{
    Write-WorkerStatus 'initializing'
    $init=Get-Content -LiteralPath (Join-Path $run 'init.json') -Raw|ConvertFrom-Json -AsHashtable
    if($init -isnot [hashtable] -or !$init.ContainsKey('request') -or $init.request -isnot [hashtable]){throw 'Worker initialization requires a request object.'}
    $currentRequest=$init.request
    if($currentRequest.ContainsKey('session_id') -and (Is-CanonicalUuid $currentRequest.session_id)){$sessionId=$currentRequest.session_id}
    if($currentRequest.ContainsKey('operation_id') -and (Is-CanonicalUuid $currentRequest.operation_id)){$operationId=$currentRequest.operation_id}
    if($currentRequest.ContainsKey('generation') -and (Is-CanonicalUuid $currentRequest.generation)){$generation=$currentRequest.generation}
    foreach($key in @('session_id','request_id','operation_id','generation')){
        if(!$currentRequest.ContainsKey($key) -or !(Is-CanonicalUuid $currentRequest[$key])){throw ('Invalid worker request identity: '+$key)}
    }
    $sessionId=$currentRequest.session_id;$operationId=$currentRequest.operation_id;$generation=$currentRequest.generation
    if(!$init.ContainsKey('operation_id') -or !$init.ContainsKey('generation') -or $init.operation_id -cne $operationId -or $init.generation -cne $generation -or
       !$currentRequest.ContainsKey('action') -or $currentRequest.action -cne 'open-copy'){throw 'Worker startup identity or action does not match its request.'}
    foreach($name in $sourceFiles){$sourceHashes[$name]=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $name)).Hash.ToLowerInvariant()}
    Write-WorkerStatus 'not_ready'
    if(!$nativeExecutionAllowed){
        Write-Response $currentRequest @{ok=$false;status='refused';reason='native_execution_frozen';native_write=$false;native_execution_enabled=$false}
        Write-WorkerStatus 'native_execution_frozen'
        return
    }
    # This point remains unreachable until a separately reviewed source change.
    . (Join-Path $PSScriptRoot 'native-common.ps1')
    $documentId=[guid]::NewGuid().ToString()
    Record 'worker_start' @{worker_pid=$PID;start_utc=$born.ToString('o');source_role=$init.request.role;source_sha256=$init.source_sha256;idle_limit_seconds=$init.max_idle_seconds}
    $exe=Initialize-NativeInterop
    Record 'environment' @{executable_sha256=(Hash $exe);interop_sha256=(Hash (Join-Path (Split-Path $exe) 'Interop.ChemDraw.dll'));native_version=(Get-Item -LiteralPath $exe).VersionInfo.FileVersion;signature='Valid'}
    Check-Source
    $activeContext=Start-Owned;$app=$activeContext.application;$binding=$activeContext.binding
    $mime=if([IO.Path]::GetExtension($init.copy) -eq '.cdx'){'chemical/x-cdx'}else{'text/xml'}
    $doc=[NativeChemDraw]::Open($app,$init.copy,$mime)
    $activeContext.document=$doc;$activeContext.document_present=$true;$activeContext.document_id=$documentId
    if(![NativeChemDraw]::ActivateAndVerify($app,$doc)){throw 'Native document activation/identity failed.'}
    $initial=Observe ($init.request.request_id+'-initial') $null $null $true
    # The baseline is the post-initial-export state. Repeat with the ordinary
    # strict checker: initial AS/BS normalization is never allowed on later edits.
    $last=Observe ($init.request.request_id+'-opened-stable')
    $stability=Helper @('compare',$initial.snapshot_file,$last.snapshot_file,(Join-Path $run 'evidence/open-baseline-stability.json'))
    if(!$stability.ok){throw 'Initial native export did not establish a stable complete-object baseline.'}
    Write-Response $init.request @{ok=$true;status='opened-copy';native_write='copy/open/export only';source_sha256=$init.source_sha256;role=$init.request.role;initial_native_normalization=$initial.export_check;baseline_stability=$stability}
    :requests while(!$stop -and ([DateTime]::UtcNow-$lastActivity).TotalSeconds -lt $init.max_idle_seconds -and ([DateTime]::UtcNow-$born).TotalHours -lt 2){
        $pending=@(Get-ChildItem -LiteralPath (Join-Path $run 'inbox') -Filter '*.json'|Where-Object {!(Test-Path -LiteralPath (Join-Path $run ('replies/'+$_.Name)))}|Sort-Object CreationTimeUtc)
        if($pending.Count -eq 0){Start-Sleep -Milliseconds 120;continue requests}
        $requestPath=$pending[0].FullName;$q=Get-Content -LiteralPath $requestPath -Raw|ConvertFrom-Json -AsHashtable
        $lastActivity=[DateTime]::UtcNow;$writeStarted=$false;$observationsComplete=$false;$bindingCurrent=$false
        $currentRequest=$q
        try{
            foreach($key in @('request_id','operation_id','generation')){if(!$q.ContainsKey($key) -or !(Is-CanonicalUuid $q[$key])){throw ('Invalid inbox identity: '+$key)}}
            $operationId=$q.operation_id
            if($q.generation -cne $generation){Write-Response $q @{ok=$false;reason='Wrong worker generation; no write';native_write=$false};continue requests}
            if($q.session_id -cne $sessionId -or $q.document_id -cne $documentId -or $q.revision -ne $revision){
                Write-Response $q @{ok=$false;reason='Wrong session/document/revision; no write';native_write=$false;observation_kind='last verified'};continue requests
            }
            Check-Source
            if($q.action -ne 'inspect'){
                foreach($name in $sourceFiles){if((Hash (Join-Path $PSScriptRoot $name)) -cne $sourceHashes[$name]){throw 'Tool source changed during retained session; start a new explicit copy.'}}
            }
            $pre=Capture (Join-Path $run ('evidence/'+$q.request_id+'-pre'))
            if($pre.fingerprint -cne $last.fingerprint){
                $poisoned=$true;$preserveOnExit=$true;$revision++;$last=Observe ($q.request_id+'-external-change')
                Write-Response $q @{ok=$false;reason='External object state change detected; revision advanced and mutation locked';native_write=$false};continue requests
            }
            if($q.action -ne 'inspect' -and ($poisoned -or (Test-Path -LiteralPath (Join-Path $run 'UNCERTAIN.json')))){
                Write-Response $q @{ok=$false;reason='Session frozen after failure/deadline; no blind retry';native_write=$false};continue requests
            }
            $detail=@{}
            switch($q.action){
                'inspect' {
                    $pendingKeepOpen=$q.ContainsKey('keep_open') -and $q.keep_open
                    if($pendingKeepOpen){
                        if(!$q.ContainsKey('end_session') -or !$q.end_session -or $poisoned -or $lastSavedDocumentId -cne $documentId -or $lastSavedRevision -ne $revision){throw 'keep_open requires end_session and this exact current saved document revision.'}
                    }
                    $last=Observe ($q.request_id+'-inspect')
                    if($pendingKeepOpen){
                        if($poisoned -or $q.revision -ne $revision -or $q.document_id -cne $documentId -or $lastSavedDocumentId -cne $documentId -or $lastSavedRevision -ne $revision -or $last.fingerprint -cne $pre.fingerprint){
                            $preserveOnExit=$true;throw 'Final saved-revision observation failed; no ownership transfer committed.'
                        }
                        # Commit detach and stop only after a successful final observation.
                        $activeContext.saved_revision_verified=$true;$keepOpen=$true;$stop=$true
                    }
                    if($q.ContainsKey('end_session') -and $q.end_session){$stop=$true;$detail.session_ending=$true;$detail.keep_open=$keepOpen}
                }
                'relative-position' {
                    if($init.request.role -eq 'no-edit-control'){Write-Response $q @{ok=$false;reason='No-edit control forbids object writes';native_write=$false};continue requests}
                    $planPath=Join-Path $run ('evidence/'+$q.request_id+'-plan.json')
                    $motion=Helper @('plan',$requestPath,($pre.xml -replace '\.cdxml$','.snapshot.json'),$planPath)
                    if(!$motion.ok){$last=Observe ($q.request_id+'-refused');Write-Response $q @{ok=$false;reason=$motion.reason;native_write=$false;candidates=$motion.candidates};continue requests}
                    $matches=@($doc.Captions|Where-Object {$_.ID -eq $motion.caption_id})
                    if($matches.Count -ne 1){throw 'Caption identity is no longer unique.'}
                    # Re-read immediately before the sole native object write.
                    $ready=Capture (Join-Path $run ('evidence/'+$q.request_id+'-ready'))
                    if($ready.fingerprint -cne $pre.fingerprint -or (Test-Path -LiteralPath (Join-Path $run 'UNCERTAIN.json'))){throw 'Pre-write state/deadline changed; not replayed.'}
                    Record 'position_intent' $motion
                    $writeStarted=$true
                    [NativeChemDraw]::Position($matches[0],[double]$motion.computed_anchor[0],[double]$motion.computed_anchor[1])
                    $revision++;$last=Observe ($q.request_id+'-positioned') $motion.caption_id $planPath
                    $check=Helper @('verify-move',($pre.xml -replace '\.cdxml$','.snapshot.json'),$last.snapshot_file,$planPath,(Join-Path $run ('evidence/'+$q.request_id+'-check.json')))
                    $detail.motion=$motion;$detail.verification=$check
                    if(!$check.ok){$poisoned=$true;Write-Response $q @{ok=$false;reason='Post-write full object/position check failed; evidence preserved, session frozen';native_write=$true;detail=$detail};continue requests}
                }
                'save' {
                    if($q.stem -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$'){throw 'Use a new simple output stem.'}
                    foreach($ext in @('cdxml','cdx')){if(Test-Path -LiteralPath (Join-Path $run ('saved/'+$q.stem+'.'+$ext))){throw 'Refusing to overwrite a saved artifact.'}}
                    $written=@();$writeStarted=$true
                    foreach($ext in @('cdxml','cdx')){
                        if(Test-Path -LiteralPath (Join-Path $run 'UNCERTAIN.json')){throw 'Deadline expired; no additional save attempted.'}
                        $mime=if($ext -eq 'cdx'){'chemical/x-cdx'}else{'text/xml'}
                        $file=Save-Native (Join-Path $run ('saved/'+$q.stem+'.'+$ext)) $mime
                        $aid=[guid]::NewGuid().ToString();$file.artifact_id=$aid;$file.format=$ext;$file.saved_document_id=$documentId;$file.saved_revision=$revision
                        $artifacts[$aid]=$file;$written+=,$file
                    }
                    $revision++;$last=Observe ($q.request_id+'-saved')
                    $lastSavedDocumentId=$documentId;$lastSavedRevision=$revision
                    foreach($file in $written){$artifacts[$file.artifact_id].snapshot_file=$last.snapshot_file}
                    Json-Write (Join-Path $run 'artifacts.json') $artifacts
                    $detail.artifacts=$written
                    $detail.normalization=Helper @('compare',($pre.xml -replace '\.cdxml$','.snapshot.json'),$last.snapshot_file,(Join-Path $run ('evidence/'+$q.request_id+'-save-normalization.json')))
                }
                'reopen' {
                    if(!$artifacts.ContainsKey($q.artifact_id)){throw 'Artifact must be a file saved by this session.'}
                    $file=$artifacts[$q.artifact_id]
                    if((Hash $file.path) -cne $file.sha256){throw 'Saved artifact bytes changed; refusing reopen.'}
                    $oldDoc=$doc;$oldApp=$app;$oldBinding=$binding;$oldContext=$activeContext
                    Assert-Binding $oldApp $oldDoc $oldBinding
                    $started=Start-Owned
                    if($started.binding.pid -eq $oldBinding.pid){throw 'Reopen requires a different fresh native process.'}
                    $newApp=$started.application;$newBinding=$started.binding;$newDoc=$null;$newContext=$started
                    $newDocId=[guid]::NewGuid().ToString();$newRevision=$revision+1
                    try{
                        $mime=if($file.format -eq 'cdx'){'chemical/x-cdx'}else{'text/xml'}
                        $newDoc=[NativeChemDraw]::Open($newApp,$file.path,$mime)
                        $newContext.document=$newDoc;$newContext.document_present=$true;$newContext.document_id=$newDocId;$newContext.revision=$newRevision
                        if([NativeChemDraw]::SameIdentity($oldDoc,$newDoc) -or ![NativeChemDraw]::ActivateAndVerify($newApp,$newDoc)){throw 'Fresh reopened document identity failed.'}
                        $newSnap=Capture (Join-Path $run ('evidence/'+$q.request_id+'-pending-new')) $newApp $newDoc $newBinding $newDocId $newRevision
                        $newContext.fingerprint=$newSnap.fingerprint
                        # Re-read the OLD retained document immediately before closing it.
                        $oldReady=Capture (Join-Path $run ('evidence/'+$q.request_id+'-old-before-close'))
                        if($oldReady.fingerprint -cne $pre.fingerprint -or (Test-Path -LiteralPath (Join-Path $run 'UNCERTAIN.json'))){$poisoned=$true;$preserveOnExit=$true;throw 'Old revision/deadline changed during reopen; no old document close.'}
                    }catch{
                        $poisoned=$true;$preserveOnExit=$true
                        try{[void](Close-OwnedContext $newContext)}catch{Record 'pending_new_cleanup_failure' (Exception-Detail $_)}
                        throw
                    }
                    # Commit the complete verified new binding together. A later
                    # old-process close failure cannot create a mixed context.
                    $app=$newApp;$doc=$newDoc;$binding=$newBinding;$documentId=$newDocId;$revision=$newRevision;$activeContext=$newContext
                    # Close only the retained old document. No HWND assumption after Close.
                    try{
                        $oldCleanup=Close-OwnedContext $oldContext
                        $detail.previous_lifecycle=$oldCleanup
                        if(!$oldCleanup.observed_process_exit){$detail.old_close_warning='Previous owned application exit remains unconfirmed.'}
                    }catch{Record 'old_close_failure_new_context_retained' (Exception-Detail $_);$detail.old_close_warning=$_.Exception.Message}
                    $last=Observe ($q.request_id+'-reopened')
                    $lastSavedDocumentId=$documentId;$lastSavedRevision=$revision
                    $detail.reopened_artifact=$file;$detail.previous_binding=$oldBinding
                    $detail.normalization=Helper @('compare',$file.snapshot_file,$last.snapshot_file,(Join-Path $run ('evidence/'+$q.request_id+'-reopen-normalization.json')))
                }
                default {throw 'Unknown action.'}
            }
            Check-Source
            Write-Response $q @{ok=$true;status=$q.action;detail=$detail;native_write=$writeStarted}
        }catch{
            $observationsComplete=$false;$bindingCurrent=$false
            if($writeStarted){$poisoned=$true}
            Record 'action_failure' (Exception-Detail $_)
            Write-Response $q @{ok=$false;reason=$_.Exception.Message;native_write_started=$writeStarted;observation_kind='last verified';failure=(Exception-Detail $_)}
        }
    }
}catch{
    $poisoned=$true;$observationsComplete=$false;$bindingCurrent=$false
    $failure=Exception-Detail $_
    Record 'worker_failure' $failure
    Write-WorkerStatus 'failed' $failure
    if($null -ne $currentRequest -and $currentRequest.ContainsKey('request_id') -and (Is-CanonicalUuid $currentRequest.request_id) -and
       !(Test-Path -LiteralPath (Join-Path $run ('replies/'+$currentRequest.request_id+'.json')))){
        Write-Response $currentRequest @{ok=$false;reason=$failure.message;failure=$failure}
    }
}finally{
    $closed=@{utc=[DateTime]::UtcNow.ToString('o');generation=$generation;operation_id=$operationId;session_id=$sessionId;
        poisoned=$poisoned;source_unchanged=$null;owned_binding=$binding;applications=@();session_state='not_created';
        document_close_returned=$false;application_quit_returned=$false;observed_process_exit=$false;native_execution_enabled=$false}
    if($nativeExecutionAllowed -and $null -ne $init){
        try{Check-Source;$closed.source_unchanged=$true}catch{$closed.source_unchanged=$false;$closed.source_error=$_.Exception.Message}
    }
    foreach($context in $ownedContexts){
        try{
            $isActive=[object]::ReferenceEquals($context,$activeContext)
            $receipt=Close-OwnedContext $context ($isActive -and $keepOpen) ($isActive -and $preserveOnExit)
            $closed.applications+=,$receipt
        }catch{
            $closed.applications+=,@{context_id=$context.context_id;generation=$generation;operation_id=$context.operation_id;
                session_state='unknown';observed_process_exit=$false;document_close_returned=$false;application_quit_returned=$false;error=$_.Exception.Message}
        }
        foreach($reference in @($context.document,$context.application)){
            if($null -ne $reference -and [Runtime.InteropServices.Marshal]::IsComObject($reference)){
                try{[void][Runtime.InteropServices.Marshal]::ReleaseComObject($reference)}catch{Record 'com_release_failure' (Exception-Detail $_)}
            }
        }
    }
    if($closed.applications.Count -gt 0){
        $states=@($closed.applications|ForEach-Object {$_.session_state})
        $closed.session_state=if('unknown' -in $states){'unknown'}elseif('ending' -in $states){'ending'}elseif('detached' -in $states){'detached'}elseif('closed' -in $states){'closed'}else{'not_created'}
        $closed.document_close_returned=@($closed.applications|Where-Object {$_.document_close_returned}).Count -gt 0
        $closed.application_quit_returned=@($closed.applications|Where-Object {$_.application_quit_returned}).Count -gt 0
        $created=@($closed.applications|Where-Object {$_.session_state -ne 'not_created'})
        $closed.observed_process_exit=$created.Count -gt 0 -and @($created|Where-Object {!$_.observed_process_exit}).Count -eq 0
    }
    if($keepOpen){$closed.detached_saved_document=$true;$closed.ownership_transferred_to_user=($closed.session_state -eq 'detached')}
    if($preserveOnExit){$closed.external_or_uncertain_state_preserved=$true}
    $observationsComplete=$false;$bindingCurrent=$false
    # This is a receipt container, not a claim that Close/Quit implies process exit.
    Write-LifecycleJson -Path (Join-Path $run 'closed.json') -Value $closed -NoOverwrite
    Write-WorkerStatus $closed.session_state @{receipt='closed.json';observed_process_exit=$closed.observed_process_exit}
    Record 'worker_ended' $closed
}
