"""Small, independent semantic inputs; test data, never production templates."""
from copy import deepcopy


def proton_transfer():
    return {'ir_version':'mechanism-ir/0.1','entry_state':'ammonia_water','atom_catalog':[{'map':41,'element':'N','implicit_h':3},{'map':7,'element':'O','implicit_h':2},{'map':99,'element':'H','implicit_h':0}],
      'states':[
        {'id':'ammonia_water','label':'Ammonia and hydronium','bonds':[{'atoms':[7,99],'order':1}],'formal_charges':[{'atom':7,'value':1}],'lone_pairs':[{'atom':41,'count':1},{'atom':7,'count':1}]},
        {'id':'ammonium_water','label':'Ammonium and water','bonds':[{'atoms':[41,99],'order':1}],'formal_charges':[{'atom':41,'value':1}],'lone_pairs':[{'atom':41,'count':0},{'atom':7,'count':2}]}],
      'transitions':[{'id':'proton_move','from':'ammonia_water','to':'ammonium_water','label':'Proton transfer','kind':'elementary_step','electron_flows':[
        {'id':'nitrogen_donation','electron_count':2,'source':{'type':'lone_pair','atom':41,'pair_index':0},'target':{'type':'atom','atom':99}},
        {'id':'oxygen_recovery','electron_count':2,'source':{'type':'bond','atoms':[7,99],'electrons':'sigma'},'target':{'type':'atom','atom':7}}],
        'bond_changes':[{'atoms':[7,99],'from_order':1,'to_order':0},{'atoms':[41,99],'from_order':0,'to_order':1}],
        'charge_changes':[{'atom':7,'from':1,'to':0},{'atom':41,'from':0,'to':1}]}],
      'stereo_constraints':[]}


def electrocyclization():
    # A connectivity/electron-accounting test, not a stereochemical prediction.
    atoms=[101,17,62,29,83,46];a,b,c,d,e,f=atoms
    before=[(a,b,2),(b,c,1),(c,d,2),(d,e,1),(e,f,2)]
    after=[(a,b,1),(b,c,2),(c,d,1),(d,e,2),(e,f,1),(f,a,1)]
    state=lambda name,edges:{'id':name,'label':name,'bonds':[{'atoms':[x,y],'order':o} for x,y,o in edges],'formal_charges':[],'lone_pairs':[]}
    return {'ir_version':'mechanism-ir/0.1','entry_state':'open_chain','atom_catalog':[{'map':i,'element':'C','implicit_h':2 if i in (a,f) else 1} for i in atoms],
      'states':[state('open_chain',before),state('ring',after)],'stereo_constraints':[],
      'transitions':[{'id':'closure','from':'open_chain','to':'ring','label':'Six-electron ring closure','kind':'elementary_teaching_step','electron_flows':[
        {'id':str(i),'electron_count':2,'source':{'type':'bond','atoms':list(source),'electrons':'pi'},'target':{'type':'bond','atoms':list(target)}}
        for i,(source,target) in enumerate((((a,b),(b,c)),((c,d),(d,e)),((e,f),(f,a))))],
        'bond_changes':[{'atoms':[x,y],'from_order':o,'to_order':next((v for j,k,v in after if {x,y}=={j,k}),0)} for x,y,o in before]+[{'atoms':[f,a],'from_order':0,'to_order':1}],
        'charge_changes':[]}]}
