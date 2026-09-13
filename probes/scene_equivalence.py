"""Test-only scene comparison modulo verified whole-mechanism symmetries."""
import itertools,json,math
from collections import defaultdict,Counter
from runtime.chemical_ir import chemical_colors,linear_order,connected_components,validate_semantics


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


def unique(items,key,name):
    result={}
    for item in items:
        identity=key(item)
        if identity in result:raise ValueError('Duplicate '+name+': '+str(identity))
        result[identity]=item
    return result


def point(value):
    if not isinstance(value,(list,tuple)) or len(value)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in value):
        raise ValueError('Expected a finite two-dimensional point')


def path(value,length):
    if not isinstance(value,(list,tuple)) or len(value)!=length:raise ValueError('Wrong path/control array length')
    for p in value:point(p)


def validate_scene(scene,mechanism,am,sm):
    """Validate both scenes independently against the IR before any tolerance.

    Opaque flow/connector names may change, but their identities must be unique
    and their complete semantic inventory must match. Aromatic IR edges allow
    a valence-correct native Kekule form; no arbitrary bond-order change does.
    """
    states,transitions=linear_order(mechanism);catalog={a['map']:a for a in mechanism['atom_catalog']}
    if set(am)!=set(catalog) or len(set(am.values()))!=len(catalog):raise ValueError('Atom mapping is not a complete bijection')
    if set(sm)!={s['id'] for s in states} or len(set(sm.values()))!=len(states):raise ValueError('State mapping is not a complete bijection')
    if any(type(i) is not int for i in [*am,*am.values()]) or any(not isinstance(i,str) or not i for i in [*sm,*sm.values()]):raise ValueError('Invalid mapped identity type')
    inv={v:k for k,v in am.items()};actual=unique(scene['states'],lambda s:s['id'],'state')
    if set(actual)!=set(sm.values()):raise ValueError('State inventory differs from IR')
    for state in states:
        placed=actual[sm[state['id']]];components=placed['components']
        atoms=unique([a for c in components for a in c['atoms']],lambda a:a['map'],'atom')
        if set(atoms)!=set(am.values()):raise ValueError('Atom inventory differs from IR')
        partitions=Counter(frozenset(inv[a['map']] for a in c['atoms']) for c in components)
        if partitions!=Counter(map(frozenset,connected_components(state,catalog))):raise ValueError('Component partition differs from IR')
        charges={q['atom']:q['value'] for q in state['formal_charges']}
        expected={tuple(sorted(b['atoms'])):b['order'] for b in state['bonds']};bonds={}
        for component in components:
            members={a['map'] for a in component['atoms']}
            for bond in component['bonds']:
                ends=bond['atoms']
                if len(ends)!=2 or ends[0]==ends[1] or not set(ends)<=members:raise ValueError('Invalid bond endpoint inventory')
                e=tuple(sorted(inv[i] for i in ends))
                if e in bonds:raise ValueError('Duplicate scene bond')
                order=bond['order'];bonds[e]=order
                if isinstance(order,bool) or e not in expected or order!=expected[e] and not(expected[e]==1.5 and order in (1,2)):raise ValueError('Scene bond chemistry differs from IR')
                if bond.get('display','Solid')!='Solid' or bond.get('display2','Solid')!='Solid':raise ValueError('Unspecified scene bond stereo/display')
        if set(bonds)!=set(expected):raise ValueError('Bond inventory differs from IR')
        for native,a in atoms.items():
            i=inv[native];want=catalog[i];point(a['position'])
            if type(native) is not int or type(a['implicit_h']) is not int or isinstance(a['charge'],bool) or not isinstance(a['charge'],(int,float)):raise ValueError('Invalid atom property type')
            if (a['element'],a['implicit_h'],a['charge'])!=(want['element'],want['implicit_h'],charges.get(i,0)):raise ValueError('Scene atom chemistry differs from IR')
            if a.get('isotope',0)!=0 or a.get('radical',0) not in (0,None,'None'):raise ValueError('Unspecified isotope/radical')
            label=a.get('label')
            if label is not None:
                point(label['offset']);path([label['bbox_offset'][:2],label['bbox_offset'][2:]],2)
                if not label['runs'] or any(not isinstance(r['text'],str) or not math.isfinite(float(r['size'])) for r in label['runs']):raise ValueError('Invalid native label runs')
            valence={'H':1,'C':4,'N':3+charges.get(i,0),'O':2+charges.get(i,0)}[a['element']]
            # Check a materialized Kekule valence independently of adapter code.
            if any(expected[e]==1.5 for e in expected if i in e):
                if sum(o for e,o in bonds.items() if i in e)+a['implicit_h']!=valence:raise ValueError('Invalid aromatic valence')
        pairs=unique(placed['lone_pairs'],lambda p:(p['atom'],p['pair_index']),'lone pair')
        want={(am[p['atom']],k) for p in state['lone_pairs'] for k in range(p['count'])}
        if set(pairs)!=want:raise ValueError('Lone-pair inventory differs from IR')
        for p in pairs.values():point(p['position'])
        for relation in mechanism['stereo_constraints']:
            if state['id'] not in relation['states']:continue
            a,b=(atoms[am[i]]['position'] for i in relation['central_bond']);x,y=(atoms[am[i]]['position'] for i in relation['substituent_atoms']);d=(b[0]-a[0],b[1]-a[1])
            cross=lambda p,q:d[0]*(q[1]-p[1])-d[1]*(q[0]-p[0]);product=cross(a,x)*cross(b,y)
            if not(product<0 if relation['type']=='anti_across_double_bond' else product>0):raise ValueError('Scene stereo relation differs from IR')
    flows=unique(scene['flows'],lambda f:f['id'],'flow ID')
    flow_key=lambda f:(port_key(f['source']),port_key(f['target']),f['electron_count'])
    unique(flows.values(),flow_key,'flow relationship')
    want=Counter((port_key({'state':t['from'],**f['source']},am,sm),port_key({'state':t['from'],**f['target']},am,sm),f['electron_count']) for t in transitions for f in t['electron_flows'])
    if Counter(map(flow_key,flows.values()))!=want:raise ValueError('Flow inventory differs from IR')
    for flow in flows.values():path(flow['bezier'],4)
    connectors=unique(scene['connectors'],lambda c:c['id'],'connector ID')
    if Counter((c['from'],c['to']) for c in connectors.values())!=Counter((sm[t['from']],sm[t['to']]) for t in transitions):raise ValueError('Connector inventory differs from IR')
    for c in connectors.values():path(c['path'],2)
    for t in scene['texts']:
        point(t['position'])
        if not isinstance(t['text'],str) or not isinstance(t['font_pt'],(float,int)) or not math.isfinite(t['font_pt']) or t['font_pt']<=0:raise ValueError('Invalid caption')


def differences(base,other,am,sm):
    states={s['id']:s for s in other['states']};atom=pair=curve=connector=text=0.;valid=all(base.get(k)==other.get(k) for k in ('style','width_pt','height_pt'))
    for s in base['states']:
        t=states[sm[s['id']]];other_atoms={a['map']:a for c in t['components'] for a in c['atoms']};positions={i:a['position'] for i,a in other_atoms.items()}
        for c in s['components']:
            for a in c['atoms']:
                atom=max(atom,math.dist(a['position'],positions[am[a['map']]]))
                if a.get('label')!=other_atoms[am[a['map']]].get('label'):valid=False
        bond_records=lambda state,mapping:Counter((tuple(sorted(mapping.get(i,i) for i in b['atoms'])),b['order'],b.get('display','Solid'),b.get('display2','Solid')) for c in state['components'] for b in c['bonds'])
        if bond_records(s,am)!=bond_records(t,{}):valid=False
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
    atoms=[a['map'] for a in mechanism['atom_catalog']];identity={i:i for i in atoms};state_identity={s['id']:s['id'] for s in mechanism['states']}
    am=identity if am is None else am;sm=state_identity if sm is None else sm
    try:
        validate_semantics(mechanism)
        validate_scene(base,mechanism,identity,state_identity)
        validate_scene(other,mechanism,am,sm)
    except (KeyError,ValueError,TypeError,IndexError,OverflowError) as exc:return {'status':'failed','reason':'Invalid scene or identity inventory: '+str(exc)}
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
