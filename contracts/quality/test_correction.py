"""Synthetic unit fixtures only: fake bytes/people/times are NOT corpus evidence."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

try:
    from .validate_correction import FIELDS, validate_record, subtract
except ImportError:
    from validate_correction import FIELDS, validate_record, subtract


ALL_FIELDS = {f for fields in FIELDS.values() for f in fields} | {'step_spacing'}


def fixture(directory):
    """Manufacture deterministic test claims, never actual native/human records."""
    assets = []
    def asset(identity, kind, content, parents=()):
        data = content if isinstance(content, bytes) else json.dumps(content, sort_keys=True).encode()
        filename = identity + '.fixture'
        (directory / filename).write_bytes(data)
        assets.append({'id':identity, 'path':filename, 'kind':kind, 'bytes':len(data), 'sha256':hashlib.sha256(data).hexdigest(), 'derived_from':list(parents)})
        return identity
    asset('unit-provenance', 'provenance', b'SYNTHETIC TEST license evidence, no grant')
    asset('unit-review', 'review_evidence', b'SYNTHETIC TEST review, no actual human')
    asset('unit-timer', 'timing_log', b'SYNTHETIC TEST time, not measured')
    # Real schema-probe bytes; the surrounding native/person/time claims stay synthetic.
    ir_fixture = Path(__file__).resolve().parents[2] / 'examples' / 'corpus' / 'proton-transfer.ir.json'
    asset('unit-ir', 'ir', ir_fixture.read_bytes())
    snapshots, readbacks, correspondence, diffs = {}, [], [], []
    kinds = list(FIELDS)
    for stage, offset in (('first', 0), ('final', 2)):
        snapshot = {'revision_id':'unit-'+stage, 'ir_asset_ref':'unit-ir', 'render_asset_refs':[]}
        for fmt in ('cdx', 'cdxml'):
            native_id = asset('unit-'+stage+'-'+fmt, fmt, ('SYNTHETIC NOT NATIVE '+stage+fmt).encode())
            snapshot[fmt+'_asset_ref'] = native_id
            render_id = asset('unit-'+stage+'-'+fmt+'-render', 'native_render', ('SYNTHETIC NOT PNG '+stage+fmt).encode(), [native_id])
            snapshot['render_asset_refs'].append(render_id)
            native_asset = next(a for a in assets if a['id'] == native_id)
            assets[-1]['render_provenance'] = {'native_asset_ref':native_id, 'native_sha256':native_asset['sha256'], 'revision_id':'unit-'+stage, 'rendered_at':'2026-01-01T00:00:40+00:00'}
            objects = []
            for i, kind in enumerate(kinds):
                geometry = {'position':None,'rotation_deg':None,'anchors':None,'control_points':None}
                for prop in FIELDS[kind].values():
                    geometry[prop] = offset if prop == 'rotation_deg' else ([i+offset, 10] if prop == 'position' else [[i+offset, 10],[i+5+offset, 20]])
                objects.append({'id':fmt+'-'+kind, 'kind':kind, 'semantic_ref':'unit-entity-'+kind, 'geometry':geometry})
            native = next(a for a in assets if a['id']==native_id)
            payload = {'version':'gold-native-readback/1.0','source_asset_sha256':native['sha256'],'source_revision_id':'unit-'+stage,'format':fmt,'coordinate_frame':'unit-page','units':'pt','objects':objects,'step_spacings':[{'id':'unit-gap','from_step':'unit-step-a','to_step':'unit-step-b','value_pt':30+offset}]}
            rid = asset('unit-'+stage+'-'+fmt+'-readback','native_readback',payload,[native_id])
            readbacks.append({'stage':stage,'format':fmt,'native_asset_ref':native_id,'readback_asset_ref':rid,'status':'pass','reopened_at':'2026-01-01T00:00:30+00:00','payload':payload})
        snapshots[stage]=snapshot
    for kind in kinds:
        correspondence.append({'entity_id':'unit-'+kind,'kind':kind,'semantic_ref':'unit-entity-'+kind,'status':'unique','first':{'cdx':'cdx-'+kind,'cdxml':'cdxml-'+kind},'final':{'cdx':'cdx-'+kind,'cdxml':'cdxml-'+kind},'evidence_refs':[readbacks[0]['readback_asset_ref'],readbacks[-1]['readback_asset_ref']]})
        for field, prop in FIELDS[kind].items():
            before=next(o for o in readbacks[1]['payload']['objects'] if o['kind']==kind)['geometry'][prop]
            after=next(o for o in readbacks[3]['payload']['objects'] if o['kind']==kind)['geometry'][prop]
            diffs.append({'entity_id':'unit-'+kind,'field':field,'coordinate_frame':'unit-page','units':'degree' if field=='fragment_rotation' else 'pt','before':copy.deepcopy(before),'after':copy.deepcopy(after),'delta':subtract(after,before)})
    diffs.append({'entity_id':'unit-gap','field':'step_spacing','coordinate_frame':'unit-page','units':'pt','before':30,'after':32,'delta':2})
    reviews=[]
    targets={'chemical':['unit-ir'],'editability':[snapshots['final'][f+'_asset_ref'] for f in ('cdx','cdxml')]+[r['readback_asset_ref'] for r in readbacks],'visual':snapshots['final']['render_asset_refs'],'human_review':[snapshots['final'][f+'_asset_ref'] for f in ('cdx','cdxml')]+snapshots['final']['render_asset_refs']}
    for scope in targets:
        reviews.append({'id':'unit-review-'+scope,'scope':scope,'actor':{'id':'SYNTHETIC-reviewer-'+scope,'kind':'human'},'independent_of_author':True,'independent_of_corrector':True,'decision':'accepted','reviewed_at':'2026-01-01T00:01:00+00:00','target_asset_refs':targets[scope],'evidence_refs':['unit-review']})
    return {'version':'gold-correction-record/1.0','id':'SYNTHETIC-UNIT-RECORD','sample_id':'SYNTHETIC-UNIT-SAMPLE','record_kind':'synthetic_test','requested_tier':'silver','author':{'id':'SYNTHETIC-author','kind':'ai'},'corrector':{'id':'SYNTHETIC-corrector','kind':'human'},'step_ids':['unit-step-a','unit-step-b'],'assets':assets,'snapshots':snapshots,'readbacks':readbacks,'correspondences':correspondence,'diffs':diffs,'diff_coverage':{f:'complete' for f in ALL_FIELDS},'statuses':{s:{'status':'pass','review_refs':['unit-review-'+s]} for s in targets},'reviews':reviews,'timing':{'measurement':'session_timer','started_at':'2026-01-01T00:00:00+00:00','ended_at':'2026-01-01T00:00:20+00:00','wall_seconds':20,'manual_active_seconds':10,'automatic_seconds':1,'sessions':[{'actor_id':'SYNTHETIC-corrector','started_at':'2026-01-01T00:00:01+00:00','ended_at':'2026-01-01T00:00:15+00:00','active_seconds':10,'evidence_ref':'unit-timer'}]},'provenance':{'source_description':'SYNTHETIC UNIT TEST ONLY','source_revision':'unit-revision','created_at':'2026-01-01T00:00:00+00:00','software':'NONE; synthetic test','license_expression':'SYNTHETIC-TEST-NOT-A-LICENSE','rights_status':'approved','permissions':{'store':True,'annotate':True,'train':False,'redistribute':False},'evidence_refs':['unit-provenance']},'partition':{'policy_version':'gold-silver-holdout/1.0','split':'development','exposure':'exposed','benchmark_tags':[],'ancestors':[],'uses':{'tuning':False,'training':False,'evaluation':False,'redistribution':False}}}


class CorrectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='quality-synthetic-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.value = fixture(self.directory)

    def validate(self):
        return validate_record(self.value, self.directory)

    def reject(self, expected):
        with self.assertRaisesRegex(ValueError, expected):
            self.validate()

    def rebind_payload(self, reading):
        asset=next(a for a in self.value['assets'] if a['id']==reading['readback_asset_ref'])
        data=json.dumps(reading['payload'],sort_keys=True).encode()
        (self.directory/asset['path']).write_bytes(data)
        asset.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())

    def test_synthetic_record_never_counts_as_gold(self):
        result=self.validate()
        self.assertFalse(result['gold_eligible_by_record'])
        self.assertFalse(result['identity_authenticated'])
        self.assertFalse(result['actual_gold_collected'])
        self.assertEqual(result['ir_validation'],'schema_only')
        self.assertGreater(result['changed_diff_fields'],0)

    def test_eligibility_cannot_authenticate_manufactured_test_claims(self):
        # Explicitly exercise the boundary, not an actual collected gold sample.
        self.value.update(record_kind='observed_correction',requested_tier='gold')
        result=self.validate()
        self.assertTrue(result['gold_eligible_by_record'])
        self.assertFalse(result['identity_authenticated'])
        self.assertFalse(result['actual_gold_collected'])

    def test_declaring_gold_does_not_qualify_synthetic(self):
        self.value['requested_tier']='gold'
        self.reject('gold requirements missing')

    def test_gold_rejects_missing_human_review(self):
        self.value.update(record_kind='observed_correction',requested_tier='gold')
        self.value['statuses']['visual']={'status':'unverified','review_refs':[]}
        self.reject('gold requirements missing')

    def test_gold_rejects_automatic_correction(self):
        self.value.update(record_kind='automated_repair',requested_tier='gold')
        self.reject('gold requirements missing')

    def test_native_asset_bytes_are_verified(self):
        (self.directory/self.value['assets'][4]['path']).write_bytes(b'tampered')
        self.reject('hash|byte|size')

    def test_path_escape_is_rejected(self):
        self.value['assets'][0]['path']='../escape'
        self.reject('path|escape|outside')

    def test_duplicate_asset_identity_is_rejected(self):
        self.value['assets'].append(copy.deepcopy(self.value['assets'][0]))
        self.reject('duplicate identity')

    def test_wrong_readback_source_hash(self):
        self.value['readbacks'][0]['payload']['source_asset_sha256']='0'*64
        self.reject('source hash')

    def test_payload_must_match_hash_locked_asset(self):
        self.value['readbacks'][0]['payload']['objects'][0]['geometry']['position'][0]+=1
        self.reject('payload differs')

    def test_missing_curve_control_point(self):
        curve=next(o for o in self.value['readbacks'][0]['payload']['objects'] if o['kind']=='electron_flow')
        curve['geometry']['control_points'].pop()
        self.reject('schema')

    def test_extra_native_object_cannot_hide(self):
        r=self.value['readbacks'][0]
        extra=copy.deepcopy(r['payload']['objects'][0]);extra['id']='unit-extra';extra['semantic_ref']='unit-extra-occurrence'
        r['payload']['objects'].append(extra);self.rebind_payload(r)
        self.reject('inventory incomplete')

    def test_missing_diff_is_rejected(self):
        self.value['diffs'].pop()
        self.reject('diff inventory')

    def test_incorrect_delta_is_rejected(self):
        self.value['diffs'][-1]['delta']=123
        self.reject('incorrect numerical delta')

    def test_unrelated_field_change_cannot_escape_diff(self):
        self.value['diffs'][0]['after'][0]+=99
        self.reject('diff values disagree')

    def test_fake_not_applicable_is_rejected(self):
        self.value['diff_coverage']['step_spacing']='not_applicable'
        self.reject('incorrect diff coverage')

    def test_missing_spacing_pair_is_rejected(self):
        r=self.value['readbacks'][0];r['payload']['step_spacings']=[];self.rebind_payload(r)
        self.reject('step spacing inventory')

    def test_nonfinite_numbers_are_rejected(self):
        self.value['timing']['manual_active_seconds']=float('nan')
        self.reject('nonfinite')

    def test_boolean_is_not_a_time_number(self):
        self.value['timing']['manual_active_seconds']=True
        self.reject('schema')

    def test_active_time_must_equal_sessions(self):
        self.value['timing']['manual_active_seconds']=11
        self.reject('not supported by sessions')

    def test_overlap_cannot_double_count_active_time(self):
        self.value['timing']['sessions']*=2
        self.reject('overlapping')

    def test_unmeasured_time_is_not_zero(self):
        self.value['timing']['measurement']='unmeasured'
        self.reject('unmeasured timing')

    def test_actor_cannot_claim_own_independent_review(self):
        self.value['reviews'][0]['actor']['id']=self.value['corrector']['id']
        self.reject('independence contradicts')

    def test_scope_cannot_borrow_other_review(self):
        self.value['statuses']['chemical']['review_refs']=['unit-review-visual']
        self.reject('wrong scope')

    def test_pass_cannot_ignore_recorded_rejection(self):
        self.value['reviews'][0]['decision']='rejected'
        self.reject('uncontested')

    def test_gold_requires_storage_and_annotation_rights(self):
        self.value.update(record_kind='observed_correction',requested_tier='gold')
        self.value['provenance']['permissions']['annotate']=False
        self.reject('storage/annotation rights')

    def replace_ir(self, value):
        asset=next(a for a in self.value['assets'] if a['id']=='unit-ir')
        data=json.dumps(value).encode()
        (self.directory/asset['path']).write_bytes(data)
        asset.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())

    def test_empty_ir_cannot_be_a_mechanism(self):
        self.replace_ir({})
        self.reject('schema:')

    def test_ir_version_is_checked(self):
        asset=next(a for a in self.value['assets'] if a['id']=='unit-ir')
        ir=json.loads((self.directory/asset['path']).read_bytes())
        ir['version']='not-corpus-mechanism-ir'
        self.replace_ir(ir)
        self.reject('schema:')

    def test_ir_required_section_is_checked(self):
        asset=next(a for a in self.value['assets'] if a['id']=='unit-ir')
        ir=json.loads((self.directory/asset['path']).read_bytes())
        del ir['electron_flows']
        self.replace_ir(ir)
        self.reject('schema:')

    def test_zero_sessions_cannot_manufacture_epsilon_active_time(self):
        self.value.update(record_kind='observed_correction', requested_tier='gold')
        self.value['timing']['manual_active_seconds']=1e-8
        for session in self.value['timing']['sessions']:
            session['active_seconds']=0
        self.reject('manual time not supported by sessions')

    def test_decimal_session_total_does_not_use_geometry_tolerance(self):
        self.value['timing']['sessions'][0]['active_seconds']=0.1
        second=copy.deepcopy(self.value['timing']['sessions'][0])
        second.update(started_at='2026-01-01T00:00:16+00:00',ended_at='2026-01-01T00:00:17+00:00',active_seconds=0.2)
        self.value['timing']['sessions'].append(second)
        self.value['timing']['manual_active_seconds']=0.3
        self.assertEqual(self.validate()['status'],'pass')
        self.value['timing']['manual_active_seconds']=0.300000001
        self.reject('manual time not supported by sessions')

    def test_zero_activity_can_be_retained_but_not_gold(self):
        self.value['timing']['manual_active_seconds']=0
        self.value['timing']['sessions'][0]['active_seconds']=0
        result=self.validate()
        self.assertFalse(result['gold_eligible_by_record'])
        self.assertIn('positive measured human active time required',result['eligibility_blockers'])

    def test_review_cannot_precede_native_reopens(self):
        for reading in self.value['readbacks']:
            reading['reopened_at']='2030-01-01T00:00:00+00:00'
        self.reject('review predates necessary')

    def test_visual_review_cannot_precede_final_render(self):
        final_id=self.value['snapshots']['final']['render_asset_refs'][0]
        next(a for a in self.value['assets'] if a['id']==final_id)['render_provenance']['rendered_at']='2030-01-01T00:00:00+00:00'
        self.reject('review predates necessary')

    def test_event_comparison_uses_offsets(self):
        for review in self.value['reviews']:
            review['reviewed_at']='2026-01-01T01:01:00+01:00'
        self.assertEqual(self.validate()['status'],'pass')

    def test_shared_first_final_render_is_rejected(self):
        first_id=self.value['snapshots']['first']['render_asset_refs'][0]
        final=self.value['snapshots']['final']
        next(a for a in self.value['assets'] if a['id']==first_id)['derived_from'].append(final['cdx_asset_ref'])
        final['render_asset_refs']=[first_id]
        self.reject('render must have exactly|render belongs to different|render.*reused')

    def test_aliasing_render_path_is_rejected(self):
        first=next(a for a in self.value['assets'] if a['id']==self.value['snapshots']['first']['render_asset_refs'][0])
        final=next(a for a in self.value['assets'] if a['id']==self.value['snapshots']['final']['render_asset_refs'][0])
        final.update(path=first['path'],bytes=first['bytes'],sha256=first['sha256'])
        self.reject('render file reused')

    def test_copying_first_render_bytes_does_not_prove_final_render(self):
        self.value.update(record_kind='observed_correction',requested_tier='gold')
        first=next(a for a in self.value['assets'] if a['id']==self.value['snapshots']['first']['render_asset_refs'][0])
        final=next(a for a in self.value['assets'] if a['id']==self.value['snapshots']['final']['render_asset_refs'][0])
        (self.directory/final['path']).write_bytes((self.directory/first['path']).read_bytes())
        final.update(bytes=first['bytes'],sha256=first['sha256'])
        self.reject('distinct first/final render bytes')

    def duplicate_atom_graphic(self, auxiliary=False):
        for reading in self.value['readbacks']:
            original=next(o for o in reading['payload']['objects'] if o['kind']=='atom')
            extra=copy.deepcopy(original);extra['id']+='-copy'
            if auxiliary:
                extra.update(representation_role='auxiliary',primary_object_ref=original['id'])
            reading['payload']['objects'].append(extra)
            self.rebind_payload(reading)
        original=next(c for c in self.value['correspondences'] if c['kind']=='atom')
        extra=copy.deepcopy(original);extra['entity_id']+='-copy'
        for stage in ('first','final'):
            for fmt in ('cdx','cdxml'):
                extra[stage][fmt]+='-copy'
        if auxiliary:
            extra.update(representation_role='auxiliary',primary_entity_ref=original['entity_id'])
        self.value['correspondences'].append(extra)
        for d in list(self.value['diffs']):
            if d['entity_id']==original['entity_id']:
                extra=copy.deepcopy(d);extra['entity_id']+='-copy';self.value['diffs'].append(extra)

    def test_duplicate_primary_semantic_occurrence_is_rejected(self):
        self.duplicate_atom_graphic()
        self.reject('duplicate primary semantic occurrence')

    def test_explicit_auxiliary_graphic_preserves_single_primary(self):
        self.duplicate_atom_graphic(auxiliary=True)
        self.value.update(record_kind='observed_correction',requested_tier='gold')
        self.assertTrue(self.validate()['gold_eligible_by_record'])
        # Still synthetic claims, never authenticated native or human evidence.
        self.assertFalse(self.validate()['actual_gold_collected'])

    def test_auxiliary_graphic_cannot_point_to_different_kind(self):
        self.duplicate_atom_graphic(auxiliary=True)
        reading=self.value['readbacks'][0]
        next(o for o in reading['payload']['objects'] if o['id'].endswith('-copy'))['primary_object_ref']='cdx-charge'
        self.rebind_payload(reading)
        self.reject('auxiliary graphic has invalid primary')

    def test_named_m2_cannot_be_unseen_reserved(self):
        self.value['sample_id']='M2'
        self.value['partition'].update(benchmark_tags=['M2'],split='evaluation_reserved',exposure='unseen')
        self.reject('named benchmark must retain exposure')

    def test_named_m2_ancestor_cannot_be_unseen(self):
        self.value['partition'].update(split='evaluation_reserved',exposure='unseen')
        self.value['partition']['ancestors']=[{'sample_id':'M2','relation':'chemical_perturbation','benchmark_tags':['M2'],'split':'fixed_regression','exposure':'unseen'}]
        self.reject('named benchmark ancestor must retain exposure')

    def test_genuine_m2_perturbation_can_remain_unseen_evaluation(self):
        self.value['partition'].update(split='evaluation_reserved',exposure='unseen',benchmark_tags=['M2'])
        self.value['partition']['ancestors']=[{'sample_id':'M2','relation':'chemical_perturbation','benchmark_tags':['M2'],'split':'fixed_regression','exposure':'exposed_and_tuned'}]
        self.assertEqual(self.validate()['status'],'pass')

    def test_rotation_uses_shortest_signed_delta(self):
        for r in self.value['readbacks']:
            item=next(o for o in r['payload']['objects'] if o['kind']=='fragment')
            item['geometry']['rotation_deg']=350 if r['stage']=='first' else 10
            self.rebind_payload(r)
        d=next(d for d in self.value['diffs'] if d['field']=='fragment_rotation')
        d.update(before=350,after=10,delta=20)
        self.assertEqual(self.validate()['status'],'pass')
        d['delta']=-340
        self.reject('incorrect numerical delta')

    def test_absent_object_category_is_explicitly_not_applicable(self):
        for r in self.value['readbacks']:
            r['payload']['objects']=[o for o in r['payload']['objects'] if o['kind']!='charge']
            self.rebind_payload(r)
        self.value['correspondences']=[c for c in self.value['correspondences'] if c['kind']!='charge']
        self.value['diffs']=[d for d in self.value['diffs'] if d['field']!='charge_displacement']
        self.value['diff_coverage']['charge_displacement']='not_applicable'
        self.assertEqual(self.validate()['status'],'pass')

    def test_historical_m1_assignment_does_not_freeze_development(self):
        self.value['partition']['ancestors']=[{'sample_id':'M1','relation':'same_semantics','benchmark_tags':['M1'],'split':'fixed_regression','exposure':'exposed_and_tuned'}]
        self.assertEqual(self.validate()['status'],'pass')

    def test_rejection_cannot_be_hidden_by_status_reference_selection(self):
        rejection=copy.deepcopy(self.value['reviews'][0])
        rejection.update(id='unit-rejected-chemical',decision='rejected')
        self.value['reviews'].append(rejection)
        self.reject('rejection omitted')

    def test_m1_can_remain_exposed_development(self):
        self.value['partition']['benchmark_tags']=['M1']
        self.assertEqual(self.validate()['status'],'pass')

    def test_m1_cannot_claim_unseen(self):
        self.value['partition'].update(benchmark_tags=['M1'],exposure='unseen')
        self.reject('M1 must retain exposure')

    def test_named_m2_cannot_omit_protected_tag(self):
        self.value['sample_id']='M2'
        self.reject('named benchmark missing tag')

    def test_named_m2_ancestor_cannot_omit_protected_tag(self):
        self.value['partition']['ancestors']=[{'sample_id':'M2','relation':'same_semantics','benchmark_tags':[],'split':'development','exposure':'exposed'}]
        self.reject('named benchmark ancestor missing tag')

    def test_m2_descendant_cannot_be_promoted_to_development(self):
        self.value['partition']['ancestors']=[{'sample_id':'M2','relation':'chemical_perturbation','benchmark_tags':['M2'],'split':'fixed_regression','exposure':'exposed_and_tuned'}]
        self.reject('evaluation lineage assigned')

    def test_m2_cannot_tune_even_when_rights_allow(self):
        self.value['partition'].update(benchmark_tags=['M2'],split='fixed_regression')
        self.value['partition']['uses']['tuning']=True
        self.value['provenance']['permissions']['train']=True
        self.reject('evaluation lineage cannot tune/train')


if __name__=='__main__':
    unittest.main()
