# Diagnostic MCP compatibility verification

Source checkpoint: 2026-09-19, before publishing 0.2.0-preview.2.
Baseline: c6cfa3ec398d4659a3e61a6e48460e689f84e530 / preview.1.

## Actual failure and regression

Codex 0.155.0-alpha.9.2 sent this request through its own MCP client:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"_meta":{"progressToken":0}}}
```

Preview.1 returned -32602. A transparent stdio trace retained both messages; the
same request is checked into tests/fixtures/diagnostic_codex_0_155_0_alpha_9_2.json.
The new regression failed against the unchanged baseline. After the server fix,
the official client discovered exactly chemdraw_companion_status from preview.2,
with toolsError=null. This is an official-client protocol result, not a model call.

The probe uses documented per-process configuration and verifies its effective
command plus enabled-server list before discovery. Other MCP servers and plugins
are disabled only in that subprocess. It creates no user task, calls no model and
writes no installed connection or application cache. Preliminary probe setup
failures were retained; only a captured actual protocol exchange supports the
compatibility verdict. The earlier preview.1 native/host limits remain historical.

## Focused checks

```powershell
python -B -m unittest discover -s tests -p test_diagnostic_server.py -v
python -B -m unittest discover -s tests -p test_diagnostic_install.py -v
python -B scripts/verify_diagnostic_codex.py --codex <official-codex.exe> --python <python.exe> --server <diagnostic-server.py> --output <new-evidence-directory>
```

- Diagnostic protocol: 12/12 passed, including the actual Codex request, metadata
  on list/call, progress token zero, ignored extension metadata, strict empty tool
  arguments, malformed metadata, unissued cursors and malformed output rejection.
- Installer/connection: 24 run, 23 passed, one file-symlink test skipped because
  Windows privilege 1314 was unavailable. The real NTFS junction rejection passed.
- Total affected tests: 36 run, 35 passed, one skip, no failures/errors.
- Plugin manifest validation and whitespace checks passed.
- Lifecycle controller/owned-worker source is unchanged from preview.1. Its earlier
  49 passing source checks are historical and were not rerun for this protocol fix.

The complete catalog has no continuation cursor and never emits nextCursor. Any
supplied cursor, including null, an empty string or an unissued token, is rejected.
Metadata must be an object; progressToken must be a string or finite number, never
boolean/null. Other metadata is ignored. It cannot become diagnostic arguments,
be reflected into results or lift the native freeze.

## Remaining exact-package and host gates

Release receipts separately record the clean commit, repeated deterministic build,
source/runtime/file hashes, actual bundled-runtime protocol checks, official-client
discovery, public download, real upgrade and registered-command readback. The old
artifact and installed version remain available. Fresh desktop-model invocation,
OS-event behavior and native/scientific acceptance are separate gates. This source
checkpoint alone does not establish those outcomes.
