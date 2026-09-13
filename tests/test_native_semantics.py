"""Independent synthetic guard checks. No native calls or reserved payloads."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from runtime.native_semantics import (simple_label, native_graph, observe_atom,
    selected_carbon_h, component_scope, compare_document, observe_document,
    observation_branch,apply_branch_qualification,derive_branch_coverage,require_reopen_consistency)
from runtime.native_source_binding import (verify_process_binding, verify_observer_binding, REQUIRED,
    load_qualification,CONTROL_MATRIX)


def model(xml):
    root=ET.fromstring(xml)
    nodes,adjacency,bonds=native_graph(root)
    rows={int(n.get('id')):dict(native_id=int(n.get('id')),atom_map=m,
        atomic_number=int(n.get('Element','6')),formal_charge=int(n.get('Charge','0')),
        isotope=int(n.get('Isotope','0')),radical_native_value=0,node_type_native_value=1,
        abnormal_valence_allowed=False,implicit_h_allowed=True) for m,n in nodes.items()}
    return nodes,adjacency,rows,bonds


def carbon_formula(row,formula,used):
    row.update(selected_count=1,selected_atom_count=1,selected_bond_count=0,
               selected_atom_ids=[row['native_id']],selected_formula_html=formula,used_valences=used)


class NativeSemanticChecks(unittest.TestCase):
    def test_simple_labels_have_explicit_scope_and_reverse_orientation(self):
        for label,h,z,q in [('CH3',3,6,0),('H2N',2,7,0),('HO',1,8,0),('O',0,8,0),('NH4+',4,7,1),('Cl-',0,17,-1),('D',0,1,0)]:
            n=ET.fromstring('<n><t><s>'+label+'</s></t></n>')
            p=simple_label(n)
            self.assertEqual((p['non_node_attached_h'],p['atomic_number'],p['charge']),(h,z,q))
        for label in ['Me','Et','CH2OH','C2H5','[CH3]','CO2H','CH0','H2']:
            self.assertEqual(simple_label(ET.fromstring('<n><t><s>'+label+'</s></t></n>'))['status'],'unsupported')

    def test_unmodified_preregistered_conflict_is_refused_before_native_normalization(self):
        # This exact public preregistered seed is deliberately not a native qualification positive.
        p=Path(__file__).resolve().parents[1]/'verification/2026-09-13-p0b-semantic-readback/inputs/state-003.cdxml'
        n,a,r,_=model(p.read_text(encoding='utf-8'))
        m=next(iter(n));observed=observe_atom(n[m],n,a,r,'a'*64,warnings=0)
        self.assertEqual(observed['serialized_label_h']['value'],3)
        self.assertEqual(observed['label_non_node_h']['value'],4)
        self.assertIn('attached_h_sources_conflict',observed['conflicts'])
        self.assertIsNone(observed['non_node_attached_h']['value'])

    def test_missing_field_does_not_fill_from_expected_or_unused_valences(self):
        n,a,r,b=model('<CDXML><n id="8" AtomNumber="43"/><n id="9" AtomNumber="61" Element="8" NumHydrogens="1"/><b id="22" B="8" E="9"/></CDXML>')
        r[8].update(unused_valences=3,implicit_h_native_value=0)
        observed=dict(atoms={m:observe_atom(node,n,a,r,'a'*64,warnings=0) for m,node in n.items()},bonds=b)
        before=deepcopy(observed)
        expected={43:dict(atomic_number=6,implicit_h=3),61:dict(atomic_number=8,implicit_h=1)}
        self.assertEqual(compare_document(observed,expected,b)['status'],'unverified')
        expected[43]['implicit_h']=0
        self.assertEqual(compare_document(observed,expected,b)['status'],'unverified')
        self.assertEqual(observed,before)

    def test_expected_h_changes_only_comparison(self):
        n,a,r,b=model('<CDXML><n id="8" AtomNumber="43" NumHydrogens="3"/><n id="9" AtomNumber="61" Element="8" NumHydrogens="1"/><b id="22" B="8" E="9"/></CDXML>')
        carbon_formula(r[8],'CH<sub>3</sub><sup>&bull;</sup>',1)
        observed=dict(atoms={m:observe_atom(node,n,a,r,'a'*64,warnings=0) for m,node in n.items()},bonds=b)
        before=deepcopy(observed)
        expected={43:dict(atomic_number=6,implicit_h=3),61:dict(atomic_number=8,implicit_h=1)}
        self.assertEqual(compare_document(observed,expected,b)['status'],'match')
        expected[43]['implicit_h']=2
        self.assertEqual(compare_document(observed,expected,b)['status'],'mismatch')
        self.assertEqual(observed,before)

    def test_explicit_h_and_d_are_not_added_to_non_node_h(self):
        n,a,r,b=model('<CDXML><n id="8" AtomNumber="43" NumHydrogens="0"/><n id="9" AtomNumber="61" Element="1" NumHydrogens="0"/><n id="10" AtomNumber="79" Element="1" Isotope="2" NumHydrogens="0"><t><s>D</s></t></n><n id="11" AtomNumber="97" Element="8" NumHydrogens="0"/><b id="22" B="8" E="9"/><b id="23" B="8" E="10"/><b id="24" B="8" E="11" Order="2"/></CDXML>')
        carbon_formula(r[8],'C<sup>4&bull;</sup>',4)
        observed=observe_atom(n[43],n,a,r,'a'*64,warnings=0)
        self.assertEqual(observed['non_node_attached_h']['value'],0)
        self.assertEqual([x['isotope'] for x in observed['explicit_h_neighbor_nodes']['value']],[0,2])
        a[61][79]=a[79][61]=1
        self.assertEqual(component_scope(43,n,a,r)[1],'nonterminal_or_unqualified_hydrogen_node')

    def test_unexercised_label_only_and_carbon_field_only_branches_are_not_admitted(self):
        n,a,r,_=model('<CDXML><n id="8" AtomNumber="43" NumHydrogens="3"/><n id="9" AtomNumber="61" Element="8"><t><s>OH</s></t></n><b id="22" B="8" E="9"/></CDXML>')
        carbon=observe_atom(n[43],n,a,r,'a'*64,warnings=0)
        oxygen=observe_atom(n[61],n,a,r,'a'*64,warnings=0)
        self.assertEqual(carbon['serialized_label_h']['value'],3)
        self.assertEqual(oxygen['label_non_node_h']['value'],1)
        self.assertIsNone(carbon['non_node_attached_h']['value'])
        self.assertIsNone(oxygen['non_node_attached_h']['value'])

    def test_selected_formula_requires_exact_selection_and_cut_bonds(self):
        n=ET.fromstring('<n id="8" AtomNumber="43"/>')
        row=dict(implicit_h_allowed=True,selected_count=1,selected_atom_count=1,selected_bond_count=0,
                 selected_atom_ids=[8],used_valences=3,selected_formula_html='CH<sup>3&bull;</sup>')
        self.assertEqual(selected_carbon_h(n,row,3),(1,None))
        for key,value in [('selected_count',2),('selected_atom_ids',[9]),('selected_bond_count',1),('used_valences',2),('used_valences',True),('selected_formula_html','CH<sup>2&bull;</sup>'),('selected_formula_html','CH3'),('selected_formula_html','C2H6')]:
            changed={**row,key:value}
            self.assertIsNone(selected_carbon_h(n,changed,3)[0])

    def test_warnings_or_native_field_conflicts_do_not_resolve_h(self):
        n,a,r,b=model('<CDXML><n id="8" AtomNumber="43" NumHydrogens="3"><t><s>NH3</s></t></n><n id="9" AtomNumber="61" NumHydrogens="3"/><b id="22" B="8" E="9"/></CDXML>')
        self.assertIn('label_atomic_number_conflict',observe_atom(n[43],n,a,r,'a'*64,warnings=0)['conflicts'])
        row=observe_atom(n[61],n,a,r,'a'*64,warnings=1)
        self.assertEqual(row['non_node_attached_h']['reason'],'native_chemical_warnings')

    def test_query_radical_abnormal_and_aromatic_bonds_are_refused(self):
        xml='<CDXML><n id="8" AtomNumber="43" NumHydrogens="3"/><n id="9" AtomNumber="61" NumHydrogens="3"/><b id="22" B="8" E="9"/></CDXML>'
        for attr,value in [('NodeType','Nickname'),('Radical','Doublet'),('ImplicitHydrogens','no'),('AbnormalValence','yes')]:
            n,a,r,_=model(xml);n[43].set(attr,value)
            self.assertIsNone(observe_atom(n[43],n,a,r,'a'*64,warnings=0)['non_node_attached_h']['value'])
        for key,value in [('abnormal_valence_allowed',True),('radical_native_value',2)]:
            n,a,r,_=model(xml);r[8][key]=value
            self.assertIsNone(component_scope(43,n,a,r)[0])
        n,a,r,_=model(xml);a[43][61]=a[61][43]=1.5
        self.assertEqual(component_scope(43,n,a,r)[1],'aromatic_or_query_bond')

    def test_real_cdxml_query_fields_reject_an_otherwise_matching_api_baseline(self):
        n,a,r,b=model('<CDXML><n id="8" AtomNumber="43" NumHydrogens="3"/><n id="9" AtomNumber="61" NumHydrogens="3"/><b id="22" B="8" E="9"/></CDXML>')
        for row in r.values():carbon_formula(row,'CH<sub>3</sub><sup>&bull;</sup>',1)
        expected={m:dict(atomic_number=6,implicit_h=3) for m in n}
        def observation():return dict(atoms={m:observe_atom(node,n,a,r,'a'*64,warnings=0) for m,node in n.items()},bonds=b)
        baseline=observation()
        self.assertEqual(compare_document(baseline,expected,b)['status'],'match')
        self.assertTrue(all(x['non_node_attached_h']['source_class']=='native_api_observation' for x in baseline['atoms'].values()))
        for field,value in [('FreeSites','1'),('RingBondCount','NoRingBonds'),('SubstituentsUpTo','3'),('SubstituentsExactly','1'),('UnsaturatedBonds','MustBeAbsent'),('ImplicitHydrogens','no')]:
            n[43].set(field,value)
            actual=observation()
            self.assertEqual(compare_document(actual,expected,b)['status'],'unverified')
            self.assertTrue(all(x['non_node_attached_h']['reason']=='query_radical_abnormal_or_non_element' for x in actual['atoms'].values()))
            n[43].attrib.pop(field)
            self.assertEqual(compare_document(observation(),expected,b)['status'],'match')

    def branch_fixture(self):
        n,a,r,b=model('<CDXML><n id="8" AtomNumber="43"/><n id="9" AtomNumber="61" Element="8" NumHydrogens="1"/><b id="22" B="8" E="9"/></CDXML>')
        carbon_formula(r[8],'CH<sub>3</sub><sup>&bull;</sup>',1)
        return dict(atoms={m:observe_atom(node,n,a,r,'a'*64,warnings=0) for m,node in n.items()},bonds=b)

    def test_actual_field_source_scope_branches_limit_admission(self):
        observed=self.branch_fixture();before=deepcopy(observed)
        allowed=[observation_branch(observed['atoms'][43])]
        admitted=apply_branch_qualification(observed,allowed)
        self.assertEqual(admitted['atoms'][43]['non_node_attached_h']['value'],3)
        self.assertEqual(admitted['atoms'][61]['non_node_attached_h']['reason'],'native_branch_not_qualified')
        for field,changed in [('scope','different_scope'),('source_field','n@NumHydrogens'),('h',2),('serialized_h_present',True)]:
            wrong={**allowed[0],field:changed}
            self.assertIsNone(apply_branch_qualification(observed,[wrong])['atoms'][43]['non_node_attached_h']['value'])
        self.assertEqual(observed,before)

    def test_branch_coverage_requires_both_native_phases(self):
        observed=self.branch_fixture()
        record=dict(file='synthetic.cdxml',result='qualification_match',phases={p:dict(observations=deepcopy(observed)) for p in ('cleanup','reopen')})
        coverage=derive_branch_coverage([record])
        self.assertEqual(len(coverage),2)
        self.assertTrue(all(x['cleanup_atoms']==x['reopen_atoms']==1 for x in coverage))
        record['phases']['reopen']['observations']['atoms'][43]['non_node_attached_h']['scope']='uncovered_scope'
        with self.assertRaisesRegex(ValueError,'LACKS_CLEANUP_AND_REOPEN'):derive_branch_coverage([record])

    def test_cleanup_reopen_comparison_ignores_native_id_changes_but_rejects_h_change(self):
        cleanup=self.branch_fixture();reopen=deepcopy(cleanup)
        reopen['atoms'][43]['native_id']=1008
        require_reopen_consistency(cleanup,reopen)
        reopen['atoms'][43]['non_node_attached_h']['value']=2
        with self.assertRaisesRegex(ValueError,'CLEANUP_REOPEN_SEMANTICS_CHANGED'):
            require_reopen_consistency(cleanup,reopen)

    def test_two_key_control_summary_cannot_qualify_production(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            (folder/'freeze.json').write_text('{}',encoding='utf-8')
            evidence=dict(source_freeze_sha256='a'*64,qualification_status='qualified_covered_branches')
            (folder/'controls.json').write_text(json.dumps(evidence),encoding='utf-8')
            h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
            qualified=dict(version='native-semantic-qualification/1.0',status='qualified',profile='test-profile',
                source_freeze=dict(file='freeze.json',sha256=h(folder/'freeze.json')),
                control_receipt=dict(file='controls.json',sha256=h(folder/'controls.json')),evidence_directory='.')
            (folder/'qualification.json').write_text(json.dumps(qualified),encoding='utf-8')
            frozen=dict(profile=dict(version='test-profile'),sha256='a'*64,inputs={CONTROL_MATRIX:'b'*64},
                        matrix=dict(controls=[dict(file='x.cdxml',expected_atoms=[{}])]))
            with patch('runtime.native_source_binding.verify_source_freeze',return_value=frozen):
                with self.assertRaisesRegex(ValueError,'CONTROL_RECEIPT_INCOMPLETE'):
                    load_qualification(folder/'qualification.json')

    def test_unqualified_cyclic_unsaturation_and_multiple_cycles_are_refused(self):
        # Independently constructed cyclopentene, then a chord forming two cycles.
        root=ET.Element('CDXML')
        for i in range(5):ET.SubElement(root,'n',id=str(10+i),AtomNumber=str(70+11*i),NumHydrogens='1')
        for i in range(5):ET.SubElement(root,'b',id=str(30+i),B=str(10+i),E=str(10+(i+1)%5),Order='2' if i==0 else '1')
        n,a,r,_=model(ET.tostring(root,encoding='unicode'))
        self.assertEqual(component_scope(70,n,a,r)[1],'cyclic_unsaturation_unqualified')
        a[70][92]=a[92][70]=1
        self.assertEqual(component_scope(70,n,a,r)[1],'multiple_cycle_scope_unqualified')

    def test_legacy_observer_cannot_receive_new_qualification(self):
        with self.assertRaisesRegex(ValueError,'OBSERVER_UNQUALIFIED'):
            observe_document(Path('not-read.cdxml'),{'version':'native-atom-readback/0.4'},source_freeze='not-read.json')

    def test_actual_sidecar_verifier_rejects_label_only_snapshot_mutation(self):
        from runtime.adapters.cdxml_atom_identity import verify_atom_readback
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'atom.cdxml'
            path.write_text('<CDXML><n id="8" AtomNumber="43" NumHydrogens="3"><t><s>CH3</s></t></n></CDXML>',encoding='utf-8')
            after=path.with_name('atom-selection-after.cdxml');after.write_bytes(path.read_bytes())
            h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
            sidecar=dict(version='native-atom-readback/0.4',source_cdxml_sha256=h(path),
                chemical_export_mime='chemical/x-smiles',selection_chemical_export_unchanged=True,
                chemical_export_before_sha256='a'*64,chemical_export_after_sha256='a'*64,
                selection_graph_unchanged=True,selection_after_cdxml=dict(file=after.name,sha256=h(after)),
                atoms=[dict(native_id=8,atom_map=43,atomic_number=6,formal_charge=0,isotope=0)])
            verify_atom_readback(path,sidecar)
            after.write_text(path.read_text().replace('CH3','CH2'),encoding='utf-8')
            sidecar['selection_after_cdxml']['sha256']=h(after)
            with self.assertRaises(ValueError):verify_atom_readback(path,sidecar)

    def test_hash_syntax_and_matching_build_are_not_observer_qualification(self):
        profile=dict(observer_version='native-atom-readback/0.5',application_build='26',interop_version='22',executable_sha256='c'*64,interop_sha256='d'*64)
        freeze=dict(sha256='e'*64,sources={name:'a'*64 for name in REQUIRED},profile=profile)
        job='11111111-1111-1111-1111-111111111111'
        process=dict(job_id=job,pid=12,hwnd_bound_pid=12,hwnd=1,os_start_utc='2026-09-13T12:00:00Z',initial_documents=0,fresh_process=True,preexisting_pids=[10])
        env={k:v for k,v in profile.items() if k!='observer_version'}
        env.update(executor_sha256='a'*64,atom_observer_sha256='a'*64,common_sha256='a'*64,bridge_sha256='a'*64)
        sidecar=dict(version=profile['observer_version'],source_freeze_sha256='e'*64,environment=env,process=process,job_id=job,phase='cleanup')
        verify_observer_binding(sidecar,freeze)
        sidecar['environment']['atom_observer_sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'OBSERVER_SOURCE_MISMATCH'):verify_observer_binding(sidecar,freeze)
        process['pid']=10;process['hwnd_bound_pid']=10
        with self.assertRaises(ValueError):verify_process_binding(process,job)


if __name__=='__main__':unittest.main()
