"""Diagnostic transformations of declared inputs, outside production generation.

This exercises opaque identity and storage/orientation changes, not an unseen
chemical holdout. Existing measured fragments are explicit test controls only.
"""
from __future__ import annotations
import argparse,copy,json,math,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.chemical_ir import validate_request,validate_semantics,linear_order,connected_components
from runtime.mechanism_composer import compose,rotate_component
from runtime.adapters.chemdraw_cdxml import materialize
from scene_equivalence import compare as compare_scenes


def relabel(payload,geometry):
    result=copy.deepcopy(payload);m=result['mechanism'];rng=random.Random(271828)
    values=list(range(1001,1001+len(m['atom_catalog'])));rng.shuffle(values);atom_map={a['map']:j for a,j in zip(m['atom_catalog'],values)}
    names=[f'opaque-{i*31+13}' for i in range(len(m['states']))];rng.shuffle(names);state_map={s['id']:n for s,n in zip(m['states'],names)}
    def port(p):
        if 'atom' in p:p['atom']=atom_map[p['atom']]
        if 'atoms' in p:p['atoms']=[atom_map[i] for i in p['atoms']]
    m['entry_state']=state_map[m['entry_state']]
    for a in m['atom_catalog']:a['map']=atom_map[a['map']]
    for s in m['states']:
        s['id']=state_map[s['id']]
        for key in ('bonds','formal_charges','lone_pairs'):
            for x in s[key]:port(x)
            rng.shuffle(s[key])
    for i,t in enumerate(m['transitions']):
        t['id']=f'edge-{89-i*7}';t['from']=state_map[t['from']];t['to']=state_map[t['to']]
        for j,f in enumerate(t['electron_flows']):f['id']=f'electron-{i*53+j*11}';port(f['source']);port(f['target'])
        for key in ('bond_changes','charge_changes'):
            for x in t[key]:port(x)
            rng.shuffle(t[key])
        rng.shuffle(t['electron_flows'])
    for r in m['stereo_constraints']:
        r['states']=[state_map[s] for s in r['states']]
        for k in ('central_bond','substituent_atoms'):r[k]=[atom_map[i] for i in r[k]]
    for k in ('states','transitions','atom_catalog','stereo_constraints'):rng.shuffle(m[k])
    renamed={}
    for sid,g in geometry.items():
        g=copy.deepcopy(g);g['atoms']={atom_map[i]:a for i,a in g['atoms'].items()}
        for b in g['bonds']:b['atoms']=[atom_map[i] for i in b['atoms']]
        renamed[state_map[sid]]=g
    return result,renamed,atom_map,state_map


def positions(scene):return {s['id']:{a['map']:a['position'] for c in s['components'] for a in c['atoms']} for s in scene['states']}


def run(payload,geometry,out):
    out.mkdir(parents=True,exist_ok=False);m,style=validate_request(payload);baseline=compose(m,style,geometry);basepos=positions(baseline);records=[]
    for label in ('catalog_order_only','electron_flow_order_only','bond_endpoint_order_only'):
        altered=copy.deepcopy(m)
        if label=='catalog_order_only':altered['atom_catalog'].reverse()
        elif label=='electron_flow_order_only':
            for t in altered['transitions']:t['electron_flows'].reverse()
        else:
            for state in altered['states']:
                for bond in state['bonds']:bond['atoms'].reverse()
        validate_semantics(altered);changed=compose(altered,style,geometry)
        records.append({'case':label,'scene_equivalence':compare_scenes(baseline,changed,m),'clearance_failures':len(changed['layout_diagnostics']['curve_clearance_failures'])})
    altered,renamed,am,sm=relabel(payload,geometry);nm,ns=validate_request(altered);changed=compose(nm,ns,renamed);pos=positions(changed)
    maximum=max(math.dist(p,pos[sm[sid]][am[i]]) for sid,atoms in basepos.items() for i,p in atoms.items())
    records.append({'case':'bijective_ids_and_shuffled_arrays','max_mapped_atom_displacement_pt':maximum,'scene_equivalence':compare_scenes(baseline,changed,m,am,sm),'counts':validate_semantics(nm),'clearance_failures':len(changed['layout_diagnostics']['curve_clearance_failures'])})
    (out/'relabeled-request.json').write_text(json.dumps(altered,indent=2),encoding='utf-8');materialize(changed,out/'relabeled-composition')
    # A rigid rotation of every intrinsic connected component is a diagnostic
    # perturbation. It does not change chemical state or supply page coordinates.
    rotated=copy.deepcopy(geometry);catalog={a['map']:a for a in m['atom_catalog']}
    for state in m['states']:
        sid=state['id']
        for group in connected_components(state,catalog):
            component={'atoms':[{'map':i,**geometry[sid]['atoms'][i]} for i in group]};turned=rotate_component(component,math.radians(37))
            for a in turned['atoms']:rotated[sid]['atoms'][a['map']]['position']=a['position']
    try:
        changed=compose(m,style,rotated);materialize(changed,out/'rotated-composition')
        records.append({'case':'intrinsic_component_rotation_37_degrees','semantics_and_fit':'pass','scene_equivalence':compare_scenes(baseline,changed,m),'stereo_checks':changed['stereo_checks'],'clearance_failures':len(changed['layout_diagnostics']['curve_clearance_failures']),'quality_acceptance':'not_implied'})
    except ValueError as exc:records.append({'case':'intrinsic_component_rotation_37_degrees','semantics_and_fit':'failed','error':str(exc)})
    ordered,links=linear_order(m)
    for length in (2,4):
        if len(ordered)<length:continue
        partial=copy.deepcopy(payload);pm=partial['mechanism'];pm['states']=copy.deepcopy(ordered[:length]);pm['transitions']=copy.deepcopy(links[:length-1]);allowed={s['id'] for s in pm['states']}
        pm['stereo_constraints']=[{**r,'states':[sid for sid in r['states'] if sid in allowed]} for r in pm['stereo_constraints'] if any(sid in allowed for sid in r['states'])]
        partial['layout_policy']['minimum_row_turns']=0;vm,vs=validate_request(partial);changed=compose(vm,vs,geometry)
        materialize(changed,out/f'prefix-{length}-composition');records.append({'case':f'valid_path_prefix_{length}','semantic_and_composer_fit':'pass','counts':validate_semantics(vm),'quality_acceptance':'not_implied'})
    report={'scope':'Historical measured geometry replay, metamorphic and structural controls only; no fresh native geometry qualification or unseen chemical selection','baseline_clearance_failures':len(baseline['layout_diagnostics']['curve_clearance_failures']),'cases':records,'metamorphic_behavior':'pass' if all(c.get('scene_equivalence',{}).get('status','pass')=='pass' and c.get('semantics_and_fit','pass')=='pass' for c in records) else 'failed','native_geometry_regeneration':'separate_required','holdout':'not_started'}
    (out/'metamorphic-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--geometry',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();read=lambda x:json.loads(x.read_text(encoding='utf-8'))
    g=read(a.geometry)
    for entry in g.values():entry['atoms']={int(i):x for i,x in entry['atoms'].items()}
    report=run(read(a.request),g,a.out);print(json.dumps(report));raise SystemExit(0 if report['metamorphic_behavior']=='pass' else 1)
