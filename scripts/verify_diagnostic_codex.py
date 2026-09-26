"""Exercise the official Codex MCP client without a model, user task or config write.

Uses per-process config overrides, verifies only the diagnostic server is enabled,
and retains its actual protocol messages. The proxy changes no request/response.
"""
import argparse
import hashlib
import json
from pathlib import Path
import queue
import os
import tomllib
import subprocess
import sys
import threading
import time
import uuid


def trace_server(python, server, directory):
    """Transparent byte forwarding to one owned diagnostic process."""
    directory = Path(directory)
    child = subprocess.Popen([python, '-I', '-B', server], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    lock = threading.Lock()
    wire = (directory / 'mcp-wire.jsonl').open('a', encoding='utf-8')
    def forward(source, target, direction):
        for line in iter(source.readline, b''):
            with lock:
                wire.write(json.dumps({'direction': direction, 'message': json.loads(line)}) + '\n')
                wire.flush()
            target.write(line)
            target.flush()
    outgoing = threading.Thread(target=forward, args=(child.stdout, sys.stdout.buffer, 'server_to_client'))
    outgoing.start()
    def errors():
        with (directory / 'diagnostic-stderr.txt').open('wb') as output:
            for line in iter(child.stderr.readline, b''):
                output.write(line)
    err_thread = threading.Thread(target=errors)
    err_thread.start()
    try:
        forward(sys.stdin.buffer, child.stdin, 'client_to_server')
    finally:
        child.stdin.close()
        child.wait(timeout=10)
        outgoing.join(timeout=2)
        err_thread.join(timeout=2)
        wire.close()
        (directory / 'diagnostic-exit.json').write_text(json.dumps({'pid': child.pid, 'exit_code': child.returncode, 'stdin_eof': True}) + '\n')
    return child.returncode


def verify(codex, python, server, output):
    codex, python, server, output = map(lambda p: Path(p).resolve(), (codex, python, server, output))
    if output.exists():
        raise ValueError('Use a new output directory; existing evidence is retained')
    if server.name != 'server.py' or not (server.parent / 'companion_status.py').is_file():
        raise ValueError('Only the diagnostic server is in scope')
    output.mkdir(parents=True)
    client_args = ['-I', '-B', str(Path(__file__).resolve()), '--trace-server',
                   str(python), str(server), str(output)]
    probe_name = 'chemdraw-compat-' + uuid.uuid4().hex[:12]
    override = 'mcp_servers={' + probe_name + '={command=' + json.dumps(str(python)) + ',args=' + json.dumps(client_args) + '}}'
    config_path = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'config.toml'
    configured = tomllib.loads(config_path.read_text(encoding='utf-8')).get('mcp_servers', {}) if config_path.exists() else {}
    disabled_rows = [json.dumps(name) + '={enabled=false}' for name in configured]
    if disabled_rows:
        override = override[:-1] + ',' + ','.join(disabled_rows) + '}'
    command = [str(codex), '-c', override, '--disable', 'plugins', '--disable', 'apps',
               '--disable', 'remote_plugin', '--disable', 'code_mode_host',
               '--disable', 'browser_use', '--disable', 'computer_use',
               'app-server', '--stdio']
    events = []
    proc = subprocess.Popen(command, cwd=output, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, encoding='utf-8')
    replies = queue.Queue()
    def read_stdout():
        for line in proc.stdout:
            try:
                replies.put(json.loads(line))
            except ValueError:
                replies.put({'invalid_stdout': line})
        replies.put({'client_eof': True})
    reader = threading.Thread(target=read_stdout, daemon=True)
    reader.start()
    def read_stderr():
        with (output / 'codex-stderr.txt').open('w', encoding='utf-8') as log:
            for line in proc.stderr:
                log.write(line)
    err_reader = threading.Thread(target=read_stderr, daemon=True)
    err_reader.start()
    def request(method, rid, params):
        proc.stdin.write(json.dumps({'method': method, 'id': rid, 'params': params}) + '\n')
        proc.stdin.flush()
        deadline = time.monotonic() + 30
        while True:
            item = replies.get(timeout=max(0.01, deadline - time.monotonic()))
            if item.get('client_eof'):
                raise ValueError('Official client exited before the requested response')
            if item.get('id') == rid:
                return item
            events.append(item)
    receipt = {'probe_name': probe_name, 'codex_command': command, 'native_execution': False, 'model_called': False,
               'created_user_task': False, 'persisted_configuration_change': False}
    try:
        receipt['initialize'] = request('initialize', 1, {'clientInfo': {'name': 'chemdraw_compat_verifier', 'version': '1.0'}, 'capabilities': {'experimentalApi': True}})
        if 'error' in receipt['initialize']:
            raise ValueError(receipt['initialize'])
        proc.stdin.write(json.dumps({'method': 'initialized', 'params': {}}) + '\n')
        proc.stdin.flush()
        config_reply = request('config/read', 2, {'includeLayers': False})
        config = config_reply.get('result', {}).get('config', {})
        servers = config.get('mcp_servers', {})
        enabled = sorted(name for name, value in servers.items() if value.get('enabled', True))
        features = config.get('features', {})
        receipt['isolation'] = {'enabled_mcp_names': enabled, 'plugins': features.get('plugins'), 'apps': features.get('apps')}
        if (enabled != [probe_name] or features.get('plugins') is not False or features.get('apps') is not False
                or servers[probe_name].get('command') != str(python) or servers[probe_name].get('args') != client_args):
            raise ValueError('Supported per-process configuration did not isolate the diagnostic server')
        receipt['discovery'] = request('mcpServerStatus/list', 3, {'detail': 'toolsAndAuthOnly', 'limit': 10})
    except Exception as exc:
        receipt['probe_error'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        proc.stdin.close()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            receipt['shutdown_timeout'] = True
            proc.terminate()
            proc.wait(timeout=5)
        reader.join(timeout=2)
        err_reader.join(timeout=2)
        receipt['codex_exit_code'] = proc.returncode
        receipt['notifications'] = events
        receipt['codex_version'] = subprocess.check_output([str(codex), '--version'], text=True).strip()
        receipt['codex_sha256'] = hashlib.sha256(codex.read_bytes()).hexdigest()
        receipt['server_sha256'] = hashlib.sha256(server.read_bytes()).hexdigest()
        wire_path = output / 'mcp-wire.jsonl'
        wire = [json.loads(line) for line in wire_path.read_text(encoding='utf-8').splitlines()] if wire_path.exists() else []
        listed = [row['message'] for row in wire if row['direction'] == 'client_to_server' and row['message'].get('method') == 'tools/list']
        receipt['actual_list_requests'] = listed
        data = receipt.get('discovery', {}).get('result', {}).get('data', [])
        catalog = next((item for item in data if item['name'] == probe_name), {})
        receipt['tools_error'] = catalog.get('toolsError')
        receipt['discovered_tools'] = sorted(catalog.get('tools', {}))
        receipt['passed'] = (not receipt.get('probe_error') and not receipt.get('shutdown_timeout')
                             and proc.returncode == 0 and bool(listed)
                             and catalog.get('toolsError') is None
                             and receipt['discovered_tools'] == ['chemdraw_companion_status'])
        receipt['expected_failure_reproduced'] = (bool(listed) and '-32602' in (catalog.get('toolsError') or ''))
        (output / 'official-client-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return receipt


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == '--trace-server':
        raise SystemExit(trace_server(*sys.argv[2:]))
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('codex', 'python', 'server', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--expect-discovery-failure', action='store_true')
    args = parser.parse_args()
    receipt = verify(args.codex, args.python, args.server, args.output)
    print(json.dumps({key: receipt[key] for key in ('passed', 'expected_failure_reproduced', 'codex_version', 'codex_exit_code', 'actual_list_requests', 'discovered_tools', 'tools_error')}, indent=2))
    accepted = receipt['expected_failure_reproduced'] if args.expect_discovery_failure else receipt['passed']
    raise SystemExit(0 if accepted else 1)
