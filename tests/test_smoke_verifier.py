import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verify_smoke', ROOT / 'probes/verify_smoke.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SmokeEvidenceChecks(unittest.TestCase):
    def snapshot(self, xml):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'case.cdxml'
            path.write_text(xml, encoding='utf-8')
            return module.graph_snapshot(path)

    def test_ids_may_be_renumbered_without_changing_appearance(self):
        first = '<CDXML><n id="1" p="0 0"/><n id="2" Element="8" p="10 0"/><b B="1" E="2"/></CDXML>'
        second = '<CDXML><n id="90" Element="8" p="10 0"/><n id="80" p="0 0"/><b B="80" E="90"/></CDXML>'
        self.assertEqual(self.snapshot(first), self.snapshot(second))

    def test_charge_loss_is_not_equivalent(self):
        original = '<CDXML><n id="1" Element="8" Charge="-1" p="0 0"/></CDXML>'
        changed = original.replace('Charge="-1"', '')
        self.assertNotEqual(self.snapshot(original), self.snapshot(changed))

    def test_wedge_direction_is_not_ignored(self):
        original = '<CDXML><n id="1" p="0 0"/><n id="2" p="10 0"/><b B="1" E="2" Display="WedgeBegin"/></CDXML>'
        self.assertNotEqual(self.snapshot(original), self.snapshot(original.replace('WedgeBegin', 'WedgeEnd')))

    def test_dropped_caption_is_not_equivalent(self):
        original = '<CDXML><n id="1" p="0 0"/><t><s>condition</s></t></CDXML>'
        self.assertNotEqual(self.snapshot(original), self.snapshot('<CDXML><n id="1" p="0 0"/></CDXML>'))

    def test_arrows_require_separate_comparator(self):
        with self.assertRaisesRegex(ValueError, 'separate qualified comparator'):
            self.snapshot('<CDXML><arrow id="7"/></CDXML>')

    def test_dangling_bond_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Dangling'):
            self.snapshot('<CDXML><n id="1" p="0 0"/><b B="1" E="9"/></CDXML>')

    def test_duplicate_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.snapshot('<CDXML><n id="1" p="0 0"/><n id="1" p="10 0"/></CDXML>')


if __name__ == '__main__':
    unittest.main()
