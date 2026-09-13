"""Run an immutable candidate through existing generic Composer/native stages.

This custodian-side entry does not run a model, read a hidden target, or certify
blindness/target similarity. It preserves unsupported and failed first outputs.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--powershell', type=Path, required=True)
    parser.add_argument('--inference-receipt', type=Path)
    parser.add_argument('--head-metrics', type=Path)
    args = parser.parse_args()
    source = args.request.resolve()
    if sha(source) != args.sha256.lower():
        parser.error('Request SHA-256 mismatch; no stage was run.')
    if not args.powershell.is_file():
        parser.error('PowerShell executable does not exist.')
    run = args.out.resolve()
    run.mkdir(parents=True, exist_ok=False)
    request = run / 'request.original.json'
    request.write_bytes(source.read_bytes())
    if sha(request) != args.sha256.lower():
        raise ValueError('Request changed while copying; no stage was run.')
    receipt = {
        'version': 'paired-candidate-run/0.1', 'started_utc': utc(),
        'status': 'running', 'request_sha256': sha(request),
        'generator_executed_here': False, 'blind_inference_verified_here': False,
        'hidden_target_accessed_by_this_runner': False,
        'input_semantic_validation': 'not_run', 'stages': [],
        'evaluation': {layer: 'pending_independent_evaluator' for layer in
                       ('chemical_semantics', 'editable_objects', 'geometry', 'native_visual')},
        'manual_active_correction_seconds': None,
    }
    if args.inference_receipt:
        evidence = args.inference_receipt.resolve()
        (run / 'inference-receipt.original.json').write_bytes(evidence.read_bytes())
        receipt['inference_receipt_sha256'] = sha(run / 'inference-receipt.original.json')
    if args.head_metrics:
        calibration = run / 'independent-head-metrics.original.json'
        calibration.write_bytes(args.head_metrics.read_bytes())
        receipt['head_metrics_sha256'] = sha(calibration)
        receipt['head_metrics_independence'] = 'must be established by the custodian; not inferred from a filename'
    record = run / 'candidate-run.json'

    def save():
        record.write_text(json.dumps(receipt, indent=2), encoding='utf-8')

    def stage(name, command, timeout):
        item = {'stage': name, 'started_utc': utc(), 'command': command,
                'status': 'running', 'timeout_seconds': timeout}
        receipt['stages'].append(item)
        save()
        start = time.monotonic()
        try:
            with (run / (name + '.stdout.txt')).open('wb') as stdout, \
                    (run / (name + '.stderr.txt')).open('wb') as stderr:
                process = subprocess.run(command, cwd=ROOT, stdout=stdout,
                                         stderr=stderr, timeout=timeout, check=False)
            item.update(status='completed' if process.returncode == 0 else 'failed',
                        exit_code=process.returncode)
            worker = run / (name + '-worker.json')
            if worker.exists():
                worker_record = json.loads(worker.read_text(encoding='utf-8'))
                item['worker_status'] = worker_record['status']
                if worker_record['status'] == 'outcome_unknown':
                    item['status'] = 'outcome_unknown'
            return item['status'] == 'completed'
        except subprocess.TimeoutExpired:
            item.update(status='outcome_unknown', exit_code=None, retryable=False)
            return False
        finally:
            item.update(elapsed_seconds=time.monotonic() - start, ended_utc=utc())
            save()

    py = sys.executable
    pwsh = str(args.powershell.resolve())
    seed, fragments, composed, native = [run / name for name in
                                         ('seed', 'native-fragments', 'composed', 'native')]

    def native_command(name, script, seconds, options):
        return [py, str(ROOT / 'probes/run_with_deadline.py'), '--seconds', str(seconds),
                '--receipt', str(run / (name + '-worker.json')), pwsh,
                '-NoProfile', '-NonInteractive', '-File', str(ROOT / 'probes' / script), *options]

    save()
    completed = stage('seed', [py, str(ROOT / 'probes/run_composer.py'), 'seed',
                              '--request', str(request), '--out', str(seed)], 30)
    seed_result = seed / 'stage-result.json'
    if seed_result.is_file():
        checked = json.loads(seed_result.read_text(encoding='utf-8'))
        receipt['input_semantic_validation'] = checked['input_semantic_validation']
        receipt['seed_result'] = checked
    elif not completed:
        receipt['input_semantic_validation'] = 'unknown_after_seed_failure'
    if completed:
        receipt['input_semantic_validation'] = 'pass'
        completed = stage('fragments', native_command('fragments', 'native-ir-fragments.ps1', 180,
                          ['-InputDirectory', str(seed), '-OutputDirectory', str(fragments)]), 190)
    if completed:
        command = [py, str(ROOT / 'probes/run_composer.py'), 'compose', '--request', str(request),
                   '--seed', str(seed), '--native', str(fragments), '--out', str(composed)]
        if args.head_metrics:
            command += ['--head-metrics', str(calibration)]
        completed = stage('compose', command, 60)
    if completed:
        cdxml = composed / 'mechanism.cdxml'
        completed = stage('native', native_command('native', 'native-pair.ps1', 60,
                          ['-InputFile', str(cdxml), '-ExpectedSha256', sha(cdxml),
                           '-OutputDirectory', str(native), '-Role', 'candidate', '-Dpi', '600']), 70)
    if completed:
        events = [json.loads(line) for line in (native / 'events.jsonl').read_text(
            encoding='utf-8-sig').splitlines()]
        reopened = [event['detail'] for event in events if event['stage'] == 'disk_reopened']
        imports = [event['detail'] for event in events if event['stage'] == 'native_environment']
        completed = ({row['format'] for row in reopened} == {'cdx', 'cdxml'} and
                     len({row['pid'] for row in imports}) == 3 and
                     all(row['fresh_process'] and row['distinct_document_identity'] for row in reopened) and
                     events[-1]['stage'] == 'complete')
        receipt['native_disk_reopen'] = 'pass' if completed else 'failed'
        receipt['native_scene_exact_equality'] = {
            row['format']: row['exact_scene_equal_to_import'] for row in reopened}
    receipt['source_request_unchanged'] = sha(source) == args.sha256.lower()
    if not receipt['source_request_unchanged']:
        completed = False
    receipt['status'] = 'candidate_artifacts_ready' if completed else (
        'outcome_unknown' if any(row['status'] == 'outcome_unknown' for row in receipt['stages']) else 'failed')
    receipt['completed_utc'] = utc()
    receipt['artifacts'] = [{'file': str(path.relative_to(run)).replace('\\', '/'),
                            'bytes': path.stat().st_size, 'sha256': sha(path)}
                           for path in sorted(run.rglob('*')) if path.is_file() and path != record]
    save()
    print(json.dumps({'status': receipt['status'], 'receipt': str(record),
                      'quality_acceptance': 'not_implied'}))
    return 0 if completed else 1


if __name__ == '__main__':
    raise SystemExit(main())
