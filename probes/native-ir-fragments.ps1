param(
    [Parameter(Mandatory)][string]$InputDirectory,
    [Parameter(Mandatory)][string]$OutputDirectory,
    [switch]$IncludeAtomReadback
)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'native-common.ps1')
$run=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $run){throw 'Output directory exists.'}
[void][IO.Directory]::CreateDirectory($run)
function Record($stage,$detail){[ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;detail=$detail}|ConvertTo-Json -Depth 12 -Compress|Add-Content -LiteralPath (Join-Path $run 'events.jsonl') -Encoding utf8;Write-Host $stage}
function Save-Checked($doc,$name){$r=[NativeChemDraw]::Save($doc,(Join-Path $run $name),'text/xml',600);Record 'save_return' $r;if(!$r.Exists -or $r.Bytes -le 0){throw "Missing artifact: $name"}}
function Get-GraphAttributes([string]$file){
    [xml]$xml=[IO.File]::ReadAllText($file)
    $rows=@($xml.SelectNodes('//n | //b') | Sort-Object Name,@{Expression={$_.GetAttribute('id')}} | ForEach-Object {
        $attributes=[ordered]@{}
        foreach($attribute in ($_.Attributes | Sort-Object Name)){$attributes[$attribute.Name]=$attribute.Value}
        [ordered]@{tag=$_.Name;attributes=$attributes}
    })
    return ConvertTo-Json -InputObject $rows -Depth 8 -Compress
}
function Save-AtomReadback($doc,[string]$name,[string]$nativeFile){
    $path=Join-Path $run $name
    $graphBefore=Get-GraphAttributes $nativeFile
    $chemicalBefore=[string][NativeChemDraw]::Data($doc,'chemical/x-smiles')
    $atomRows=@($doc.Atoms|ForEach-Object{
        $atom=$_
        $row=[ordered]@{
            native_id=$atom.ID
            atom_map=$atom.AtomNumber
            atomic_number=$atom.ElementNumber
            formal_charge=$atom.Charge
            implicit_h_native_value=$atom.NumImplicitHydrogens
            implicit_h_native_property='IChemDrawAtom.NumImplicitHydrogens'
            node_type_native_value=[int]$atom.NodeType
            implicit_h_allowed=$atom.ImplicitHydrogensAllowed
            abnormal_valence_allowed=$atom.AbnormalValenceAllowed
            used_valences=$atom.UsedValences
            unused_valences=$atom.UnusedValences
            isotope=$atom.Isotope
            radical_native_value=[int]$atom.Radical
            radical_native_name=$atom.Radical.ToString()
        }
        if($atom.ElementNumber -eq 6 -and $atom.Charge -eq 0 -and $atom.Isotope -eq 0 -and [int]$atom.Radical -eq 0){
            $doc.Objects.Unselect()
            $atom.Selected=$true
            $selection=$doc.Selection.Objects
            $row.selected_count=$selection.Count
            $row.selected_atom_count=$doc.Selection.Atoms.Count
            $row.selected_bond_count=$doc.Selection.Bonds.Count
            $row.selected_atom_ids=@($doc.Selection.Atoms | Select-Object -ExpandProperty ID)
            if($row.selected_count -eq 1 -and $row.selected_atom_count -eq 1 -and $row.selected_bond_count -eq 0 -and $row.selected_atom_ids.Count -eq 1 -and $row.selected_atom_ids[0] -eq $atom.ID){
                $row.selected_formula_html=$selection.FormulaHTML
            }else{$row.selection_rejection='AMBIGUOUS_NATIVE_SELECTION'}
        }
        $row
    })
    $doc.Objects.Unselect()
    $chemicalAfter=[string][NativeChemDraw]::Data($doc,'chemical/x-smiles')
    if([string]::IsNullOrWhiteSpace($chemicalBefore) -or $chemicalBefore -ne $chemicalAfter){throw 'Native chemical export changed during atom selection readback.'}
    $afterName=[IO.Path]::GetFileNameWithoutExtension($nativeFile)+'-selection-after.cdxml'
    Save-Checked $doc $afterName
    $afterFile=Join-Path $run $afterName
    if($graphBefore -cne (Get-GraphAttributes $afterFile)){throw 'Native atom/bond attributes changed during atom selection readback.'}
    $hasher=[Security.Cryptography.SHA256]::Create()
    try{$chemicalHash=([BitConverter]::ToString($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($chemicalBefore)))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
    $readback=[ordered]@{
        version='native-atom-readback/0.4'
        observation='Atom-associated native properties and selected-object FormulaHTML after cleanup and serialization; not an independent disk reopen. NumImplicitHydrogens and UnusedValences are not universal hydrogen-count oracles.'
        source_cdxml_sha256=(Get-FileHash -LiteralPath $nativeFile).Hash.ToLowerInvariant()
        chemical_export_mime='chemical/x-smiles'
        selection_chemical_export_unchanged=$true
        chemical_export_before_sha256=$chemicalHash
        chemical_export_after_sha256=$chemicalHash
        selection_graph_unchanged=$true
        selection_after_cdxml=@{file=$afterName;sha256=(Get-FileHash -LiteralPath $afterFile).Hash.ToLowerInvariant()}
        atoms=$atomRows
    }
    [IO.File]::WriteAllText($path,($readback|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
    Record 'native_atom_readback' @{file=$name;source_cdxml_sha256=$readback.source_cdxml_sha256;sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant();atoms=$readback.atoms.Count}
    return @{file=$name;sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()}
}
$app=$null;$owned=[Collections.Generic.List[object]]::new();$failed=$false
$manifestPath=Join-Path $InputDirectory 'geometry-manifest.json';$seedPath=Join-Path $InputDirectory 'seed-provenance.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
$seedRecord=Get-Content -LiteralPath $seedPath -Raw|ConvertFrom-Json
if($seedRecord.PSObject.Properties.Name -contains 'depiction_plan_sha256'){$IncludeAtomReadback=$true}
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
        Save-Checked $doc ($file.BaseName+'.cdxml')
        $atomReadback=$null
        if($IncludeAtomReadback){$atomReadback=Save-AtomReadback $doc ($file.BaseName+'.atoms.json') (Join-Path $run ($file.BaseName+'.cdxml'))}
        [NativeChemDraw]::Close($doc)
        if((Get-FileHash -LiteralPath $file.FullName).Hash.ToLowerInvariant() -ne $inputHash){throw 'Seed changed during native operation.'}
        $artifact=@{file=$file.Name;input_sha256=$inputHash;before_sha256=(Get-FileHash -LiteralPath (Join-Path $run ($file.BaseName+'-before.cdxml'))).Hash.ToLowerInvariant();output_sha256=(Get-FileHash -LiteralPath (Join-Path $run ($file.BaseName+'.cdxml'))).Hash.ToLowerInvariant();cleanup_completed=$true;warnings=$nativeWarnings}
        if($IncludeAtomReadback){$artifact.atom_readback=$atomReadback}
        $receipt.artifacts+=$artifact
    }
    $receipt.status='complete';$receipt.completed_utc=[DateTime]::UtcNow.ToString('o');$receipt|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $receiptPath -Encoding utf8
    Record 'complete' @{scope='IR graphs materialized and laid out by ChemDraw; composition separate'}
}catch{$failed=$true;$receipt.status='failed';$receipt|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $receiptPath -Encoding utf8;Record 'probe_exception' (Get-NativeException $_)}finally{
    foreach($d in $owned){if([Runtime.InteropServices.Marshal]::IsComObject($d)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($d)}}
    if($null -ne $app -and [Runtime.InteropServices.Marshal]::IsComObject($app)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
    Write-Output $run
}
if($failed){exit 1}
