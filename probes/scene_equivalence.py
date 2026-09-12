"""Test-only scene comparison modulo verified whole-mechanism symmetries."""
import itertools,json,math
from collections import defaultdict
from runtime.chemical_ir import chemical_colors,linear_order


def port_key(port,atom_map=None,state_map=None):
    am=atom_map or {};sm=state_map or {}
    member=(am.get(port['atom'],port['atom']),) if 'atom' in port else tuple(sorted(am.get(i,i) for i in port['atoms']))
    return (sm.get(port.get('state'),port.get('state')),port['type'],port.get('pair_index',-1),port.get('electrons',''),member)


def chemistry_signature(mechanism,am):
    states,transitions=linear_order(mechanism);sid={s['id']:i for i,s in enumerate(states)}
    state_records=[]
    for s in states:
        state_records.append((sorted((tuple(sorted(am[i] for i in b['atoms'])),b['order']) for b in s['bonds']),sorted((am[q['atom']],q['value']) for q in s['formal_charges']),sorted((am[q['atom']],q['count']) for q in s['lone_pairs'])))
    flows=[sorted((port_key(f['source'],am),port_key(f['target'],am),f['electron_count']) for f in t['electron_flows']) for t in transitions]
    stereo=[]
    for r in mechanism['stereo_constraints']:
        a,b=(am[i] for i in r['central_bond']);x,y=(am[i] for i in r['substituent_atoms']);stereo.append((r['type'],sorted(sid[s] for s in r['states']),min((a,b,x,y),(b,a,y,x))))
    return json.dumps((sorted((am[a['map']],a['element'],a['implicit_h']) for a in mechanism['atom_catalog']),state_records,flows,sorted(stereo)),sort_keys=True)


def differences(base,other,am,sm):
    states={s['id']:s for s in other['states']};atom=pair=curve=connector=text=0.;valid=True
    for s in base['states']:
        t=states[sm[s['id']]];positions={a['map']:a['position'] for c in t['components'] for a in c['atoms']}
        for c in s['components']:
            for a in c['atoms']:atom=max(atom,math.dist(a['position'],positions[am[a['map']]]))
        ports={(p['atom'],p['pair_index']):p['position'] for p in t['lone_pairs']}
        for p in s['lone_pairs']:pair=max(pair,math.dist(p['position'],ports[(am[p['atom']],p['pair_index'])]))
    routes={(port_key(f['source']),port_key(f['target']),f['electron_count']):f['bezier'] for f in other['flows']}
    if len(routes)!=len(base['flows']):valid=False
    for f in base['flows']:
        key=(port_key(f['source'],am,sm),port_key(f['target'],am,sm),f['electron_count'])
        if key not in routes:valid=False;continue
        curve=max(curve,max(math.dist(a,b) for a,b in zip(f['bezier'],routes[key])))
    arrows={(c['from'],c['to']):c['path'] for c in other['connectors']}
    for c in base['connectors']:connector=max(connector,max(math.dist(a,b) for a,b in zip(c['path'],arrows[(sm[c['from']],sm[c['to']])])) )
    if len(base['texts'])!=len(other['texts']):valid=False
    for a,b in zip(base['texts'],other['texts']):
        if a['text']!=b['text'] or a['font_pt']!=b['font_pt']:valid=False
        text=max(text,math.dist(a['position'],b['position']))
    return {'relationships_equal':valid,'max_atom_displacement_pt':atom,'max_lone_pair_displacement_pt':pair,'max_curve_control_displacement_pt':curve,'max_connector_displacement_pt':connector,'max_caption_displacement_pt':text}


def compare(base,other,mechanism,am=None,sm=None):
    atoms=[a['map'] for a in mechanism['atom_catalog']];am=am or {i:i for i in atoms};sm=sm or {s['id']:s['id'] for s in mechanism['states']}
    strict=differences(base,other,am,sm);passes=lambda r:r['relationships_equal'] and max(v for k,v in r.items() if k.startswith('max_'))<=.02
    if passes(strict):return {'status':'pass','equivalence':'strict supplied identity bijection','differences':strict,'symmetry_permutation':None}
    colors=chemical_colors(mechanism);classes=defaultdict(list)
    for i in atoms:classes[colors[i]].append(i)
    groups=list(classes.values());budget=math.prod(math.factorial(len(g)) for g in groups)
    if budget>4096:return {'status':'failed','strict_differences':strict,'reason':'Unresolved symmetry exceeds the declared comparator bound; no symmetry assumed'}
    identity={i:i for i in atoms};want=chemistry_signature(mechanism,identity)
    for candidate in itertools.product(*(itertools.permutations(g) for g in groups)):
        permutation={i:j for g,order in zip(groups,candidate) for i,j in zip(g,order)}
        if permutation==identity or chemistry_signature(mechanism,permutation)!=want:continue
        values=differences(base,other,{i:am[permutation[i]] for i in atoms},sm)
        if passes(values):return {'status':'pass','equivalence':'Verified single global graph/charge/H/LP/flow/stereo automorphism across every state','differences':values,'strict_differences':strict,'symmetry_permutation':{str(i):j for i,j in permutation.items() if i!=j}}
    return {'status':'failed','equivalence':'No verified symmetry makes scenes equivalent','differences':strict}
