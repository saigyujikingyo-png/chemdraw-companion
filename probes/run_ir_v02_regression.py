"""Run an explicit synthetic runtime subset with protected-payload read guards.

This does not discover/run corpus suites or native integration automatically.
The source-only inventory records exclusions without importing their modules.
"""
from __future__ import annotations
import argparse
import ast
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SAFE_MODULES = {
    'test_arrow_ports', 'test_generic_mask_scene', 'test_scene_equivalence',
    'test_cdxml_atom_identity', 'test_ir_v02_runtime', 'test_native_observation', 'test_native_semantics',
}
EXCLUDED_GENERAL = {
    'test_independent_chemistry_and_different_flow_count',
    'test_schema_rejects_oracle_or_layout_coordinates',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; previous evidence is immutable.')
    sys.path[:0] = [str(ROOT), str(ROOT / 'tests'), str(ROOT / 'probes')]
    selected, excluded, unscheduled = [], [], []
    for path in sorted((ROOT / 'tests').glob('test_*.py')):
        source = ast.parse(path.read_text(encoding='utf-8'))
        for cls in [n for n in source.body if isinstance(n, ast.ClassDef)]:
            for method in [n for n in cls.body if isinstance(n, ast.FunctionDef)
                           and n.name.startswith('test_')]:
                name = '.'.join((path.stem, cls.name, method.name))
                if path.stem in ('test_native_provenance', 'test_readback_guards'):
                    excluded.append(dict(test=name, reason='Setup reads excluded evaluation chemistry, including style-only access.'))
                elif path.stem == 'test_general_ir' and method.name in EXCLUDED_GENERAL:
                    excluded.append(dict(test=name, reason='Reads the excluded request before replacing chemistry or checking its schema.'))
                elif path.stem in SAFE_MODULES or path.stem == 'test_general_ir':
                    selected.append(name)
                else:
                    unscheduled.append(dict(test=name, reason='Outside this explicitly audited runtime integration subset.'))

    reads, denied = set(), []
    protected = re.compile(r'(^|[/_.-])(m2|holdout)(?=$|[/_.-])', re.IGNORECASE)
    payload_extensions = {'.json', '.cdxml', '.cdx', '.png', '.jpg', '.jpeg', '.pdf', '.zip'}

    def audit(event, arguments):
        if event != 'open' or not isinstance(arguments[0], (str, bytes)):
            return
        name = str(arguments[0]).replace('\\', '/')
        mode = arguments[1]
        if isinstance(mode, str) and not ('r' in mode or '+' in mode):
            return
        # Source references and metadata names are not chemical payload reads.
        # Protected inputs may not even be opened by a failing negative control.
        if Path(name).suffix.lower() in payload_extensions and protected.search(name):
            denied.append(name)
            raise PermissionError('Excluded evaluation payload access blocked by the phase regression guard.')
        reads.add(name)

    sys.addaudithook(audit)
    suite = unittest.defaultTestLoader.loadTestsFromNames(selected)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    record = {
        'version': 'ir-v02-runtime-regression/0.1',
        'scope': 'Explicit synthetic runtime subset; no corpus or blind native run.',
        'inventory_test_count': len(selected) + len(excluded) + len(unscheduled),
        'selected_count': len(selected), 'tests_run': result.testsRun,
        'passed_count': result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
        'failed_count': len(result.failures), 'error_count': len(result.errors),
        'skipped': [(test.id(), reason) for test, reason in result.skipped],
        'excluded_count': len(excluded), 'excluded': excluded,
        'unscheduled_count': len(unscheduled), 'unscheduled': unscheduled,
        'selected': selected, 'blocked_payload_reads': denied,
        'read_paths': sorted(reads),
        'limitations': 'Selection is source-audited; the path guard is additional defense, not proof against renamed or embedded derivatives.',
        'status': 'pass' if result.wasSuccessful() and not denied and result.testsRun == len(selected) else 'failed',
        'quality_acceptance': 'not_implied',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2)
    print(json.dumps({k: record[k] for k in ('status', 'inventory_test_count', 'tests_run',
                                           'passed_count', 'excluded_count', 'unscheduled_count')}))
    return 0 if record['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
