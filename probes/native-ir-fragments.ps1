param([Parameter(Mandatory)][string]$InputDirectory,[Parameter(Mandatory)][string]$OutputDirectory)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'native-common.ps1')
$run=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $run){throw 'Output directory exists.'}
[void][IO.Directory]::CreateDirectory($run)
function Record($stage,$detail){[ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;detail=$detail}|ConvertTo-Json -Depth 12 -Compress|Add-Content -LiteralPath (Join-Path $run 'events.jsonl') -Encoding utf8;Write-Host $stage}
function Save-Checked($doc,$name){$r=[NativeChemDraw]::Save($doc,(Join-Path $run $name),'text/xml',600);Record 'save_return' $r;if(!$r.Exists -or $r.Bytes -le 0){throw "Missing artifact: $name"}}
$app=$null;$owned=[Collections.Generic.List[object]]::new();$failed=$false
$manifestPath=Join-Path $InputDirectory 'geometry-manifest.json';$seedPath=Join-Path $InputDirectory 'seed-provenance.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
$receipt=[ordered]@{version='native-geometry-receipt/0.1';status='running';operation='ChemDraw.Objects.Clean(true)';run_id=[guid]::NewGuid().ToString();started_utc=[DateTime]::UtcNow.ToString('o');manifest_sha256=(Get-FileHash -LiteralPath $manifestPath).Hash.ToLowerInvariant();seed_provenance_sha256=(Get-FileHash -LiteralPath $seedPath).Hash.ToLowerInvariant();environment=$null;artifacts=@()}
$receiptPath=Join-Path $run 'native-geometry-receipt.json'
$receipt|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $receiptPath -Encoding utf8
try{
    $exe=Initialize-NativeInterop;$prior=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
    $app=New-Object -ComObject ChemDraw_x64.Application;$new=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Where-Object {$_.Id -notin $prior -and $_.Path -eq $exe})
    if($app.Documents.Count -ne 0 -or $new.Count -ne 1 -or [NativeChemDraw]::ApplicationProcess($app) -ne $new[0].Id){throw 'Fresh application/process identity not established.'}
    Record 'isolation' @{application=$app.Name;pid=$new[0].Id;preexisting_process_count=$prior.Count;native_hwnd_process_verified=$true}
    $interop=Join-Path (Split-Path $exe) 'Interop.ChemDraw.dll'
    $receipt.environment=[ordered]@{application_build=(Get-Item -LiteralPath $exe).VersionInfo.FileVersion;interop_version=(Get-Item -LiteralPath $interop).VersionInfo.FileVersion;executable_sha256=(Get-FileHash -LiteralPath $exe).Hash.ToLowerInvariant();interop_sha256=(Get-FileHash -LiteralPath $interop).Hash.ToLowerInvariant();executor_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash.ToLowerInvariant();bridge_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'NativeChemDraw.cs')).Hash.ToLowerInvariant();owned_pid=$new[0].Id;hwnd_bound_pid=[NativeChemDraw]::ApplicationProcess($app)}
    foreach($entry in $manifest){
        if([IO.Path]::GetFileName($entry.file) -ne $entry.file -or [IO.Path]::GetExtension($entry.file) -ne '.cdxml'){throw 'Invalid native seed filename.'}
        $file=Get-Item -LiteralPath (Join-Path $InputDirectory $entry.file)
        $inputHash=(Get-FileHash -LiteralPath $file.FullName).Hash.ToLowerInvariant()
        Record 'open_intent' @{id=$file.BaseName;sha256=(Get-FileHash -LiteralPath $file.FullName).Hash}
        $doc=[NativeChemDraw]::Open($app,$file.FullName,'text/xml');$owned.Add($doc)
        Save-Checked $doc ($file.BaseName+'-before.cdxml')
        Record 'cleanup_intent' @{id=$file.BaseName;de_novo=$true;atoms=$doc.Atoms.Count;bonds=$doc.Bonds.Count}
        $doc.Objects.Clean($true)
        Record 'cleanup_return' @{id=$file.BaseName;atoms=$doc.Atoms.Count;bonds=$doc.Bonds.Count;warnings=$doc.NumChemicalWarnings;smiles=[NativeChemDraw]::Data($doc,'chemical/x-smiles')}
        $nativeWarnings=$doc.NumChemicalWarnings
        Save-Checked $doc ($file.BaseName+'.cdxml');[NativeChemDraw]::Close($doc)
        if((Get-FileHash -LiteralPath $file.FullName).Hash.ToLowerInvariant() -ne $inputHash){throw 'Seed changed during native operation.'}
        $receipt.artifacts+=@{file=$file.Name;input_sha256=$inputHash;before_sha256=(Get-FileHash -LiteralPath (Join-Path $run ($file.BaseName+'-before.cdxml'))).Hash.ToLowerInvariant();output_sha256=(Get-FileHash -LiteralPath (Join-Path $run ($file.BaseName+'.cdxml'))).Hash.ToLowerInvariant();cleanup_completed=$true;warnings=$nativeWarnings}
    }
    $receipt.status='complete';$receipt.completed_utc=[DateTime]::UtcNow.ToString('o');$receipt|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $receiptPath -Encoding utf8
    Record 'complete' @{scope='IR graphs materialized and laid out by ChemDraw; composition separate'}
}catch{$failed=$true;$receipt.status='failed';$receipt|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $receiptPath -Encoding utf8;Record 'probe_exception' (Get-NativeException $_)}finally{
    foreach($d in $owned){if([Runtime.InteropServices.Marshal]::IsComObject($d)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($d)}}
    if($null -ne $app -and [Runtime.InteropServices.Marshal]::IsComObject($app)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
    Write-Output $run
}
if($failed){exit 1}
