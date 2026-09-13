"""Direct developer entry for versioned chemical IR / Composer boundaries."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime.chemical_ir import validate_request, validate_semantics, canonical_hash
from runtime.adapters.chemdraw_cdxml import seed_documents, read_geometry, materialize
from runtime.adapters.cdxml_atom_identity import NativeDepictionError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['validate', 'seed', 'compose'])
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed', type=Path)
    parser.add_argument('--native', type=Path)
    parser.add_argument('--head-metrics', type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Output directory exists; previous evidence is immutable.')
    if args.mode == 'compose' and (args.seed is None or args.native is None):
        parser.error('compose requires --seed and --native.')
    bundle, plan, validation, phase = None, None, None, 'input_validation'
    result = {'mode': args.mode, 'status': 'running', 'input_semantic_validation': 'not_run',
              'chemical_validity': 'not_established', 'native_quality': 'not_implied'}
    try:
        payload = json.loads(args.request.read_text(encoding='utf-8-sig'))
        if payload.get('mechanism', {}).get('ir_version') == 'mechanism-ir/0.2':
            from runtime.ir_v02_runtime import prepare_request, require_supported
            bundle = prepare_request(payload)
            mechanism, style, plan = bundle['mechanism'], bundle['style'], bundle['plan']
            validation = bundle['validation']
            result['input_semantic_validation'] = validation['checked_invariants']['status']
            result['contract_source_commit'] = bundle['contract_source_commit']
            result.update({k: plan[k] for k in ('ir_sha256', 'chemical_inventory_sha256', 'depiction_plan_sha256')})
            phase = 'depiction_capability'
            require_supported(bundle)
        else:
            mechanism, style = validate_request(payload)
            validation = validate_semantics(mechanism)
            result['input_semantic_validation'] = 'pass'
        if args.mode == 'seed':
            phase = 'native_seed'
            seed_documents(mechanism, style, args.out, depiction_plan=plan)
        elif args.mode == 'compose':
            from runtime.mechanism_composer import compose
            phase = 'native_geometry_readback'
            manifest = json.loads((args.seed / 'geometry-manifest.json').read_text(encoding='utf-8'))
            geometry = read_geometry(mechanism, manifest, args.native, input_folder=args.seed,
                                     style=style, depiction_plan=plan)
            head = json.loads(args.head_metrics.read_text(encoding='utf-8')) if args.head_metrics else None
            phase = 'layout'
            scene = compose(mechanism, style, geometry, head, depiction_plan=plan)
            materialize(scene, args.out)
            (args.out / 'native-geometry.json').write_text(json.dumps(geometry, indent=2), encoding='utf-8')
            if plan and scene['layout_diagnostics']['curve_clearance_failures']:
                raise NativeDepictionError('COMPOSER_GEOMETRY_FRONTIER', '$.flows',
                                           'First scene retained; routes fail the existing label-clearance guard.',
                                           {'flows': scene['layout_diagnostics']['curve_clearance_failures']})
        else:
            args.out.mkdir(parents=True, exist_ok=False)
        result['status'] = 'complete'
    except Exception as exc:
        if phase == 'input_validation':
            result['input_semantic_validation'] = 'failed'
        if hasattr(exc, 'to_dict'):
            diagnostic = exc.to_dict()
        elif hasattr(exc, 'as_dict'):
            diagnostic = exc.as_dict()
        else:
            diagnostic = {'code': 'COMPOSER_GEOMETRY_FRONTIER' if phase == 'layout' and isinstance(exc, ValueError) else 'RUNTIME_STAGE_FAILED',
                          'path': phase, 'message': str(exc), 'error_type': type(exc).__name__}
        result.update(status='geometry_frontier' if diagnostic['code'] == 'COMPOSER_GEOMETRY_FRONTIER' else 'failed',
                      failed_phase=phase, diagnostic=diagnostic)
    args.out.mkdir(parents=True, exist_ok=True)
    if bundle is not None:
        from runtime.ir_v02_runtime import write_contract_records
        write_contract_records(bundle, args.out)
    elif validation is not None:
        (args.out / 'semantic-receipt.json').write_text(json.dumps({
            'request_sha256': canonical_hash(payload), 'validation': validation,
            'automatic_anti_selection': 'unverified; input supplies complete semantic IR'}, indent=2), encoding='utf-8')
    with (args.out / 'stage-result.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({**result, 'output': str(args.out)}))
    return 0 if result['status'] == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
