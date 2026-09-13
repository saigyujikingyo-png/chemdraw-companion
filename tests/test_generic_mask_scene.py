"""Independent relationship controls, without benchmark geometry or native calls."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'probes'))
from generic_mask_scene import convert


def fixture():
    scene={'style':{'canvas_width_mm':100,'canvas_height_mm':80,'bond_length_pt':15},'states':[{'id':'s','components':[{'atoms':[{'map':7},{'map':9}]}]}]}
    mapping={'states':[{'id':'s','atoms':{'7':{'native_id':'11'},'9':{'native_id':'12'}},'lone_pairs':[{'native_id':'21','atom':7,'pair_index':0},{'native_id':'22','atom':7,'pair_index':1}]}],
             'flows':[{'id':'flow','native_id':'31','source':{'state':'s','type':'lone_pair','atom':7,'pair_index':1},'target':{'state':'s','type':'atom','atom':9}}]}
    return scene,mapping


class MaskRelationshipChecks(unittest.TestCase):
    def test_distinct_pair_slots_keep_declared_source(self):
        scene,mapping=fixture();result=convert(scene,mapping)
        self.assertEqual({(p['atom_map'],p['pair_index']):p['native_id'] for p in result['lone_pairs']},{(7,0):'21',(7,1):'22'})
        self.assertEqual(result['flows'][0]['source']['pair_index'],1)
        self.assertEqual(result['flows'][0]['source']['component'],result['flows'][0]['target']['component'])

    def test_unqualified_bond_sink_is_rejected(self):
        scene,mapping=fixture();mapping['flows'][0]['target']={'state':'s','type':'bond','atoms':[7,9]}
        with self.assertRaisesRegex(ValueError,'bond-sink'):convert(scene,mapping)


if __name__=='__main__':unittest.main()
