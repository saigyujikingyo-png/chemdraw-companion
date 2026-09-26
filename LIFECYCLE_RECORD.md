# Runtime lifecycle record

Version: 0.2 diagnostic preview. Shared rule: 2026-09-19.1.
Current implementation baseline: diagnostic-mcp-compat 6949b139899ac44fe5e5200b76060b2535a5e145.
Historical native-p0 source baseline: 5a01ffc1230a8c06acb063a2ab8409879aed4fe5.
Historical operational freeze: b9363abfce19481d33e8d6409cb3d8d7dd477310.

## Scope and ownership

The [architecture convergence decision at df617b70d351fd8bfdedf0fc190dbcd8b3bb43be](https://github.com/saigyujikingyo-png/chemdraw-companion/blob/df617b70d351fd8bfdedf0fc190dbcd8b3bb43be/docs/ARCHITECTURE_CONVERGENCE.md)
is the current ownership entrypoint. One existing local Product Max owns product
architecture, implementation, acceptance and bounded delegation. The earlier
architecture/native branch-owner split is historical; Ultra is consultation-only
and the former remote owner retires after verified takeover. Actual takeover and
archive states are recorded in private receipts, not inferred from this document.
Earlier branches and partial acceptance records are retained; the Product Max
assumes custody of preserved source-side static evidence and its outstanding
transfer/reconciliation work without claiming local receipt or authorizing deletion.
Missing originals are not reconstructed from current tests. Governance accepted a
bounded source-only exception for CD-LC-01 through CD-LC-04. Native execution,
protected samples, geometry/chemistry qualification and incident closure remain frozen.

Future remote Max tasks are temporary bounded executors under the same owner.
The standing authorization, permitted research purposes and exclusions are defined
in the pinned decision. It requires exact source/input and exposure boundaries,
outputs/acceptance, budget/stop conditions, isolated directories, normally one
unfinished task per experiment, creation reconciliation and no further delegation.
Archive only after acceptance. Verify the actual device, supported project/task
creation route and actual Max model/effort before use; observed remote read/message
support is not proof of task creation. This documentation update starts no task,
training, model download, installation, native operation or runtime migration.

The next narrow task is a separately recorded actual Agent call to the existing
native-disabled diagnostic status interface, checking its output contract and
installed-source provenance. It is planned, not executed by this takeover; native
requalification and any later semantic/geometry inheritance keep their own gates.

The installed preview is an **on_demand_local_companion**: the calling host starts
a stdio diagnostic frontend, and EOF ends it. It has no native owner, durable jobs,
tunnel, network access, account credentials, startup registration or restart loop.
Multiple diagnostic frontends may coexist. A plugin PowerShell launch shim, when
used, synchronously owns one Python child; the direct Codex MCP adapter launches
that Python child without the shim. Frontend creation is not native readiness.
Boot/logon does not start this preview. Logoff/shutdown ends it without accepted
scientific work. Sleep/resume may leave the existing host pipe alive; a fresh
status call recomputes package hashes. Network availability is irrelevant.

## Repaired source path (portable verification only)

The native edit controller requires explicit `agent-edit-result/0.2-draft.2` opt-in.
Its default and legacy entry points refuse native dispatch. There is no environment
or CLI switch to lift the freeze. Tests inject a private process boundary into the
actual producer; this is not a native integration result. The worker independently
refuses before loading vendor interop. Re-enabling a native adapter is a separate
reviewed source change and native acceptance gate.

The canonical state root owns one controller claim and one unresolved native
session. Path resolution normalizes aliases before claiming. Intent and assigned
request/operation/session/generation IDs precede copy, spawn intent or enqueue.
The fingerprint binds the canonical root and normalized request. Same request and
same input observes the same attempt; changed input is refused. Uncertain attempts,
legacy session directories and stale controller claims are preserved and block
new startup. The source does not automatically reclaim an abruptly abandoned
claim or replay an operation. Such a claim requires an explicit owner inspection;
no automated kill or lock-delete recovery is provided in this preview.

Worker PID/start/executable identity and document-bound observations determine
current readiness. Process death or PID reuse invalidates bindings, while previously
validated known effects remain historical evidence. Closing begins an unavailable
`ending` state before any later request can enqueue. Timeout means the frontend
stopped waiting; it does not mean cancellation, worker termination or safe replay.
Late replies are retained alongside prior failure receipts and quarantined. The
same accepted attempt may reconcile a valid terminal closure without dispatch.

Cleanup uses the retained application and exact PID/start/executable/document
scope. An application created before Open failure has its own ownership record.
Document Close returned, application Quit returned and observed process exit are
separate fields. PID reuse or incomplete ownership remains unknown. Saved-document
detach requires explicit end_session/keep_open and exact saved-revision proof.
A closed.json filename and a terminal index filename are never exit proof.

## Result contracts

`contracts/output/edit-result.schema.json` and common.schema.json preserve the
architecture draft.1 definitions unchanged. `edit-result-lifecycle.schema.json`
is the explicit draft.2 producer contract; it adds generation, worker state,
dispatch stage and quarantine. The only unknown-effect case permitting a null
operation ID is `registry_unreadable`, where both trusted identity records are
unreadable; no replacement ID is invented. Known IDs are recovered from immutable
intent whenever possible. Legacy native_write semantics are not redefined.

Malformed JSON, unknown actions and invalid IDs have no accepted operation. They
use the separate `edit-preflight-error/0.1` schema, with dispatch=not_started.
They are not edit-result successes or fabricated sessions. The diagnostic MCP
has its own `chemdraw-status/0.1` output schema, structuredContent and an equivalent
serialized text block. Protocol/argument failures use JSON-RPC error envelopes.

## Installation and rollback

The self-contained Windows x64 preview installs into an owned version directory;
its complete file manifest, source commit and upstream runtime hash are recorded.
Installation verifies before copying, after copying and through a non-native
self-check. Existing versions and pointer receipts remain available. File rollback
and host connection rollback are separate verified steps. The connector uses the
supported Codex CLI and refuses unrelated existing entries. It preserves the
separate ChemAIst `chemdraw-agent` identity and all vendor software/user files.

## Evidence boundaries

Focused controller tests cover one-effect malformed replies, concurrency, actual
child-process crash gaps, corrupt state, late replies, identity reuse and closure.
Portable PowerShell tests exercise the actual cleanup helper and worker entry with
synthetic boundaries and a vendor-initialization sentinel. These tests do not prove
actual COM timing, native cleanup, user-session non-interference, scientific quality,
installed OS-event behavior, host/model calls, or successful delivery to another
host. Those gates remain separately unverified. Exact dated build/test/source
receipts are produced before publication or connection switching. The historical
PARTIAL status and the shared incident remain open.
