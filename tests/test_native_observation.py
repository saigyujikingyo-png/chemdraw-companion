"""Pure evidence-boundary controls; no native or evaluation payload access."""
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from runtime.native_observation import (quantity, observe_serialized_label_h, observe_atom_label,
                                        complete_atom_bond_evidence, compare_quantity, verify_frozen_sources)


class NativeObservationChecks(unittest.TestCase):
    def test_missing_zero_and_malformed_fields_remain_distinct(self):
        node = ET.fromstring('<n id="17" AtomNumber="29"/>')
        missing = observe_serialized_label_h(node, 'a'*64)
        node.set('NumHydrogens', '0'); zero = observe_serialized_label_h(node, 'a'*64)
        node.set('NumHydrogens', '-1'); malformed = observe_serialized_label_h(node, 'a'*64)
        self.assertEqual((missing['present'], missing['value'], missing['source_class']), (False,None,'unknown'))
        self.assertEqual((zero['present'], zero['value'], zero['source_class']), (True,0,'explicit_native_field'))
        self.assertEqual((malformed['present'], malformed['value'], malformed['reason']), (True,None,'malformed_field'))

    def test_only_nested_label_h_change_is_not_an_unchanged_graph(self):
        root = ET.fromstring('<CDXML><n id="17" AtomNumber="29"><t id="18"><s font="3">CH2</s></t></n></CDXML>')
        other = deepcopy(root); other.find('.//s').text = 'CH3'
        self.assertEqual(root.find('n').attrib, other.find('n').attrib)
        self.assertNotEqual(complete_atom_bond_evidence(root), complete_atom_bond_evidence(other))
        self.assertNotEqual(observe_atom_label(root.find('n'),'a'*64)['value'], observe_atom_label(other.find('n'),'b'*64)['value'])

    def test_expected_change_never_changes_or_fills_observed_value(self):
        node = ET.fromstring('<n id="17" AtomNumber="29" NumHydrogens="2"/>')
        observed = observe_serialized_label_h(node,'a'*64); before = deepcopy(observed)
        self.assertEqual(compare_quantity(observed,2)['status'],'match')
        self.assertEqual(compare_quantity(observed,3)['status'],'mismatch')
        self.assertEqual(observed,before)
        node.attrib.pop('NumHydrogens'); unknown = observe_serialized_label_h(node,'a'*64)
        self.assertEqual(compare_quantity(unknown,2)['status'],'unverified')
        self.assertIsNone(unknown['value'])

    def test_freeze_requires_matching_bytes_and_complete_required_sources(self):
        with tempfile.TemporaryDirectory() as parent:
            root=Path(parent);p=root/'observer.ps1';p.write_bytes(b'original\n')
            rows=[dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest())]
            self.assertEqual(verify_frozen_sources(root,rows,required_files=[p.name]),{p.name:rows[0]['sha256']})
            p.write_bytes(b'changed\n')
            with self.assertRaisesRegex(ValueError,'NATIVE_SOURCE_MISMATCH'):verify_frozen_sources(root,rows)
            p.write_bytes(b'original\n')
            with self.assertRaisesRegex(ValueError,'Required qualification'):verify_frozen_sources(root,rows,required_files=['parser.py'])
            with self.assertRaises(ValueError):verify_frozen_sources(root,rows+rows)
            with self.assertRaises(ValueError):verify_frozen_sources(root,[dict(file='../escape.py',sha256='a'*64)])

    def test_unknown_cannot_contain_a_resolved_value(self):
        with self.assertRaises(ValueError):
            quantity('non_node_attached_h',2,'unknown',field='missing',artifact_sha256='a'*64,
                     native_id=17,atom_map=29,scope='synthetic control')


if __name__=='__main__':unittest.main()
