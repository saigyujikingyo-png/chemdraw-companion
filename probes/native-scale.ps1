param([Parameter(Mandatory)][string]$InputFile,[Parameter(Mandatory)][string]$OutputDirectory)
$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'native-common.ps1')
$run=[IO.Path]::GetFullPath($OutputDirectory);if(Test-Path -LiteralPath $run){throw 'Output exists'};[void][IO.Directory]::CreateDirectory($run)
$exe=Initialize-NativeInterop;$prior=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id);$a=New-Object -ComObject ChemDraw_x64.Application
if($a.Documents.Count -ne 0 -or [NativeChemDraw]::ApplicationProcess($a) -in $prior){throw 'Fresh application identity not established'}
$d=[NativeChemDraw]::Open($a,$InputFile,'text/xml')
try{
    foreach($dpi in @(72.0,600.0)){
        @{utc=[DateTime]::UtcNow.ToString('o');stage='save_intent';dpi=$dpi}|ConvertTo-Json -Compress|Add-Content -LiteralPath (Join-Path $run 'events.jsonl')
        $r=[NativeChemDraw]::Save($d,(Join-Path $run ('native-'+$dpi+'.png')),'image/png',$dpi)
        $r|ConvertTo-Json -Compress|Add-Content -LiteralPath (Join-Path $run 'events.jsonl');if(!$r.Exists){throw 'Native export failed'}
    }
    [NativeChemDraw]::Close($d)
}finally{[void][Runtime.InteropServices.Marshal]::ReleaseComObject($d);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($a)}
Write-Output $run
