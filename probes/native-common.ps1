# Shared developer-probe helpers, not a production broker.
$ErrorActionPreference='Stop'
function Initialize-NativeInterop {
    $clsid=(Get-Item -LiteralPath 'Registry::HKEY_CLASSES_ROOT\ChemDraw_x64.Application\CLSID').GetValue('')
    $server=(Get-Item -LiteralPath ('Registry::HKEY_CLASSES_ROOT\CLSID\'+$clsid+'\LocalServer32')).GetValue('')
    $executable=($server -replace '(?i)\s+/Automation\s*$','').Trim('"')
    $interop=Join-Path (Split-Path $executable) 'Interop.ChemDraw.dll'
    foreach($file in @($executable,$interop)) {
        if((Get-AuthenticodeSignature -LiteralPath $file).Status.ToString() -ne 'Valid') {throw 'Vendor binary signature is not valid.'}
    }
    [void][Reflection.Assembly]::LoadFrom($interop)
    if(-not ('NativeChemDraw' -as [type])) {
        $references=@($interop)
        if($PSVersionTable.PSEdition -eq 'Core') { $references+=Join-Path $PSHOME 'ref\mscorlib.dll' }
        Add-Type -Path (Join-Path $PSScriptRoot 'NativeChemDraw.cs') -ReferencedAssemblies $references
    }
    return $executable
}
function Get-NativeException($Record) {
    $chain=@();$ex=$Record.Exception
    while($null -ne $ex) {
        $chain+=@{type=$ex.GetType().FullName;message=$ex.Message;hresult=('0x{0:X8}' -f $ex.HResult);source=$ex.Source}
        $ex=$ex.InnerException
    }
    return @{chain=$chain;fully_qualified_error_id=$Record.FullyQualifiedErrorId;script_stack=$Record.ScriptStackTrace}
}
