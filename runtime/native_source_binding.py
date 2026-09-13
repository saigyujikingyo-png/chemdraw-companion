"""Exact local implementation/build binding for the new semantic profile.

The caller controls the trusted freeze and qualification receipt. These checks
are integrity checks, not authentication against a party replacing all files.
"""
import hashlib
import json
from pathlib import Path
import re
from runtime.native_observation import verify_frozen_sources

ROOT = Path(__file__).resolve().parents[1]
CONTROL_MATRIX = 'verification/2026-09-13-p0b-semantic-readback/inputs/control-matrix.json'
REQUIRED = (
    'probes/native-semantic-fragments.ps1', 'probes/native-atom-observation.ps1',
    'probes/native-common.ps1', 'probes/NativeChemDraw.cs',
    'runtime/native_source_binding.py', 'runtime/native_observation.py',
    'runtime/native_semantics.py', 'runtime/native_semantic_profile.json',
    'runtime/native_provenance.py', 'runtime/adapters/cdxml_atom_identity.py',
    'runtime/adapters/chemdraw_cdxml.py', 'probes/run_composer.py',
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def verify_source_freeze(path):
    freeze = read_json(path)
    if freeze.get('version') != 'native-semantic-source-freeze/1.0':
        raise ValueError('NATIVE_SEMANTIC_SOURCE_FREEZE_REQUIRED')
    sources = verify_frozen_sources(ROOT, freeze['sources'], required_files=REQUIRED)
    inputs = verify_frozen_sources(ROOT, freeze['inputs'], required_files=(CONTROL_MATRIX,))
    profile = read_json(ROOT/'runtime/native_semantic_profile.json')
    if freeze.get('profile') != profile['version'] or freeze.get('profile_sha256') != sources['runtime/native_semantic_profile.json']:
        raise ValueError('NATIVE_SEMANTIC_PROFILE_MISMATCH')
    return dict(sha256=digest(path), sources=sources, profile=profile, inputs=inputs,
                matrix=read_json(ROOT/CONTROL_MATRIX))


def verify_process_binding(value, job_id):
    if (not re.fullmatch(r'[0-9a-f-]{36}', str(job_id)) or value.get('job_id') != job_id
            or not isinstance(value.get('pid'), int) or value['pid'] <= 0
            or value.get('pid') != value.get('hwnd_bound_pid')
            or not isinstance(value.get('hwnd'), int) or value['hwnd'] == 0
            or value.get('initial_documents') != 0 or value.get('fresh_process') is not True
            or value['pid'] in value.get('preexisting_pids', [])
            or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z', str(value.get('os_start_utc')))):
        raise ValueError('NATIVE_SEMANTIC_PROCESS_BINDING_FAILED')


def verify_observer_binding(sidecar, freeze):
    if sidecar.get('version') != freeze['profile']['observer_version']:
        raise ValueError('NATIVE_SEMANTIC_OBSERVER_UNQUALIFIED')
    if sidecar.get('source_freeze_sha256') != freeze['sha256']:
        raise ValueError('NATIVE_SEMANTIC_SOURCE_FREEZE_MISMATCH')
    environment = sidecar['environment']
    for key in ('application_build', 'interop_version', 'executable_sha256', 'interop_sha256'):
        if environment.get(key) != freeze['profile'][key]:
            raise ValueError('NATIVE_SEMANTIC_BUILD_MISMATCH: '+key)
    for key, name in [('executor_sha256', REQUIRED[0]), ('atom_observer_sha256', REQUIRED[1]),
                      ('common_sha256', REQUIRED[2]), ('bridge_sha256', REQUIRED[3])]:
        if environment.get(key) != freeze['sources'][name]:
            raise ValueError('NATIVE_SEMANTIC_OBSERVER_SOURCE_MISMATCH: '+name)
    verify_process_binding(sidecar['process'], sidecar['job_id'])
    if sidecar.get('phase') not in ('cleanup', 'fresh_process_reopen'):
        raise ValueError('NATIVE_SEMANTIC_PHASE_UNQUALIFIED')


def load_qualification(path):
    """Only production admission needs a separate passed control receipt."""
    path = Path(path)
    record = read_json(path)
    if record.get('version') != 'native-semantic-qualification/1.0' or record.get('status') != 'qualified':
        raise ValueError('NATIVE_SEMANTIC_QUALIFICATION_REQUIRED')
    def bound_file(row):
        p = (path.parent/row['file']).resolve()
        if not p.is_relative_to(path.parent.resolve()) or digest(p) != row['sha256']:
            raise ValueError('NATIVE_SEMANTIC_QUALIFICATION_EVIDENCE_MISMATCH')
        return p
    freeze_path = bound_file(record['source_freeze'])
    freeze = verify_source_freeze(freeze_path)
    evidence = read_json(bound_file(record['control_receipt']))
    if record.get('profile') != freeze['profile']['version']:
        raise ValueError('NATIVE_SEMANTIC_QUALIFICATION_SCOPE_MISMATCH')
    validate_control_receipt_header(evidence, freeze)
    evidence_root=(path.parent/record['evidence_directory']).resolve()
    if not evidence_root.is_relative_to(path.parent.resolve()) or not evidence_root.is_dir():
        raise ValueError('NATIVE_SEMANTIC_QUALIFICATION_EVIDENCE_MISSING')
    branches=verify_control_evidence(evidence,evidence_root,freeze,freeze_path)
    return dict(source_freeze=str(freeze_path),admitted_branches=branches)


def validate_control_receipt_header(evidence, freeze):
    controls=freeze['matrix']['controls']
    if (evidence.get('version')!='native-semantic-control-receipt/1.1'
            or evidence.get('profile')!=freeze['profile']['version']
            or evidence.get('source_freeze_sha256')!=freeze['sha256']
            or evidence.get('matrix_sha256')!=freeze['inputs'][CONTROL_MATRIX]
            or evidence.get('qualification_status')!='qualified_covered_branches'
            or evidence.get('control_count')!=len(controls)
            or evidence.get('atom_count')!=sum(len(c['expected_atoms']) for c in controls)
            or evidence.get('distinct_native_process_count')!=2*len(controls)
            or evidence.get('all_expected_mutations_preserved_observations') is not True
            or evidence.get('source_bytes_rechecked') is not True
            or not isinstance(evidence.get('branch_coverage'),list) or not evidence['branch_coverage']
            or not isinstance(evidence.get('evidence_files'),list) or not evidence['evidence_files']
            or not isinstance(evidence.get('controls'),list) or len(evidence['controls'])!=len(controls)):
        raise ValueError('NATIVE_SEMANTIC_CONTROL_RECEIPT_INCOMPLETE')
    expected={c['file']:(c['control'],c['purpose'],c['seed_sha256']) for c in controls}
    actual={c['file']:(c['control'],c['purpose'],c['exact_preregistration_sha256']) for c in evidence['controls']}
    if len(actual)!=len(evidence['controls']) or actual!=expected:
        raise ValueError('NATIVE_SEMANTIC_CONTROL_MATRIX_MISMATCH')


def verify_control_evidence(evidence, folder, freeze, freeze_path):
    """Recheck the existing complete control receipt and real hash-bound files.

    No native calls occur. A truncated summary, missing source artifact, changed
    native observer or unsupported branch cannot act as qualification evidence.
    """
    from collections import Counter
    from runtime.native_semantics import (observe_document,compare_document,control_expectation,
        derive_branch_coverage,require_reopen_consistency)
    controls=freeze['matrix']['controls']
    native_name,analysis_name=evidence['native_folder'],evidence['analysis_folder']
    if any(not isinstance(n,str) or Path(n).name!=n or n in ('','.','..') for n in (native_name,analysis_name)):
        raise ValueError('NATIVE_SEMANTIC_EVIDENCE_PATH_INVALID')
    native=folder/native_name
    required={native_name+'/native-geometry-receipt.json'}
    for c in controls:
        stem=Path(c['file']).stem
        required.add(native_name+'/'+stem+'-before.cdxml')
        required.add(analysis_name+'/'+stem+'.semantic.json')
        for prefix in (native_name+'/',native_name+'/clean/'):
            required.update(prefix+name for name in (c['file'],stem+'.atoms.json',stem+'-selection-after.cdxml'))
    rows=evidence['evidence_files']
    if len(rows)!=len(required) or {r['file'] for r in rows}!=required:
        raise ValueError('NATIVE_SEMANTIC_CONTROL_EVIDENCE_COVERAGE_MISMATCH')
    verify_frozen_sources(folder,rows,required_files=required)
    native_receipt=read_json(native/'native-geometry-receipt.json')
    if (digest(native/'native-geometry-receipt.json')!=evidence['native_receipt_sha256']
            or native_receipt.get('version')!='native-geometry-receipt/0.2'
            or native_receipt.get('status')!='complete' or native_receipt.get('source_bytes_rechecked') is not True
            or native_receipt.get('source_freeze_sha256')!=freeze['sha256']
            or native_receipt.get('manifest_sha256')!=freeze['inputs'][str(Path(CONTROL_MATRIX).with_name('geometry-manifest.json')).replace('\\','/')]
            or native_receipt.get('seed_provenance_sha256')!=freeze['inputs'][str(Path(CONTROL_MATRIX).with_name('seed-provenance.json')).replace('\\','/')]
            or native_receipt.get('operation')!='ChemDraw.Objects.Clean(true)'):
        raise ValueError('NATIVE_SEMANTIC_CONTROL_EXECUTION_MISMATCH')
    by_file={a['file']:a for a in native_receipt['artifacts']}
    if len(by_file)!=len(controls) or len(by_file)!=len(native_receipt['artifacts']) or set(by_file)!={c['file'] for c in controls}:
        raise ValueError('NATIVE_SEMANTIC_CONTROL_EXECUTION_COVERAGE_MISMATCH')
    verified=[];processes=set();counts=Counter()
    canonical=lambda value:json.dumps(json.loads(json.dumps(value)),sort_keys=True,separators=(',',':'))
    for control in controls:
        name=control['file'];artifact=by_file[name]
        stored=read_json(folder/analysis_name/(Path(name).stem+'.semantic.json'))
        if (stored.get('control')!=control['control'] or stored.get('file')!=name or stored.get('purpose')!=control['purpose']
                or stored.get('exact_preregistration_sha256')!=control['seed_sha256']
                or artifact['input_sha256']!=control['seed_sha256'] or artifact.get('cleanup_completed') is not True
                or artifact.get('different_process_reopen') is not True or artifact.get('distinct_document_identity') is not True
                or artifact.get('cleanup_file')!='clean/'+name
                or artifact.get('before_sha256')!=digest(native/(Path(name).stem+'-before.cdxml'))
                or artifact.get('output_sha256')!=digest(native/name)
                or artifact.get('cleanup_sha256')!=digest(native/'clean'/name)
                or artifact['cleanup_process']['pid']==artifact['reopen_process']['pid']):
            raise ValueError('NATIVE_SEMANTIC_CONTROL_SOURCE_MISMATCH')
        expected=control_expectation(control)
        for phase,base,binding_key,sidecar_key in [('cleanup',native/'clean','cleanup_process','cleanup_atom_readback'),
                                                  ('reopen',native,'reopen_process','atom_readback')]:
            binding=artifact[binding_key]
            verify_process_binding(binding,native_receipt['run_id'])
            processes.add((binding['pid'],binding['os_start_utc']))
            sidecar_path=base/(Path(name).stem+'.atoms.json');sidecar=read_json(sidecar_path)
            if (artifact[sidecar_key]['file']!=sidecar_path.name or artifact[sidecar_key]['sha256']!=digest(sidecar_path)
                    or sidecar['process']!=binding or sidecar['environment']!=native_receipt['environment']
                    or sidecar['job_id']!=native_receipt['run_id']
                    or sidecar['phase']!=('cleanup' if phase=='cleanup' else 'fresh_process_reopen')):
                raise ValueError('NATIVE_SEMANTIC_CONTROL_OBSERVER_MISMATCH')
            observed=observe_document(base/name,sidecar,source_freeze=freeze_path,qualification_control=True)
            comparison=compare_document(observed,expected,control['expected_bonds'])
            value=stored['phases'][phase]
            if (canonical(observed)!=canonical(value['observations']) or canonical(comparison)!=canonical(value['comparison'])
                    or value.get('warnings')!=sidecar['chemical_warnings']
                    or sidecar['chemical_warnings']!=artifact['warnings' if phase=='cleanup' else 'reopen_warnings']
                    or value.get('expected_mutation_preserves_observations') is not True):
                raise ValueError('NATIVE_SEMANTIC_CONTROL_READBACK_MISMATCH')
        require_reopen_consistency(stored['phases']['cleanup']['observations'],stored['phases']['reopen']['observations'])
        positive=control['purpose']=='qualification_candidate' or control['control'] in ('ammonium','chloride')
        if positive:
            if any(p['comparison']['status']!='match' or p['warnings']!=0 or p['production_adapter']['status']!='match' for p in stored['phases'].values()):
                raise ValueError('NATIVE_SEMANTIC_POSITIVE_CONTROL_NOT_MATCHED')
            outcome='qualification_match'
        elif control['purpose']=='unsupported_negative':
            if any(p['comparison']['status']!='unverified' or p['production_adapter']['status']!='refused'
                   or any(a['non_node_attached_h']['value'] is not None for a in p['observations']['atoms'].values())
                   for p in stored['phases'].values()):
                raise ValueError('NATIVE_SEMANTIC_NEGATIVE_CONTROL_NOT_REFUSED')
            outcome='expected_scope_refusal'
        else:outcome='diagnostic_observation_only'
        if stored['result']!=outcome:raise ValueError('NATIVE_SEMANTIC_CONTROL_OUTCOME_MISMATCH')
        verified.append(stored);counts[outcome]+=1
    if len(processes)!=2*len(controls) or dict(counts)!=evidence['counts']:
        raise ValueError('NATIVE_SEMANTIC_CONTROL_COUNTS_MISMATCH')
    coverage=derive_branch_coverage(verified)
    if coverage!=evidence['branch_coverage'] or [r['branch'] for r in coverage]!=evidence['admitted_branches']:
        raise ValueError('NATIVE_SEMANTIC_BRANCH_COVERAGE_MISMATCH')
    return evidence['admitted_branches']
