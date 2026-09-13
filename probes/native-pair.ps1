param(
    [Parameter(Mandatory)][string]$InputFile,
    [Parameter(Mandatory)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedSha256,
    [Parameter(Mandatory)][string]$OutputDirectory,
    [Parameter(Mandatory)][ValidateSet('target','candidate')][string]$Role,
    [ValidateRange(72,1200)][int]$Dpi=600
)
# Developer-only native custodian. Run through run_with_deadline.py.
# Target outputs contain hidden answer data and must never enter a generator.
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'native-common.ps1')
. (Join-Path $PSScriptRoot 'native-snapshot.ps1')
$source=Get-Item -LiteralPath $InputFile
if($source.PSIsContainer -or $source.Extension.ToLowerInvariant() -notin @('.cdx','.cdxml')){throw 'Expected one CDX or CDXML input file.'}
$sourceHash=(Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
if($sourceHash -ne $ExpectedSha256.ToLowerInvariant()){throw 'Input SHA-256 mismatch; native execution refused.'}
$run=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $run){throw 'Output exists; preserve the first attempt and reconcile before any retry.'}
[void][IO.Directory]::CreateDirectory($run)
function Record($stage,$detail){
    [ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;detail=$detail}|
        ConvertTo-Json -Depth 40 -Compress|Add-Content -LiteralPath (Join-Path $run 'events.jsonl') -Encoding utf8
    Write-Host $stage
}
function Canonical($value){
    if($null -eq $value){return $null}
    if($value -is [Collections.IDictionary]){
        $result=[ordered]@{}
        foreach($key in @($value.Keys|Sort-Object)){$result[$key]=Canonical $value[$key]}
        return $result
    }
    if($value -is [Array]){
        $items=@(foreach($item in $value){Canonical $item})
        return ,$items
    }
    return $value
}
function Scene-Json($document){return (Canonical (Get-NativeSceneSnapshot $document)|ConvertTo-Json -Depth 40 -Compress)}
function Hash-Text([string]$value){
    $sha=[Security.Cryptography.SHA256]::Create()
    try{return [Convert]::ToHexString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($value))).ToLowerInvariant()}
    finally{$sha.Dispose()}
}
function File-Record([string]$path){
    $item=Get-Item -LiteralPath $path
    return [ordered]@{file=$item.Name;bytes=$item.Length;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
}
$app=$null;$boundPid=0;$owned=[Collections.Generic.List[object]]::new();$applications=[Collections.Generic.List[object]]::new();$failed=$false
function Start-FreshApplication([string]$stage){
    $prior=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
    $script:app=New-Object -ComObject ChemDraw_x64.Application
    $applications.Add($app)
    $new=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Where-Object {$_.Id -notin $prior -and $_.Path -eq $exe})
    $script:boundPid=[NativeChemDraw]::ApplicationProcess($app)
    if($app.Documents.Count -ne 0 -or $new.Count -ne 1 -or $boundPid -ne $new[0].Id){throw 'Fresh isolated native process and HWND identity not established.'}
    Record 'native_environment' @{stage=$stage;application=$app.Name;pid=$boundPid;preexisting_pids=$prior;initial_documents=$app.Documents.Count;executable=$exe;file_version=(Get-Item -LiteralPath $exe).VersionInfo.FileVersion;product_version=(Get-Item -LiteralPath $exe).VersionInfo.ProductVersion;executable_sha256=(Get-FileHash -LiteralPath $exe).Hash;interop_sha256=(Get-FileHash -LiteralPath (Join-Path (Split-Path $exe) 'Interop.ChemDraw.dll')).Hash;vendor_signatures='Valid';dpi_requested=$Dpi}
}
function Assert-Application {
    if([NativeChemDraw]::ApplicationProcess($app) -ne $boundPid){throw 'Native application identity changed.'}
    if($app.Documents.Count -ne 1){throw 'Expected exactly one custodian document before native serialization.'}
}
function Save-Checked($document,[string]$name,[string]$mime,[string]$expectedScene){
    Assert-Application
    $before=Scene-Json $document
    if($before -cne $expectedScene){throw 'EXPORT_REVISION_MISMATCH before save.'}
    $path=Join-Path $run $name
    Record 'save_intent' @{file=$name;mime=$mime;dpi=$Dpi;scene_sha256=(Hash-Text $before)}
    $saved=[NativeChemDraw]::Save($document,$path,$mime,$Dpi)
    Record 'save_return' $saved
    if(!$saved.Exists -or $saved.Bytes -le 0){throw 'Native serialization produced no bytes.'}
    Assert-Application
    $after=Scene-Json $document
    if($before -cne $after){throw 'EXPORT_REVISION_MISMATCH after save.'}
    Record 'artifact' @{artifact=(File-Record $path);before_scene_sha256=(Hash-Text $before);after_scene_sha256=(Hash-Text $after);producer='ChemDraw Document.SaveAs'}
}
try{
    $copy=Join-Path $run ('source'+$source.Extension.ToLowerInvariant())
    [IO.File]::Copy($source.FullName,$copy,$false)
    if((File-Record $copy).sha256 -ne $sourceHash){throw 'Custodian copy SHA-256 mismatch.'}
    Record 'input' @{role=$Role;original=(File-Record $source.FullName);copy=(File-Record $copy);original_path=$source.FullName;generator_access='forbidden for all target data except independently delivered reference PNG';object_edits='none';clean_called=$false}
    $exe=Initialize-NativeInterop
    Start-FreshApplication 'import'
    $mime=if($source.Extension.ToLowerInvariant() -eq '.cdx'){'chemical/x-cdx'}else{'text/xml'}
    Record 'open_intent' @{file=[IO.Path]::GetFileName($copy);mime=$mime}
    $doc=[NativeChemDraw]::Open($app,$copy,$mime);$owned.Add($doc)
    Assert-Application
    $baseline=Scene-Json $doc
    [IO.File]::WriteAllText((Join-Path $run ($Role+'.import-scene.json')),$baseline,[Text.UTF8Encoding]::new($false))
    Record 'import_scene' @{file=($Role+'.import-scene.json');scene_sha256=(Hash-Text $baseline)}
    Save-Checked $doc ($Role+'.native.cdxml') 'text/xml' $baseline
    Save-Checked $doc ($Role+'.native.cdx') 'chemical/x-cdx' $baseline
    $imageName=if($Role -eq 'target'){'reference.png'}else{'candidate.png'}
    Save-Checked $doc $imageName 'image/png' $baseline
    [NativeChemDraw]::Close($doc)
    Record 'closed' @{source='import';remaining_documents=$app.Documents.Count}
    foreach($ext in @('cdx','cdxml')){
        # A retained same-process COM identity is not independent disk-open
        # evidence on all vendor builds. A fresh process starts with no loaded
        # documents and cannot reuse the preceding process's document cache.
        Start-FreshApplication ('reopen_'+$ext)
        $path=Join-Path $run ($Role+'.native.'+$ext)
        $mime=if($ext -eq 'cdx'){'chemical/x-cdx'}else{'text/xml'}
        Record 'disk_reopen_intent' @{artifact=(File-Record $path);mime=$mime}
        $reopened=[NativeChemDraw]::Open($app,$path,$mime)
        # Require a different retained COM identity as an additional check.
        foreach($previous in $owned){if([NativeChemDraw]::SameIdentity($previous,$reopened)){throw 'Disk reopen reused a retained document identity.'}}
        $owned.Add($reopened)
        Assert-Application
        $scene=Scene-Json $reopened
        $sceneName=$Role+'.'+$ext+'-reopened-scene.json'
        [IO.File]::WriteAllText((Join-Path $run $sceneName),$scene,[Text.UTF8Encoding]::new($false))
        Record 'disk_reopened' @{format=$ext;pid=$boundPid;fresh_process=$true;scene_file=$sceneName;scene_sha256=(Hash-Text $scene);distinct_document_identity=$true;exact_scene_equal_to_import=($scene -ceq $baseline);normalized_evaluation='separate; native IDs may change'}
        Save-Checked $reopened ($Role+'.'+$ext+'-readback.cdxml') 'text/xml' $scene
        Save-Checked $reopened ($Role+'.'+$ext+'-reopened.png') 'image/png' $scene
        [NativeChemDraw]::Close($reopened)
        Record 'closed' @{source=$ext;remaining_documents=$app.Documents.Count}
    }
    if((File-Record $source.FullName).sha256 -ne $sourceHash -or (File-Record $copy).sha256 -ne $sourceHash){throw 'Original input or custodian copy changed.'}
    Record 'complete' @{role=$Role;native_transport='completed';original_sha256=$sourceHash;original_unchanged=$true;copy_unchanged=$true;remaining_documents=$app.Documents.Count;object_edits='none';clean_called=$false;semantic_visual_acceptance='separate_required';blind_generator='not_run'}
}catch{
    $failed=$true;Record 'probe_exception' (Get-NativeException $_)
}finally{
    foreach($document in $owned){if([Runtime.InteropServices.Marshal]::IsComObject($document)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($document)}}
    foreach($application in $applications){if([Runtime.InteropServices.Marshal]::IsComObject($application)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($application)}}
    Write-Output $run
}
if($failed){exit 1}
