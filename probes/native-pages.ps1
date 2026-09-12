param([Parameter(Mandatory)][string]$InputDirectory,[Parameter(Mandatory)][string]$OutputDirectory)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'native-common.ps1')
$run=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $run){throw 'Output directory already exists; first output must be preserved.'}
[void][IO.Directory]::CreateDirectory($run)
function Record($stage,$detail){[ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;detail=$detail}|ConvertTo-Json -Depth 12 -Compress|Add-Content -LiteralPath (Join-Path $run 'events.jsonl') -Encoding utf8;Write-Host $stage}
function Snapshot($doc){return @{atoms=@($doc.Atoms|ForEach-Object{@{id=$_.ID;number=$_.AtomNumber;element=$_.ElementNumber;charge=$_.Charge;x=$_.Position.X;y=$_.Position.Y}});atom_count=$doc.Atoms.Count;bond_count=$doc.Bonds.Count;captions=$doc.Captions.Count;curves=$doc.Splines.Count;symbols=$doc.Symbols.Count;arrows=$doc.Arrows.Count;warnings=$doc.NumChemicalWarnings;formula=$doc.Objects.Formula}}
function Save-Checked($doc,$name,$mime){$p=Join-Path $run $name;Record 'save_intent' @{name=$name;mime=$mime};$r=[NativeChemDraw]::Save($doc,$p,$mime,600);Record 'save_return' $r;if(!$r.Exists -or $r.Bytes -le 0){throw "Native artifact missing: $name"};Record 'artifact' @{name=$name;bytes=$r.Bytes;sha256=(Get-FileHash -LiteralPath $p).Hash}}
$app=$null;$owned=[Collections.Generic.List[object]]::new();$failed=$false
try{
    $exe=Initialize-NativeInterop;$prior=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
    $app=New-Object -ComObject ChemDraw_x64.Application
    $new=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Where-Object {$_.Id -notin $prior -and $_.Path -eq $exe})
    $boundPid=[NativeChemDraw]::ApplicationProcess($app)
    if($app.Documents.Count -ne 0 -or $new.Count -ne 1 -or $boundPid -ne $new[0].Id){throw 'Fresh isolated process not established.'}
    Record 'isolation' @{application=$app.Name;pid=$new[0].Id;hwnd_bound_pid=$boundPid;preexisting_process_count=$prior.Count}
    $order=@{S1=0;R1=1;M1=2}
    foreach($source in @(Get-ChildItem -LiteralPath $InputDirectory -Filter '*.cdxml' -File|Sort-Object @{Expression={if($order.ContainsKey($_.BaseName)){$order[$_.BaseName]}else{3}}},Name)){
        $id=$source.BaseName
        Record 'open_intent' @{id=$id;input_sha256=(Get-FileHash -LiteralPath $source.FullName).Hash}
        $doc=[NativeChemDraw]::Open($app,$source.FullName,'text/xml');$owned.Add($doc)
        Record ('native_import_'+$id) (Snapshot $doc)
        Record ('native_smiles_'+$id) @{value=[NativeChemDraw]::Data($doc,'chemical/x-smiles')}
        Save-Checked $doc ($id+'.cdxml') 'text/xml';Save-Checked $doc ($id+'.cdx') 'chemical/x-cdx'
        Save-Checked $doc ($id+'.png') 'image/png';Save-Checked $doc ($id+'.jpg') 'image/jpeg'
        [NativeChemDraw]::Close($doc)
        foreach($ext in @('cdx','cdxml')){
            $mime=if($ext -eq 'cdx'){'chemical/x-cdx'}else{'text/xml'}
            $reopened=[NativeChemDraw]::Open($app,(Join-Path $run ($id+'.'+$ext)),$mime);$owned.Add($reopened)
            Record ('disk_reopen_'+$id+'_'+$ext) (Snapshot $reopened)
            Save-Checked $reopened ($id+'-'+$ext+'-readback.cdxml') 'text/xml'
            Record 'edit_intent' @{id=$id;source_format=$ext;edits='atom position; caption; curve control point; symbol position where present'}
            if($reopened.Atoms.Count -gt 0){$atom=$reopened.Atoms.Item(1);[NativeChemDraw]::Position($atom,$atom.Position.X+0.5,$atom.Position.Y)}
            if($reopened.Captions.Count -gt 0){$reopened.Captions.Item(1).Text+=' [edit verified]'}
            if($reopened.Splines.Count -gt 0){$s=$reopened.Splines.Item(1);$p=$s.GetPoint(3);[NativeChemDraw]::SplinePoint($s,3,$p.X,$p.Y-1.5)}
            if($reopened.Symbols.Count -gt 0){$s=$reopened.Symbols.Item(1);[NativeChemDraw]::Position($s,$s.Position.X+0.5,$s.Position.Y)}
            Save-Checked $reopened ($id+'-'+$ext+'-edited.'+$ext) $mime
            [NativeChemDraw]::Close($reopened)
            $check=[NativeChemDraw]::Open($app,(Join-Path $run ($id+'-'+$ext+'-edited.'+$ext)),$mime);$owned.Add($check)
            Record ('edit_reopened_'+$id+'_'+$ext) (Snapshot $check)
            Save-Checked $check ($id+'-'+$ext+'-edited-readback.cdxml') 'text/xml'
            [NativeChemDraw]::Close($check)
        }
    }
    Record 'complete' @{scope='native render, independent CDX/CDXML disk reopen and edited copies';semantic_visual_acceptance='separate_required'}
}catch{$failed=$true;Record 'probe_exception' (Get-NativeException $_)}finally{
    foreach($d in $owned){if([Runtime.InteropServices.Marshal]::IsComObject($d)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($d)}}
    if($null -ne $app -and [Runtime.InteropServices.Marshal]::IsComObject($app)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
    Write-Output $run
}
if($failed){exit 1}
