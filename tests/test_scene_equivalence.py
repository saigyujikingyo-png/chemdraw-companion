import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'probes'));sys.path.insert(0,str(ROOT/'tests'))
from general_ir_cases import proton_transfer
from runtime.chemical_ir import validate_semantics
from scene_equivalence import compare


class SceneSymmetryChecks(unittest.TestCase):
    def setUp(self):
        self.m=proton_transfer();first=max(a['map'] for a in self.m['atom_catalog'])+10;self.spectators=(first,first+10)
        for i in self.spectators:
            self.m['atom_catalog'].append({'map':i,'element':'O','implicit_h':2})
            for state in self.m['states']:state['lone_pairs'].append({'atom':i,'count':2})
        validate_semantics(self.m);self.scene={'states':[],'flows':[],'connectors':[],'texts':[]}
        for state in self.m['states']:
            points={a['map']:[index*20.,20.] for index,a in enumerate(self.m['atom_catalog'])}
            self.scene['states'].append({'id':state['id'],'components':[{'atoms':[{'map':i,'position':p} for i,p in points.items()]}],'lone_pairs':[{'atom':p['atom'],'pair_index':k,'position':[points[p['atom']][0]+k*4,30.]} for p in state['lone_pairs'] for k in range(p['count'])]})
        for t in self.m['transitions']:
            self.scene['connectors'].append({'from':t['from'],'to':t['to'],'path':[[0.,0.],[10.,0.]]})
            for f in t['electron_flows']:self.scene['flows'].append({**copy.deepcopy(f),'source':{'state':t['from'],**f['source']},'target':{'state':t['from'],**f['target']},'bezier':[[0.,0.],[5.,5.],[10.,5.],[15.,0.]]})

    def swap(self,scene,state_index):
        s=scene['states'][state_index];a,b=self.spectators;atoms={a['map']:a for c in s['components'] for a in c['atoms']};atoms[a]['position'],atoms[b]['position']=atoms[b]['position'],atoms[a]['position']
        pairs={(p['atom'],p['pair_index']):p for p in s['lone_pairs']}
        for k in range(2):pairs[(a,k)]['position'],pairs[(b,k)]['position']=pairs[(b,k)]['position'],pairs[(a,k)]['position']

    def test_true_global_spectator_exchange_is_allowed(self):
        changed=copy.deepcopy(self.scene)
        for k in range(len(changed['states'])):self.swap(changed,k)
        result=compare(self.scene,changed,self.m)
        self.assertEqual(result['status'],'pass');self.assertIsNotNone(result['symmetry_permutation'])

    def test_inconsistent_state_local_exchange_is_rejected(self):
        changed=copy.deepcopy(self.scene);self.swap(changed,0)
        self.assertEqual(compare(self.scene,changed,self.m)['status'],'failed')

    def test_curve_change_cannot_pass_atom_only_equivalence(self):
        changed=copy.deepcopy(self.scene);changed['flows'][0]['bezier'][2][1]+=4
        self.assertEqual(compare(self.scene,changed,self.m)['status'],'failed')


if __name__=='__main__':unittest.main()
