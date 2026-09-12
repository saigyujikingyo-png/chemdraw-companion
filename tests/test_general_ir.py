import ast,copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from general_ir_cases import proton_transfer,electrocyclization
from runtime.chemical_ir import validate_semantics,validate_request,linear_order
from runtime.adapters.chemdraw_cdxml import materialize
import xml.etree.ElementTree as ET


class GeneralIrChecks(unittest.TestCase):
    def test_independent_chemistry_and_different_flow_count(self):
        self.assertEqual(validate_semantics(proton_transfer())['flow_count'],2)
        case=electrocyclization()
        self.assertEqual(case['transitions'][0]['charge_changes'],[])
        self.assertEqual(validate_semantics(case)['flow_count'],3)
        payload=json.loads((ROOT/'examples/m2-composer-request.json').read_text(encoding='utf-8'))
        for mechanism in (proton_transfer(),case):
            payload['mechanism']=mechanism;validate_request(payload)

    def test_simultaneous_flow_order_is_irrelevant(self):
        case=electrocyclization();case['transitions'][0]['electron_flows'].reverse()
        self.assertEqual(validate_semantics(case)['state_count'],2)

    def test_graph_order_not_lexical_or_storage(self):
        case=proton_transfer();case['states'].reverse()
        self.assertEqual(linear_order(case)[0][0]['id'],case['entry_state'])

    def test_reversed_donor_rejected(self):
        case=proton_transfer();case['transitions'][0]['electron_flows'][1]['target']['atom']=99
        with self.assertRaisesRegex(ValueError,'graph/charge change'):validate_semantics(case)

    def test_nonexistent_lone_pair_rejected(self):
        case=proton_transfer();case['transitions'][0]['electron_flows'][0]['source']['pair_index']=1
        with self.assertRaisesRegex(ValueError,'Unavailable donor'):validate_semantics(case)

    def test_carbon_lone_pair_outside_scope_rejected(self):
        case=electrocyclization();case['states'][0]['lone_pairs']=[{'atom':101,'count':1}]
        with self.assertRaisesRegex(ValueError,'Unsupported H/C'):validate_semantics(case)

    def test_cycle_and_disconnected_states_rejected(self):
        case=proton_transfer();bad=copy.deepcopy(case);bad['states'].append({**copy.deepcopy(bad['states'][0]),'id':'orphan'})
        with self.assertRaisesRegex(ValueError,'Disconnected'):validate_semantics(bad)
        bad=copy.deepcopy(case);bad['transitions'].append({**copy.deepcopy(bad['transitions'][0]),'id':'return','from':'ammonium_water','to':'ammonia_water'})
        with self.assertRaisesRegex(ValueError,'entry state'):validate_semantics(bad)

    def test_schema_rejects_oracle_or_layout_coordinates(self):
        payload=json.loads((ROOT/'examples/m2-composer-request.json').read_text(encoding='utf-8'));validate_request(payload)
        payload['mechanism']['expected_product']='answer'
        with self.assertRaises(Exception):validate_request(payload)

    def test_cdxml_bond_enum_serialization(self):
        style={'font_pt':8,'font_family':'Arial','bond_length_pt':14.4,'stroke_pt':.6,'canvas_width_mm':80,'canvas_height_mm':80}
        atom=lambda i,x:{'map':i,'element':'C','implicit_h':2,'charge':0,'position':[x,0],'label':None}
        scene={'style':style,'width_pt':100,'height_pt':100,'states':[{'id':'any','components':[{'atoms':[atom(50,0),atom(2,14.4)],'bonds':[{'atoms':[50,2],'order':2.0,'display':'Solid'}]}],'lone_pairs':[]}],'texts':[],'flows':[],'connectors':[]}
        with tempfile.TemporaryDirectory() as parent:
            folder=Path(parent)/'out';materialize(scene,folder)
            self.assertEqual(ET.parse(folder/'mechanism.cdxml').find('.//b').get('Order'),'2')

    def test_runtime_has_no_oracle_imports(self):
        for path in (ROOT/'runtime').rglob('*.py'):
            tree=ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node,(ast.Import,ast.ImportFrom)):
                    names=[a.name for a in node.names]+[getattr(node,'module','') or '']
                    self.assertFalse(any(s.startswith(('probes','tests','examples')) or 'fixture' in s for s in names),path)


if __name__=='__main__':unittest.main()
