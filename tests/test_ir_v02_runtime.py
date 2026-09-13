"""v0.2 integration guards using independent, small synthetic inputs."""
import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import shutil
from unittest.mock import patch
import xml.etree.ElementTree as ET
from contracts.ir_v02 import ATOMIC_NUMBERS, lower_depiction
from runtime.ir_v02_runtime import prepare_request, require_supported
from runtime.adapters.chemdraw_cdxml import seed_documents, materialize
from runtime.adapters.cdxml_atom_identity import NativeDepictionError, node_attributes, read_explicit_geometry
from runtime.mechanism_composer import compose, lone_pair_ports
from runtime.chemical_ir import chemical_colors
from runtime.native_provenance import verify_geometry_receipt, file_hash
from ir_v02_cases import selected_pairs, ammonium_salt, nonendpoint


class DepictionRuntimeChecks(unittest.TestCase):
    def test_native_atom_sidecar_receipt_hash_and_identity_are_enforced(self):
        # Entirely synthetic receipt: verifies the consumer boundary, not native execution.
        bundle = prepare_request(ammonium_salt())
        with tempfile.TemporaryDirectory() as parent:
            seed, output = Path(parent)/'seed', Path(parent)/'native'
            seed_documents(bundle['mechanism'],bundle['style'],seed,depiction_plan=bundle['plan'])
            output.mkdir()
            manifest = json.loads((seed/'geometry-manifest.json').read_text())
            name = manifest[0]['file']; native = output/name
            for target in (native, output/(native.stem+'-before.cdxml'), output/(native.stem+'-selection-after.cdxml')):
                shutil.copyfile(seed/name,target)
            atoms = [dict(native_id=int(n.get('id')),atom_map=n.get('AtomNumber'),atomic_number=int(n.get('Element','6')),
                          formal_charge=int(n.get('Charge','0')),isotope=int(n.get('Isotope','0')))
                     for n in ET.parse(native).getroot().iter('n')]
            sidecar = dict(version='native-atom-readback/0.4',source_cdxml_sha256=file_hash(native),atoms=atoms,
                           chemical_export_mime='chemical/x-smiles',selection_chemical_export_unchanged=True,
                           chemical_export_before_sha256='1'*64,chemical_export_after_sha256='1'*64,
                           selection_graph_unchanged=True,
                           selection_after_cdxml=dict(file=native.stem+'-selection-after.cdxml',sha256=file_hash(native)))
            sidecar_path = output/(native.stem+'.atoms.json')
            sidecar_path.write_text(json.dumps(sidecar))
            artifact = dict(file=name,input_sha256=file_hash(seed/name),output_sha256=file_hash(native),
                            before_sha256=file_hash(native),cleanup_completed=True,warnings=0,
                            atom_readback=dict(file=sidecar_path.name,sha256=file_hash(sidecar_path)))
            receipt = dict(version='native-geometry-receipt/0.1',status='complete',operation='ChemDraw.Objects.Clean(true)',
                           seed_provenance_sha256=file_hash(seed/'seed-provenance.json'),manifest_sha256=file_hash(seed/'geometry-manifest.json'),
                           artifacts=[artifact],environment=dict(application_build='26.0.0.6141',interop_version='22.0.0.0',
                               executable_sha256='f5383228898b6e6be08abded9f6db0909d0841a2f6a5bbef50ba00f44af8a084',
                               interop_sha256='ecaed777a648df79927c79c3d7a33e1a813c6b027c4111396b7139fdda81959a',
                               executor_sha256='2'*64,bridge_sha256='3'*64,owned_pid=1,hwnd_bound_pid=1))
            receipt_path = output/'native-geometry-receipt.json'
            receipt_path.write_text(json.dumps(receipt))
            call = lambda: verify_geometry_receipt(bundle['mechanism'],bundle['style'],manifest,seed,output,depiction_plan=bundle['plan'])
            self.assertIn(name,call()['atom_readbacks'])
            for mutation in ('sidecar_hash','source_hash','atom_map','coverage','graph'):
                changed = deepcopy(sidecar)
                after = output/sidecar['selection_after_cdxml']['file']
                shutil.copyfile(native,after)
                if mutation == 'source_hash': changed['source_cdxml_sha256'] = '0'*64
                if mutation == 'atom_map': changed['atoms'][0]['atom_map'] = 99
                if mutation == 'coverage': changed['atoms'] = []
                if mutation == 'graph':
                    tree = ET.parse(after); next(tree.getroot().iter('n')).set('p','99 99'); tree.write(after)
                    changed['selection_after_cdxml']['sha256'] = file_hash(after)
                sidecar_path.write_text(json.dumps(changed))
                artifact['atom_readback']['sha256'] = '0'*64 if mutation == 'sidecar_hash' else file_hash(sidecar_path)
                receipt_path.write_text(json.dumps(receipt))
                with self.subTest(mutation=mutation), self.assertRaises(ValueError): call()

    def test_full_table_encoding_is_not_a_native_quality_claim(self):
        self.assertEqual(len(ATOMIC_NUMBERS), 118)
        for element, number in ATOMIC_NUMBERS.items():
            self.assertEqual(node_attributes({'implicit_h': 0}, number)['Element'], str(number))

    def test_nonendpoint_flow_bypasses_legacy_validator(self):
        with patch('runtime.chemical_ir.validate_semantics', side_effect=AssertionError('Legacy validator called')):
            bundle = prepare_request(nonendpoint())
            require_supported(bundle)
        flow = bundle['plan']['electron_flows'][0]
        self.assertEqual(flow['source']['chemical_port']['atoms'], [1, 2])
        self.assertEqual(flow['sink']['chemical_port'], {'type': 'atom', 'atom': 3})
        self.assertEqual(bundle['compiled']['transitions'][0]['electron_flows'][0]['sink']['atom'], 3)

    def test_hidden_counterion_preserves_inventory_and_excludes_native_atom(self):
        bundle = prepare_request(ammonium_salt()); require_supported(bundle)
        with tempfile.TemporaryDirectory() as parent:
            folder = Path(parent) / 'seed'
            seed_documents(bundle['mechanism'], bundle['style'], folder, depiction_plan=bundle['plan'])
            nodes = list(ET.parse(folder / 'state-000.cdxml').getroot().iter('n'))
            self.assertEqual([n.get('AtomNumber') for n in nodes], ['10'])
            preserved = json.loads((folder / 'lowered-depiction.json').read_text())
            self.assertEqual(len(preserved['chemical_inventory']['atom_catalog']), 2)
            self.assertEqual(preserved['states'][0]['hidden_species'][0]['chemical_atom_refs'], [20])

    def test_display_edit_changes_only_depiction_hash_and_not_chemical_roles(self):
        source = selected_pairs()['mechanism']; changed = deepcopy(source)
        changed['depiction_states'][0]['lone_pairs'] = []
        a, b = lower_depiction(source), lower_depiction(changed)
        self.assertEqual(a['chemical_inventory_sha256'], b['chemical_inventory_sha256'])
        self.assertNotEqual(a['depiction_plan_sha256'], b['depiction_plan_sha256'])
        self.assertEqual(chemical_colors(source), chemical_colors(changed))

    def test_selected_pair_index_and_virtual_donor_are_separate(self):
        bundle = prepare_request(selected_pairs()); require_supported(bundle)
        self.assertEqual(bundle['plan']['states'][0]['lone_pair_slots'][0]['pair_index'], 2)
        self.assertEqual(bundle['plan']['electron_flows'][0]['source']['kind'], 'virtual_lone_pair')
        state = {'bonds': [], 'lone_pairs': [{'atom': 1, 'count': 3}]}
        components = [{'atoms': [{'map': 1, 'position': [0, 0], 'label': None}], 'bonds': []}]
        slots = [{'atom_ref': 1, 'pair_index': 2, 'orientation': 'auto', 'draw_lone_pair': True},
                 {'atom_ref': 1, 'pair_index': 0, 'orientation': 'auto', 'draw_lone_pair': False}]
        pairs = lone_pair_ports(state, components, 14.4, slots)
        self.assertEqual({p['pair_index'] for p in pairs}, {0, 2})
        self.assertEqual([p['pair_index'] for p in pairs if p['draw_lone_pair']], [2])
        self.assertEqual(sum(p['dot_axis'][k] * p['position'][k] for k in range(2) for p in pairs), 0)

    def test_abbreviation_has_typed_rejection_without_expansion(self):
        payload = ammonium_salt()
        payload['mechanism']['depiction_states'][0]['species'][0].update(role='abbreviated', label='Ammonium')
        bundle = prepare_request(payload)
        with self.assertRaises(NativeDepictionError): require_supported(bundle)
        self.assertEqual(bundle['plan']['states'][0]['visible_atoms'], [])
        self.assertEqual(bundle['plan']['states'][0]['abbreviations'][0]['label'], 'Ammonium')
        self.assertEqual(bundle['validation']['checked_invariants']['status'], 'pass')

    def test_condition_species_caption_is_preserved(self):
        bundle = prepare_request(ammonium_salt('condition_caption')); require_supported(bundle)
        state = bundle['plan']['states'][0]
        self.assertEqual(len(state['visible_atoms']), 1)
        self.assertEqual(state['captions'][1]['role'], 'condition')
        self.assertEqual(state['captions'][1]['species_refs'], ['anion'])

    def test_explicit_orientation_is_not_silently_replaced_by_auto(self):
        payload = selected_pairs()
        payload['mechanism']['depiction_states'][0]['lone_pairs'][0]['slots'][0]['orientation'] = 'north'
        bundle = prepare_request(payload)
        with self.assertRaises(NativeDepictionError): require_supported(bundle)
        self.assertEqual(bundle['plan']['states'][0]['lone_pair_slots'][0]['orientation'], 'north')

    def test_native_readback_rejects_unexpected_visible_counterion(self):
        with tempfile.TemporaryDirectory() as parent:
            path = Path(parent) / 'native.cdxml'
            path.write_text('<CDXML><n id="1" AtomNumber="10" Element="7" NumHydrogens="4" Charge="1" p="0 0"/><n id="2" AtomNumber="20" Element="17" NumHydrogens="0" Charge="-1" p="30 0"/></CDXML>')
            with self.assertRaises(NativeDepictionError) as ctx:
                read_explicit_geometry(path, {10: dict(element='N', atomic_number=7, implicit_h=4, charge=1)}, [])
            self.assertEqual(ctx.exception.code, 'NATIVE_VISIBLE_INVENTORY_CHANGED')

    def test_forged_lowered_plan_is_rejected_before_seed_writes(self):
        bundle = prepare_request(ammonium_salt())
        forged = deepcopy(bundle['plan']); forged['chemical_inventory']['atom_catalog'].pop()
        with tempfile.TemporaryDirectory() as parent:
            folder = Path(parent) / 'seed'
            with self.assertRaises(NativeDepictionError) as ctx:
                seed_documents(bundle['mechanism'], bundle['style'], folder, depiction_plan=forged)
            self.assertEqual(ctx.exception.code, 'DEPICTION_PLAN_MISMATCH')
            self.assertFalse(folder.exists())

    def test_one_electron_flow_never_becomes_full_head(self):
        scene = {'style': selected_pairs()['layout_policy'], 'width_pt': 100, 'height_pt': 100,
                 'states': [], 'texts': [], 'connectors': [],
                 'flows': [{'id': 'radical-control', 'electron_count': 1}]}
        with tempfile.TemporaryDirectory() as parent:
            folder = Path(parent) / 'out'
            with self.assertRaises(NativeDepictionError) as ctx: materialize(scene, folder)
            self.assertEqual(ctx.exception.code, 'NATIVE_FLOW_ELECTRON_COUNT_UNSUPPORTED')
            self.assertFalse((folder / 'mechanism.cdxml').exists())

    def test_cli_records_semantic_success_separately_from_capability_failure(self):
        from probes.run_composer import main
        payload = ammonium_salt()
        payload['mechanism']['depiction_states'][0]['species'][0].update(role='abbreviated', label='Ammonium')
        with tempfile.TemporaryDirectory() as parent:
            request, out = Path(parent) / 'request.json', Path(parent) / 'out'
            request.write_text(json.dumps(payload), encoding='utf-8')
            with patch.object(sys, 'argv', ['run_composer', 'seed', '--request', str(request), '--out', str(out)]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 1)
            result = json.loads((out / 'stage-result.json').read_text())
            self.assertEqual(result['input_semantic_validation'], 'pass')
            self.assertEqual(result['failed_phase'], 'depiction_capability')
            self.assertFalse(list(out.glob('*.cdxml')))


if __name__ == '__main__': unittest.main()
