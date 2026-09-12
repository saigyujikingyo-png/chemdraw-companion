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


def verify(mechanism,scene,mapping,path):
    root=ET.parse(path).getroot();ids=[n.get('id') for n in root.iter() if n.get('id')];byid={n.get('id'):n for n in root.iter() if n.get('id')};issues=[];fingerprint=[];positions={};glyphs={};bond_lengths=[]
    if len(ids)!=len(set(ids)):issues.append('duplicate_native_ids')
    catalog={a['map']:a for a in mechanism['atom_catalog']};states={s['id']:s for s in mechanism['states']};bindings={s['id']:s for s in mapping['states']}
    if set(states)!=set(bindings):issues.append('state_inventory')
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
                bond_lengths.append(math.dist(positions[sid][pair[0]],positions[sid][pair[1]]))
            elif (b.get('B') in local)!=(b.get('E') in local):issues.append('cross_state_bond:'+sid)
        expected={bond_key(b['atoms']):b['order'] for b in state['bonds']}
        if set(expected)!=set(actual):issues.append('bond_inventory:'+sid)
        for pair,order in expected.items():
            if actual.get(pair)!=order and not(order==1.5 and actual.get(pair) in (1,2)):issues.append(f'bond_order:{sid}:{pair}')
        for atom,spec in catalog.items():
            valence=sum(v for pair,v in actual.items() if atom in pair)+spec['implicit_h']
            if spec['element'] in ('H','C') and valence!={'H':1,'C':4}[spec['element']]:issues.append(f'valence_or_h:{sid}:{atom}')
            if spec['element'] in ('N','O'):
                lp=next(x['count'] for x in state['lone_pairs'] if x['atom']==atom)
                if valence+lp!=4 or q.get(atom,0)!={'N':5,'O':6}[spec['element']]-valence-2*lp:issues.append(f'heteroatom_valence_or_h:{sid}:{atom}')
        fingerprint.append((sid,'bonds',sorted(actual.items())))
        expected_lp={x['atom']:x['count'] for x in state['lone_pairs'] if x['count']};actual_lp=Counter(x['atom'] for x in record['lone_pairs'])
        if dict(actual_lp)!=expected_lp:issues.append('lone_pair_mapping:'+sid)
        for lp in record['lone_pairs']:
            n=byid.get(lp['native_id'])
            if n is None or n.tag!='graphic' or n.get('SymbolType')!='LonePair':issues.append('lone_pair_loss:'+sid)
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
    texts=[''.join(s.text or '' for s in t.findall('s')) for t in root.iter('t')]
    for text in scene['texts']:
        if text['text'] not in texts:issues.append('caption_loss:'+text['text'])
    B=scene['style']['bond_length_pt'];outliers=[n for n in bond_lengths if abs(n-B)>B*.1]
    normalized=json.dumps(fingerprint,sort_keys=True,separators=(',',':')).encode()
    return {'file':path.name,'semantic_and_native_inventory':'pass' if not issues else 'failed','issues':issues,'counts':expected_counts,'lone_pairs':expected_symbols,'chemical_fingerprint':hashlib.sha256(normalized).hexdigest(),'curve_max_native_rounding_pt':max(deltas,default=0),'native_glyph_bbox_clearance_failures':clearance,'bond_length_pt_range':[min(bond_lengths),max(bond_lengths)],'ordinary_bond_length_outliers':len(outliers),'actual_mask_collision_acceptance':'unverified','owner_visual_review':'pending'}


def run(request,scene,mapping,folder):
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
    report={'native_results':results,'saved_source_arrow_aliases':alias_receipt,'native_warnings':warnings,'both_format_fingerprints_equal':len({r['chemical_fingerprint'] for r in results})==1,'manual_active_correction_seconds':None,'manual_edit_count':None,'base_m2':'failed_or_pending_required_quality_controls','automatic_anti_selection':'unverified_complete_ir_supplied','holdout':'not_started'}
    (folder/'composition-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--composition',type=Path,required=True);p.add_argument('--native',type=Path,required=True);a=p.parse_args();read=lambda x:json.loads(x.read_text(encoding='utf-8'))
    r=run(read(a.request),read(a.composition/'mechanism.scene.json'),read(a.composition/'mechanism.mapping.json'),a.native)
    print(json.dumps({'native_semantics':[x['semantic_and_native_inventory'] for x in r['native_results']],'native_warnings':r['native_warnings'],'issues':len(r['native_results'][0]['issues']),'bbox_clearance_failures':len(r['native_results'][0]['native_glyph_bbox_clearance_failures']),'bond_length_outliers':r['native_results'][0]['ordinary_bond_length_outliers']}))
