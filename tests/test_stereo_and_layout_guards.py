"""Independent stereo counterexamples and bounded annotation constraints."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'probes'))
from acyclic_smiles_check import same_stereo
from runtime.annotation_layout import annotation_gap


class StereoAndLayoutGuards(unittest.TestCase):
    def test_branch_permutation_preserves_input_stereo(self):
        self.assertTrue(same_stereo('[NH3+:1][C@@H:2]([CH3:3])[C:4](=[O:5])[O-:6]','[NH3+][C@H](C([O-])=O)C'))

    def test_enantiomer_missing_stereo_and_isotope_are_rejected(self):
        original='[NH3+][C@@H](C)C(=O)[O-]'
        for other in ['[NH3+][C@H](C)C(=O)[O-]','[NH3+]C(C)C(=O)[O-]','[NH3+][13C@@H](C)C(=O)[O-]']:
            self.assertFalse(same_stereo(original,other))

    def test_unsupported_smiles_cannot_pass(self):
        with self.assertRaises(ValueError):same_stereo('C1CC1','C1CC1')

    def test_annotation_gap_covers_head_and_control_port(self):
        for B,extension in [(14.4,4.22),(20,7),(10,0)]:
            self.assertGreater(annotation_gap(B,extension)-extension-B/6,.22*B)


if __name__=='__main__':unittest.main()
