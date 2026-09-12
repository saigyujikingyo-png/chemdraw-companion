# Complete readback shared by native edit probes.
function Get-NativeSceneSnapshot($doc){
    return @{
        snapshot_version='native-scene/0.2'
        atoms=@($doc.Atoms|ForEach-Object{@{id=$_.ID;type='atom';element=$_.ElementNumber;charge=$_.Charge;implicit_h=$_.NumImplicitHydrogens;isotope=$_.Isotope;radical=[int]$_.Radical;stereo=[int]$_.Stereochemistry;node_type=[int]$_.NodeType;number=$_.AtomNumber;label=$_.LabelText;x=$_.Position.X;y=$_.Position.Y}})
        bonds=@($doc.Bonds|ForEach-Object{@{id=$_.ID;type='bond';a=$_.Atom1.ID;b=$_.Atom2.ID;order=[int]$_.BondOrder;display=[int]$_.BondDisplay;display2=[int]$_.BondDisplay2;stereo=[int]$_.Stereochemistry}})
        curves=@($doc.Splines|ForEach-Object{$s=$_;@{id=$s.ID;type='spline';num_points=$s.NumPoints;head=[int]$s.ArrowHeadPositionAtEnd;tail=[int]$s.ArrowHeadPositionAtStart;head_type=[int]$s.ArrowHeadType;line_type=[int]$s.LineType;fill_type=[int]$s.FillType;head_size=$s.HeadSize;head_width=$s.HeadWidth;points=@(1..$s.NumPoints|ForEach-Object{$p=$s.GetPoint($_);@($p.X,$p.Y)})}})
        symbols=@($doc.Symbols|ForEach-Object{@{id=$_.ID;type='symbol';symbol_type=[int]$_.SymbolType;is_radical=$_.IsRadical;is_charge=$_.IsCharge;points=[NativeChemDraw]::SymbolPoints($_)}})
        captions=@($doc.Captions|ForEach-Object{@{id=$_.ID;type='caption';text=$_.Text;anchor=@($_.Position.X,$_.Position.Y);left=$_.Left;top=$_.Top;family=$_.Family;size=$_.Size;face=[int]$_.Face;angle=$_.Angle;styles=@($_.Styles|ForEach-Object{@{family=$_.Family;size=$_.Size;face=[int]$_.Face}})}})
        arrows=@($doc.Arrows|ForEach-Object{@{id=$_.ID;type='arrow';start=@($_.Start.X,$_.Start.Y);end=@($_.End.X,$_.End.Y);head=[int]$_.ArrowHeadPositionStart;tail=[int]$_.ArrowHeadPositionTail;head_type=[int]$_.ArrowHeadType;line_type=[int]$_.LineType;head_size=$_.HeadSize;head_width=$_.HeadWidth}})
        warnings=$doc.NumChemicalWarnings
        style=@{bond_length=$doc.Settings.BondLength;line_width=$doc.Settings.LineWidth;label_size=$doc.Settings.LabelSize;caption_size=$doc.Settings.CaptionSize}
    }
}
