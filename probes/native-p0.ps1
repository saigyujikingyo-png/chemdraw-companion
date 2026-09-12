param(
    [string]$EvidenceRoot = (Join-Path (Split-Path $PSScriptRoot) '.local\native-probes')
)

# Developer-only feasibility probe. No MCP service, installer or entitlement claim.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'native-common.ps1')
$runPath = Join-Path ([IO.Path]::GetFullPath($EvidenceRoot)) ([DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8))
if ($runPath -match '(?i)(^|[\\/])OneDrive([^\\/]*)([\\/]|$)') { throw 'Live native probes must remain outside cloud sync.' }
$ancestor = [IO.DirectoryInfo]::new($runPath)
while ($null -ne $ancestor) {
    if ($ancestor.Exists -and ($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Reparse-point evidence roots are not supported by this probe.' }
    $ancestor = $ancestor.Parent
}
[void][IO.Directory]::CreateDirectory($runPath)
$journalPath = Join-Path $runPath 'events.jsonl'
function Write-Event([string]$Stage, $Details) {
    [ordered]@{ utc=[DateTime]::UtcNow.ToString('o'); stage=$Stage; details=$Details } |
        ConvertTo-Json -Depth 12 -Compress | Add-Content -LiteralPath $journalPath -Encoding utf8
    Write-Host $Stage
}
function Get-Snapshot($Document) {
    $atoms = @($Document.Atoms | ForEach-Object {
        [ordered]@{ id=$_.ID; element=$_.ElementNumber; charge=$_.Charge; hydrogens=$_.NumImplicitHydrogens; stereo=$_.Stereochemistry; x=$_.Position.X; y=$_.Position.Y }
    })
    return [ordered]@{ atoms=$atoms; atom_count=$Document.Atoms.Count; bond_count=$Document.Bonds.Count; caption_count=$Document.Captions.Count; warnings=$Document.NumChemicalWarnings; formula=$Document.Objects.Formula }
}
function Save-Native($Document, [string]$Name, [string]$Mime, [int]$Resolution=600) {
    [string]$requestedPath=Join-Path $runPath $Name
    if (Test-Path -LiteralPath $requestedPath) { throw "Refusing to overwrite probe artifact $Name" }
    Write-Event 'save_intent' @{ file=$Name; mime=$Mime; requested_resolution=$Resolution }
    $receipt=[NativeChemDraw]::Save($Document,$requestedPath,$Mime,$Resolution)
    Write-Event 'save_return' $receipt
    if (!(Test-Path -LiteralPath $requestedPath)) { throw "SaveAs returned without producing requested artifact $Name" }
    $info=Get-Item -LiteralPath $requestedPath
    if ($info.Length -eq 0) { throw "Empty native artifact $Name" }
    Write-Event 'save_complete' @{ file=$Name; bytes=$info.Length; sha256=(Get-FileHash -LiteralPath $requestedPath -Algorithm SHA256).Hash }
}
function Close-Owned($Document) {
    [NativeChemDraw]::Close($Document)
}
$application=$null; $ownedDocuments=[Collections.Generic.List[object]]::new()
$mutationStarted=$false
$result=[ordered]@{ probe_version='0.2.0'; status='running'; license_entitlement='unverified'; paired_addin='not_verified'; production_route='developer_probe_only'; gates=@{S1='not_run';R1='not_run';M1='not_run';M2='not_run';visual_review='unverified';owner_acceptance='pending';host_receipt='unverified'} }
try {
    [void](Initialize-NativeInterop)
    $clsid=(Get-Item -LiteralPath 'Registry::HKEY_CLASSES_ROOT\ChemDraw_x64.Application\CLSID').GetValue('')
    $server=(Get-Item -LiteralPath ('Registry::HKEY_CLASSES_ROOT\CLSID\'+$clsid+'\LocalServer32')).GetValue('')
    $executable=($server -replace '(?i)\s+/Automation\s*$','').Trim('"')
    $signature=Get-AuthenticodeSignature -LiteralPath $executable
    if ($signature.Status.ToString() -ne 'Valid') { throw 'Registered native server does not have a valid Authenticode signature.' }
    Write-Event 'registered_server' @{ filename=[IO.Path]::GetFileName($executable); version=(Get-Item -LiteralPath $executable).VersionInfo.FileVersion; signature=$signature.Status.ToString(); sha256=(Get-FileHash -LiteralPath $executable).Hash }
    $beforeProcessIds=@(Get-Process -Name ChemDraw -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
    $application=New-Object -ComObject 'ChemDraw_x64.Application'
    if ($application.Documents.Count -ne 0) { throw 'DOCUMENT_BINDING_UNSAFE: COM activation exposed pre-existing documents.' }
    $newProcesses=@(Get-Process -Name ChemDraw -ErrorAction SilentlyContinue | Where-Object { $_.Id -notin $beforeProcessIds -and $_.Path -eq $executable })
    if ($newProcesses.Count -ne 1) { throw 'DOCUMENT_BINDING_UNSAFE: cannot identify one fresh native process.' }
    $windowProcess=[NativeChemDraw]::ApplicationProcess($application)
    if($windowProcess -ne $newProcesses[0].Id){throw 'DOCUMENT_BINDING_UNSAFE: native application HWND does not identify the fresh process.'}
    $result.application=$application.name
    $result.isolation='new_vendor_process_with_zero_preexisting_documents_and_retained_com_references'
    Write-Event 'application_isolated' @{ name=$application.name; fresh_process_count=$newProcesses.Count; document_count=$application.Documents.Count; existing_processes_untouched=$beforeProcessIds.Count }

    # N1: identical blank A/B, deliberately change active document before writes.
    $mutationStarted=$true
    $docA=$application.Documents.Add(); $ownedDocuments.Add($docA)
    $docB=$application.Documents.Add(); $ownedDocuments.Add($docB)
    if ($docA.Atoms.Count -ne 0 -or $docB.Atoms.Count -ne 0) { throw 'Expected two blank disposable documents.' }
    Write-Event 'N1_identical_blank' @{ A=(Get-Snapshot $docA); B=(Get-Snapshot $docB) }
    if(![NativeChemDraw]::ActivateAndVerify($application,$docB)){throw 'ActiveDocument identity readback does not match B.'}
    Write-Event 'N1_active_B_identity_verified' @{same_com_iunknown=$true;application_process_verified=$true}
    Write-Event 'N1_write_A_intent_while_B_active' @{}
    $atomA=$docA.MakeAtom(); $atomA.ElementNumber=8
    if ($docA.Atoms.Count -ne 1 -or $docB.Atoms.Count -ne 0) { throw 'DOCUMENT_BINDING_UNSAFE: A write did not remain on A.' }
    Write-Event 'N1_write_A_complete' @{ A=(Get-Snapshot $docA); B=(Get-Snapshot $docB) }
    if(![NativeChemDraw]::ActivateAndVerify($application,$docA)){throw 'ActiveDocument identity readback does not match A.'}
    Write-Event 'N1_active_A_identity_verified' @{same_com_iunknown=$true}
    Write-Event 'N1_write_B_intent_while_A_active' @{}
    $atomB=$docB.MakeAtom(); $atomB.ElementNumber=7
    if ($docA.Atoms.Count -ne 1 -or $docB.Atoms.Count -ne 1 -or $docA.Atoms.Item(1).ElementNumber -ne 8 -or $docB.Atoms.Item(1).ElementNumber -ne 7) { throw 'DOCUMENT_BINDING_UNSAFE: reverse write changed the wrong document.' }
    Write-Event 'N1_write_B_complete' @{ A=(Get-Snapshot $docA); B=(Get-Snapshot $docB) }
    $result.gates.N1_retained_com_reference='pass_for_this_disposable_process_only'
    Save-Native $docA 'N1-A.cdxml' 'text/xml'
    Save-Native $docB 'N1-B.cdxml' 'text/xml'
    Close-Owned $docA; Close-Owned $docB

    # This N1 probe is bounded. Separate fixture probes cover S1/R1/M1/M2.
    $result.gates.S1='not_run'
    $result.gates.visual_review='unverified'
    $result.gates.owner_acceptance='pending'
    $result.gates.R1='not_run'; $result.gates.M1='not_run'
    $result.status='probe_complete_not_a_product_pass'
} catch {
    $result.status='probe_failed'
    $disposition=if($mutationStarted){'unknown'}else{'none'}
    $result.error=[ordered]@{message=$_.Exception.Message;type=$_.Exception.GetType().FullName;hresult=('0x{0:X8}' -f $_.Exception.HResult);retryable=$false;mutation_outcome=$disposition;next_action='Inspect the existing journal and owned documents; do not replay writes.'}
    $result.error.exception_detail=Get-NativeException $_
    Write-Event 'probe_error' $result.error
} finally {
    $result.completed_utc=[DateTime]::UtcNow.ToString('o')
    $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $runPath 'result.json') -Encoding utf8
    # Do not call Application.Quit or kill a process. Retain failures for inspection.
    foreach ($owned in $ownedDocuments) { if ([Runtime.InteropServices.Marshal]::IsComObject($owned)) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($owned) } }
    if ($null -ne $application -and [Runtime.InteropServices.Marshal]::IsComObject($application)) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($application) }
    Write-Output $runPath
}
if ($result.status -eq 'probe_failed') { exit 1 }
