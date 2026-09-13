"""Runtime preparation for the independent v0.2 chemical/depiction contract."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
from contracts.ir_v02 import (ATOMIC_NUMBERS, compile_electron_flows,
    lower_depiction, validate_mechanism, validate_depiction_capabilities)
from runtime.chemical_ir import linear_order
from runtime.adapters.cdxml_atom_identity import NativeDepictionError

CONTRACT_SOURCE_COMMIT = 'ea8f6b7b324f9f0fd0091b52052486374de4f4e7'
# This declares encoding/adapter support, not native quality for every element.
# Every actual atom occurrence still requires native identity readback.
CAPABILITIES = {
    'elements': list(ATOMIC_NUMBERS), 'isotopes': True, 'radicals': False,
    'roles': ['explicitly_drawn', 'condition_caption', 'reagent_caption',
              'catalyst_caption', 'counterion_hidden', 'spectator_hidden',
              'implicit', 'omitted_by_convention'],
    'flow_electron_counts': [2], 'virtual_lone_pair_ports': True,
    'orientations': ['auto'], 'typed_captions': True,
}


def prepare_request(payload):
    """Dispatch explicitly; never call the legacy HCNO semantic validator."""
    from jsonschema import Draft202012Validator
    schema_path = Path(__file__).resolve().parents[1] / 'contracts/composer-request.schema.json'
    envelope = json.loads(schema_path.read_text(encoding='utf-8'))
    envelope['properties']['mechanism'] = {'type': 'object'}
    envelope['properties']['contract_version'] = {'enum': ['composer-request/0.1', 'composer-request/0.2']}
    Draft202012Validator(envelope).validate(payload)
    mechanism, style = deepcopy(payload['mechanism']), deepcopy(payload['layout_policy'])
    validation = validate_mechanism(mechanism)
    compiled, plan = compile_electron_flows(mechanism), lower_depiction(mechanism)
    capability = validate_depiction_capabilities(mechanism, CAPABILITIES)
    extra = []
    try:
        linear_order(mechanism)
    except ValueError as exc:
        extra.append({'code': 'NATIVE_PATHWAY_TOPOLOGY_UNSUPPORTED', 'reason': str(exc)})
    for state in plan['states']:
        if not state['visible_atoms']:
            extra.append({'code': 'NATIVE_CAPTION_ONLY_STATE_UNSUPPORTED', 'state_ref': state['state_ref'],
                          'reason': 'An entirely caption-only panel has not been qualified.'})
        visible = {a['atom_ref'] for a in state['visible_atoms']}
        for relation in mechanism['stereo_constraints']:
            if state['state_ref'] in relation['states'] and not set(relation['central_bond'] + relation['substituent_atoms']) <= visible:
                extra.append({'code': 'NATIVE_HIDDEN_STEREO_UNSUPPORTED', 'state_ref': state['state_ref']})
    capability['diagnostics'].extend(extra)
    if extra:
        capability['status'] = 'unsupported_or_unknown'
    capability['declaration_scope'] = 'Adapter encoding only. Actual native identity, geometry and visual quality require separate readback/evaluation.'
    return {'mechanism': mechanism, 'style': style, 'validation': validation,
            'compiled': compiled, 'plan': plan, 'capability': capability,
            'contract_source_commit': CONTRACT_SOURCE_COMMIT}


def require_supported(bundle):
    if bundle['capability']['diagnostics']:
        raise NativeDepictionError('NATIVE_DEPICTION_UNSUPPORTED', '$.depiction_states',
                                   'The explicit depiction intent exceeds this native adapter profile.',
                                   {'diagnostics': bundle['capability']['diagnostics']})


def verify_runtime_plan(mechanism, style, plan):
    if mechanism.get('ir_version') != 'mechanism-ir/0.2':
        if plan is not None:
            raise NativeDepictionError('DEPICTION_VERSION_MISMATCH', '$', 'A v0.2 plan requires a v0.2 mechanism.')
        return
    if plan is None:
        raise NativeDepictionError('DEPICTION_PLAN_REQUIRED', '$', 'The v0.2 runtime requires an explicit lowered plan.')
    bundle = prepare_request({'contract_version': 'composer-request/0.2',
                              'mechanism': mechanism, 'layout_policy': style})
    if bundle['plan'] != plan:
        raise NativeDepictionError('DEPICTION_PLAN_MISMATCH', '$', 'Lowered plan differs from deterministic lowering of the supplied IR.')
    require_supported(bundle)


def write_contract_records(bundle, folder):
    for name, key in [('semantic-receipt.json', 'validation'),
                      ('compiled-electron-flows.json', 'compiled'),
                      ('lowered-depiction.json', 'plan'),
                      ('depiction-capability.json', 'capability')]:
        path = folder / name
        if path.exists():
            if json.loads(path.read_text(encoding='utf-8')) != bundle[key]:
                raise NativeDepictionError('CONTRACT_RECORD_CONFLICT', name,
                                           'Existing contract evidence differs from the current request.')
        else:
            with path.open('x', encoding='utf-8') as stream:
                json.dump(bundle[key], stream, indent=2)
