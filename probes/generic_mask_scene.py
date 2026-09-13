"""Translate declared mapping into test-only mask relationships, not geometry.

This initial subset supports atom sinks. Bond sinks fail explicitly pending a
qualified visible native bond-port measurement. No production code imports it.
"""
import argparse,json
from pathlib import Path


def convert(scene,mapping):
    style=scene['style'];result={'canvas_mm':[style['canvas_width_mm'],style['canvas_height_mm']],'style':{'bond_pt':style['bond_length_pt']},'components':[],'lone_pairs':[],'flows':[]};binding={s['id']:s for s in mapping['states']};owners={}
    for s in scene['states']:
        for index,c in enumerate(s['components']):
            identity=f'{s["id"]}:component-{index}';atoms={str(a['map']):binding[s['id']]['atoms'][str(a['map'])] for a in c['atoms']}
            result['components'].append({'id':identity,'native_atom_bindings':atoms})
            for key in atoms:owners[(s['id'],int(key))]=identity
        for p in binding[s['id']]['lone_pairs']:result['lone_pairs'].append({'native_id':p['native_id'],'component':owners[(s['id'],p['atom'])],'atom_map':p['atom'],'pair_index':p['pair_index']})
    def port(p):
        members=[p['atom']] if 'atom' in p else p['atoms'];components={owners[(p['state'],i)] for i in members}
        if len(components)!=1:raise ValueError('Port spans disconnected source components')
        result={'type':p['type'],'component':next(iter(components))}
        if 'atom' in p:result['atom_map']=p['atom']
        else:result['atom_maps']=p['atoms']
        if 'pair_index' in p:result['pair_index']=p['pair_index']
        return result
    for f in mapping['flows']:
        if f['target']['type']!='atom':raise ValueError('Visible bond-sink masks are not qualified in this pilot adapter')
        result['flows'].append({**f,'source':port(f['source']),'target':port(f['target'])})
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--composition',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    read=lambda name:json.loads((a.composition/name).read_text());scene=convert(read('mechanism.scene.json'),read('mechanism.mapping.json'));(a.out/'mechanism.scene.json').write_text(json.dumps(scene,indent=2))
