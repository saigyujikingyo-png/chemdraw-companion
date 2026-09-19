# Diagnostic package and host slice design

Design checkpoint: 2026-09-19, before the exact source/package freeze. Release,
installation and host acceptance are recorded separately; this design is not
acceptance evidence.
Review scope: the previously accepted native-disabled minimal package/host slice.

## User-visible capability and contracts

One tool, `chemdraw_companion_status`, accepts exactly an empty object. It reads only
its own build metadata and complete file manifest, re-hashes its own package, and
returns `chemdraw-status/0.1`. Fields include exact source commit/package version,
integrity/checked-file count, native_execution_enabled=false, native_acceptance=frozen,
diagnostics-only capability, timestamp, runtime and on-demand/EOF lifecycle. Every
successful or package-mismatch tool result is producer-validated, supplied as
structuredContent, and mirrored as serialized JSON text. Package mismatch sets
ok=false and isError=true. It never repairs or starts native software.

`contracts/output/diagnostic-status.schema.json` is the published tool contract.
Malformed JSON, invalid request/arguments, missing initialization, unknown methods
and server output failures use bounded standard JSON-RPC errors (-32700, -32600,
-32602, -32002, -32601, -32603), covered separately by the JSON-RPC error schema.
The controller's draft.2 edit-result and its independent preflight-error schema
are separate from this single diagnostic MCP tool. No edit tool is advertised.

## Freeze enforcement

The package allowlist excludes all probes, native bridge code, vendor assemblies,
scientific fixtures, historic state and native dependencies. The diagnostic server
imports only the standard library and its package integrity verifier. It has no
native execution command or enabling flag. In source, both legacy/public controller
and PowerShell worker independently refuse native execution; testing uses private
portable boundaries. Neither schema conformance nor installation lifts the freeze.

## Exact package contents and dependencies

- Plugin manifest and stdio MCP configuration, diagnostic server/core/verifier.
- Install/connection scripts and double-click Windows launchers; installation guide.
- MIT licence, third-party notices, lifecycle record and diagnostic result schema.
- Generated source-to-package build-info and a complete per-file SHA-256 manifest.
- The official unmodified CPython 3.13.15 Windows x64 embeddable runtime, including
  its LICENSE.txt. Upstream ZIP SHA-256:
  d1f04d990aee1253d8569e8e5104e30fa9f5fa830899f14843448872d936a2cf.

No third-party Python package is bundled. jsonschema and its pinned dependencies
are used only in the isolated source-validation environment. The builder reads an
explicit file allowlist from one clean committed revision, records each source
hash, rejects unsafe upstream ZIP members and emits a deterministic ZIP plus
SHA256SUMS/build receipt. The final commit, artifact and manifest hashes remain
pending until the complete repair and installer tests are frozen.

## Installation, connection and rollback

The user extracts the ZIP and double-clicks Install.cmd. The bundled runtime
validates the package before copying, stages inside the product's local-app-data
root, verifies the copied payload, performs server.py --self-check without native
work and atomically publishes versions/<version>/chemdraw-companion. Existing
incompatible version files are preserved and refused. Reinstall of identical
bytes is idempotent. Prior current.json values and receipts remain recoverable;
no recursive deletion or data migration is part of installation.

Connection is a separate explicit Connect Codex.cmd action after review. It uses
supported `codex mcp get/add` commands for the exact `chemdraw-companion` entry,
launching its installed runtime/python.exe -I -B server.py. It reads back the
registration, refuses unrelated collisions, preserves owned prior connection
receipts for restoration, and does not manually edit Codex configuration/caches.
The optional plugin manifest is validated separately; no personal marketplace
entry or cache switch is made during this review. File rollback and connection
rollback have distinct receipts, and neither alone implies the host changed.

ChemAIst's `chemdraw-agent` identity, runtime, marketplace entry and data stay
untouched. Vendor ChemDraw and legacy edit-loop sessions are neither read nor
adopted by the installer. There is no startup task, tunnel, daemon or credentials.
Multiple diagnostic frontends are permitted and stop on stdin EOF; the optional
plugin PowerShell shim synchronously owns one Python child.

## Evidence required before claims

1. Focused source/controller/worker boundary tests; no reduction in CD-LC-01..04 scope.
2. Actual stdio initialize/list/call/error/EOF tests with independent schema validation.
3. Installer staging, idempotence, tamper/collision rejection and rollback tests.
4. Exact clean commit, source mapping, upstream hash, all package file hashes and
   actual bundled-runtime self-check/stdio verification.
5. Governance review before release or real installed connection switching.
6. Separate installed readback, fresh host discovery and actual host tool call;
   host/model acceptance remains pending until observed. Native/OS/science and
   historic transfer gaps remain open regardless of these results.
