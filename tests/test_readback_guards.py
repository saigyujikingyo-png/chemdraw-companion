"""Reviewer fault injections against immutable recorded native evidence."""
import copy,importlib.util,json,tempfile,unittest,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('composition_checker',ROOT/'probes/verify_composition.py');checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)


class NativeReadbackGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        archive=ROOT/'verification/2026-09-12-native-control/raw-evidence.zip'
        with zipfile.ZipFile(archive) as z:
            prefix='generic-composer-20260912/composition-repair-1/'
            cls.scene=json.loads(z.read(prefix+'mechanism.scene.json'));cls.mapping=json.loads(z.read(prefix+'mechanism.mapping.json'))
        cls.mechanism=json.loads((ROOT/'examples/m2-composer-request.json').read_text(encoding='utf-8'))['mechanism']
        cls.xml=(ROOT/'verification/2026-09-12-native-control/samples/M2/M2.cdxml').read_bytes()

    def inspect(self,mutate):
        root=ET.fromstring(self.xml);mutate(root)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'injected.cdxml';ET.ElementTree(root).write(path,encoding='utf-8')
            return checker.verify(self.mechanism,self.scene,self.mapping,path)

    def test_native_hydrogen_override_changes_fingerprint_and_fails(self):
        nid=next(iter(self.mapping['states'][0]['atoms'].values()))['native_id']
        original=self.inspect(lambda _:None)
        result=self.inspect(lambda r:r.find(f'.//n[@id="{nid}"]').set('NumHydrogens','4'))
        self.assertTrue(any('native_hydrogen' in s for s in result['issues']))
        self.assertNotEqual(original['chemical_fingerprint'],result['chemical_fingerprint'])

    def test_displaced_state_fails_actual_anchor_and_containment(self):
        def mutate(root):
            for a in self.mapping['states'][0]['atoms'].values():
                n=root.find(f'.//n[@id="{a["native_id"]}"]');x,y=map(float,n.get('p').split());n.set('p',f'{x+500} {y+500}')
                for t in n.findall('t'):
                    x,y=map(float,t.get('p').split());t.set('p',f'{x+500} {y+500}')
                    b=list(map(float,t.get('BoundingBox').split()));t.set('BoundingBox',' '.join(str(v+500) for v in b))
        result=self.inspect(mutate)
        self.assertIn('page_containment',result['issues']);self.assertTrue(any(s.startswith(('detached_lone_pair','native_anchor')) for s in result['issues']))

    def test_lone_pair_in_wrong_corner_is_rejected(self):
        nid=self.mapping['states'][0]['lone_pairs'][0]['native_id']
        result=self.inspect(lambda r:r.find(f'.//graphic[@id="{nid}"]').set('BoundingBox','0 0 2 0'))
        self.assertTrue(any(s.startswith('detached_lone_pair') for s in result['issues']))

    def test_missing_arrowhead_fails(self):
        nid=self.mapping['flows'][0]['native_id']
        result=self.inspect(lambda r:r.find(f'.//curve[@id="{nid}"]').attrib.pop('ArrowheadHead'))
        self.assertTrue(any(s.startswith('curve_geometry') for s in result['issues']))

    def test_native_h_inference_does_not_use_ir(self):
        carbon=ET.fromstring('<n Element="6"/>')
        self.assertEqual(checker.actual_hydrogens(carbon,1),(3,'native_graph_valence'))
        carbon.set('NumHydrogens','4')
        with self.assertRaises(ValueError):checker.actual_hydrogens(carbon,1)

    def test_product_side_flow_binding_is_rejected(self):
        changed=copy.deepcopy(self.mapping);changed['flows'][0]['target']['state']=self.mechanism['transitions'][0]['to']
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'source.cdxml';path.write_bytes(self.xml)
            result=checker.verify(self.mechanism,self.scene,changed,path)
        self.assertTrue(any(i.startswith('flow_semantic_binding') for i in result['issues']))

    def test_native_font_run_overrides_cannot_hide_behind_root_default(self):
        result=self.inspect(lambda r:r.find('.//s').set('size','10'))
        self.assertIn('native_text_run_style',result['issues'])


if __name__=='__main__':unittest.main()
