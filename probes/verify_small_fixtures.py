"""Test-only S1/R1/M1 graph, object and disk comparison. Not a Composer."""
import argparse,copy,json,math
from pathlib import Path
import xml.etree.ElementTree as ET
from verify_composition import actual_hydrogens,numbers,cubic,point_box,white_canvas
from verify_native_edits import expected_motion,account_changed_text_bounds,compare
from acyclic_smiles_check import same_stereo

EXPECTED={
 'alanine':({1:(7,1),2:(6,0),3:(6,0),4:(6,0),5:(8,0),6:(8,-1)},{(1,2):1,(2,3):1,(2,4):1,(4,5):2,(4,6):1}),
 'hydroxide':({1:(8,-1)},{}),'bromomethane':({2:(6,0),3:(35,0)},{(2,3):1}),
 'methanol':({1:(8,0),2:(6,0)},{(1,2):1}),'bromide':({3:(35,-1)},{}),
}
HYDROGENS={'alanine':{1:3,2:1,3:3,4:0,5:0,6:0},'hydroxide':{1:1},'bromomethane':{2:3,3:0},'methanol':{1:1,2:3},'bromide':{3:0}}


def verify(scene,path):
    root=ET.parse(path).getroot();nodes={n.get('id'):n for n in root.iter() if n.get('id')};issues=[];positions={};glyphs={};h_readback=[];B=scene['style']['bond_pt'];font=scene['style']['label_pt'];lengths=[]
    for component in scene['components']:
        expected_atoms,expected_bonds=EXPECTED[component['kind']];local={}
        for label,data in component['native_atom_bindings'].items():
            atom=int(label);nid=data['native_id'];local[nid]=atom;n=nodes.get(nid)
            if n is None or (int(n.get('Element',6)),int(n.get('Charge',0)))!=expected_atoms[atom]:issues.append('atom:'+component['id']+':'+label)
            positions[(component['id'],atom)]=numbers(n.get('p'))
            if n.get('Isotope') not in (None,'0'):issues.append('isotope:'+component['id']+':'+label)
            if n.find('t') is not None:glyphs[(component['id'],atom)]=numbers(n.find('t').get('BoundingBox'))
        actual={tuple(sorted((local[b.get('B')],local[b.get('E')]))):float(b.get('Order',1)) for b in root.iter('b') if b.get('B') in local and b.get('E') in local}
        if actual!=expected_bonds:issues.append('bonds:'+component['id'])
        for label,data in component['native_atom_bindings'].items():
            atom=int(label);n=nodes[data['native_id']];valence=sum(v for pair,v in actual.items() if atom in pair)
            try:
                if int(n.get('Element',6))==35:
                    h=int(n.get('NumHydrogens','0'))
                    if h!=0 or valence!=1+int(n.get('Charge',0)):raise ValueError('Br valence')
                    method='native_Br_valence_and_zero_H'
                else:h,method=actual_hydrogens(n,valence)
                if h!=HYDROGENS[component['kind']][atom]:issues.append('hydrogens:'+component['id']+':'+label)
                h_readback.append({'component':component['id'],'atom':atom,'h':h,'method':method})
            except ValueError:issues.append('invalid_hydrogens:'+component['id']+':'+label)
        for a,b in actual:lengths.append(math.dist(positions[(component['id'],a)],positions[(component['id'],b)]))
        stereo=[{'atoms':[local[b.get('B')],local[b.get('E')]],'display':b.get('Display')} for b in root.iter('b') if b.get('B') in local and ('Wedge' in b.get('Display','') or 'Hash' in b.get('Display',''))]
        if stereo!=component.get('directed_stereo_bonds',[]):issues.append('directed_stereo_bonds:'+component['id'])
        if stereo:
            # A reflected plane with the same wedge marker reverses chirality.
            keys=sorted(map(int,component['native_atom_bindings']))[:3]
            expected=[(component['native_atom_bindings'][str(i)]['x'],component['native_atom_bindings'][str(i)]['y']) for i in keys]
            actual_points=[positions[(component['id'],i)] for i in keys]
            signed=lambda p:(p[1][0]-p[0][0])*(p[2][1]-p[0][1])-(p[1][1]-p[0][1])*(p[2][0]-p[0][0])
            if signed(expected)*signed(actual_points)<=0:issues.append('stereo_plane_reflection')
    for caption in scene['captions']:
        if caption['text'] not in [''.join(s.text or '' for s in t.findall('s')) for t in root.iter('t')]:issues.append('caption:'+caption['text'])
    pairs={};ports=[];attack_angle=None
    for pair in scene.get('lone_pairs',[]):
        n=nodes.get(pair['native_id'])
        if n is None or n.get('SymbolType')!='LonePair':issues.append('lone_pair_type');continue
        bb=numbers(n.get('BoundingBox'));center=((bb[0]+bb[2])/2,(bb[1]+bb[3])/2);key=(pair['component'],pair['atom_map']);pairs[key]=center
        if not .2*B<=math.dist(center,positions[key])<=1.1*B:issues.append('detached_lone_pair')
    for f in scene['flows']:
        n=nodes.get(f['native_id'])
        if n is None or n.tag!='curve' or n.get('ArrowheadHead')!='Full' or len(n.get('CurvePoints','').split())!=12:issues.append('curve:'+f['id'])
        if n is None or len(n.get('CurvePoints','').split())!=12:continue
        values=numbers(n.get('CurvePoints'));points=list(zip(values[::2],values[1::2]));native=[points[0],points[2],points[3],points[5]]
        if max(math.dist(a,b) for a,b in zip(native,f['bezier']))>.02:issues.append('curve_readback_geometry:'+f['id'])
        for side,point in [('source',native[0]),('target',native[-1])]:
            port=f[side];key=(port['component'],port.get('atom_map'))
            if port['type']=='lone_pair':distance=math.dist(point,pairs[key])
            elif port['type']=='bond':
                a,b=(positions[(port['component'],i)] for i in port['atom_maps']);distance=math.dist(point,((a[0]+b[0])/2,(a[1]+b[1])/2))
            elif key in glyphs:
                box=glyphs[key];distance=point_box(point,box)
                if box[0]<point[0]<box[2] and box[1]<point[1]<box[3]:distance=1e9
            else:distance=abs(math.dist(point,positions[key])-B/6)
            ports.append({'flow':f['id'],'side':side,'deviation_pt':distance})
            limit=B*.20+(scene.get('native_head_metrics',{}).get('conservative_forward_extension_pt',0) if side=='target' else 0)
            if distance>limit:issues.append('native_control_anchor:'+f['id']+':'+side)
        if f['id']=='attack':
            carbon=positions[('substrate',2)];leaving=positions[('substrate',3)];approach=(native[3][0]-native[2][0],native[3][1]-native[2][1]);bond=(leaving[0]-carbon[0],leaving[1]-carbon[1]);cosine=sum(a*b for a,b in zip(approach,bond))/(math.hypot(*approach)*math.hypot(*bond));attack_angle=math.degrees(math.acos(max(-1,min(1,cosine))))
            if attack_angle>30:issues.append('backside_attack_angle')
    target_atoms=sum(len(c['native_atom_bindings']) for c in scene['components']);target_bonds=sum(len(EXPECTED[c['kind']][1]) for c in scene['components'])
    if len(list(root.iter('n')))!=target_atoms or len(list(root.iter('b')))!=target_bonds:issues.append('atom_bond_count')
    if len(list(root.iter('curve')))!=len(scene['flows']):issues.append('curve_count')
    if len([g for g in root.iter('graphic') if g.get('SymbolType')=='LonePair'])!=len(scene.get('lone_pairs',[])):issues.append('lone_pair_count')
    wedges=[b.attrib for b in root.iter('b') if 'Wedge' in b.get('Display','') or 'WedgedHash' in b.get('Display','')]
    if scene['fixture']=='S1' and not wedges:issues.append('missing_stereo_wedge')
    if scene['fixture'] in ('R1','M1') and len(list(root.iter('arrow')))!=1:issues.append('step_arrow_count')
    fonts={f.get('id'):f.get('name') for f in root.findall('fonttable/font')}
    if any(abs(float(s.get('size','nan'))-font)>.001 or not math.isfinite(float(s.get('size','nan'))) or fonts.get(s.get('font'))!=scene['style']['font'] for s in root.iter('s')):issues.append('actual_text_run_style')
    if any(abs(length-B)>.10*B for length in lengths):issues.append('ordinary_bond_length')
    width,height=(v*72/25.4 for v in scene['canvas_mm']);outside=[]
    for n in root.iter():
        if n.tag not in ('n','t','graphic','curve','arrow') or n.get('SupersededBy') or white_canvas(n,width,height):continue
        points=[]
        if n.get('p'):points.append(numbers(n.get('p')))
        if n.get('BoundingBox'):
            a,b,c,d=numbers(n.get('BoundingBox'));points.extend([(a,b),(c,d)])
        if any(not(.01<p[0]<width-.01 and .01<p[1]<height-.01) for p in points):outside.append(n.get('id',n.tag))
    if outside:issues.append('page_containment')
    return {'file':path.name,'graph_and_object_readback':'pass' if not issues else 'failed','issues':issues,'atom_count':target_atoms,'bond_count':target_bonds,'native_hydrogens':h_readback,'native_ports':ports,'backside_attack_degrees':attack_angle,'actual_font_pt':sorted({float(s.get('size')) for s in root.iter('s')}),'bond_length_range_pt':[min(lengths),max(lengths)],'outside_canvas':outside,'visible_stereo_wedges':len(wedges),'absolute_cip_assignment':'not_claimed_input_stereo_preservation_checked_separately','quality_and_owner_review':'pending_native_masks_and_owner'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--composition',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--report',type=Path);a=p.parse_args();results=[]
    events=[json.loads(line) for line in (a.native/'events.jsonl').read_text(encoding='utf-8-sig').splitlines()];stage={e['stage']:e['detail'] for e in events};indices={e['stage']:i for i,e in enumerate(events)}
    for fixture in ('S1','R1','M1'):
        scene=json.loads((a.composition/(fixture+'.scene.json')).read_text(encoding='utf-8'))
        edits=[]
        for ext in ('cdx','cdxml'):
            suffix=fixture+'_'+ext;issues=[]
            try:
                names=[v+suffix for v in ('before_','motion_intent_','motion_edited_','motion_reopened_')]
                if [indices[n] for n in names]!=sorted(indices[n] for n in names):raise ValueError('Event order')
                before,intent,edited,reopened=(stage[n] for n in names);expected=expected_motion(before,intent);account_changed_text_bounds(expected,edited,intent);issues+=compare(expected,edited)+compare(edited,reopened)
                if before['warnings']!=0:issues.append('native_warnings')
            except (KeyError,ValueError,TypeError) as exc:issues.append('incomplete_native_edit_evidence:'+str(exc))
            edits.append({'format':ext,'status':'pass' if not issues else 'failed','issues':issues})
        stereo='not_applicable'
        if fixture=='S1':
            source=json.loads((Path(__file__).parent/'fixtures/s1-r1-m1-fragments.json').read_text(encoding='utf-8'))[0]['smiles']
            try:stereo='pass' if all(same_stereo(source,stage[key]['value']) for key in ['native_smiles_S1','disk_smiles_S1_cdx','disk_smiles_S1_cdxml']) else 'failed'
            except (KeyError,ValueError):stereo='failed_or_missing_native_smiles'
        results.append({'fixture':fixture,'checks':[verify(scene,a.native/name) for name in (fixture+'.cdxml',fixture+'-cdx-readback.cdxml',fixture+'-cdxml-readback.cdxml')],'native_edit_checks':edits,'input_tetrahedral_stereo_preservation':stereo,'native_warnings':[stage[key]['warnings'] for key in ['native_import_'+fixture,'disk_reopen_'+fixture+'_cdx','disk_reopen_'+fixture+'_cdxml']],'manual_active_correction_seconds':None})
    report={'results':results,'native_quality_acceptance':'pending_final_size_masks_and_owner_review'}
    destination=a.report or a.native/'small-fixture-verification.json'
    if destination.exists():raise FileExistsError(destination)
    destination.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({'scope':'Native semantics, declared edits, style, containment and ports; masks/owner acceptance separate','results':[{'fixture':r['fixture'],'issues':[c['issues'] for c in r['checks']],'stereo':r['input_tetrahedral_stereo_preservation'],'edit_checks':r['native_edit_checks'],'warnings':r['native_warnings']} for r in results]}))
    raise SystemExit(0 if all(c['graph_and_object_readback']=='pass' for r in results for c in r['checks']) and all(e['status']=='pass' for r in results for e in r['native_edit_checks']) and all(r['input_tetrahedral_stereo_preservation'] in ('pass','not_applicable') and not any(r['native_warnings']) for r in results) else 1)
