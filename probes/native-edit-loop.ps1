param([Parameter(Mandatory)][string]$SessionDirectory,[Parameter(Mandatory)][string]$PythonExe)
# Bounded, hidden, local STA owner. No listener, service registration or GUI automation.
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'native-common.ps1')
$run=[IO.Path]::GetFullPath($SessionDirectory)
$init=Get-Content -LiteralPath (Join-Path $run 'init.json') -Raw|ConvertFrom-Json -AsHashtable
$sessionId=$init.request.session_id;$revision=0;$documentId=[guid]::NewGuid().ToString()
$app=$null;$doc=$null;$binding=$null;$last=$null;$poisoned=$false;$stop=$false
$keepOpen=$false;$preserveOnExit=$false;$lastSavedDocumentId=$null;$lastSavedRevision=-1
$artifacts=@{};$allApplications=[Collections.Generic.List[object]]::new()
$born=[DateTime]::UtcNow;$lastActivity=$born
$sourceFiles=@('native-edit-loop.ps1','native_edit_loop.py','NativeChemDraw.cs','native-common.ps1')
$sourceHashes=@{}
foreach($name in $sourceFiles){$sourceHashes[$name]=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $name)).Hash.ToLowerInvariant()}
function Json-Write($path,$value){
    [IO.File]::WriteAllText($path,($value|ConvertTo-Json -Depth 100),[Text.UTF8Encoding]::new($false))
}
function Record($stage,$detail){
    $entry=@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;detail=$detail}
    [IO.File]::AppendAllText((Join-Path $run 'events.jsonl'),($entry|ConvertTo-Json -Depth 100 -Compress)+"`n",[Text.UTF8Encoding]::new($false))
}
function Hash($path){return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Helper([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments){
    & $PythonExe (Join-Path $PSScriptRoot 'native_edit_loop.py') --internal @Arguments
    if($LASTEXITCODE -ne 0){throw 'Deterministic snapshot/check helper failed; see worker.log.'}
    return Get-Content -LiteralPath $Arguments[-1] -Raw|ConvertFrom-Json -AsHashtable
}
function Assert-Binding($application,$document,$bound){
    $process=Get-Process -Id $bound.pid
    if([int][NativeChemDraw]::ApplicationProcess($application) -ne $bound.pid -or
       [long]$application.MainWindow -ne $bound.hwnd -or
       $process.StartTime.ToUniversalTime().ToString('o') -cne $bound.start_utc -or
       $application.Documents.Count -ne 1 -or
       ![NativeChemDraw]::SameIdentity($application.ActiveDocument,$document)){
        throw 'PID/start/HWND/document identity guard failed.'
    }
}
function Start-Owned {
    $prior=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|ForEach-Object {@{pid=$_.Id;start_utc=$_.StartTime.ToUniversalTime().ToString('o');hwnd=[long]$_.MainWindowHandle}})
    $application=New-Object -ComObject ChemDraw_x64.Application
    $allApplications.Add($application)
    $fresh=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Where-Object {$_.Id -notin @($prior|ForEach-Object {$_.pid}) -and $_.Path -eq $exe})
    $nativePid=[int][NativeChemDraw]::ApplicationProcess($application)
    if($application.Documents.Count -ne 0 -or $fresh.Count -ne 1 -or $fresh[0].Id -ne $nativePid){
        throw 'Fresh owned application could not be established. No preexisting document may be used.'
    }
    $bound=@{pid=$nativePid;start_utc=$fresh[0].StartTime.ToUniversalTime().ToString('o');hwnd=[long]$application.MainWindow;initial_documents=0;preexisting=$prior}
    Record 'owned_process_bound' $bound
    return @{application=$application;binding=$bound}
}
function Quit-EmptyOwned($application,$bound,$retainedDocument=$null){
    # A last-document close may destroy/change HWND. Ownership ends at the last
    # verified document observation; require retained app, exact PID/start and no
    # documents before graceful Quit. Never reconnect to a released process.
    $process=Get-Process -Id $bound.pid -ErrorAction SilentlyContinue
    $empty=$application.Documents.Count -eq 0
    $onlyRetained=$null -ne $retainedDocument -and $application.Documents.Count -eq 1 -and [NativeChemDraw]::SameIdentity($application.ActiveDocument,$retainedDocument)
    if($null -ne $process -and $process.StartTime.ToUniversalTime().ToString('o') -ceq $bound.start_utc -and ($empty -or $onlyRetained)){
        Record 'quit_empty_owned_intent' $bound
        ([ChemDraw.IChemDrawApplication]$application).Quit()
        Record 'quit_empty_owned_return' $bound
    }
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
    return $after
}
function Write-Response($request,$response){
    $response.request_id=$request.request_id;$response.session_id=$sessionId
    $response.document_id=$documentId;$response.revision=$revision
    $response.session_poisoned=$poisoned
    $response.tool_source_hashes=$sourceHashes
    if($null -ne $last){$response.observation=$last}
    $path=Join-Path $run ('replies/'+$request.request_id+'.json')
    Json-Write ($path+'.tmp') $response
    [IO.File]::Move(($path+'.tmp'),$path)
    Record 'action_response' @{request_id=$request.request_id;action=$request.action;ok=$response.ok;revision=$revision;poisoned=$poisoned}
}
function Check-Source {
    if((Hash $init.source) -cne $init.source_sha256 -or (Hash $init.copy) -cne $init.source_sha256){throw 'Original/copy hash changed outside this session.'}
}
try{
    Record 'worker_start' @{worker_pid=$PID;start_utc=$born.ToString('o');source_role=$init.request.role;source_sha256=$init.source_sha256;idle_limit_seconds=$init.max_idle_seconds}
    $exe=Initialize-NativeInterop
    Record 'environment' @{executable_sha256=(Hash $exe);interop_sha256=(Hash (Join-Path (Split-Path $exe) 'Interop.ChemDraw.dll'));native_version=(Get-Item -LiteralPath $exe).VersionInfo.FileVersion;signature='Valid'}
    Check-Source
    $started=Start-Owned;$app=$started.application;$binding=$started.binding
    $mime=if([IO.Path]::GetExtension($init.copy) -eq '.cdx'){'chemical/x-cdx'}else{'text/xml'}
    $doc=[NativeChemDraw]::Open($app,$init.copy,$mime)
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
        $lastActivity=[DateTime]::UtcNow;$writeStarted=$false
        try{
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
                        $keepOpen=$true;$stop=$true
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
                    $oldDoc=$doc;$oldApp=$app;$oldBinding=$binding
                    Assert-Binding $oldApp $oldDoc $oldBinding
                    $started=Start-Owned
                    if($started.binding.pid -eq $oldBinding.pid){throw 'Reopen requires a different fresh native process.'}
                    $newApp=$started.application;$newBinding=$started.binding;$newDoc=$null
                    $newDocId=[guid]::NewGuid().ToString();$newRevision=$revision+1
                    try{
                        $mime=if($file.format -eq 'cdx'){'chemical/x-cdx'}else{'text/xml'}
                        $newDoc=[NativeChemDraw]::Open($newApp,$file.path,$mime)
                        if([NativeChemDraw]::SameIdentity($oldDoc,$newDoc) -or ![NativeChemDraw]::ActivateAndVerify($newApp,$newDoc)){throw 'Fresh reopened document identity failed.'}
                        $newSnap=Capture (Join-Path $run ('evidence/'+$q.request_id+'-pending-new')) $newApp $newDoc $newBinding $newDocId $newRevision
                        # Re-read the OLD retained document immediately before closing it.
                        $oldReady=Capture (Join-Path $run ('evidence/'+$q.request_id+'-old-before-close'))
                        if($oldReady.fingerprint -cne $pre.fingerprint -or (Test-Path -LiteralPath (Join-Path $run 'UNCERTAIN.json'))){$poisoned=$true;$preserveOnExit=$true;throw 'Old revision/deadline changed during reopen; no old document close.'}
                    }catch{
                        $poisoned=$true;$preserveOnExit=$true
                        if($null -ne $newDoc){try{Assert-Binding $newApp $newDoc $newBinding;[NativeChemDraw]::Close($newDoc);Quit-EmptyOwned $newApp $newBinding $newDoc}catch{Record 'pending_new_cleanup_failure' (Get-NativeException $_)}}
                        else{try{Quit-EmptyOwned $newApp $newBinding}catch{Record 'pending_empty_cleanup_failure' (Get-NativeException $_)}}
                        throw
                    }
                    # Commit the complete verified new binding together. A later
                    # old-process close failure cannot create a mixed context.
                    $app=$newApp;$doc=$newDoc;$binding=$newBinding;$documentId=$newDocId;$revision=$newRevision
                    # Close only the retained old document. No HWND assumption after Close.
                    try{
                        [NativeChemDraw]::Close($oldDoc)
                        Record 'old_document_close_return' @{last_verified_binding=$oldBinding;binding_end='before Close'}
                        Record 'post_close_documents' @{binding=$oldBinding;count=$oldApp.Documents.Count}
                        Quit-EmptyOwned $oldApp $oldBinding $oldDoc
                        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($oldDoc)
                    }catch{Record 'old_close_failure_new_context_retained' (Get-NativeException $_);$detail.old_close_warning=$_.Exception.Message}
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
            if($writeStarted){$poisoned=$true}
            Record 'action_failure' (Get-NativeException $_)
            Write-Response $q @{ok=$false;reason=$_.Exception.Message;native_write_started=$writeStarted;observation_kind='last verified';failure=(Get-NativeException $_)}
        }
    }
}catch{
    $poisoned=$true
    Record 'worker_failure' (Get-NativeException $_)
    if(!(Test-Path -LiteralPath (Join-Path $run ('replies/'+$init.request.request_id+'.json')))){
        Write-Response $init.request @{ok=$false;reason=$_.Exception.Message;failure=(Get-NativeException $_)}
    }
}finally{
    $closed=@{utc=[DateTime]::UtcNow.ToString('o');poisoned=$poisoned;source_unchanged=$false;owned_binding=$binding}
    try{Check-Source;$closed.source_unchanged=$true}catch{$closed.source_error=$_.Exception.Message}
    if($keepOpen){$closed.detached_saved_document=$true;$closed.document_full_name=[string]$doc.FullName;$closed.ownership_transferred_to_user=$true}
    if($preserveOnExit){$closed.external_or_uncertain_state_preserved=$true}
    if($null -ne $doc -and !$keepOpen -and !$preserveOnExit){
        try{
            Assert-Binding $app $doc $binding
            if($null -ne $last){$endSnap=Capture (Join-Path $run 'evidence/final-before-close');if($endSnap.fingerprint -cne $last.fingerprint){throw 'External change before close; leave document open.'}}
            [NativeChemDraw]::Close($doc);$closed.native_close_returned=$true;$closed.documents_after_close=$app.Documents.Count
            Quit-EmptyOwned $app $binding $doc
        }catch{$closed.close_error=$_.Exception.Message}
        if([Runtime.InteropServices.Marshal]::IsComObject($doc)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc)}
    }
    foreach($application in $allApplications){if([Runtime.InteropServices.Marshal]::IsComObject($application)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($application)}}
    Json-Write (Join-Path $run 'closed.json') $closed
    Record 'worker_closed' $closed
}
