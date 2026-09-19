"""Read-only status core for the native-disabled ChemDraw Companion preview."""
import json
from datetime import datetime, timezone
from pathlib import Path
import platform
import re

VERSION = '0.2.0-preview.1'
LIFECYCLE = {'class':'on_demand_local_companion','owner':'calling_host','persistent':False,'shutdown':'stdin_eof'}
PROPERTIES = {
    'result_version': {'const':'chemdraw-status/0.1'},
    'product': {'const':'ChemDraw Companion'},
    'package_version': {'const':VERSION},
    'source_commit': {'anyOf':[{'type':'string','pattern':'^[a-f0-9]{40}$'},{'type':'null'}]},
    'ok': {'type':'boolean'},
    'package_integrity': {'enum':['verified','unverified','mismatch']},
    'checked_files': {'type':'integer','minimum':0},
    'native_execution_enabled': {'const':False},
    'native_acceptance': {'const':'frozen'},
    'available_capabilities': {'const':['diagnostics']},
    'lifecycle': {'const':LIFECYCLE},
    'runtime_python': {'type':'string','minLength':1,'maxLength':64},
    'observed_at': {'type':'string','format':'date-time'},
    'message': {'type':'string','minLength':1,'maxLength':512},
}
STATUS_SCHEMA = {'$schema':'https://json-schema.org/draft/2020-12/schema',
                 '$id':'urn:chembridge:chemdraw:output:diagnostic-status:0.1',
                 'type':'object','additionalProperties':False,
                 'properties':PROPERTIES,'required':list(PROPERTIES)}


def validate_status(value):
    """Exact small production contract; independent JSON Schema validation lives in tests."""
    if not isinstance(value, dict) or set(value) != set(PROPERTIES):
        raise ValueError('Status output fields do not match the diagnostic contract')
    for key in ('result_version','product','package_version','native_execution_enabled',
                'native_acceptance','available_capabilities','lifecycle'):
        expected=PROPERTIES[key]['const']
        if type(value[key]) is not type(expected) or json.dumps(value[key],sort_keys=True,allow_nan=False) != json.dumps(expected,sort_keys=True):
            raise ValueError('Invalid status field: '+key)
    if type(value['ok']) is not bool or type(value['checked_files']) is not int or value['checked_files'] < 0:
        raise ValueError('Invalid status disposition or file count')
    if value['source_commit'] is not None and (not isinstance(value['source_commit'],str) or not re.fullmatch('[a-f0-9]{40}',value['source_commit'])):
        raise ValueError('Invalid source revision')
    if value['package_integrity'] not in ('verified','unverified','mismatch'):
        raise ValueError('Invalid package integrity state')
    if value['ok'] != (value['package_integrity']=='verified'):
        raise ValueError('Integrity disposition contradicts ok')
    if value['ok'] and value['source_commit'] is None:
        raise ValueError('Verified package requires its exact source commit')
    for key,limit in (('runtime_python',64),('message',512)):
        if not isinstance(value[key],str) or not 1 <= len(value[key]) <= limit:
            raise ValueError('Invalid bounded status text')
    observed=datetime.fromisoformat(value['observed_at'].replace('Z','+00:00'))
    if observed.tzinfo is None:
        raise ValueError('Status timestamp needs a timezone')
    return value


def status(package_root):
    root=Path(package_root).resolve()
    commit=None; checked=0; integrity='unverified'
    message='Diagnostic preview only. Native execution and native acceptance remain frozen.'
    if (root/'package-manifest.json').is_file():
        try:
            from package_integrity import verify_package
            result=verify_package(root)
            checked=result['checked_files']
            info=json.loads((root/'build-info.json').read_text(encoding='utf-8'))
            candidate=info.get('source_commit')
            valid_info=(info.get('product')=='chemdraw-companion' and info.get('version')==VERSION
                        and isinstance(candidate,str) and re.fullmatch('[a-f0-9]{40}',candidate))
            commit=candidate if valid_info else None
            integrity='verified' if result['ok'] and valid_info else 'mismatch'
            if integrity=='mismatch':
                message='Package verification failed. Reinstall an intact reviewed package; native execution remains frozen.'
        except (OSError,ValueError,KeyError,TypeError,ImportError):
            integrity='mismatch'
            message='Package metadata or files could not be verified; native execution remains frozen.'
    return validate_status({
        'result_version':'chemdraw-status/0.1','product':'ChemDraw Companion','package_version':VERSION,
        'source_commit':commit,'ok':integrity=='verified','package_integrity':integrity,'checked_files':checked,
        'native_execution_enabled':False,'native_acceptance':'frozen','available_capabilities':['diagnostics'],
        'lifecycle':dict(LIFECYCLE),'runtime_python':platform.python_version(),
        'observed_at':datetime.now(timezone.utc).isoformat(),'message':message,
    })
