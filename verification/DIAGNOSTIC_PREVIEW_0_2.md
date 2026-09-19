# Diagnostic preview portable verification

Date: 2026-09-19. Version: 0.2.0-preview.1. Scope: CD-LC-01 through CD-LC-04
source repairs and the native-disabled diagnostic package. The native operational
freeze and historical PARTIAL acceptance are unchanged.

## Focused source checks

Python 3.13.15 on Windows x64, with the isolated dependencies pinned in
requirements-lifecycle-win-py313.lock. Run only these explicitly scoped modules:

```powershell
python -B -m unittest discover -s tests -p test_lifecycle_controller.py -v
python -B -m unittest discover -s tests -p test_owned_lifecycle.py -v
python -B -m unittest discover -s tests -p test_diagnostic_server.py -v
python -B -m unittest discover -s tests -p test_diagnostic_install.py -v
```

| Module | Run | Passed | Skipped |
| --- | ---: | ---: | ---: |
| Lifecycle controller | 32 | 32 | 0 |
| Owned cleanup and frozen worker | 17 | 17 | 0 |
| Diagnostic MCP | 7 | 7 | 0 |
| Installer and Codex adapter | 24 | 23 | 1 |
| Total | 80 | 79 | 1 |

There were no failures or errors in the final integrated run (21.001 seconds).
An independent Governance execution reached the same results and retained SHA-256
snapshots before and after testing. The file-symlink test was skipped because the
current Windows account lacked privilege 1314. A temporary NTFS directory-junction
rejection was actually exercised and passed; this is separate from the skipped
file-symlink case. The plugin manifest validator and dependency consistency check
also passed. Private raw test outputs retain earlier failed attempts.

These are portable synthetic-boundary checks: they include actual producer calls,
PowerShell helper execution against synthetic objects, five real child-process
crash gaps, stdio subprocesses and synthetic installations/CLI adapters. They do
not start ChemDraw, load vendor interop or access protected samples. Source tests
must not be reported as native or fresh host-model acceptance.

## Exact package checks and delivery

The builder requires a clean committed source and reads an explicit allowlist
through git show. It checks the official runtime archive hash, retains its licence,
and produces build-info.json, a complete file manifest, a deterministic release ZIP,
SHA256SUMS.txt and a build receipt. The ordinary builder entry disables bytecode
before loading the packaged integrity verifier. Exact artifact, source and manifest
hashes are recorded separately after the source commit is frozen.

Release verification must additionally use the included runtime for self-check,
stdio initialize/list/call/error/EOF and complete manifest readback. Governance
reviews those exact files before publication or a real connection switch. Actual
local installation, registration, a fresh host tool call, benchmark model identity,
and delivery each require their own receipts; passing this document's source
checks does not establish them.

The package contains no native controller, bridge, scientific fixtures or vendor
binaries. Native cleanup timing, real owned-process exit, OS-event behavior,
scientific correctness, other-host qualification and the shared incident remain
unverified or frozen as recorded in LIFECYCLE_RECORD.md.
