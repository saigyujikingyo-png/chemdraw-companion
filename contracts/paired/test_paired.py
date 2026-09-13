import copy, hashlib, json, tempfile, unittest
from pathlib import Path
from target_extract import extract
from hidden_evaluate import compare, rigid_fit, unique_isomorphism
from validate_paired import validate

XML = '<CDXML><page id="1"><fragment id="2"><n id="3" Element="8" p="0 0"/><n id="4" Element="6" p="10 0"/><n id="5" Element="7" p="10 10"/><b id="6" B="3" E="4"/><b id="7" B="4" E="5"/></fragment><graphic id="8" GraphicType="Arc" ArrowType="FullHead" SupersededBy="9"/><arrow id="9" AngularSize="90" ArrowheadHead="Full" Head3D="1 2 0" Tail3D="3 4 0"/><graphic id="10" SymbolType="LonePair" BoundingBox="1 2 3 4"/></page></CDXML>'
class PairedTests(unittest.TestCase):
    def inventory(self, text=XML):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'input.cdxml'; p.write_text(text); return extract(p)
    def test_legacy_arc_not_double_counted(self):
        x=self.inventory(); self.assertEqual(x['complexity_profile']['curved_arrow_candidate_count'],1); self.assertEqual(x['complexity_profile']['lone_pair_object_count'],1)
    def test_native_circle_charge_symbol_spelling(self):
        x=self.inventory(XML.replace('SymbolType="LonePair"','SymbolType="CircleMinus"'))
        self.assertEqual(x['complexity_profile']['charge_symbol_count'],1)
    def test_curve_never_becomes_semantic_binding(self):
        x=self.inventory(); self.assertTrue(all(o['semantic_sink'] is None for o in x['objects'])); self.assertIsNone(x['complexity_profile']['confirmed_electron_flow_count'])
    def test_duplicate_native_id_rejected(self):
        with self.assertRaises(ValueError): self.inventory(XML.replace('id="4"','id="3"'))
    def test_entity_declaration_rejected(self):
        with self.assertRaises(ValueError): self.inventory('<!DOCTYPE CDXML [<!ENTITY x "secret">]>'+XML)
    def test_nonfinite_positions_not_accepted(self):
        x=self.inventory(XML.replace('p="0 0"','p="NaN 0"')); self.assertEqual(len(x['warnings']),1)
    def test_unique_graph_and_identity_deltas_are_not_full_pass(self):
        x=self.inventory(); r=compare(x,x); self.assertEqual(r['semantic']['matched_fragment_count'],1); self.assertEqual(set(r['gates'].values()),{'unmeasured'}); self.assertFalse(r['correction']['actual_gold']); validate('evaluator',r)
    def test_graph_charge_mismatch_not_matched(self):
        r=compare(self.inventory(),self.inventory(XML.replace('Element="8"','Element="8" Charge="-1"'))); self.assertEqual(r['semantic']['matched_fragment_count'],0)
    def test_symmetric_graph_is_ambiguous(self):
        g={'nodes':{'a':('C',),'b':('C',)},'edges':{frozenset(('a','b')):('1',)}}
        self.assertEqual(unique_isomorphism(g,g)[1],'ambiguous')
    def test_rigid_alignment_recovers_rotation_without_scale(self):
        f=rigid_fit([[0,0],[1,0],[0,2]],[[5,6],[5,7],[3,6]]); self.assertAlmostEqual(f['rotation_radians'],1.5707963267948966); self.assertLess(f['aligned_rmsd'],1e-9)
    def test_mismatch_correction_hash_rejected(self):
        r=compare(self.inventory(),self.inventory()); r['correction']['target_sha256']='0'*64
        with self.assertRaises(ValueError): validate('evaluator',r)
    def test_single_atom_orientation_unmeasured(self):
        self.assertIsNone(rigid_fit([[0,0]],[[2,3]])['rotation_radians'])
    def test_bond_stereo_not_silently_mapped(self):
        r=compare(self.inventory(),self.inventory(XML.replace('id="6" B=','id="6" Display="WedgeBegin" B='))); self.assertEqual(r['semantic']['matched_fragment_count'],0)

    def test_dangling_and_duplicate_bonds_refuse_matching(self):
        for bond in ['<b id="90" B="4" E="99"/>','<b id="90" B="3" E="4"/>','<b id="90" B="3" E="3"/>']:
            r=compare(self.inventory(),self.inventory(XML.replace('</fragment>',bond+'</fragment>')))
            self.assertEqual(r['semantic']['matched_fragment_count'],0); self.assertTrue(r['geometry']['ambiguities'])
    def test_legacy_curve_head_bits(self):
        r=self.inventory(XML.replace('</page>','<curve id="91" CurveType="8"/></page>'))
        self.assertEqual(r['complexity_profile']['curved_arrow_candidate_count'],2)
    def test_zero_angle_is_not_curved(self):
        r=self.inventory(XML.replace('AngularSize="90"','AngularSize="0.00"'))
        self.assertEqual(r['complexity_profile']['curved_arrow_candidate_count'],0)
    def test_dangling_supersession_retained_with_warning(self):
        r=self.inventory(XML.replace('SupersededBy="9"','SupersededBy="999"'))
        self.assertEqual(r['complexity_profile']['curved_arrow_candidate_count'],2); self.assertTrue(r['warnings'])

if __name__=='__main__': unittest.main()
