"""Independent atom-serialization controls; no corpus or evaluation inputs."""
import unittest
import xml.etree.ElementTree as ET
from runtime.adapters.cdxml_atom_identity import (
    NativeDepictionError, node_attributes, read_node_identity,
)


class ExplicitNativeIdentityChecks(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
