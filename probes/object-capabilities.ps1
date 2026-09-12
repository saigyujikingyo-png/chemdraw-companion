param([string]$EvidenceRoot=(Join-Path (Split-Path $PSScriptRoot) '.local\object-capabilities'))
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'native-common.ps1')
$run=Join-Path ([IO.Path]::GetFullPath($EvidenceRoot)) ([DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8))
[void][IO.Directory]::CreateDirectory($run)
function Record($stage,$detail){[ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;detail=$detail}|ConvertTo-Json -Depth 16 -Compress|Add-Content -LiteralPath (Join-Path $run 'events.jsonl') -Encoding utf8;Write-Host $stage}
function Snapshot($doc){
    return @{atoms=@($doc.Atoms|ForEach-Object{@{id=$_.ID;element=$_.ElementNumber;charge=$_.Charge;x=$_.Position.X;y=$_.Position.Y}});bonds=@($doc.Bonds|ForEach-Object{@{id=$_.ID;a=$_.Atom1.ID;b=$_.Atom2.ID;order=[int]$_.BondOrder}});splines=@($doc.Splines|ForEach-Object{$s=$_;@{id=$s.ID;points=@(1..$s.NumPoints|ForEach-Object{$p=$s.GetPoint($_);@($p.X,$p.Y)});num_points=$s.NumPoints;head=[int]$s.ArrowHeadPositionAtEnd}});captions=@($doc.Captions|ForEach-Object{@{id=$_.ID;text=$_.Text}});symbols=@($doc.Symbols|ForEach-Object{@{id=$_.ID;type=[int]$_.SymbolType;x=$_.Position.X;y=$_.Position.Y}});arrows=$doc.Arrows.Count;groups=$doc.Groups.Count;formula=$doc.Objects.Formula;warnings=$doc.NumChemicalWarnings}
}
function Save-Checked($doc,$name,$mime){$path=Join-Path $run $name;Record 'save_intent' @{name=$name;mime=$mime};$r=[NativeChemDraw]::Save($doc,$path,$mime,600);Record 'save_return' $r;if(!$r.Exists -or $r.Bytes -le 0){throw "Missing native artifact: $name"}}
$app=$null;$owned=[Collections.Generic.List[object]]::new();$failed=$false
try{
    $exe=Initialize-NativeInterop;$before=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
    $app=New-Object -ComObject ChemDraw_x64.Application
    $new=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Where-Object {$_.Id -notin $before -and $_.Path -eq $exe})
    if($app.Documents.Count -ne 0 -or $new.Count -ne 1){throw 'Fresh isolated process not established.'}
    Record 'isolation' @{application=$app.Name;pid=$new[0].Id;preexisting_process_count=$before.Count}
    $doc=$app.Documents.Add();$owned.Add($doc)
    $doc.Settings.LabelSize=8;$doc.Settings.CaptionSize=8;$doc.Settings.BondLength=14.4;$doc.Settings.LineWidth=0.6
    $c=$doc.MakeAtom();$c.ElementNumber=6;[NativeChemDraw]::Position($c,100,100)
    $o=$doc.MakeAtom();$o.ElementNumber=8;$o.Charge=-1;[NativeChemDraw]::Position($o,114.4,100)
    $bond=$doc.MakeBond($c,$o)
    [NativeChemDraw]::Atom($c,6,0,3);[NativeChemDraw]::Atom($o,8,-1,0)
    $caption=$doc.MakeCaption();[NativeChemDraw]::Caption($caption,'Native object control',8,95,70)
    $curve=$doc.MakeSpline();$curve.NumPoints=6
    [NativeChemDraw]::SplinePoint($curve,1,120,90);[NativeChemDraw]::SplinePoint($curve,2,120,90);[NativeChemDraw]::SplinePoint($curve,3,128,73);[NativeChemDraw]::SplinePoint($curve,4,145,73);[NativeChemDraw]::SplinePoint($curve,5,155,95);[NativeChemDraw]::SplinePoint($curve,6,155,95)
    $curve.ArrowHeadType=1;$curve.ArrowHeadPositionAtStart=1;$curve.ArrowHeadPositionAtEnd=2
    $symbol=$doc.MakeSymbol(0);[NativeChemDraw]::LonePair($symbol,113,91,116,91)
    $arrow=$doc.MakeArrow();[NativeChemDraw]::Arrow($arrow,205,100,170,100)
    Record 'created' (Snapshot $doc)
    Save-Checked $doc 'first-output.cdxml' 'text/xml';Save-Checked $doc 'first-output.jpg' 'image/jpeg'
    $group=$doc.MakeGroup();$c.Group=$group;$o.Group=$group;$bond.Group=$group
    $group.Objects.Move(12,6);Record 'fragment_moved' (Snapshot $doc)
    $group.Objects.Rotate(30,$false);Record 'fragment_rotated' (Snapshot $doc)
    $group.Objects.Scale(1.1,$false,$false);Record 'fragment_scaled' (Snapshot $doc)
    $group.Objects.Clean($true);Record 'native_cleanup' (Snapshot $doc)
    Save-Checked $doc 'objects.cdxml' 'text/xml';Save-Checked $doc 'objects.cdx' 'chemical/x-cdx';Save-Checked $doc 'objects.png' 'image/png';Save-Checked $doc 'objects.jpg' 'image/jpeg'
    [NativeChemDraw]::Close($doc)
    foreach($ext in @('cdx','cdxml')){
        $mime=if($ext -eq 'cdx'){'chemical/x-cdx'}else{'text/xml'}
        $reopened=[NativeChemDraw]::Open($app,(Join-Path $run ('objects.'+$ext)),$mime);$owned.Add($reopened)
        Record ('disk_reopen_'+$ext) (Snapshot $reopened)
        if($reopened.Atoms.Count -ne 2 -or $reopened.Bonds.Count -ne 1 -or $reopened.Splines.Count -ne 1 -or $reopened.Symbols.Count -ne 1){throw 'Native object loss on reopen.'}
        $ro=@($reopened.Atoms|Where-Object ElementNumber -eq 8)[0];$ro.Charge=0
        $reopened.Bonds.Item(1).BondOrder=2
        $reopened.Captions.Item(1).Text='Edited after '+$ext+' disk reopen'
        $rs=$reopened.Splines.Item(1);$rp=$rs.GetPoint(1);[NativeChemDraw]::SplinePoint($rs,1,$rp.X,$rp.Y-3)
        $rl=$reopened.Symbols.Item(1);[NativeChemDraw]::Position($rl,$rl.Position.X+2,$rl.Position.Y)
        Record ('edited_'+$ext) (Snapshot $reopened)
        Save-Checked $reopened ($ext+'-edited.cdxml') 'text/xml'
        [NativeChemDraw]::Close($reopened)
        $check=[NativeChemDraw]::Open($app,(Join-Path $run ($ext+'-edited.cdxml')),'text/xml');$owned.Add($check)
        Record ('edit_reopened_'+$ext) (Snapshot $check)
        if($check.Bonds.Item(1).BondOrder -ne 2 -or $check.Captions.Item(1).Text -notmatch 'Edited after'){throw 'Object edits did not survive disk roundtrip.'}
        [NativeChemDraw]::Close($check)
    }
    Record 'complete' @{scope='object control capability probe';mechanism_quality='not_established'}
}catch{$failed=$true;Record 'probe_exception' (Get-NativeException $_)}finally{
    foreach($d in $owned){if([Runtime.InteropServices.Marshal]::IsComObject($d)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($d)}}
    if($null -ne $app -and [Runtime.InteropServices.Marshal]::IsComObject($app)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
    Write-Output $run
}
if($failed){exit 1}
