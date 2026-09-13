param(
    [Parameter(Mandatory)][string]$InputDirectory,
    [Parameter(Mandatory)][string]$OutputDirectory,
    [Parameter(Mandatory)][string]$SourceFreeze
)
# New v1 executor. All previous native-ir-fragments artifacts keep their scope.
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$repoRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$freezeFile=Get-Item -LiteralPath $SourceFreeze
$freeze=Get-Content -LiteralPath $freezeFile.FullName -Raw|ConvertFrom-Json
function Assert-FrozenSource {
    if($freeze.version -ne 'native-semantic-source-freeze/1.0'){throw 'Wrong source freeze version.'}
    $seen=@{}
    foreach($entry in (@($freeze.sources)+@($freeze.inputs))){
        $path=[IO.Path]::GetFullPath((Join-Path $repoRoot $entry.file))
        if([IO.Path]::IsPathRooted($entry.file) -or !$path.StartsWith($repoRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $seen.ContainsKey($entry.file)){throw 'Invalid or duplicate source path.'}
        if((Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() -cne $entry.sha256){throw ('Frozen source bytes changed: '+$entry.file)}
        $seen[$entry.file]=$true
    }
    foreach($required in @('probes/native-semantic-fragments.ps1','probes/native-atom-observation.ps1','probes/native-common.ps1','probes/NativeChemDraw.cs','runtime/native_semantic_profile.json','runtime/native_semantics.py','runtime/native_source_binding.py')){
        if(!$seen.ContainsKey($required)){throw ('Missing frozen source: '+$required)}
    }
    if((Get-FileHash -LiteralPath (Join-Path $repoRoot 'runtime/native_semantic_profile.json')).Hash.ToLowerInvariant() -cne $freeze.profile_sha256){throw 'Profile hash mismatch.'}
}
Assert-FrozenSource
$freezeHash=(Get-FileHash -LiteralPath $freezeFile.FullName).Hash.ToLowerInvariant()
. (Join-Path $PSScriptRoot 'native-common.ps1')
. (Join-Path $PSScriptRoot 'native-atom-observation.ps1')
$run=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $run){throw 'Output exists; preserve and review the first attempt.'}
[void][IO.Directory]::CreateDirectory($run)
$cleanFolder=Join-Path $run 'clean';[void][IO.Directory]::CreateDirectory($cleanFolder)
function Record($stage,$detail){
    [ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;detail=$detail}|ConvertTo-Json -Depth 30 -Compress|Add-Content -LiteralPath (Join-Path $run 'events.jsonl') -Encoding utf8
    Write-Host $stage
}
function Hash([string]$path){return (Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()}
function Assert-Bound($application,$binding,[int]$documents){
    $process=Get-Process -Id $binding.pid
    if([NativeChemDraw]::ApplicationProcess($application) -ne $binding.pid -or [long]$application.MainWindow -ne $binding.hwnd -or $process.StartTime.ToUniversalTime().ToString('o') -cne $binding.os_start_utc -or $application.Documents.Count -ne $documents){throw 'Native process/document identity changed.'}
}
function Start-OwnedApplication([string]$phase){
    $prior=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
    $application=New-Object -ComObject ChemDraw_x64.Application
    $applications.Add($application)
    $new=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Where-Object {$_.Id -notin $prior -and $_.Path -eq $exe})
    $boundPid=[int][NativeChemDraw]::ApplicationProcess($application)
    if($new.Count -ne 1 -or $boundPid -ne $new[0].Id -or $application.Documents.Count -ne 0){throw 'Fresh initially empty native process not established.'}
    $binding=[ordered]@{job_id=$receipt.run_id;phase=$phase;pid=$boundPid;hwnd_bound_pid=$boundPid;hwnd=[long]$application.MainWindow;os_start_utc=$new[0].StartTime.ToUniversalTime().ToString('o');preexisting_pids=$prior;initial_documents=0;fresh_process=$true}
    Record 'native_process_bound' $binding
    return @{application=$application;binding=$binding}
}
function Save-Observed($doc,[string]$path,$application,$binding){
    Assert-Bound $application $binding 1
    $saved=[NativeChemDraw]::Save($doc,$path,'text/xml',600)
    Record 'save_return' $saved
    if(!$saved.Exists -or $saved.Bytes -le 0){throw 'Native file missing.'}
    Assert-Bound $application $binding 1
}
$applications=[Collections.Generic.List[object]]::new();$owned=[Collections.Generic.List[object]]::new();$failed=$false
$manifestPath=Join-Path $InputDirectory 'geometry-manifest.json';$seedPath=Join-Path $InputDirectory 'seed-provenance.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
$seed=Get-Content -LiteralPath $seedPath -Raw|ConvertFrom-Json
$receipt=[ordered]@{version='native-geometry-receipt/0.2';status='running';operation='ChemDraw.Objects.Clean(true)';run_id=[guid]::NewGuid().ToString();started_utc=[DateTime]::UtcNow.ToString('o');source_freeze_sha256=$freezeHash;manifest_sha256=(Hash $manifestPath);seed_provenance_sha256=(Hash $seedPath);environment=$null;artifacts=@()}
$receiptPath=Join-Path $run 'native-geometry-receipt.json'
function Write-Receipt {$receipt|ConvertTo-Json -Depth 35|Set-Content -LiteralPath $receiptPath -Encoding utf8}
Write-Receipt
try{
    $exe=Initialize-NativeInterop;$interop=Join-Path (Split-Path $exe) 'Interop.ChemDraw.dll'
    $environment=[ordered]@{application_build=(Get-Item -LiteralPath $exe).VersionInfo.FileVersion;interop_version=(Get-Item -LiteralPath $interop).VersionInfo.FileVersion;executable_sha256=(Hash $exe);interop_sha256=(Hash $interop);executor_sha256=(Hash $PSCommandPath);atom_observer_sha256=(Hash (Join-Path $PSScriptRoot 'native-atom-observation.ps1'));common_sha256=(Hash (Join-Path $PSScriptRoot 'native-common.ps1'));bridge_sha256=(Hash (Join-Path $PSScriptRoot 'NativeChemDraw.cs'))}
    $profile=Get-Content -LiteralPath (Join-Path $repoRoot 'runtime/native_semantic_profile.json') -Raw|ConvertFrom-Json
    foreach($key in @('application_build','interop_version','executable_sha256','interop_sha256')){if($environment[$key] -cne $profile.$key){throw ('Native build outside freeze: '+$key)}}
    $receipt.environment=$environment;Write-Receipt
    foreach($entry in $manifest){
        Assert-FrozenSource
        if([IO.Path]::GetFileName($entry.file) -ne $entry.file -or [IO.Path]::GetExtension($entry.file) -ne '.cdxml'){throw 'Invalid seed filename.'}
        $file=Get-Item -LiteralPath (Join-Path $InputDirectory $entry.file)
        $inputHash=Hash $file.FullName
        $seedEntries=@($seed.inputs|Where-Object {$_.file -ceq $entry.file})
        if($seedEntries.Count -ne 1 -or $seedEntries[0].sha256 -cne $inputHash){throw 'Seed bytes do not match the declared input.'}
        $first=Start-OwnedApplication 'cleanup';$app=$first.application
        Record 'open_intent' @{file=$entry.file;sha256=$inputHash;phase='cleanup'}
        $doc=[NativeChemDraw]::Open($app,$file.FullName,'text/xml');$owned.Add($doc)
        $beforePath=Join-Path $run ($file.BaseName+'-before.cdxml')
        Save-Observed $doc $beforePath $app $first.binding
        Record 'cleanup_intent' @{file=$entry.file;atoms=$doc.Atoms.Count;bonds=$doc.Bonds.Count}
        $doc.Objects.Clean($true);$warnings=[int]$doc.NumChemicalWarnings
        $cleanPath=Join-Path $cleanFolder $entry.file
        Save-Observed $doc $cleanPath $app $first.binding
        $cleanReadback=Write-NativeAtomObservation $doc $cleanPath $first.binding $environment $freezeHash $receipt.run_id 'cleanup'
        Assert-Bound $app $first.binding 1
        [NativeChemDraw]::Close($doc);Assert-Bound $app $first.binding 0
        $second=Start-OwnedApplication 'fresh_process_reopen';$reopenApp=$second.application
        if($first.binding.pid -eq $second.binding.pid){throw 'Reopen is not a different fresh native process.'}
        Record 'reopen_intent' @{file=$entry.file;sha256=(Hash $cleanPath);clean_pid=$first.binding.pid;reopen_pid=$second.binding.pid;cleanup_on_reopen=$false}
        $reopened=[NativeChemDraw]::Open($reopenApp,$cleanPath,'text/xml');$owned.Add($reopened)
        if([NativeChemDraw]::SameIdentity($doc,$reopened)){throw 'Fresh process reused the retained document identity.'}
        $outputPath=Join-Path $run $entry.file
        Save-Observed $reopened $outputPath $reopenApp $second.binding
        $reopenWarnings=[int]$reopened.NumChemicalWarnings
        $readback=Write-NativeAtomObservation $reopened $outputPath $second.binding $environment $freezeHash $receipt.run_id 'fresh_process_reopen'
        Assert-Bound $reopenApp $second.binding 1
        [NativeChemDraw]::Close($reopened);Assert-Bound $reopenApp $second.binding 0
        if((Hash $file.FullName) -cne $inputHash){throw 'Original seed changed.'}
        $artifact=[ordered]@{file=$entry.file;input_sha256=$inputHash;before_sha256=(Hash $beforePath);output_sha256=(Hash $outputPath);cleanup_completed=$true;warnings=$warnings;reopen_warnings=$reopenWarnings;cleanup_file=('clean/'+$entry.file);cleanup_sha256=(Hash $cleanPath);cleanup_atom_readback=$cleanReadback;atom_readback=$readback;cleanup_process=$first.binding;reopen_process=$second.binding;different_process_reopen=$true;distinct_document_identity=$true}
        $receipt.artifacts+=$artifact;Write-Receipt
        Record 'control_native_complete' @{file=$entry.file;warnings=$warnings;reopen_warnings=$reopenWarnings;clean_pid=$first.binding.pid;reopen_pid=$second.binding.pid}
    }
    Assert-FrozenSource
    if((Hash $freezeFile.FullName) -cne $freezeHash -or (Hash $manifestPath) -cne $receipt.manifest_sha256 -or (Hash $seedPath) -cne $receipt.seed_provenance_sha256){throw 'Source freeze or input manifest changed during execution.'}
    $receipt.status='complete';$receipt.completed_utc=[DateTime]::UtcNow.ToString('o');$receipt.source_bytes_rechecked=$true;Write-Receipt
    Record 'complete' @{artifacts=$receipt.artifacts.Count;semantic_comparison='separate';native_visual_acceptance='not_implied'}
}catch{
    $failed=$true;$receipt.status='failed';$receipt.failure=Get-NativeException $_;Write-Receipt
    Record 'probe_exception' $receipt.failure
}finally{
    foreach($document in $owned){if([Runtime.InteropServices.Marshal]::IsComObject($document)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($document)}}
    foreach($application in $applications){if([Runtime.InteropServices.Marshal]::IsComObject($application)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($application)}}
    Write-Output $run
}
if($failed){exit 1}
