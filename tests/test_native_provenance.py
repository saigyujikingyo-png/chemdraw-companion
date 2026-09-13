import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from general_ir_cases import proton_transfer
from runtime.adapters.chemdraw_cdxml import seed_documents,read_geometry
from runtime.native_provenance import verify_geometry_receipt,check_style


class NativeProvenanceGuards(unittest.TestCase):
    def setUp(self):
        self.m=proton_transfer();self.style=json.loads((ROOT/'examples/m2-composer-request.json').read_text(encoding='utf-8'))['layout_policy']

    def test_seed_cannot_claim_native_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            seed=Path(folder)/'seed';manifest=seed_documents(self.m,self.style,seed)
            with self.assertRaisesRegex(ValueError,'execution receipt'):read_geometry(self.m,manifest,seed,input_folder=seed,style=self.style)

    def test_missing_receipt_and_incomplete_status_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            seed=Path(folder)/'seed';manifest=seed_documents(self.m,self.style,seed)
            (seed/'native-geometry-receipt.json').write_text(json.dumps({'version':'native-geometry-receipt/0.1','status':'running','operation':'ChemDraw.Objects.Clean(true)'}),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Uncompleted'):verify_geometry_receipt(self.m,self.style,manifest,seed,seed)

    def test_nonfinite_and_wrong_style_rejected(self):
        import xml.etree.ElementTree as ET
        with tempfile.TemporaryDirectory() as folder:
            seed=Path(folder)/'seed';manifest=seed_documents(self.m,self.style,seed);path=seed/manifest[0]['file'];root=ET.parse(path).getroot()
            for value in ('nan','7'):
                root.set('LabelSize',value);ET.ElementTree(root).write(path,encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'style mismatch'):check_style(path,self.style)


if __name__=='__main__':unittest.main()
