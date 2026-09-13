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
    profile = read_json(ROOT/'runtime/native_semantic_profile.json')
    if freeze.get('profile') != profile['version'] or freeze.get('profile_sha256') != sources['runtime/native_semantic_profile.json']:
        raise ValueError('NATIVE_SEMANTIC_PROFILE_MISMATCH')
    return dict(sha256=digest(path), sources=sources, profile=profile)


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
    if (record.get('profile') != freeze['profile']['version']
            or evidence.get('source_freeze_sha256') != freeze['sha256']
            or evidence.get('qualification_status') != 'qualified_declared_scope'):
        raise ValueError('NATIVE_SEMANTIC_QUALIFICATION_SCOPE_MISMATCH')
    return str(freeze_path)
