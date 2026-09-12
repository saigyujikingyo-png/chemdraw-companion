param([Parameter(Mandatory)][string]$InputDirectory,[Parameter(Mandatory)][string]$OutputDirectory)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'native-common.ps1')
$run=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $run){throw 'Output directory exists.'}
[void][IO.Directory]::CreateDirectory($run)
function Record($stage,$detail){[ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;detail=$detail}|ConvertTo-Json -Depth 12 -Compress|Add-Content -LiteralPath (Join-Path $run 'events.jsonl') -Encoding utf8;Write-Host $stage}
function Save-Checked($doc,$name){$r=[NativeChemDraw]::Save($doc,(Join-Path $run $name),'text/xml',600);Record 'save_return' $r;if(!$r.Exists -or $r.Bytes -le 0){throw "Missing artifact: $name"}}
$app=$null;$owned=[Collections.Generic.List[object]]::new();$failed=$false
try{
    $exe=Initialize-NativeInterop;$prior=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
    $app=New-Object -ComObject ChemDraw_x64.Application;$new=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Where-Object {$_.Id -notin $prior -and $_.Path -eq $exe})
    if($app.Documents.Count -ne 0 -or $new.Count -ne 1 -or [NativeChemDraw]::ApplicationProcess($app) -ne $new[0].Id){throw 'Fresh application/process identity not established.'}
    Record 'isolation' @{application=$app.Name;pid=$new[0].Id;preexisting_process_count=$prior.Count;native_hwnd_process_verified=$true}
    foreach($file in @(Get-ChildItem -LiteralPath $InputDirectory -Filter '*.cdxml' -File|Sort-Object Name)){
        Record 'open_intent' @{id=$file.BaseName;sha256=(Get-FileHash -LiteralPath $file.FullName).Hash}
        $doc=[NativeChemDraw]::Open($app,$file.FullName,'text/xml');$owned.Add($doc)
        Save-Checked $doc ($file.BaseName+'-before.cdxml')
        Record 'cleanup_intent' @{id=$file.BaseName;de_novo=$true;atoms=$doc.Atoms.Count;bonds=$doc.Bonds.Count}
        $doc.Objects.Clean($true)
        Record 'cleanup_return' @{id=$file.BaseName;atoms=$doc.Atoms.Count;bonds=$doc.Bonds.Count;warnings=$doc.NumChemicalWarnings;smiles=[NativeChemDraw]::Data($doc,'chemical/x-smiles')}
        Save-Checked $doc ($file.BaseName+'.cdxml');[NativeChemDraw]::Close($doc)
    }
    Record 'complete' @{scope='IR graphs materialized and laid out by ChemDraw; composition separate'}
}catch{$failed=$true;Record 'probe_exception' (Get-NativeException $_)}finally{
    foreach($d in $owned){if([Runtime.InteropServices.Marshal]::IsComObject($d)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($d)}}
    if($null -ne $app -and [Runtime.InteropServices.Marshal]::IsComObject($app)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
    Write-Output $run
}
if($failed){exit 1}
