# Native architecture, draft 0.1.0

Status: implementable design; every native capability below is unverified on an execution device. Shared rules: 2026-09-12.4. Contract major: 1. P0 is a bounded feasibility stage, not a full drawing product.

## Decisions and boundary

1. Use a separate `chemdraw-companion` repository, product identity and runtime namespace. Do not add chemistry business logic to Origin. Start with documentation/contracts plus the smallest three-case worker. Extract shared infrastructure only after measured duplication; carry provenance and licences for any reused code.
2. Prefer the official ChemDraw Add-in API for native insertion, readback and available exports. Pair it with one local broker and a supervised desktop worker for only the missing, verified native operations. No guessed COM ProgID, undocumented method or presumed ChemScript entitlement.
3. Generate initial molecular geometry with a verified native structure input/cleanup route. `addSMILES`/`addInChI` are first candidates. A signed, licensed ChemScript interface or supported desktop command is a secondary probe, not an installed capability by assumption. Whole-page arrangement and electron-flow anchors remain our deterministic, separately checked responsibility.
4. Never repair a rejected layout merely by swapping its renderer. Importing coordinate-bearing CDXML preserves that design. Native-generated fragments may be measured and arranged as a new scene, then imported; record this as native fragment generation plus companion page layout, not vendor-designed page layout.
5. No open-source primary-rendering fallback when `native_required=true` (always true for P0). An unavailable native route returns a blocked result. Independent libraries may check graphs, stereochemistry and atom mappings; they cannot certify electron-flow meaning or visual quality alone.

```mermaid
flowchart LR
  H[General agent host] --> M[Five MCP tools]
  M --> B[Local broker: identity, jobs, artifacts]
  B --> R[Recipe and scene compiler]
  R --> V[Semantic checks]
  V --> W[Serialized native worker]
  W <--> A[Official ChemDraw add-in]
  W <--> D[Supervised desktop adapter]
  A <--> C[Licensed ChemDraw]
  D <--> C
  C --> Q[Readback, reopen and figure checks]
  Q --> F[Immutable artifacts and provenance]
  F --> H
```

The cloud adapter is an authenticated transport to the same personal execution broker; it is not another renderer. Reuse a verified existing account connection when authorized, but give this product its own scopes, IDs, queues and artifact namespace. Local operation must work without cloud service or university storage. No second paid model is embedded in the execution layer.

## Thin native adapter

Implement an internal capability-based interface, separate from public MCP. Operations: `probe`, `bindDisposableDocument`, `snapshot`, `insertStructure`, `applyScene`, `serializeEditable`, `exportFigure`, `openCopy`, `inspectReadback`, `release`. These are OUR interface names, not claims that the vendor API has these methods. Each method declares its actual backend and required capabilities.

P0 probe order:

- Record OS, application build and edition, installation scope, running process, add-in support and lawful entitlement from the actual device. Store licence status/category, never licence values. The reported design input of ChemDraw 26.0.0 is historical detection on one device.
- Install/load a minimal add-in through the supported manager. Verify runtime/add-in handshake and a disposable document readback.
- Insert one known structure through `addSMILES` and compare returned native geometry and chemical graph. Verify style behavior. Probe clean-up separately only if actually exposed.
- Probe CDXML and CDX serialization plus PNG output. Selection SVG must have an explicit, verified scope; it does not imply whole-document SVG. PDF/other formats require separate native-route evidence.
- Decode native CDX bytes to a new local artifact where supported; record `native_serialization`, distinct from a desktop Save operation. Reopen that disk file in ChemDraw and compare its chemical and drawable objects. Writing vendor bytes is not a reopen test.
- Verify the controlled native route can create/identify/reopen a disposable document. Stop at `DOCUMENT_BINDING_UNSAFE` if the workflow cannot protect other documents.

No native call runs solely because a named function exists. The capability result records `documented`, `detected`, `native_verified`, `failed`, `unsupported` or `unverified`, the test ID, backend, scope, application version and timestamp. Host verification is a separate field. Do not collapse this evidence into one boolean.

## Identity, document binding and concurrency

A session identifies an authenticated principal, execution device, broker instance, worker generation, application process identity, native document binding and scene revision. Never accept a title, current window or file path alone as authority to edit. Native IDs are internal; hosts receive opaque session IDs and revision tokens.

One process-wide native write lane is the default; separate host conversations queue. A broker lock excludes other plugin jobs, not human input. Before EACH native mutation, the worker must verify the intended document and expected readback fingerprint. Repeat after mutation. Add-in messages include a paired nonce and worker generation to reject stale callbacks.

The Add-in documentation only identifies an active document, without a documented stable document ID or atomic compare-and-write. P0 must experimentally qualify whether a retained document handle stays bound when focus changes. Do not equate a content hash with document identity: identical blank documents have identical hashes. Accept a binding only if a verified document handle OR a plugin-owned isolated application/document lifecycle unambiguously excludes another target. Application focus alone is insufficient. If exclusivity cannot be established, stop before mutations; provide a supervised probe, not an unattended-support claim.

P0 creates disposable plugin-owned documents. Importing an existing document means copying its bytes into a private job directory first. Original files and open user documents are never modified. Continued edits produce a new version in the same session after an exact expected-revision check; final outputs are immutable. Unsupported objects in imported CDX/CDXML cannot be silently dropped by a scene conversion. Preserve them losslessly through the vendor document or return `UNSUPPORTED_OBJECT`.

Use a monotonic scene revision plus a normalized semantic-and-appearance digest. Native serializers may reorder XML/object IDs: keep byte hashes for integrity and separate normalized graph, drawable-object and style fingerprints for equivalence. Unexpected manual changes invalidate the lease with `REVISION_CONFLICT`. A change of application process, worker generation or document binding invalidates all pending mutation tickets.

A check-before/check-after protocol alone cannot eliminate an active-document race. The adapter must pass the deliberate document-switch test. If the only safe route is a supervised single-document session, advertise exactly that constraint. Do not enable editing arbitrary already-open documents in P0.

## Typed scenes and native layout

Recipes take chemical intent, not unrestricted JavaScript, shell snippets or arbitrary native calls. A scene contains stable component IDs, atom/bond references, participant roles, explicit labels/charges, stereochemistry and constraints. Electron flows contain explicit donor and acceptor references, electron count and intended bond/charge changes. An unspecified named mechanism is an intake error, not permission to substitute a canned mechanism.

Native engine establishes molecular geometry when supported. The companion arranges component boxes, conditions, reaction arrows and electron-flow curves using deterministic constraints. Preserve bonds/stereocentres within native fragments; translation and rotation are allowed only if wedges and labels remain meaningful. Never reflect a stereochemical fragment without semantic revalidation. Any CDXML construction or transformation records its producer independently of the final native image.

Apply a named versioned style profile with explicit units and final physical size. Start with `chembridge-review-v1`: a provisional house profile, not university, ACS or other publication certification. P0 test width is 85 mm; run a 170 mm readability check where relevant. Numeric style values must be recorded in the result rather than inherited silently from a user's last document. Establish typography/bond lengths from the actual native template, then freeze the accepted fixture profile; owner review remains pending until performed.

Lay out fragment rows and labels first, reserve condition and charge/lone-pair regions, then route curved arrows with explicit source/target ports. Run deterministic collision/geometry checks and render through ChemDraw. At most two bounded layout repairs in a job; otherwise return a reviewable failed-quality artifact. A passing native export never clears failed chemical or visual checks.

## Job durability and recovery

Persist an atomic job record, operation intent, idempotency key, request digest, identity and expected revision BEFORE writing. Start with atomic files and OS locks, plus a bounded event journal; add a database only for a demonstrated need. Store live state outside sync. ACKed submissions survive broker restart.

States: `queued -> preflight -> running -> verifying -> succeeded`. Alternatives: `needs_input`, `blocked`, `failed`, `cancelled`, or `outcome_unknown`. These are job states, not product release approvals. `succeeded` means required automated recipe checks passed; owner review, host receipt and release approval retain separate statuses.

Idempotency is principal/device scoped. Same key + same canonical request returns the existing job; same key + different request is `IDEMPOTENCY_CONFLICT`. Timeouts and lost callbacks after a write enter `outcome_unknown`. Reconcile the existing journal, document and artifacts before any new submission. Never blindly append/import again. Return a checkpoint and read-only inspect action when safe reconciliation is impossible.

Cancellation is cooperative at declared safe boundaries. After a native call has begun, show `cancellation_requested`; terminal `cancelled` requires verified quiescence. Do not kill a user's ChemDraw process or roll back over manual changes. If the worker crashes, quarantine the disposable job and mark its document lease invalid. Recovery creates a new disposable copy from the last verified checkpoint; it does not overwrite a published artifact.

Initial budgets are configurable engineering limits, not performance claims: 2-second submission acknowledgement, 20-second maximum long poll, 180-second recipe execution deadline, bounded native call timeouts and 2 layout corrections. Record actual timings. Use one native lane; cap queue length and reject excess work with retry guidance. Keep compact status responses below a 4 KiB target and expensive schemas/images on demand.

## Security and artifact delivery

Bind the local broker to loopback only; validate Host/Origin and reject unauthorized callers. Do not use permissive CORS, URL query-string secrets or a publicly exposed desktop control port. Pair a packaged local add-in with short-lived one-use bootstrap material, then reuse per-user encrypted credentials. The feasibility probe must confirm which local transport the installed add-in webview actually permits; do not assume WebSockets, file URLs or TLS behavior. Do not bypass vendor/browser security if a route is blocked.

Authenticate every job, event and artifact request. Enforce principal/session ownership even when callers know another UUID. Scope export destinations to opaque authorized destination IDs, resolve paths inside registered roots, reject traversal and unsafe reparse targets. Artifact retrieval resolves registered IDs, never caller-supplied arbitrary filesystem paths. Local paths are not cloud-accessible links.

Store native file bytes, exported figures, source scene, style settings, quality report and manifest as immutable, hashed artifacts. Record each producing/transformation stage and reopen results. Transport may stream an attachment or issue an expiring authenticated download. Mark host receipt only after observed transfer/readback evidence; a link merely being returned is `available`. The user's chosen authorized destination governs delivery, not OneDrive.

## Installation and versioning

One product entry, stable tool names, stable product ID `chembridge.chemdraw-companion`. Protocol contract major 1, recipe/style versions, broker version, add-in version and tool-manifest SHA-256 are separate. Reject incompatible broker/add-in pairs; do not silently use stale host tools. Discovery support does not establish a fresh host workflow.

Target a per-user Windows package with bundled runtime, self-test and readable status/repair UI. Do not bundle ChemDraw, licensed SDKs or activation material unless redistribution permission is established. Detect per-user/system installations and report missing prerequisites precisely. Add-in Manager installation may remain a guided manual step; count it and never label it one-click automation until proved.

Stage updates beside the active version, drain jobs, preserve encrypted credentials/configuration and switch only after handshake/self-test. Retain a working previous version and a config snapshot. Use backward-compatible state migration or explicit rollback migration; a binary rollback cannot repair an incompatible data schema by itself. Uninstall removes only owned registrations and offers preservation of user artifacts/configuration; do not touch Origin or ChemAIst.

P0 has no installer/release pass. Later delivery uses English GitHub Releases, checksums, compatibility table, measured size/startup/memory, upgrade/reinstall/path-variation/recovery evidence and a real Terra max host workflow.
