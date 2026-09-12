param([Parameter(Mandatory)][string]$InputDirectory,[Parameter(Mandatory)][string]$OutputDirectory)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'native-common.ps1')
$run=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $run){throw 'Diagnostic output exists; retain all native renders.'}
[void][IO.Directory]::CreateDirectory($run)
function Record($stage,$detail){[ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;detail=$detail}|ConvertTo-Json -Depth 12 -Compress|Add-Content -LiteralPath (Join-Path $run 'events.jsonl') -Encoding utf8;Write-Host $stage}
$app=$null;$owned=[Collections.Generic.List[object]]::new();$failed=$false
try{
    $exe=Initialize-NativeInterop;$prior=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
    $app=New-Object -ComObject ChemDraw_x64.Application;$new=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Where-Object {$_.Id -notin $prior -and $_.Path -eq $exe})
    if($app.Documents.Count -ne 0 -or $new.Count -ne 1 -or [NativeChemDraw]::ApplicationProcess($app) -ne $new[0].Id){throw 'Fresh isolated native identity not established.'}
    Record 'isolation' @{application=$app.Name;pid=$new[0].Id;hwnd_bound_pid=[NativeChemDraw]::ApplicationProcess($app);exe_sha256=(Get-FileHash -LiteralPath $exe).Hash;executor_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;bridge_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'NativeChemDraw.cs')).Hash}
    foreach($source in @(Get-ChildItem -LiteralPath $InputDirectory -Filter '*.cdxml' -File|Sort-Object Name)){
        Record 'open_intent' @{file=$source.Name;sha256=(Get-FileHash -LiteralPath $source.FullName).Hash}
        $doc=[NativeChemDraw]::Open($app,$source.FullName,'text/xml');$owned.Add($doc)
        Record 'native_readback' @{file=$source.Name;atoms=$doc.Atoms.Count;bonds=$doc.Bonds.Count;curves=$doc.Splines.Count;symbols=$doc.Symbols.Count;captions=$doc.Captions.Count;warnings=$doc.NumChemicalWarnings}
        foreach($format in @(@('.cdxml','text/xml'),@('.png','image/png'))){
            $path=Join-Path $run ($source.BaseName+$format[0]);$saved=[NativeChemDraw]::Save($doc,$path,$format[1],600)
            if(!$saved.Exists -or $saved.Bytes -le 0){throw 'Native render postcondition failed.'}
            Record 'native_artifact' @{file=[IO.Path]::GetFileName($path);mime=$format[1];bytes=$saved.Bytes;sha256=(Get-FileHash -LiteralPath $path).Hash}
        }
        [NativeChemDraw]::Close($doc)
    }
    Record 'complete' @{scope='Native renders of declared diagnostic copies; original artifacts unchanged'}
}catch{$failed=$true;Record 'probe_exception' (Get-NativeException $_)}finally{
    foreach($d in $owned){if([Runtime.InteropServices.Marshal]::IsComObject($d)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($d)}}
    if($null -ne $app -and [Runtime.InteropServices.Marshal]::IsComObject($app)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
}
if($failed){exit 1}
