"""First-party, AI-proposed development input; not gold or an unseen test.

The independent alkoxide/ammonium candidate is authored as complete intended
chemistry. No benchmark, native geometry, annotation or answer file is loaded.
The corpus encoding is a fixture-side representation, not a runtime lowering.
"""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.chemical_ir import connected_components,validate_request


def candidate():
    a,b,o,n,h=101,211,307,419,521
    bonds=lambda edges:[{'atoms':[x,y],'order':1} for x,y in edges]
    m={'ir_version':'mechanism-ir/0.1','entry_state':'ion_pair','atom_catalog':[{'map':i,'element':e,'implicit_h':count} for i,e,count in ((a,'C',3),(b,'C',2),(o,'O',0),(n,'N',3),(h,'H',0))],
       'states':[{'id':'ion_pair','label':'Ethoxide and ammonium (proposed)','bonds':bonds(((a,b),(b,o),(n,h))),'formal_charges':[{'atom':o,'value':-1},{'atom':n,'value':1}],'lone_pairs':[{'atom':o,'count':3},{'atom':n,'count':0}]},
                 {'id':'neutral_pair','label':'Ethanol and ammonia (proposed)','bonds':bonds(((a,b),(b,o),(o,h))),'formal_charges':[],'lone_pairs':[{'atom':o,'count':2},{'atom':n,'count':1}]}],
       'transitions':[{'id':'proton_exchange','from':'ion_pair','to':'neutral_pair','kind':'elementary_step','label':'Proton transfer; no kinetic claim','electron_flows':[
           {'id':'oxygen_donation','electron_count':2,'source':{'type':'lone_pair','atom':o,'pair_index':0},'target':{'type':'atom','atom':h}},
           {'id':'nitrogen_recovery','electron_count':2,'source':{'type':'bond','atoms':[n,h],'electrons':'sigma'},'target':{'type':'atom','atom':n}}],
           'bond_changes':[{'atoms':[n,h],'from_order':1,'to_order':0},{'atoms':[o,h],'from_order':0,'to_order':1}],
           'charge_changes':[{'atom':o,'from':-1,'to':0},{'atom':n,'from':1,'to':0}]}], 'stereo_constraints':[]}
    return {'contract_version':'composer-request/0.1','mechanism':m,'layout_policy':{'flow':'serpentine','first_row_direction':'left_to_right','max_columns':2,'minimum_row_turns':0,'canvas_width_mm':170,'canvas_height_mm':110,'outer_margin_mm':5,'row_gap_bond_lengths':2,'font_family':'Arial','font_pt':8,'bond_length_pt':14.4,'stroke_pt':.6,'minimum_native_dpi':600}}


def encode_fixture(m):
    fields=('atoms','states','species','molecules','atom_occurrences','bonds','charges','radicals','lone_pairs','reaction_steps','reaction_arrows','condition_texts','electron_flows','layout_constraints')
    r={'version':'corpus-mechanism-ir/0.1','id':'development-alkoxide-ammonium-01','entry_state':m['entry_state'],'scope':{'atom_inventory':'closed','omissions':['AI-proposed teaching-level bookkeeping; no solvent, rate or experimental mechanism evidence. All transferred H atoms are explicit.'],'scientific_status':'unreviewed'},**{f:[] for f in fields}}
    catalog={a['map']:a for a in m['atom_catalog']};occ=lambda sid,i:f'{sid}:atom-{i}';edge=lambda sid,ends:sid+':bond-'+ '-'.join(str(i) for i in sorted(ends))
    r['atoms']=[{'id':f'atom-{i}','element':a['element'],'isotope':None} for i,a in catalog.items()]
    for state in m['states']:
        sid=state['id'];species=[]
        for index,group in enumerate(connected_components(state,catalog)):
            mid=f'{sid}:molecule-{index}';spid=f'{sid}:species-{index}';species.append(spid)
            r['molecules'].append({'id':mid,'state_ref':sid,'atom_refs':[occ(sid,i) for i in group],'bond_refs':[edge(sid,b['atoms']) for b in state['bonds'] if b['atoms'][0] in group]})
            r['species'].append({'id':spid,'state_ref':sid,'molecule_refs':[mid],'role':'participant','stoichiometry':1})
            r['atom_occurrences'] += [{'id':occ(sid,i),'state_ref':sid,'atom_ref':f'atom-{i}','molecule_ref':mid,'implicit_h':catalog[i]['implicit_h']} for i in group]
        r['states'].append({'id':sid,'label':state['label'],'species_refs':species})
        r['bonds'] += [{'id':edge(sid,b['atoms']),'state_ref':sid,'atom_refs':[occ(sid,i) for i in b['atoms']],'order':b['order'],'stereo':'none'} for b in state['bonds']]
        r['charges'] += [{'id':sid+':charge-'+str(q['atom']),'atom_ref':occ(sid,q['atom']),'value':q['value'],'display':'shown'} for q in state['formal_charges']]
        r['lone_pairs'] += [{'id':f'{sid}:pair-{q["atom"]}-{k}','atom_ref':occ(sid,q['atom']),'slot':k,'display':'shown'} for q in state['lone_pairs'] for k in range(q['count'])]
    def port(p,sid):
        if p['type']=='atom':return {'type':'atom','state_ref':sid,'atom_ref':occ(sid,p['atom'])}
        if p['type']=='lone_pair':return {'type':'lone_pair','state_ref':sid,'lone_pair_ref':f'{sid}:pair-{p["atom"]}-{p["pair_index"]}'}
        return {'type':'bond','state_ref':sid,'bond_ref':edge(sid,p['atoms']),'electron_kind':p['electrons']}
    for t in m['transitions']:
        tid=t['id'];condition=tid+':condition'
        r['reaction_steps'].append({'id':tid,'from_state':t['from'],'to_state':t['to'],'kind':'teaching_elementary','electron_flow_refs':[f['id'] for f in t['electron_flows']],'condition_refs':[condition]})
        r['reaction_arrows'].append({'id':tid+':arrow','step_ref':tid,'kind':'forward','from_state':t['from'],'to_state':t['to']})
        r['condition_texts'].append({'id':condition,'step_ref':tid,'text':t['label'],'kind':'annotation','evidence_status':'specified'})
        r['electron_flows'] += [{'id':f['id'],'step_ref':tid,'electron_count':f['electron_count'],'source':port(f['source'],t['from']),'sink':port(f['target'],t['from']),'simultaneous_group':tid} for f in t['electron_flows']]
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);request=candidate();validate_request(request)
    for name,value in [('runtime-request.json',request),('mechanism.ir.json',encode_fixture(request['mechanism']))]:(a.out/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
