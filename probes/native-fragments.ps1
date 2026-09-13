param([Parameter(Mandatory)][string]$Manifest,[Parameter(Mandatory)][string]$OutputDirectory)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'native-common.ps1')
$run=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $run){throw 'Output directory already exists; native first output must be preserved.'}
[void][IO.Directory]::CreateDirectory($run)
function Record($stage,$detail){[ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;detail=$detail}|ConvertTo-Json -Depth 12 -Compress|Add-Content -LiteralPath (Join-Path $run 'events.jsonl') -Encoding utf8;Write-Host $stage}
function Save-Checked($doc,$name){$p=Join-Path $run $name;Record 'save_intent' @{name=$name};$r=[NativeChemDraw]::Save($doc,$p,'text/xml',600);Record 'save_return' $r;if(!$r.Exists -or $r.Bytes -le 0){throw "Native artifact missing: $name"}}
$app=$null;$owned=[Collections.Generic.List[object]]::new();$failed=$false
try{
    $exe=Initialize-NativeInterop;$prior=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
    $app=New-Object -ComObject ChemDraw_x64.Application
    $new=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Where-Object {$_.Id -notin $prior -and $_.Path -eq $exe})
    if($app.Documents.Count -ne 0 -or $new.Count -ne 1){throw 'Fresh isolated process not established.'}
    Record 'isolation' @{application=$app.Name;pid=$new[0].Id;preexisting_process_count=$prior.Count}
    $requests=Get-Content -LiteralPath $Manifest -Raw|ConvertFrom-Json
    foreach($request in $requests){
        if($request.id -notmatch '^[A-Za-z0-9_-]+$'){throw 'Unsafe fragment id.'}
        $smilesPath=Join-Path $run ($request.id+'.smiles');[IO.File]::WriteAllText($smilesPath,$request.smiles,[Text.Encoding]::UTF8)
        Record 'open_intent' @{id=$request.id;smiles=$request.smiles}
        $doc=[NativeChemDraw]::Open($app,$smilesPath,'chemical/x-smiles');$owned.Add($doc)
        Record 'native_import' @{id=$request.id;atoms=$doc.Atoms.Count;bonds=$doc.Bonds.Count;formula=$doc.Objects.Formula;warnings=$doc.NumChemicalWarnings}
        Save-Checked $doc ($request.id+'-before.cdxml')
        Record 'cleanup_intent' @{id=$request.id;de_novo=$true}
        $doc.Objects.Clean($true)
        Record 'cleanup_return' @{id=$request.id;atoms=$doc.Atoms.Count;bonds=$doc.Bonds.Count;warnings=$doc.NumChemicalWarnings;atom_maps=@($doc.Atoms|ForEach-Object{@{id=$_.ID;atom_number=$_.AtomNumber;stereo=[int]$_.Stereochemistry;charge=$_.Charge;hydrogens=$_.NumImplicitHydrogens}})}
        Save-Checked $doc ($request.id+'.cdxml')
        [NativeChemDraw]::Close($doc)
    }
    Record 'complete' @{scope='native fragment generation; page composition and mechanism verification remain separate'}
}catch{$failed=$true;Record 'probe_exception' (Get-NativeException $_)}finally{
    foreach($d in $owned){if([Runtime.InteropServices.Marshal]::IsComObject($d)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($d)}}
    if($null -ne $app -and [Runtime.InteropServices.Marshal]::IsComObject($app)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
    Write-Output $run
}
if($failed){exit 1}
