"""Independent, input-sized native CDXML verifier. Never used by generation."""
from __future__ import annotations
import argparse,copy,hashlib,json,math
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET


def numbers(value):return tuple(map(float,value.split()))
def bond_key(pair):return tuple(sorted(pair))
def point_box(p,b):return math.hypot(max(b[0]-p[0],0,p[0]-b[2]),max(b[1]-p[1],0,p[1]-b[3]))
def cubic(p,t):return tuple((1-t)**3*p[0][k]+3*(1-t)**2*t*p[1][k]+3*(1-t)*t*t*p[2][k]+t**3*p[3][k] for k in (0,1))


def white_canvas(node,width,height):
    if node.tag!='graphic' or node.get('GraphicType')!='Rectangle' or node.get('color') not in ('1','2'):return False
    box=numbers(node.get('BoundingBox',''))
    return len(box)==4 and max(abs(a-b) for a,b in zip(box,(0,0,width,height)))<.05 and float(node.get('LineWidth','1'))<=.02


def actual_hydrogens(node,bond_valence):
    """CDXML explicit count takes precedence; otherwise infer from native graph.

    This narrow closed-shell inference does not read the intended IR H count.
    Unsupported valence/charge/radical representations must not be certified.
    """
    element=int(node.get('Element','6'));charge=int(node.get('Charge','0'))
    if node.get('Radical') not in (None,'None'):raise ValueError('Unsupported native radical')
    valence={1:1,6:4,7:3+charge,8:2+charge}.get(element)
    if valence is None:raise ValueError('Unsupported native hydrogen inference')
    if 'NumHydrogens' in node.attrib:
        count=int(node.get('NumHydrogens'));source='native_NumHydrogens'
    else:
        value=valence-bond_valence
        if value<0 or value!=int(value):raise ValueError('Ambiguous native inferred hydrogens')
        count=int(value);source='native_graph_valence'
    if count<0 or bond_valence+count!=valence:raise ValueError('Native H/valence mismatch')
    return count,source


def port_distance(point,port,positions,glyphs,pairs,state,B):
    if port['type']=='lone_pair':return math.dist(point,pairs[(port['atom'],port['pair_index'])])
    if port['type']=='bond':
        a,b=(positions[i] for i in port['atoms']);mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
        if 'electrons' in port:return math.dist(point,mid)
        length=math.dist(a,b)
        if length==0:return float('inf')
        normal=(-(b[1]-a[1])/length,(b[0]-a[0])/length)
        return min(math.dist(point,(mid[0]+sign*B*.15*normal[0],mid[1]+sign*B*.15*normal[1])) for sign in (-1,1))
    atom=port['atom'];center=positions[atom];box=glyphs.get((state,atom))
    if box:
        if box[0]<point[0]<box[2] and box[1]<point[1]<box[3]:return float('inf')
        return point_box(point,box)
    return abs(math.dist(point,center)-B/6)


def verify(mechanism,scene,mapping,path):
    root=ET.parse(path).getroot();ids=[n.get('id') for n in root.iter() if n.get('id')];byid={n.get('id'):n for n in root.iter() if n.get('id')};issues=[];fingerprint=[];positions={};glyphs={};bond_lengths=[]
    if len(ids)!=len(set(ids)):issues.append('duplicate_native_ids')
    catalog={a['map']:a for a in mechanism['atom_catalog']};states={s['id']:s for s in mechanism['states']};bindings={s['id']:s for s in mapping['states']};native_pairs={};B=scene['style']['bond_length_pt'];hydrogen_readback=[]
    if set(states)!=set(bindings):issues.append('state_inventory')
    if len(bindings)!=len(mapping['states']):issues.append('duplicate_state_mapping')
    declared={f['id']:{'source':{'state':t['from'],**f['source']},'target':{'state':t['from'],**f['target']}} for t in mechanism['transitions'] for f in t['electron_flows']}
    if {f['id'] for f in mapping['flows']}!=set(declared) or len(mapping['flows'])!=len(declared):issues.append('flow_binding_inventory')
    for f in mapping['flows']:
        if f['id'] not in declared or any(f[side]!=declared[f['id']][side] for side in ('source','target')):issues.append('flow_semantic_binding:'+f['id'])
    for sid,state in states.items():
        record=bindings[sid];q={x['atom']:x['value'] for x in state['formal_charges']};local={};positions[sid]={}
        if set(map(int,record['atoms']))!=set(catalog):issues.append('mapped_atom_inventory:'+sid)
        for key,data in record['atoms'].items():
            atom=int(key);n=byid.get(data['native_id']);local[data['native_id']]=atom
            if n is None or n.tag!='n':issues.append(f'missing_atom:{sid}:{atom}');continue
            properties=(int(n.get('Element','6')),int(n.get('Charge','0')),n.get('AtomNumber'))
            expected=({'H':1,'C':6,'N':7,'O':8}[catalog[atom]['element']],q.get(atom,0),str(atom))
            if properties!=expected:issues.append(f'atom_semantics:{sid}:{atom}')
            positions[sid][atom]=numbers(n.get('p'));fingerprint.append((sid,atom,properties))
            for t in n.findall('t'):
                if t.get('BoundingBox'):glyphs[(sid,atom)]=numbers(t.get('BoundingBox'))
        actual={};native_h={}
        for b in root.iter('b'):
            if b.get('B') in local and b.get('E') in local:
                pair=bond_key((local[b.get('B')],local[b.get('E')]));actual[pair]=float(b.get('Order','1'))
                if 'Wedge' in b.get('Display','') or 'Hash' in b.get('Display',''):issues.append('unsupported_native_tetrahedral_stereo:'+sid)
                bond_lengths.append(math.dist(positions[sid][pair[0]],positions[sid][pair[1]]))
            elif (b.get('B') in local)!=(b.get('E') in local):issues.append('cross_state_bond:'+sid)
        expected={bond_key(b['atoms']):b['order'] for b in state['bonds']}
        if set(expected)!=set(actual):issues.append('bond_inventory:'+sid)
        for pair,order in expected.items():
            if actual.get(pair)!=order and not(order==1.5 and actual.get(pair) in (1,2)):issues.append(f'bond_order:{sid}:{pair}')
        for atom,spec in catalog.items():
            bond_valence=sum(v for pair,v in actual.items() if atom in pair)
            n=byid[record['atoms'][str(atom)]['native_id']]
            try:
                native_h,source=actual_hydrogens(n,bond_valence)
                if native_h!=spec['implicit_h']:issues.append(f'native_hydrogens:{sid}:{atom}')
                hydrogen_readback.append({'state':sid,'atom':atom,'count':native_h,'source':source})
                fingerprint.append((sid,atom,'native_hydrogens',native_h))
            except (ValueError,TypeError):
                native_h=-100;issues.append(f'native_hydrogen_representation:{sid}:{atom}')
                fingerprint.append((sid,atom,'invalid_native_hydrogens',n.get('NumHydrogens')))
            if n.get('Isotope') not in (None,'0'):issues.append(f'unexpected_isotope:{sid}:{atom}')
            valence=bond_valence+native_h
            if spec['element'] in ('H','C') and valence!={'H':1,'C':4}[spec['element']]:issues.append(f'valence_or_h:{sid}:{atom}')
            if spec['element'] in ('N','O'):
                lp=next(x['count'] for x in state['lone_pairs'] if x['atom']==atom)
                if valence+lp!=4 or q.get(atom,0)!={'N':5,'O':6}[spec['element']]-valence-2*lp:issues.append(f'heteroatom_valence_or_h:{sid}:{atom}')
        fingerprint.append((sid,'bonds',sorted(actual.items())))
        expected_lp={x['atom']:x['count'] for x in state['lone_pairs'] if x['count']};actual_lp=Counter(x['atom'] for x in record['lone_pairs'])
        if dict(actual_lp)!=expected_lp:issues.append('lone_pair_mapping:'+sid)
        if len({p['native_id'] for p in record['lone_pairs']})!=len(record['lone_pairs']):issues.append('duplicate_lone_pair_binding:'+sid)
        for lp in record['lone_pairs']:
            n=byid.get(lp['native_id'])
            if n is None or n.tag!='graphic' or n.get('SymbolType')!='LonePair':issues.append('lone_pair_loss:'+sid);continue
            if not n.get('BoundingBox'):issues.append('lone_pair_geometry_missing:'+sid);continue
            box=numbers(n.get('BoundingBox'));center=((box[0]+box[2])/2,(box[1]+box[3])/2);native_pairs[(sid,lp['atom'],lp['pair_index'])]=center
            atom_position=positions[sid][lp['atom']];distance=math.dist(center,atom_position)
            # The electron inventory and atom association come from IR; the
            # association's actual geometric validity comes from readback.
            if not B*.2<=distance<=B*1.1:issues.append(f'detached_lone_pair:{sid}:{lp["atom"]}:{lp["pair_index"]}')
    for relation in mechanism['stereo_constraints']:
        a,b=relation['central_bond'];x,y=relation['substituent_atoms']
        for sid in relation['states']:
            ps=positions[sid];d=(ps[b][0]-ps[a][0],ps[b][1]-ps[a][1]);cross=lambda p,q:d[0]*(q[1]-p[1])-d[1]*(q[0]-p[0]);v=cross(ps[a],ps[x])*cross(ps[b],ps[y])
            if not(v<0 if relation['type']=='anti_across_double_bond' else v>0):issues.append('stereo_relation:'+sid)
    expected_counts={'n':len(catalog)*len(states),'b':sum(len(s['bonds']) for s in states.values()),'curve':sum(len(t['electron_flows']) for t in mechanism['transitions']),'arrow':len(mechanism['transitions'])}
    for tag,count in expected_counts.items():
        if len(list(root.iter(tag)))!=count:issues.append('global_inventory:'+tag)
    expected_symbols=sum(x['count'] for s in states.values() for x in s['lone_pairs'])
    if len([n for n in root.iter('graphic') if n.get('SymbolType')=='LonePair'])!=expected_symbols:issues.append('global_lone_pair_inventory')
    deltas=[];clearance=[];target_deviations=[]
    for flow in mapping['flows']:
        n=byid.get(flow['native_id'])
        if n is None or n.tag!='curve':issues.append('curve_loss:'+flow['id']);continue
        values=numbers(n.get('CurvePoints',''));points=list(zip(values[::2],values[1::2]));p=flow['bezier'];want=[p[0],p[0],p[1],p[2],p[3],p[3]]
        delta=max((math.dist(a,b) for a,b in zip(points,want)),default=1e9) if len(points)==6 else 1e9;deltas.append(delta)
        if delta>.02 or n.get('ArrowheadHead')!='Full':issues.append('curve_geometry:'+flow['id'])
        if len(points)==6:
            native=[points[0],points[2],points[3],points[5]];hits=[];minimum=1e9
            sid=flow['source']['state'];pairs={(a,k):p for (s,a,k),p in native_pairs.items() if s==sid}
            for side,point in (('source',native[0]),('target',native[-1])):
                try:distance=port_distance(point,flow[side],positions[sid],glyphs,pairs,sid,B)
                except (KeyError,ValueError):distance=float('inf')
                target_deviations.append({'flow':flow['id'],'side':side,'deviation_pt':distance if math.isfinite(distance) else None})
                if not math.isfinite(distance) or distance>B*.20:issues.append(f'native_anchor:{flow["id"]}:{side}')
            for occurrence,box in glyphs.items():
                if occurrence[0]!=flow['source']['state']:continue
                distance=min(point_box(cubic(native,t/100),box) for t in range(7,94));minimum=min(minimum,distance)
                if distance<scene['style']['bond_length_pt']*.18:hits.append({'atom':occurrence[1],'distance_pt':distance})
            if hits:clearance.append({'flow':flow['id'],'glyph_bbox_clearance_pt':minimum,'contacts':hits})
    for connector in mapping['connectors']:
        n=byid.get(connector['native_id'])
        # The native writer retains the input ID on a legacy line graphic and
        # explicitly links it to the current arrow object. Never infer by order.
        visited=set()
        while n is not None and n.get('SupersededBy'):
            if n.get('id') in visited:issues.append('cyclic_native_alias:'+connector['id']);break
            visited.add(n.get('id'));n=byid.get(n.get('SupersededBy'))
        if n is None or n.tag!='arrow' or n.get('ArrowheadHead')!='Full':issues.append('step_arrow_loss:'+connector['id'])
        elif max(math.dist(numbers(n.get('Tail3D'))[:2],connector['path'][0]),math.dist(numbers(n.get('Head3D'))[:2],connector['path'][1]))>.02:issues.append('step_arrow_geometry:'+connector['id'])
    texts=[''.join(s.text or '' for s in t.findall('s')) for t in root.findall('page/t')]
    if Counter(texts)!=Counter(t['text'] for t in scene['texts']):issues.append('caption_inventory_or_type')
    for text in scene['texts']:
        if text['text'] not in texts:issues.append('caption_loss:'+text['text'])
    fonts={f.get('id'):f.get('name') for f in root.findall('fonttable/font')}
    for run in root.iter('s'):
        size=float(run.get('size','nan'))
        if not math.isfinite(size) or abs(size-scene['style']['font_pt'])>.001 or fonts.get(run.get('font'))!=scene['style']['font_family']:issues.append('native_text_run_style');break
    width,height=scene['width_pt'],scene['height_pt'];containment=[]
    for n in root.iter():
        if n.tag not in ('n','t','graphic','curve','arrow'):continue
        if n.get('SupersededBy'):continue
        if white_canvas(n,width,height):continue
        points=[]
        if n.get('p'):points.append(numbers(n.get('p')))
        if n.get('BoundingBox'):
            x,y,z,w=numbers(n.get('BoundingBox'));points.extend(((x,y),(z,w)))
        if n.tag=='curve' and n.get('CurvePoints'):
            values=numbers(n.get('CurvePoints'));p=list(zip(values[::2],values[1::2]))
            if len(p)==6:points.extend(cubic([p[0],p[2],p[3],p[5]],i/100) for i in range(101))
        if any(not(.01<=p[0]<=width-.01 and .01<=p[1]<=height-.01) for p in points):containment.append(n.get('id',n.tag))
    if containment:issues.append('page_containment')
    outliers=[n for n in bond_lengths if abs(n-B)>B*.1]
    normalized=json.dumps(fingerprint,sort_keys=True,separators=(',',':')).encode()
    return {'file':path.name,'semantic_and_native_inventory':'pass' if not issues else 'failed','issues':issues,'counts':expected_counts,'lone_pairs':expected_symbols,'native_hydrogen_readback':hydrogen_readback,'native_port_deviations':target_deviations,'out_of_page_objects':containment,'chemical_fingerprint':hashlib.sha256(normalized).hexdigest(),'curve_max_native_rounding_pt':max(deltas,default=0),'native_glyph_bbox_clearance_failures':clearance,'bond_length_pt_range':[min(bond_lengths),max(bond_lengths)],'ordinary_bond_length_outliers':len(outliers),'actual_mask_collision_acceptance':'unverified','owner_visual_review':'pending'}


def run(request,scene,mapping,folder,report_path=None):
    first=folder/'mechanism.cdxml';results=[verify(request['mechanism'],scene,mapping,first)]
    # Bind each subsequent disk open to IDs emitted by its actual saved source,
    # not the pre-import document. Each export may replace the legacy alias.
    updated=copy.deepcopy(mapping);nodes={n.get('id'):n for n in ET.parse(first).getroot().iter() if n.get('id')};alias_receipt=[]
    for connector in updated['connectors']:
        old=connector['native_id'];n=nodes[old];seen=set()
        while n.get('SupersededBy'):
            if n.get('id') in seen:raise ValueError('Cyclic native alias')
            seen.add(n.get('id'));n=nodes[n.get('SupersededBy')]
        connector['native_id']=n.get('id');alias_receipt.append({'semantic_id':connector['id'],'input_native_id':old,'saved_native_id':n.get('id'),'evidence':'explicit SupersededBy chain in saved source'})
    results += [verify(request['mechanism'],scene,updated,folder/name) for name in ('mechanism-cdx-readback.cdxml','mechanism-cdxml-readback.cdxml')]
    events=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    warnings=[e['detail']['warnings'] for e in events if e['stage'].startswith(('native_import_','disk_reopen_'))]
    same=len({r['chemical_fingerprint'] for r in results})==1
    readback='pass' if same and len(warnings)==3 and not any(warnings) and all(r['semantic_and_native_inventory']=='pass' for r in results) else 'failed'
    known_geometry_fail=any(r['native_glyph_bbox_clearance_failures'] or r['ordinary_bond_length_outliers'] for r in results)
    report={'native_results':results,'saved_source_arrow_aliases':alias_receipt,'native_warnings':warnings,'both_format_fingerprints_equal':same,'readback_gate':readback,'full_quality_gate':'failed' if readback=='failed' or known_geometry_fail else 'blocked_required_native_masks_visible_head_ports_and_owner_review','manual_active_correction_seconds':None,'manual_edit_count':None,'automatic_anti_selection':'unverified_complete_ir_supplied','holdout':'not_started'}
    destination=report_path or folder/'composition-verification.json'
    if destination.exists():raise FileExistsError(destination)
    destination.write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--composition',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--report',type=Path);p.add_argument('--scope',choices=['readback','full'],default='full');a=p.parse_args();read=lambda x:json.loads(x.read_text(encoding='utf-8'))
    r=run(read(a.request),read(a.composition/'mechanism.scene.json'),read(a.composition/'mechanism.mapping.json'),a.native,a.report)
    print(json.dumps({'native_semantics':[x['semantic_and_native_inventory'] for x in r['native_results']],'native_warnings':r['native_warnings'],'issues':len(r['native_results'][0]['issues']),'bbox_clearance_failures':len(r['native_results'][0]['native_glyph_bbox_clearance_failures']),'bond_length_outliers':r['native_results'][0]['ordinary_bond_length_outliers']}))
    raise SystemExit(0 if r['readback_gate' if a.scope=='readback' else 'full_quality_gate']=='pass' else 1)
