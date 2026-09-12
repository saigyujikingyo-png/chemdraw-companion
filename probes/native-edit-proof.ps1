param([Parameter(Mandatory)][string]$SourceDirectory,[Parameter(Mandatory)][string]$Scene,[Parameter(Mandatory)][string]$Stem,[Parameter(Mandatory)][string]$OutputDirectory)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'native-common.ps1')
$run=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $run){throw 'Evidence directory exists.'}
[void][IO.Directory]::CreateDirectory($run)
function Record($stage,$detail){[ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;detail=$detail}|ConvertTo-Json -Depth 20 -Compress|Add-Content -LiteralPath (Join-Path $run 'events.jsonl') -Encoding utf8;Write-Host $stage}
function Save-Checked($doc,$name,$mime){$r=[NativeChemDraw]::Save($doc,(Join-Path $run $name),$mime,600);Record 'save_return' $r;if(!$r.Exists -or $r.Bytes -le 0){throw 'Native save postcondition failed.'}}
. (Join-Path $PSScriptRoot 'native-snapshot.ps1')
$layout=Get-Content -LiteralPath $Scene -Raw|ConvertFrom-Json -AsHashtable
$selected=$layout.states[0];$binding=$selected.atoms.GetEnumerator()|Sort-Object {[int]$_.Key}|Select-Object -First 1
$app=$null;$owned=[Collections.Generic.List[object]]::new();$failed=$false
try{
    $exe=Initialize-NativeInterop;$prior=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
    $app=New-Object -ComObject ChemDraw_x64.Application;$new=@(Get-Process ChemDraw -ErrorAction SilentlyContinue|Where-Object {$_.Id -notin $prior -and $_.Path -eq $exe})
    if($app.Documents.Count -ne 0 -or $new.Count -ne 1 -or [NativeChemDraw]::ApplicationProcess($app) -ne $new[0].Id){throw 'Fresh application identity not established.'}
    Record 'isolation' @{application=$app.Name;pid=$new[0].Id;hwnd_process_verified=$true}
    foreach($ext in @('cdx','cdxml')){
        $mime=if($ext -eq 'cdx'){'chemical/x-cdx'}else{'text/xml'};$source=Join-Path $SourceDirectory ($Stem+'.'+$ext)
        Record 'disk_open_intent' @{format=$ext;sha256=(Get-FileHash -LiteralPath $source).Hash}
        $doc=[NativeChemDraw]::Open($app,$source,$mime);$owned.Add($doc)
        $atomLookup=@{};foreach($n in $doc.Atoms){$atomLookup[$n.ID]=$n}
        $before=Get-NativeSceneSnapshot $doc;Record ('before_'+$ext) $before
        $atom=[NativeChemDraw]::FindAtom($doc,[int]$binding.Value.native_id);$fragment=$atom.Fragment
        $movedIds=@($fragment.Atoms|ForEach-Object {$_.ID});$movedMaps=@($selected.atoms.GetEnumerator()|Where-Object {[int]$_.Value.native_id -in $movedIds}|ForEach-Object {[int]$_.Key})
        if($movedMaps.Count -ne $fragment.Atoms.Count){throw 'Fragment includes atoms outside the selected occurrence.'}
        function Port-Delta($port){if($port.state -ne $selected.id){return 0.0};if($port.type -in @('atom','lone_pair')){if($port.atom -in $movedMaps){return 3.0}else{return 0.0}};return 3.0*@($port.atoms|Where-Object {$_ -in $movedMaps}).Count/2.0}
        $curveChanges=@{}
        foreach($flow in $layout.flows){$ds=Port-Delta $flow.source;$dt=Port-Delta $flow.target;if($ds -eq 0 -and $dt -eq 0){continue};$curveChanges[[string]$flow.native_id]=@($ds,0,$ds,0,((2*$ds+$dt)/3),0,(($ds+2*$dt)/3),0,$dt,0,$dt,0)}
        $firstCurveId=[string]$layout.flows[0].native_id
        if(!$curveChanges.ContainsKey($firstCurveId)){$curveChanges[$firstCurveId]=@(0.0)*12}
        $curveChanges[$firstCurveId][5]-=.75
        $captionId=$doc.Captions.Item(1).ID;$oldText=$doc.Captions.Item(1).Text;$newText=$oldText+' [native edit proof]'
        $intent=@{version='native-edit-intent/0.2';source_format=$ext;atom_translation=@{ids=$movedIds;dx=3.0;dy=0.0};symbol_translations=@($selected.lone_pairs|Where-Object {$_.atom -in $movedMaps}|ForEach-Object {@{id=[int]$_.native_id;deltas=@(3.0,0.0,3.0,0.0)}});curve_changes=@($curveChanges.GetEnumerator()|ForEach-Object {@{id=[int]$_.Key;deltas=$_.Value}});caption_replacements=@(@{id=$captionId;from=$oldText;to=$newText})}
        Record ('motion_intent_'+$ext) $intent
        Record 'fragment_move_intent' @{source_format=$ext;state=$selected.id;atom_ids=$movedIds;dx=3.0;dy=0}
        $fragment.Objects.Move(3.0,0.0)
        foreach($old in $before.atoms){$current=$atomLookup[$old.id];$expected=$old.x+$(if($old.id -in $movedIds){3.0}else{0.0});$position=$current.Position;if([Math]::Abs($position.X-$expected) -gt 0.02 -or [Math]::Abs($position.Y-$old.y) -gt 0.02){throw 'Wrong atom changed during fragment movement.'}}
        foreach($lp in $selected.lone_pairs){
            if($lp.atom -notin $movedMaps){continue};$symbol=[NativeChemDraw]::FindSymbol($doc,[int]$lp.native_id);$old=@($before.symbols|Where-Object id -eq ([int]$lp.native_id))[0].points;$now=[NativeChemDraw]::SymbolPoints($symbol)
            if([Math]::Abs($now[0]-$old[0]) -lt .02){[NativeChemDraw]::LonePair($symbol,$old[0]+3,$old[1],$old[2]+3,$old[3])}
            elseif([Math]::Abs($now[0]-$old[0]-3) -gt .02){throw 'Unexplained electron symbol motion.'}
        }
        foreach($flow in $layout.flows){
            $ds=Port-Delta $flow.source;$dt=Port-Delta $flow.target;if($ds -eq 0 -and $dt -eq 0){continue}
            $curve=[NativeChemDraw]::FindCurve($doc,[int]$flow.native_id);$deltas=@($ds,$ds,((2*$ds+$dt)/3),(($ds+2*$dt)/3),$dt,$dt)
            for($i=1;$i -le 6;$i++){$p=$curve.GetPoint($i);[NativeChemDraw]::SplinePoint($curve,$i,$p.X+$deltas[$i-1],$p.Y)}
            Record 'companion_port_reroute' @{flow=$flow.id;source_dx=$ds;target_dx=$dt;rule='affine endpoint displacement propagated to cubic controls; no vendor anchor claim'}
        }
        $first=[NativeChemDraw]::FindCurve($doc,[int]$layout.flows[0].native_id);$point=$first.GetPoint(3);[NativeChemDraw]::SplinePoint($first,3,$point.X,$point.Y-0.75)
        $doc.Captions.Item(1).Text=$newText
        Record ('motion_edited_'+$ext) (Get-NativeSceneSnapshot $doc)
        Save-Checked $doc ($ext+'-motion.'+$ext) $mime;[NativeChemDraw]::Close($doc)
        $check=[NativeChemDraw]::Open($app,(Join-Path $run ($ext+'-motion.'+$ext)),$mime);$owned.Add($check)
        Record ('motion_reopened_'+$ext) (Get-NativeSceneSnapshot $check);Save-Checked $check ($ext+'-motion-readback.cdxml') 'text/xml'
        # Deliberately changed chemistry is confined to a labelled diagnostic.
        $changed=[NativeChemDraw]::FindAtom($check,[int]$binding.Value.native_id)
        $pair=$check.Symbols.Item(1);$removedId=$pair.ID
        $diagnosticText='DIAGNOSTIC: formal charge changed and one lone pair removed'
        Record ('diagnostic_intent_'+$ext) @{version='native-edit-intent/0.2';source_format=$ext;charge_change=@{id=$changed.ID;from=$changed.Charge;to=1};removed_symbol_id=$removedId;caption_replacements=@(@{id=$check.Captions.Item(1).ID;from=$check.Captions.Item(1).Text;to=$diagnosticText})}
        $changed.Charge=1;$pair.Delete();$check.Captions.Item(1).Text=$diagnosticText
        Record ('diagnostic_edited_'+$ext) (Get-NativeSceneSnapshot $check)
        Record 'diagnostic_charge_pair_change' @{atom_id=$changed.ID;new_charge=1;removed_pair_id=$removedId;not_accepted_chemistry=$true}
        Save-Checked $check ($ext+'-charge-pair-diagnostic.'+$ext) $mime;[NativeChemDraw]::Close($check)
        $diagnostic=[NativeChemDraw]::Open($app,(Join-Path $run ($ext+'-charge-pair-diagnostic.'+$ext)),$mime);$owned.Add($diagnostic)
        Record ('diagnostic_reopened_'+$ext) (Get-NativeSceneSnapshot $diagnostic);Save-Checked $diagnostic ($ext+'-diagnostic-readback.cdxml') 'text/xml';[NativeChemDraw]::Close($diagnostic)
    }
    Record 'complete' @{scope='native object edit control only; does not qualify composition quality';manual_active_seconds=$null}
}catch{$failed=$true;Record 'probe_exception' (Get-NativeException $_)}finally{
    foreach($d in $owned){if($null -ne $d -and [Runtime.InteropServices.Marshal]::IsComObject($d)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($d)}}
    if($null -ne $app -and [Runtime.InteropServices.Marshal]::IsComObject($app)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
    Write-Output $run
}
if($failed){exit 1}
