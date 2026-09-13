# Shared, read-only atom observer. Does not open, clean, close or activate apps.
function Get-SemanticXmlEvidence($node){
    $attributes=[ordered]@{}
    foreach($a in @($node.Attributes|Sort-Object Name)){$attributes[$a.Name]=$a.Value}
    $children=@(foreach($child in $node.ChildNodes){
        if($child.NodeType -eq [Xml.XmlNodeType]::Element){Get-SemanticXmlEvidence $child}
        elseif($child.NodeType -in @([Xml.XmlNodeType]::Text,[Xml.XmlNodeType]::CDATA,[Xml.XmlNodeType]::SignificantWhitespace)){
            if($node.Name -eq 's' -or -not [string]::IsNullOrWhiteSpace($child.Value)){[ordered]@{text=$child.Value}}
        }
    })
    return [ordered]@{tag=$node.Name;attributes=$attributes;children=$children}
}
function Get-SemanticGraphEvidence([string]$path){
    [xml]$xml=[IO.File]::ReadAllText($path)
    $rows=@(foreach($n in @($xml.SelectNodes('//n | //b')|Sort-Object Name,@{Expression={$_.GetAttribute('id')}})){Get-SemanticXmlEvidence $n})
    return ConvertTo-Json -InputObject $rows -Depth 80 -Compress
}
function Get-SemanticTextHash([string]$value){
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($value))).ToLowerInvariant()
}
function Write-NativeAtomObservation($doc,[string]$nativeFile,$processBinding,$environment,[string]$sourceFreezeHash,[string]$jobId,[string]$phase){
    $folder=Split-Path $nativeFile
    $stem=[IO.Path]::GetFileNameWithoutExtension($nativeFile)
    $sidecarPath=Join-Path $folder ($stem+'.atoms.json')
    if(Test-Path -LiteralPath $sidecarPath){throw 'Atom sidecar already exists.'}
    $sourceHash=(Get-FileHash -LiteralPath $nativeFile).Hash.ToLowerInvariant()
    $graphBefore=Get-SemanticGraphEvidence $nativeFile
    $chemicalBefore=[string][NativeChemDraw]::Data($doc,'chemical/x-smiles')
    $warningsBefore=[int]$doc.NumChemicalWarnings
    $atomRows=@(foreach($atom in $doc.Atoms){
        $row=[ordered]@{
            native_id=$atom.ID;atom_map=$atom.AtomNumber;atomic_number=$atom.ElementNumber
            formal_charge=$atom.Charge;implicit_h_native_value=$atom.NumImplicitHydrogens
            implicit_h_native_property='IChemDrawAtom.NumImplicitHydrogens'
            node_type_native_value=[int]$atom.NodeType;implicit_h_allowed=$atom.ImplicitHydrogensAllowed
            abnormal_valence_allowed=$atom.AbnormalValenceAllowed;used_valences=$atom.UsedValences
            unused_valences=$atom.UnusedValences;isotope=$atom.Isotope
            radical_native_value=[int]$atom.Radical;radical_native_name=$atom.Radical.ToString()
        }
        if($atom.ElementNumber -eq 6 -and $atom.Charge -eq 0 -and $atom.Isotope -eq 0 -and [int]$atom.Radical -eq 0){
            $doc.Objects.Unselect();$atom.Selected=$true
            $selection=$doc.Selection.Objects
            $row.selected_count=$selection.Count;$row.selected_atom_count=$doc.Selection.Atoms.Count
            $row.selected_bond_count=$doc.Selection.Bonds.Count
            $row.selected_atom_ids=@($doc.Selection.Atoms|Select-Object -ExpandProperty ID)
            if($row.selected_count -eq 1 -and $row.selected_atom_count -eq 1 -and $row.selected_bond_count -eq 0 -and $row.selected_atom_ids.Count -eq 1 -and $row.selected_atom_ids[0] -eq $atom.ID){
                $row.selected_formula_html=$selection.FormulaHTML
            }else{$row.selection_rejection='AMBIGUOUS_NATIVE_SELECTION'}
        }
        $row
    })
    $doc.Objects.Unselect()
    $chemicalAfter=[string][NativeChemDraw]::Data($doc,'chemical/x-smiles')
    $warningsAfter=[int]$doc.NumChemicalWarnings
    if([string]::IsNullOrWhiteSpace($chemicalBefore) -or $chemicalBefore -cne $chemicalAfter){throw 'Native chemical export changed during observation.'}
    if($warningsBefore -ne $warningsAfter){throw 'Native warnings changed during observation.'}
    $afterName=$stem+'-selection-after.cdxml';$afterPath=Join-Path $folder $afterName
    $saved=[NativeChemDraw]::Save($doc,$afterPath,'text/xml',600)
    if(!$saved.Exists -or $saved.Bytes -le 0){throw 'Missing selection-after native snapshot.'}
    if($graphBefore -cne (Get-SemanticGraphEvidence $afterPath)){throw 'Native atom, bond or nested label changed during observation.'}
    if((Get-FileHash -LiteralPath $nativeFile).Hash.ToLowerInvariant() -ne $sourceHash){throw 'Observed source bytes changed.'}
    $readback=[ordered]@{
        version='native-atom-readback/0.5';phase=$phase;job_id=$jobId;source_freeze_sha256=$sourceFreezeHash
        observation='Raw properties and exact single-atom FormulaHTML; H interpretation and independent expected comparison are separate.'
        process=$processBinding;environment=$environment;source_cdxml_sha256=$sourceHash
        chemical_warnings=$warningsBefore;chemical_warnings_after=$warningsAfter
        chemical_export_mime='chemical/x-smiles';chemical_export_before=$chemicalBefore;chemical_export_after=$chemicalAfter
        selection_chemical_export_unchanged=$true;chemical_export_before_sha256=(Get-SemanticTextHash $chemicalBefore)
        chemical_export_after_sha256=(Get-SemanticTextHash $chemicalAfter);selection_graph_unchanged=$true;selection_labels_unchanged=$true
        selection_after_cdxml=@{file=$afterName;sha256=(Get-FileHash -LiteralPath $afterPath).Hash.ToLowerInvariant()}
        atoms=$atomRows
    }
    [IO.File]::WriteAllText($sidecarPath,($readback|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
    return @{file=([IO.Path]::GetFileName($sidecarPath));sha256=(Get-FileHash -LiteralPath $sidecarPath).Hash.ToLowerInvariant()}
}
