"""Reaction-neutral linear mechanism validation and identity.

No benchmark oracle, molecule name, state label, drawing or page coordinate is
an input to chemical decisions. Current semantic scope is closed-shell H/C/N/O
with explicit heteroatom lone-pair inventories and two-electron transitions.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib,json
from pathlib import Path

def edge(pair):
    if len(pair)!=2 or pair[0]==pair[1]:raise ValueError('Invalid bond endpoints')
    return frozenset(pair)

def connected_components(state,catalog):
    adjacent={i:set() for i in catalog}
    for b in state['bonds']:
        a,c=b['atoms'];adjacent[a].add(c);adjacent[c].add(a)
    result=[];remaining=set(catalog)
    # Opaque IDs break identity ties only. Packing never branches on their value.
    for first in catalog:
        if first not in remaining:continue
        stack=[first];group=set()
        while stack:
            atom=stack.pop()
            if atom in group:continue
            group.add(atom);stack.extend(adjacent[atom]-group)
        result.append(group);remaining-=group
    return result

def linear_order(mechanism):
    states={s['id']:s for s in mechanism['states']}
    if len(states)!=len(mechanism['states']):raise ValueError('Duplicate state identity')
    outgoing={};incoming=Counter();transitions={}
    for t in mechanism['transitions']:
        if t['id'] in transitions or t['from'] not in states or t['to'] not in states:raise ValueError('Invalid transition identity')
        if t['from'] in outgoing:raise ValueError('Branching pathways are not supported')
        outgoing[t['from']]=t;incoming[t['to']]+=1;transitions[t['id']]=t
    current=mechanism['entry_state'];order=[];links=[]
    if current not in states or incoming[current]:raise ValueError('Invalid entry state')
    while True:
        if current in order:raise ValueError('Cyclic pathways are not supported')
        order.append(current)
        if current not in outgoing:break
        t=outgoing[current];links.append(t);current=t['to']
        if incoming[current]!=1:raise ValueError('Merged pathways are not supported')
    if len(order)!=len(states) or len(links)!=len(transitions):raise ValueError('Disconnected pathway')
    return [states[i] for i in order],links

def validate_request(payload):
    # Resolve only the two generic schemas, locally; no network or oracle import.
    from jsonschema import Draft202012Validator
    from referencing import Registry,Resource
    contracts=Path(__file__).resolve().parents[1]/'contracts'
    ir=json.loads((contracts/'mechanism-ir.schema.json').read_text(encoding='utf-8'))
    request=json.loads((contracts/'composer-request.schema.json').read_text(encoding='utf-8'))
    registry=Registry().with_resource(ir['$id'],Resource.from_contents(ir))
    Draft202012Validator(request,registry=registry).validate(payload)
    mechanism=deepcopy(payload['mechanism']);validate_semantics(mechanism)
    return mechanism,deepcopy(payload['layout_policy'])

def validate_semantics(mechanism):
    atoms={a['map']:a for a in mechanism['atom_catalog']}
    if len(atoms)!=len(mechanism['atom_catalog']):raise ValueError('Duplicate atom identity')
    if any(a['element'] not in {'H','C','N','O'} for a in atoms.values()):raise ValueError('Element outside the declared semantic scope')
    states,transitions=linear_order(mechanism);graphs={};charges={};pairs={};total_charge=None
    for state in states:
        name=state['id'];g={edge(b['atoms']):b['order'] for b in state['bonds']};q={x['atom']:x['value'] for x in state['formal_charges']};lp={x['atom']:x['count'] for x in state['lone_pairs']}
        if len(g)!=len(state['bonds']) or len(q)!=len(state['formal_charges']) or len(lp)!=len(state['lone_pairs']):raise ValueError('Duplicate bond, charge or lone-pair entry')
        if not set(q)|set(lp)<=set(atoms):raise ValueError('Unmapped atomic property')
        valence={i:a['implicit_h'] for i,a in atoms.items()}
        for endpoints,order in g.items():
            if not endpoints<=set(atoms):raise ValueError('Unmapped bond atom')
            for atom in endpoints:valence[atom]+=order
        for atom,spec in atoms.items():
            el=spec['element'];v=valence[atom];formal=q.get(atom,0)
            if el in ('H','C'):
                if v!={'H':1,'C':4}[el] or formal!=0 or lp.get(atom,0)!=0:raise ValueError('Unsupported H/C valence, charge or lone pair')
            else:
                if atom not in lp or v+lp[atom]!=4 or formal!={'N':5,'O':6}[el]-v-2*lp[atom]:raise ValueError('Heteroatom charge, octet or electron-pair mismatch')
        if total_charge is None:total_charge=sum(q.values())
        if total_charge!=sum(q.values()):raise ValueError('System charge is not conserved')
        graphs[name],charges[name],pairs[name]=g,q,lp
    seen_flows=set()
    for t in transitions:
        before,after=t['from'],t['to'];g,h=graphs[before],graphs[after];q,z=charges[before],charges[after];delta=Counter();dq=Counter();used=set()
        for flow in t['electron_flows']:
            if flow['id'] in seen_flows or flow['electron_count']!=2:raise ValueError('Invalid electron-flow identity/count')
            seen_flows.add(flow['id']);source,target=flow['source'],flow['target']
            if source['type']=='lone_pair':
                donor=source['atom'];slot=source['pair_index'];key=('lp',donor,slot)
                if not 0<=slot<pairs[before].get(donor,0):raise ValueError('Unavailable donor lone pair')
                if target['type']=='atom':acceptor=target['atom']
                else:
                    pair=edge(target['atoms'])
                    if donor not in pair:raise ValueError('Donor absent from target bond')
                    acceptor=next(iter(pair-{donor}))
                if acceptor not in atoms or acceptor==donor:raise ValueError('Invalid acceptor atom')
                delta[edge((donor,acceptor))]+=1
            else:
                pair=edge(source['atoms']);kind=source['electrons'];key=('bond',pair,kind)
                if pair not in g or not ((kind=='sigma' and g[pair]==1) or (kind=='pi' and g[pair]>=2)):raise ValueError('Invalid source bond electrons')
                delta[pair]-=1
                if target['type']=='atom':
                    acceptor=target['atom']
                    if acceptor not in pair:raise ValueError('Ambiguous migrating-bond target')
                    donor=next(iter(pair-{acceptor}))
                else:
                    future=edge(target['atoms']);shared=pair&future
                    if len(shared)!=1 or not future<=set(atoms):raise ValueError('Invalid prospective bond')
                    donor=next(iter(pair-shared));acceptor=next(iter(future-shared));delta[future]+=1
            if key in used:raise ValueError('Electron donor reused within simultaneous step')
            used.add(key);dq[donor]+=1;dq[acceptor]-=1
        clean=lambda values:{k:v for k,v in values.items() if v}
        expected_delta={e:h.get(e,0)-g.get(e,0) for e in set(g)|set(h)};expected_charge={i:z.get(i,0)-q.get(i,0) for i in atoms}
        if clean(delta)!=clean(expected_delta) or clean(dq)!=clean(expected_charge):raise ValueError('Electron moves do not explain complete graph/charge change')
        declared={edge(b['atoms']):(b['from_order'],b['to_order']) for b in t['bond_changes']};expected={e:(g.get(e,0),h.get(e,0)) for e,d in expected_delta.items() if d}
        if len(declared)!=len(t['bond_changes']) or declared!=expected:raise ValueError('Declared bond differences mismatch')
        declared_q={x['atom']:(x['from'],x['to']) for x in t['charge_changes']};expected_q={i:(q.get(i,0),z.get(i,0)) for i,d in expected_charge.items() if d}
        if len(declared_q)!=len(t['charge_changes']) or declared_q!=expected_q:raise ValueError('Declared charge differences mismatch')
    for relation in mechanism['stereo_constraints']:
        a,b=relation['central_bond'];x,y=relation['substituent_atoms']
        for sid in relation['states']:
            g=graphs.get(sid)
            if g is None or g.get(edge((a,b)))!=2 or g.get(edge((a,x)))!=1 or g.get(edge((b,y)))!=1:raise ValueError('Stereo constraint does not identify bonded substituents')
    return {'ordered_states':[s['id'] for s in states],'ordered_transitions':[t['id'] for t in transitions],'state_count':len(states),'flow_count':len(seen_flows),'system_charge':total_charge,'scope':'closed-shell H/C/N/O, linear pathways, explicit transferred H'}

def canonical_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
