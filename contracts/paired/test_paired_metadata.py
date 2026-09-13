"""Synthetic metadata regressions; no test fixture is a native or human acceptance receipt."""
import copy
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from jsonschema import ValidationError
from validate_paired import validate


REJECTIONS = (ValueError, ValidationError, OSError)
TIMESTAMP = '2026-09-13T11:00:00Z'
COUNTS = ('curved_arrow_count', 'curved_arrow_candidate_count', 'lone_pair_count',
          'charge_count', 'radical_count', 'molecule_count', 'state_count',
          'step_count', 'caption_count', 'simultaneous_flow_count', 'common_scaffold_count')


class PairedMetadataTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix='paired-metadata-synthetic-')
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.original = self.asset('original_target', 'original.cdxml',
                                   b'<CDXML><page id="1"/></CDXML>', 'chemical/x-cdxml')
        self.source = {
            'source_url': 'https://example.invalid/synthetic-review-fixture',
            'citation': 'Synthetic test only; not an acquired sample or human approval.',
            'author_or_project': 'Synthetic fixture', 'retrieved_at': TIMESTAMP,
            'original_sha256': self.original['sha256'], 'asset_types': ['CDXML'],
            'redistributable': 'unknown', 'license': None, 'license_evidence_url': None,
            'container': None,
        }

    def asset(self, role, locator, content, media_type='application/json'):
        path = self.root / locator
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return dict(role=role, relative_locator=locator, sha256=hashlib.sha256(content).hexdigest(),
                    bytes=len(content), media_type=media_type)

    def json_asset(self, role, locator, value=None):
        value = {'synthetic': True, 'role': role} if value is None else value
        return self.asset(role, locator, json.dumps(value, sort_keys=True).encode())

    def source_record(self):
        return dict(version='paired-source-manifest/1.0', sample_id='synthetic-only',
                    source=copy.deepcopy(self.source), assets=[copy.deepcopy(self.original)],
                    raw_asset_distribution='private_only', retrieval_notes=[])

    def registry(self):
        complexity = dict.fromkeys(COUNTS, None)
        complexity.update(dense_anchor_risk=None, multirow=None, snake_layout=None)
        record = dict(version='paired-registry/1.0', sample_id='synthetic-only',
                      source=copy.deepcopy(self.source), mechanism_family='proton_transfer',
                      complexity_profile=complexity, condition_text_present=None,
                      structured_target_available=True, native_render_available=False,
                      research_status='inventory_only', redistributable='unknown',
                      split='research_development', frozen_or_descendant=False, lineage=[],
                      exposure_history=[], assets=[copy.deepcopy(self.original)], evidence_notes=[])
        record.update(dict.fromkeys(('curved_arrow_count', 'lone_pair_count', 'charge_count',
                                     'state_count', 'step_count'), None))
        return record

    def split(self, task='A_png_reconstruction', status='completed'):
        png = io.BytesIO()
        Image.new('RGB', (1, 1), 'white').save(png, format='PNG')
        image = self.asset('reference_png', 'generator_input/reference.png', png.getvalue(), 'image/png')
        inputs = [image] if task == 'A_png_reconstruction' else [
            self.asset('request_text', 'generator_input/request.txt', b'Synthetic proton transfer request.', 'text/plain')]
        original = dict(self.original, role='target_cdxml')
        hidden = [original] + [self.json_asset(role, 'hidden_target/'+role+'.json')
                               for role in ('target_readback', 'target_inventory', 'target_geometry')]
        packet = self.json_asset('model_request_packet', 'evaluation/model-request.json')
        receipt = self.json_asset('isolation_receipt', 'evaluation/isolation-receipt.json')
        candidate = self.json_asset('candidate_ir', 'candidate/mechanism.ir.json')
        run = dict(run_id='synthetic-run', timestamp=TIMESTAMP, task=task,
                   requested_model='synthetic-model', actual_model='synthetic-model',
                   reasoning_effort='max', prompt='Synthetic test; no actual model call.',
                   exposed_assets=copy.deepcopy(inputs), exposed_payload_sha256=packet['sha256'],
                   isolation_receipt_sha256=receipt['sha256'], generator_tools=[],
                   target_access_test='pass', status=status)
        return dict(version='paired-hidden-split/1.0', sample_id='synthetic-only', task=task,
                    generator_input=inputs, hidden_target=hidden, candidate=[candidate],
                    evaluation=[packet, receipt], run=run, sealed_before_generation=True,
                    target_geometry_exposed=False)

    def correction(self):
        return dict(version='paired-correction-deltas/1.0', tier='silver', actual_gold=False,
                    direction='candidate_to_target', target_sha256='a'*64, candidate_sha256='b'*64,
                    deltas=[], unmeasured_kinds=[], human_active_seconds=None)

    def evaluation(self):
        c = self.correction()
        return dict(version='paired-evaluation/1.0', target_sha256=c['target_sha256'],
                    candidate_sha256=c['candidate_sha256'],
                    gates=dict.fromkeys(('chemical_correctness', 'native_editability',
                                         'visual_quality', 'human_acceptance'), 'unmeasured'),
                    semantic={}, objects={}, geometry={}, native_visual={}, correction=c,
                    limits=['Synthetic metadata only; no native/chemical/human qualification.'])

    def reject(self, kind, record, check_bytes=False):
        with self.assertRaises(REJECTIONS):
            validate(kind, record, self.root if check_bytes else None)

    def test_private_unknown_rights_source_remains_admissible_without_authentication(self):
        result = validate('source-manifest', self.source_record(), self.root)
        self.assertEqual(result['assets_checked'], 1)
        self.assertFalse(result['native_claim_authenticated'])
        self.assertFalse(result['human_claim_authenticated'])

    def test_original_source_hash_must_bind_checked_original(self):
        record = self.source_record(); record['source']['original_sha256'] = '0'*64
        self.reject('source-manifest', record, True)

    def test_source_retrieval_timestamp_requires_valid_timezone_aware_datetime(self):
        for value in ('not a timestamp', '2026-09-13', '2026-09-13T11:00:00'):
            with self.subTest(retrieved_at=value):
                record = self.source_record(); record['source']['retrieved_at'] = value
                self.reject('source-manifest', record)

    def test_missing_or_duplicate_original_role_rejected(self):
        for assets in ([], [self.original, self.original]):
            with self.subTest(count=len(assets)):
                record = self.source_record(); record['assets'] = assets
                self.reject('source-manifest', record)

    def test_original_role_cannot_be_replaced_by_unrelated_asset_role(self):
        record = self.source_record(); record['assets'][0]['role'] = 'preview'
        self.reject('source-manifest', record)

    def test_source_bytes_are_rechecked(self):
        (self.root/self.original['relative_locator']).write_bytes(b'changed')
        self.reject('source-manifest', self.source_record(), True)

    def test_asset_cannot_escape_root(self):
        record = self.source_record(); record['assets'][0]['relative_locator'] = '../outside.cdxml'
        self.reject('source-manifest', record, True)

    def test_unknown_rights_cannot_be_promoted_by_registry_disagreement(self):
        record = self.registry(); record['redistributable'] = 'yes'
        self.reject('registry', record)

    def test_m2_namespaced_lineage_is_excluded(self):
        for lineage in ('benchmark:M2', 'urn:sample:M2', 'M2', 'external/beckmann-derivative'):
            with self.subTest(lineage=lineage):
                record = self.registry(); record['lineage'] = [lineage]
                self.reject('registry', record)
                record['split'] = 'excluded'
                self.assertTrue(validate('registry', record)['schema_valid'])

    def test_m1_exposed_development_is_not_m2(self):
        record = self.registry(); record['sample_id'] = 'M1'; record['lineage'] = ['benchmark:M1']
        self.assertTrue(validate('registry', record)['schema_valid'])

    def test_frozen_descendant_without_name_cannot_enter_development(self):
        record = self.registry(); record['frozen_or_descendant'] = True
        self.reject('registry', record)

    def test_native_paired_claim_requires_full_native_evidence_roles(self):
        record = self.registry(); record['research_status'] = 'native_paired'
        self.reject('registry', record)

    def test_native_render_availability_requires_reference_asset(self):
        record = self.registry(); record['native_render_available'] = True
        self.reject('registry', record)

    def test_counts_reject_negative_fractional_boolean_and_nonfinite_values(self):
        for value in (-1, 0.5, True, float('nan'), float('inf')):
            for location in ('root', 'complexity'):
                with self.subTest(value=value, location=location):
                    record = self.registry()
                    target = record if location == 'root' else record['complexity_profile']
                    target['curved_arrow_count'] = value
                    self.reject('registry', record)

    def test_zero_and_unknown_counts_remain_valid(self):
        record = self.registry(); record['curved_arrow_count'] = 0
        record['complexity_profile']['curved_arrow_count'] = 0
        self.assertTrue(validate('registry', record)['schema_valid'])

    def test_complete_synthetic_metadata_is_not_native_or_human_qualification(self):
        result = validate('hidden-split', self.split(), self.root)
        self.assertEqual(result['assets_checked'], 8)
        self.assertFalse(result['native_claim_authenticated'])
        self.assertFalse(result['human_claim_authenticated'])

    def test_run_cannot_pass_without_actual_byte_check(self):
        self.reject('hidden-split', self.split())

    def test_each_hidden_target_component_is_required(self):
        for role in ('target_cdxml', 'target_readback', 'target_inventory', 'target_geometry'):
            with self.subTest(role=role):
                record = self.split()
                record['hidden_target'] = [a for a in record['hidden_target'] if a['role'] != role]
                self.reject('hidden-split', record, True)

    def test_completed_inference_requires_candidate_ir(self):
        record = self.split(); record['candidate'] = []
        self.reject('hidden-split', record, True)

    def test_completed_inference_requires_identified_actual_model(self):
        for value in (None, '', '   '):
            with self.subTest(actual_model=value):
                record = self.split(); record['run']['actual_model'] = value
                self.reject('hidden-split', record, True)

    def test_failed_inference_can_preserve_missing_output_and_unknown_actual_model(self):
        record = self.split(status='failed'); record['candidate'] = []; record['run']['actual_model'] = None
        self.assertTrue(validate('hidden-split', record, self.root)['schema_valid'])

    def test_task_b_requires_request_or_semantic_ir_not_schema_only(self):
        record = self.split(task='B_blind_composition')
        record['generator_input'][0]['role'] = 'runtime_ir_schema'
        record['run']['exposed_assets'] = copy.deepcopy(record['generator_input'])
        self.reject('hidden-split', record, True)

    def test_task_b_request_input_is_valid(self):
        self.assertTrue(validate('hidden-split', self.split(task='B_blind_composition'), self.root)['schema_valid'])

    def test_payload_and_receipt_hashes_must_have_corresponding_assets(self):
        for field in ('exposed_payload_sha256', 'isolation_receipt_sha256'):
            with self.subTest(field=field):
                record = self.split(); record['run'][field] = '0'*64
                self.reject('hidden-split', record, True)

    def test_bound_run_evidence_bytes_cannot_be_changed(self):
        for role in ('model_request_packet', 'isolation_receipt'):
            with self.subTest(role=role):
                record = self.split()
                asset = next(a for a in record['evaluation'] if a['role'] == role)
                (self.root/asset['relative_locator']).write_bytes(b'changed after binding')
                self.reject('hidden-split', record, True)

    def test_run_exposure_list_must_match_generator_assets(self):
        record = self.split(); record['run']['exposed_assets'] = []
        self.reject('hidden-split', record, True)

    def test_hidden_bytes_cannot_be_exposed_as_runtime_schema(self):
        record = self.split()
        record['generator_input'].append(dict(record['hidden_target'][2], role='runtime_ir_schema'))
        record['run']['exposed_assets'] = copy.deepcopy(record['generator_input'])
        self.reject('hidden-split', record, True)

    def test_unsealed_or_failed_denial_probe_cannot_claim_run(self):
        for mutation in ('unsealed', 'fail', 'not_run'):
            with self.subTest(mutation=mutation):
                record = self.split()
                if mutation == 'unsealed': record['sealed_before_generation'] = False
                else: record['run']['target_access_test'] = mutation
                self.reject('hidden-split', record, True)

    def test_run_timestamp_is_an_actual_datetime(self):
        for value in ('not a timestamp', '2026-09-13', '2026-09-13T11:00:00'):
            with self.subTest(timestamp=value):
                record = self.split(); record['run']['timestamp'] = value
                self.reject('hidden-split', record, True)

    def test_png_signature_without_decodable_image_is_rejected(self):
        record = self.split()
        bad = self.asset('reference_png', 'generator_input/reference.png', bytes.fromhex('89504e470d0a1a0a'), 'image/png')
        record['generator_input'] = [bad]; record['run']['exposed_assets'] = [copy.deepcopy(bad)]
        self.reject('hidden-split', record, True)

    def test_unsupported_pass_gate_cannot_be_self_declared(self):
        for gate in self.evaluation()['gates']:
            with self.subTest(gate=gate):
                record = self.evaluation(); record['gates'][gate] = 'pass'
                self.reject('evaluator', record)

    def test_correction_hash_must_match_evaluation_hash(self):
        record = self.evaluation(); record['correction']['target_sha256'] = '0'*64
        self.reject('evaluator', record)

    def test_known_finite_vector_and_angle_deltas_are_admissible(self):
        record = self.correction()
        record['deltas'] = [dict(kind='atom_displacement', target_id='t', candidate_id='c',
                                 value=[1.5, -2], unit='CDXML points', frame='unaligned_native_global'),
                            dict(kind='fragment_rotation', target_id='t', candidate_id='c',
                                 value=0.25, unit='radians', frame='candidate_to_target_global_rigid')]
        self.assertTrue(validate('correction-delta', record)['schema_valid'])

    def test_invalid_delta_shape_unit_frame_and_nonfinite_values_rejected(self):
        delta = dict(kind='atom_displacement', target_id='t', candidate_id='c', value=[1, 2],
                     unit='CDXML points', frame='unaligned_native_global')
        mutations = [('value', {'junk': ['not a number']}), ('value', [1]), ('value', [True, 0]),
                     ('value', [1, float('inf')]), ('unit', 'banana'), ('frame', 'unspecified')]
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                record = self.correction(); changed = copy.deepcopy(delta); changed[field] = value
                record['deltas'] = [changed]; self.reject('correction-delta', record)

    def test_reserved_delta_is_not_silently_accepted_as_implemented(self):
        record = self.correction()
        record['deltas'] = [dict(kind='curve_shape', target_id='t', candidate_id='c', value={},
                                 unit='CDXML points', frame='unaligned_native_global')]
        self.reject('correction-delta', record)

    def test_nonfinite_or_negative_human_time_rejected(self):
        for value in (float('nan'), float('inf'), -1):
            with self.subTest(value=value):
                record = self.correction(); record['human_active_seconds'] = value
                self.reject('correction-delta', record)

    def test_silver_record_cannot_claim_actual_gold(self):
        record = self.correction(); record['actual_gold'] = True
        self.reject('correction-delta', record)


if __name__ == '__main__':
    unittest.main()
