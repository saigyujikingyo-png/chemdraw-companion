param([string]$EvidenceRoot=(Join-Path (Split-Path $PSScriptRoot) '.local\saveas-matrix'))
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'native-common.ps1')
$run=Join-Path ([IO.Path]::GetFullPath($EvidenceRoot)) ([DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8))
[void][IO.Directory]::CreateDirectory($run)
function Record($stage,$detail) {
    [ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;detail=$detail} | ConvertTo-Json -Depth 14 -Compress | Add-Content -LiteralPath (Join-Path $run 'events.jsonl') -Encoding utf8
    Write-Host $stage
}
function Save-Checked($doc,[string]$name,[string]$mime) {
    $requestedPath=Join-Path $run $name
    Record 'save_intent' @{requested_path=$requestedPath;mime=$mime;dpi=600;route='typed_vendor_interop'}
    $receipt=[NativeChemDraw]::Save($doc,$requestedPath,$mime,600)
    Record 'save_return' $receipt
    if(!$receipt.Exists -or $receipt.Bytes -eq 0) {throw "Native artifact not created: $name"}
    Record 'artifact' @{name=$name;bytes=$receipt.Bytes;sha256=(Get-FileHash -LiteralPath $requestedPath).Hash}
}
$app=$null;$docs=[Collections.Generic.List[object]]::new();$failed=$false
try {
    $executable=Initialize-NativeInterop
    $prior=@(Get-Process -Name ChemDraw -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
    $app=New-Object -ComObject 'ChemDraw_x64.Application'
    $fresh=@(Get-Process -Name ChemDraw -ErrorAction SilentlyContinue | Where-Object {$_.Id -notin $prior -and $_.Path -eq $executable})
    if($app.Documents.Count -ne 0 -or $fresh.Count -ne 1) {throw 'Fresh isolated process not established.'}
    Record 'isolation' @{application=$app.Name;pid=$fresh[0].Id;preexisting_processes=$prior.Count;ps=$PSVersionTable.PSVersion.ToString();apartment=[Threading.Thread]::CurrentThread.ApartmentState.ToString()}
    $inputFile=Join-Path $run 'ethanol.smiles'
    [IO.File]::WriteAllText($inputFile,'CCO',[Text.Encoding]::ASCII)
    # Independent documents, distinct output paths: deliberate comparisons, not
    # replay of an uncertain mutation against the same document or destination.
    foreach($route in @('powershell_after_interop_load','typed_vendor_interop')) {
        $doc=[NativeChemDraw]::Open($app,$inputFile,'chemical/x-smiles');$docs.Add($doc)
        $requestedPath=Join-Path $run ($route+'.cdxml')
        Record 'comparison_intent' @{route=$route;requested_path=$requestedPath;atoms=$doc.Atoms.Count;bonds=$doc.Bonds.Count}
        if($route -eq 'powershell_after_interop_load') {
            [object]$file=$requestedPath;[object]$format='text/xml';[object]$dpi=600;[object]$width=[Type]::Missing;[object]$height=[Type]::Missing
            try {
                $value=$doc.SaveAs([ref]$file,[ref]$format,[ref]$dpi,[ref]$width,[ref]$height)
                Record 'comparison_return' @{route=$route;requested_path=$requestedPath;returned_path=$file;returned_mime=$format;returned_dpi=$dpi;exists=[IO.File]::Exists($requestedPath);return_is_null=($null -eq $value)}
            } catch { Record 'vendor_exception' (Get-NativeException $_) }
        } else {
            Save-Checked $doc 'typed_vendor_interop.cdxml' 'text/xml'
            Save-Checked $doc 'ethanol.cdx' 'chemical/x-cdx'
            Save-Checked $doc 'ethanol.png' 'image/png'
            Save-Checked $doc 'ethanol.jpg' 'image/jpeg'
        }
        [NativeChemDraw]::Close($doc)
    }
    foreach($entry in @(@{name='cdx';file='ethanol.cdx';mime='chemical/x-cdx'},@{name='cdxml';file='typed_vendor_interop.cdxml';mime='text/xml'})) {
        $doc=[NativeChemDraw]::Open($app,(Join-Path $run $entry.file),$entry.mime);$docs.Add($doc)
        Record 'disk_reopen' @{format=$entry.name;atoms=$doc.Atoms.Count;bonds=$doc.Bonds.Count;formula=$doc.Objects.Formula}
        if($doc.Atoms.Count -ne 3 -or $doc.Bonds.Count -ne 2 -or $doc.Objects.Formula -ne 'C2H6O') {throw 'Disk round-trip graph mismatch.'}
        $oxygen=@($doc.Atoms | Where-Object ElementNumber -eq 8)[0]
        Record 'edit_intent' @{source=$entry.name;atom_id=$oxygen.ID;old_charge=$oxygen.Charge;new_charge=-1}
        $oxygen.Charge=-1
        Save-Checked $doc ($entry.name+'-edited.cdxml') 'text/xml'
        [NativeChemDraw]::Close($doc)
        $edited=[NativeChemDraw]::Open($app,(Join-Path $run ($entry.name+'-edited.cdxml')),'text/xml');$docs.Add($edited)
        $editedO=@($edited.Atoms | Where-Object ElementNumber -eq 8)[0]
        if($editedO.Charge -ne -1) {throw 'Edit did not survive disk save/reopen.'}
        Record 'edit_reopened' @{source=$entry.name;oxygen_charge=$editedO.Charge;formula=$edited.Objects.Formula}
        [NativeChemDraw]::Close($edited)
    }
    # An invalid format on a new disposable document checks the actual exception
    # surface. It is not an application/entitlement diagnosis.
    $invalid=[NativeChemDraw]::Open($app,$inputFile,'chemical/x-smiles');$docs.Add($invalid)
    try { $r=[NativeChemDraw]::Save($invalid,(Join-Path $run 'invalid-format.bin'),'application/x-invalid-chemdraw-probe',600);Record 'invalid_format_return' $r }
    catch {Record 'invalid_format_vendor_exception' (Get-NativeException $_)}
    [NativeChemDraw]::Close($invalid)
    Record 'complete' @{scope='SaveAs transport and disk edit smoke only';product_gate='not_established';license_entitlement='unverified'}
} catch { $failed=$true;Record 'probe_exception' (Get-NativeException $_) }
finally {
    foreach($doc in $docs) {if([Runtime.InteropServices.Marshal]::IsComObject($doc)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc)}}
    if($null -ne $app -and [Runtime.InteropServices.Marshal]::IsComObject($app)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
    Write-Output $run
}
if($failed){exit 1}
