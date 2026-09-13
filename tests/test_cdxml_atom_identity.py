"""Independent atom-serialization controls; no corpus or evaluation inputs."""
import unittest
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
from runtime.adapters.cdxml_atom_identity import (
    NativeDepictionError, node_attributes, read_node_identity, read_explicit_geometry,
    qualified_carbon_neighborhood,
)


class ExplicitNativeIdentityChecks(unittest.TestCase):
    def carbon_observation(self, unused=2, used=2):
        h = '' if unused == 0 else 'H' if unused == 1 else f'H<sub>{unused}</sub>'
        cut = '' if used == 0 else f'<sup>{used if used > 1 else ""}&bull;</sup>'
        return dict(native_id=100, atom_map='11', atomic_number=6, formal_charge=0,
                    isotope=0, radical_native_value=0, node_type_native_value=1,
                    implicit_h_allowed=True, abnormal_valence_allowed=False,
                    implicit_h_native_value=0, used_valences=used, unused_valences=unused,
                    selected_count=1, selected_atom_count=1, selected_bond_count=0,
                    selected_atom_ids=[100], selected_formula_html='C'+h+cut)

    def sidecar(self, path, atoms):
        after = path.with_name(path.stem + '-selection-after.cdxml')
        after.write_bytes(path.read_bytes())
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return dict(version='native-atom-readback/0.4', source_cdxml_sha256=digest, atoms=atoms,
                    chemical_export_mime='chemical/x-smiles', selection_chemical_export_unchanged=True,
                    chemical_export_before_sha256='1'*64, chemical_export_after_sha256='1'*64,
                    selection_graph_unchanged=True, selection_after_cdxml=dict(file=after.name,sha256=digest))

    def test_missing_h_is_unknown_even_for_familiar_elements(self):
        for number, hydrogens in ((6, 4), (7, 3), (8, 2), (11, 0), (15, 3)):
            with self.subTest(number=number), self.assertRaises(NativeDepictionError) as ctx:
                read_node_identity(ET.fromstring(f'<n Element="{number}"/>'),
                                   dict(atomic_number=number, implicit_h=hydrogens))
            self.assertEqual(ctx.exception.code, 'NATIVE_HYDROGEN_UNVERIFIED')

    def test_observed_h_is_compared_and_not_replaced_by_expected(self):
        node = ET.fromstring('<n Element="7" NumHydrogens="0"/>')
        with self.assertRaises(NativeDepictionError) as ctx:
            read_node_identity(node, dict(atomic_number=7, implicit_h=3))
        self.assertEqual(ctx.exception.details['observed'], 0)
        node.set('NumHydrogens', '3')
        self.assertEqual(read_node_identity(node, dict(atomic_number=7, implicit_h=3))['implicit_h'], 3)

    def test_isotope_charge_and_non_hcno_identity_are_checked(self):
        expected = dict(atomic_number=15, implicit_h=4, isotope=31, charge=1)
        node = ET.Element('n', node_attributes(expected, 15))
        self.assertEqual(read_node_identity(node, expected)['isotope'], 31)
        for field, value in (('Element', '16'), ('Charge', '0'), ('Isotope', '32')):
            changed = ET.fromstring(ET.tostring(node))
            changed.set(field, value)
            with self.subTest(field=field), self.assertRaises(NativeDepictionError):
                read_node_identity(changed, expected)

    def test_nonfinite_h_and_radical_are_not_silently_normalized(self):
        for attrs in ({'NumHydrogens': 'nan'}, {'NumHydrogens': '1.5'},
                      {'NumHydrogens': '0', 'Radical': 'Doublet'}):
            with self.subTest(attrs=attrs), self.assertRaises(NativeDepictionError):
                read_node_identity(ET.Element('n', attrs), dict(atomic_number=6, implicit_h=0))

    def test_h_is_observed_not_calculated_from_expected_ir(self):
        node = ET.fromstring('<n id="100" AtomNumber="11"/>')
        observation = self.carbon_observation()
        expected = dict(atomic_number=6, implicit_h=2)
        actual = read_node_identity(node, expected, native_observation=observation, native_bond_valence=2, native_neighborhood_qualified=True)
        self.assertEqual(actual['implicit_h'], 2)
        self.assertIn('FormulaHTML', actual['implicit_h_source'])
        with self.assertRaises(NativeDepictionError) as ctx:
            read_node_identity(node, {**expected, 'implicit_h': 3}, native_observation=observation, native_bond_valence=2, native_neighborhood_qualified=True)
        self.assertEqual(ctx.exception.code, 'NATIVE_ATOM_IDENTITY_CHANGED')
        self.assertEqual(ctx.exception.details['observed'], 2)

    def test_chloride_unused_valence_is_not_promoted_to_hydrogen(self):
        node = ET.fromstring('<n id="100" AtomNumber="11" Element="17" Charge="-1"/>')
        observation = {**self.carbon_observation(1, 0), 'atomic_number': 17, 'formal_charge': -1}
        with self.assertRaises(NativeDepictionError) as ctx:
            read_node_identity(node, dict(atomic_number=17, charge=-1, implicit_h=0),
                               native_observation=observation, native_bond_valence=0)
        self.assertEqual(ctx.exception.code, 'NATIVE_HYDROGEN_UNVERIFIED')
        node.set('NumHydrogens', '0')
        self.assertEqual(read_node_identity(node, dict(atomic_number=17, charge=-1, implicit_h=0),
                         native_observation=observation, native_bond_valence=0)['implicit_h'], 0)

    def test_unqualified_native_profiles_stay_unknown(self):
        node = ET.fromstring('<n id="100" AtomNumber="11"/>')
        for change in ({'formal_charge':1}, {'radical_native_value':1}, {'node_type_native_value':4},
                       {'implicit_h_allowed':False}, {'abnormal_valence_allowed':True},
                       {'used_valences':3}, {'used_valences':True},
                       {'native_id':99}, {'atom_map':'12'}, {'isotope':13},
                       {'selected_count':2}, {'selected_atom_ids':[101]},
                       {'selected_atom_count':2}, {'selected_bond_count':1}, {'selected_bond_count':False},
                       {'selected_formula_html':'C<sub>2</sub>H<sub>4</sub>'},
                       {'selected_formula_html':'CH<sub>4</sub>'},
                       {'selected_formula_html':'<sup>13</sup>CH<sub>2</sub><sup>2&bull;</sup>'},
                       {'selected_formula_html':'CH<sub>2</sub><sup>+</sup>'},
                       {'selected_formula_html':'CH<sub>3</sub><sup>&bull;</sup>'},
                       {'selected_formula_html':'CH<sub>2</sub><sup>3&bull;</sup>'}):
            with self.subTest(change=change), self.assertRaises(NativeDepictionError) as ctx:
                read_node_identity(node, dict(atomic_number=6, implicit_h=2),
                    native_observation={**self.carbon_observation(), **change}, native_bond_valence=2, native_neighborhood_qualified=True)
            self.assertEqual(ctx.exception.code, 'NATIVE_HYDROGEN_UNVERIFIED')

    def test_formula_h_zero_to_three_does_not_use_raw_valence_h_fields(self):
        node = ET.fromstring('<n id="100" AtomNumber="11"/>')
        for h in range(4):
            observation = self.carbon_observation(h, 4-h)
            observation['unused_valences'] = 99
            observation['implicit_h_native_value'] = 99
            with self.subTest(h=h):
                observed = read_node_identity(node, dict(atomic_number=6, implicit_h=h),
                    native_observation=observation, native_bond_valence=4-h, native_neighborhood_qualified=True)
                self.assertEqual(observed['implicit_h'], h)

    def test_h4_rings_and_unqualified_explicit_h_profiles_are_rejected(self):
        nodes = {i:ET.fromstring(f'<n Element="6"/>') for i in (11,27,43)}
        chain = {11:{27:2},27:{11:2,43:1},43:{27:1}}
        self.assertTrue(qualified_carbon_neighborhood(11,nodes,chain))
        for isotope in (0,2):
            nodes[27] = ET.fromstring(f'<n Element="1" Isotope="{isotope}" NumHydrogens="0"/>')
            self.assertTrue(qualified_carbon_neighborhood(11,nodes,{11:{27:1,43:1},27:{11:1},43:{11:1}}))
            self.assertFalse(qualified_carbon_neighborhood(11,nodes,chain))
        nodes[27].set('Isotope','3')
        self.assertFalse(qualified_carbon_neighborhood(11,nodes,{11:{27:1},27:{11:1},43:{}}))
        nodes[27] = ET.fromstring('<n Element="6"/>')
        self.assertFalse(qualified_carbon_neighborhood(11,nodes,{11:{27:1,43:2},27:{11:1,43:1},43:{27:1,11:2}}))
        self.assertFalse(qualified_carbon_neighborhood(11,nodes,{11:{27:1.5},27:{11:1.5},43:{}}))
        self.assertFalse(qualified_carbon_neighborhood(11,nodes,{11:{},27:{},43:{}}))
        with self.assertRaises(NativeDepictionError) as ctx:
            read_node_identity(ET.fromstring('<n id="100" AtomNumber="11"/>'),dict(atomic_number=6,implicit_h=4),
                native_observation=self.carbon_observation(4,0),native_bond_valence=0,native_neighborhood_qualified=True)
        self.assertEqual(ctx.exception.code,'NATIVE_HYDROGEN_UNVERIFIED')

    def test_sidecar_requires_matching_native_bytes_and_coverage(self):
        with tempfile.TemporaryDirectory() as parent:
            path = Path(parent) / 'native.cdxml'
            path.write_text('<CDXML><n id="100" AtomNumber="11" p="0 0"/><n id="101" AtomNumber="27" Element="9" NumHydrogens="0" p="10 0"/><b id="200" B="100" E="101" Order="1"/></CDXML>')
            carbon = self.carbon_observation(3, 1)
            fluoride = {**self.carbon_observation(0, 1), 'native_id':101, 'atom_map':'27', 'atomic_number':9}
            observations = self.sidecar(path, [carbon, fluoride])
            expected = {11:dict(element='C',atomic_number=6,implicit_h=3), 27:dict(element='F',atomic_number=9,implicit_h=0)}
            bonds = [dict(atoms=[11,27],order=1)]
            self.assertEqual(read_explicit_geometry(path, expected, bonds, atom_readback=observations)['atoms'][11]['implicit_h'], 3)
            for mutation in ('hash', 'missing', 'duplicate', 'chemical_export', 'mapped_atom', 'after_hash', 'graph_flag', 'filename'):
                changed = deepcopy(observations)
                if mutation == 'hash': changed['source_cdxml_sha256'] = '0'*64
                if mutation == 'missing': changed['atoms'].pop()
                if mutation == 'duplicate': changed['atoms'].append(carbon)
                if mutation == 'chemical_export': changed['chemical_export_after_sha256'] = '2'*64
                if mutation == 'mapped_atom': changed['atoms'][0]['atom_map'] = '12'
                if mutation == 'after_hash': changed['selection_after_cdxml']['sha256'] = '0'*64
                if mutation == 'graph_flag': changed['selection_graph_unchanged'] = False
                if mutation == 'filename': changed['selection_after_cdxml']['file'] = '../native.cdxml'
                with self.subTest(mutation=mutation), self.assertRaises(NativeDepictionError) as ctx:
                    read_explicit_geometry(path, expected, bonds, atom_readback=changed)
                self.assertEqual(ctx.exception.code, 'NATIVE_ATOM_OBSERVATION_UNVERIFIED')
            after_path = path.parent / observations['selection_after_cdxml']['file']
            for original, changed_text in (('Order="1"','Order="2"'), ('p="0 0"','p="1 0"'), ('B="100"','B="101"')):
                after_path.write_text(path.read_text().replace(original, changed_text))
                observations['selection_after_cdxml']['sha256'] = hashlib.sha256(after_path.read_bytes()).hexdigest()
                with self.subTest(original=original), self.assertRaises(NativeDepictionError) as ctx:
                    read_explicit_geometry(path, expected, bonds, atom_readback=observations)
                self.assertEqual(ctx.exception.code, 'NATIVE_ATOM_OBSERVATION_UNVERIFIED')


if __name__ == '__main__':
    unittest.main()
