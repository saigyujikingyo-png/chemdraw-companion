# MCP and scene interface contract 1.0 (draft 0.1.0)

Normative design for the P0 implementation; not a claim that these tools are installed. JSON Schema defines wire syntax; the invariants and validation rules below define semantics. Unknown fields/versions/recipes fail explicitly. All five tools use the same contracts in local and cloud hosts.

## Five stable entrypoints

| Tool | Input | Result and side effects |
| --- | --- | --- |
| `chemdraw_status` | optional `session_id`, `detail=compact|capabilities` | Product/broker/add-in/contract/manifest identity; actual capability evidence; queue health. Read-only; never launches a scientific job. |
| `chemdraw_help` | `topic`, optional `cursor` | One recipe, error, capability or style schema at a time; bounded page. No full catalog by default. |
| `chemdraw_run` | request below | Durably submit one recipe or continued revision; returns job identity immediately. Native writes occur asynchronously only after preflight. |
| `chemdraw_job` | `job_id`, `action=inspect|cancel|reconcile`, optional `after_event`, `wait_ms` (0..20000) | Compact progress or terminal result; cancel is cooperative; reconcile inspects uncertain writes without replaying them. |
| `chemdraw_artifact` | `artifact_id`, `action=describe|deliver`, optional `destination_id` | Manifest/preview metadata or delivery through an authorized host/destination. Never an arbitrary path-read endpoint. |

A session starts when an accepted `run` allocates a new scene. The run response returns its opaque ID; the initial revision is reserved until native verification commits it. A continued run provides `session_id` AND `expected_revision`. Status reports expired leases. No separate session-control tool is needed in P0; cancellation and documented idle expiry release worker resources, while immutable artifacts remain.

Common response envelope:

```json
{
  "contract_version": "1.0",
  "request_id": "opaque",
  "ok": true,
  "data": {},
  "warnings": [],
  "error": null
}
```

`ok` means the requested tool action was accepted/completed, not that native quality or delivery passed. A first accepted `run` returns `job_id`, `session_id`, `state=queued`, `revision=null` and a recommended poll interval. Idempotent replay instead returns that same job's CURRENT state and committed revision if one exists; it must not reset a completed job to queued. A succeeded job returns committed `revision`, artifact IDs and independent gate states. Error results set `ok=false`, `data=null` and a structured error. Do not put secrets, full native files or full stack traces in normal tool output.

## Run request

See [run-request.schema.json](../contracts/run-request.schema.json) and the three [examples](../examples). Required fields:

- `contract_version`: exactly `1.0`.
- `idempotency_key`: caller-generated stable key, reused if transport outcome is uncertain.
- `recipe`: one of `structure_sheet.v1`, `reaction_scheme.v1`, `electron_flow_step.v1`.
- `target`: `{mode:"new"}` or `{mode:"continue",session_id,expected_revision}`. P0 does not mutate arbitrary open documents. General file editing is deferred.
- `inputs`: a typed recipe-specific object as below.
- `output`: `native_required:true`, `editable_format:"cdx"`, `figure_format:"png"`, optional authorized `destination_id`. CDXML is an additional readback/interchange artifact. Other formats require a later additive capability-qualified contract.
- `style`: `{profile_id:"chembridge-review-v1",final_width_mm:85|170}`. The width denotes a fixed physical canvas, not an ink-bounding-box stretch. Keep the declared physical font and bond sizes. Values are proposal defaults, not accepted course/publisher styles.

The same complete scene input is used for continuation, with stable component and atom-map IDs. P0 deterministically rebuilds an isolated new revision document from the previous verified scene and the requested changes. This avoids treating vendor `add*` methods as replacement. Preserve old revisions and compare the intended diff. A future patch operation must separately specify deletion, unknown-object retention and ID mapping.

Preflight verifies schema, request ownership, idempotency, exact revision, required native capabilities, chemical semantics, profile and resource limits before native mutation. A revision mismatch returns the current token plus a compact diff; the host obtains the latest scene before requesting a new revision. Never auto-merge a stale chemical edit.

Initial limits: at most 6 structures per sheet; ordinary reaction up to 3 reactants and 3 products; mechanism one explicit elementary step, up to 3 reactants/products and 3 two-electron arrows. SMILES input up to 4096 characters per component; maximum 200 heavy atoms per scene. Reject larger inputs rather than silently truncate. These are bounded P0 choices, not general ChemDraw limits.

### Structure sheet

`inputs.structures[]`: `{id, smiles, label}`. IDs are unique stable strings. Preserve isotopes, explicit hydrogens, charges and requested stereochemistry. Unspecified stereochemistry remains unspecified. If the independent parser and native readback disagree, return a semantic error; do not pick whichever result looks cleaner.

### Ordinary reaction

`inputs.reactants[]` and `products[]`: component objects as above. `conditions[]`: display strings supplied for the intended reaction, with no inferred yield or experimental result. `balance_mode`: `complete` or `declared_partial`. If partial, nonempty `omitted_species_note` is required and appears in the verification report. A reaction scheme is not an electron-flow mechanism. P0 fixtures use complete atom/charge balance and explicit mappings.

### Electron-flow step

Same participants, plus `reaction_smiles` (fully mapped), `electron_flows[]`, `bond_changes[]`, `charge_changes[]`. Components and reaction SMILES must denote the same mapped graphs. Every relevant heavy atom has one unique positive map ID, conserved across the step; transferred hydrogens must be explicit mapped atoms. Do not imply blanket support for proton transfers, radicals, organometallics or arbitrary mechanisms from this schema.

Each flow is `{id,electron_count:2,source,target}`. Source type is `lone_pair` (component+atom map+pair index) or `bond` (component+two atom maps); target is `atom` or `bond` with matching references. Atom pair ports are validated for valence/charge and later placed in native geometry. All flows in this elementary step are simultaneous and are validated against the same pre-step graph. Their array order is only a stable display order; never apply them sequentially as chemical intermediates. For P0 every source and target component reference must point to a reactant-side component and its mapped atoms, even when the same map occurs in a product. Product participants specify the post-step graph. In particular, the two SN2 arrows must not generate a five-coordinate carbon intermediate. A bond change declares mapped atoms, `from_order` and `to_order` (0 means absent); charge changes declare atom map, `from` and `to`. These declarations must equal the graph difference; they are not instructions to forge a passing readback.

P0 implements only the explicitly specified SN2 teaching fixture and tightly matching validated variants after qualification. The example is hydroxide plus bromomethane to methanol plus bromide, with two curved arrows: O lone pair to methyl C; C-Br bond to Br. Unsupported mechanism semantics fail even if the JSON passes. A schema being more expressive than the first fixture is not feature coverage.

## Native worker command receipt

An internal command carries `job_id`, `command_id`, `principal_id`, `device_id`, `worker_generation`, `session_id`, `expected_revision`, `binding_token`, `operation`, typed args and deadline. The journal records its intent before dispatch. A reply includes actual API/backend name, application build/edition category, start/end times, before/after fingerprints, object-ID mapping where observed, native warnings, disposition (`not_started|completed|unknown`) and artifact hashes.

A lost reply after native dispatch is not safe-to-retry. `reconcile` compares the same command journal and fresh native state. Only an observed `not_started` or an intact completed receipt permits a deterministic next step. Otherwise the job remains `outcome_unknown`, with the disposable document quarantined and an actionable recovery hint.

## Output provenance and gate states

Every manifest includes `manifest_version`, product/contract/recipe/style/build identities, job/session/revision, principal-scoped artifact IDs, file names, MIME types, byte counts and SHA-256. Public manifests omit private identifiers/paths and use sanitized aliases.

For EACH artifact, record `stages[]` with operation, producer/backend/version, input hashes, output hash and evidence IDs. Examples of distinct stages: `native_structure_generation`, `companion_scene_layout`, `native_cdxml_import`, `native_cdx_serialization`, `native_png_render`, `native_disk_reopen`, `independent_graph_validation`, `host_delivery`. Use `not_performed` for stages that did not run. Never describe every stage simply as native because the last image came from ChemDraw.

Gate fields: `native_execution`, `chemical_semantics`, `layout_geometry`, `native_editability`, `visual_review`, `owner_acceptance`, `host_receipt`. Each has `status=pass|fail|pending|unverified|not_applicable`, evidence IDs and reason. `owner_acceptance` records the actual reviewer decision/reference, never inferred from silence. Job success does not automatically set owner or host gates to pass. Full P0 requires separate P0-A/B/C evidence and all four fixtures S1/R1/M1/M2 plus owner acceptance. M2 uses an internal mechanism-test contract, not a fourth public recipe; existing job-data wire gates remain unchanged.

Editable package minimum: native CDX saved bytes, native CDXML readback, native PNG with resolution and physical-size metadata, source scene, effective style, verification report and provenance manifest. If native CDX is not produced and reopened, return a blocked/failed gate; do not label an independently written CDXML as equivalent completion. CDXML-only experimentation is allowed but remains a diagnostic artifact.

Document/image snapshots are not promised atomic by the vendor guide. Export under a qualified document binding, record matching pre/post normalized fingerprints around each export, and reject changes with `EXPORT_REVISION_MISMATCH`. These checks detect observed changes; they do not create an atomic vendor API guarantee. P0 must additionally test user/document interference.

Artifact `delivery.status`: `available|transferred|receipt_verified|blocked|failed`. `receipt_verified` requires a receiver-side observed hash/size or direct reopen of the delivered file, with route and manual steps recorded. Do not confuse MCP resource publication or an expiring URL with received bytes.

## Error contract

An error contains `code`, `message`, `stage`, `retryable`, `mutation_outcome=none|known|unknown`, `job_id` if assigned, `evidence_ids` and `next_action`. These fields must be short and corrective. Credentials/login belong in a supported owner interface, not a tool argument.

| Code | Required behavior |
| --- | --- |
| `INVALID_ARGUMENT` / `UNSUPPORTED_RECIPE` | Reject before native action; return field and supported contract/version. |
| `CHEMICAL_INPUT_AMBIGUOUS` / `SEMANTIC_MISMATCH` | Identify missing mapping/stereo/flow or conflicting readback; never invent chemistry. |
| `APP_UNAVAILABLE` / `LICENSE_ACTION_REQUIRED` | Exact observed missing application/entitlement action; preserve existing connection. |
| `CAPABILITY_UNVERIFIED` / `NATIVE_ROUTE_UNAVAILABLE` | Name missing method/format and probe evidence; no renderer fallback. |
| `DOCUMENT_BINDING_UNSAFE` / `REVISION_CONFLICT` | Stop writes; retain original/copy and require safe binding/current scene. |
| `IDENTITY_MISMATCH` / `PROTOCOL_MISMATCH` | Reject stale broker/add-in/tool map; use supported repair entrypoint. |
| `IDEMPOTENCY_CONFLICT` | Return existing job; different input needs a new key. |
| `NATIVE_OUTCOME_UNKNOWN` | Reconcile existing command; `retryable=false` until outcome is known. |
| `QUALITY_GATE_FAILED` / `UNSUPPORTED_OBJECT` | Retain diagnostic artifacts; report failed criterion, no success claim. |
| `EXPORT_REVISION_MISMATCH` | Discard/quarantine inconsistent export; no artifact association to stale revision. |
| `DELIVERY_BLOCKED` / `DESTINATION_DENIED` | Keep native result; state failed route and authorized alternatives without claiming receipt. |
| `RESOURCE_LIMIT` / `JOB_TIMEOUT` | Bounded failure/cancellation; report actual deadline and mutation disposition. |

## M2 internal feasibility contract

The mandatory [M2 test](M2_BECKMANN_SNAKE.md) uses [composer-request.schema.json](../contracts/composer-request.schema.json) at the general IR/Composer boundary and a qualified adapter before packaging. mechanism-test-case.schema.json remains a test-side reference oracle only. The [generalization gate](M2_GENERALIZATION_GATE.md) requires an implementation freeze and untuned holdout after base M2. Public single-step recipe limits remain unchanged. Its developer receipt adds P0-A/B/C, both-format reopen/edit and first-output/manual-correction evidence; public tools do not yet support general multi-step mechanisms.

## Compatibility rules

Adding optional response metadata is minor-compatible. Removing/renaming tools, altering defaults/units, changing required input fields, idempotency/revision meaning or producer claims is breaking. Never mutate a released recipe/style's semantics in place. Pin schema + example hashes in implementation receipts; changes need architecture review and negative-test updates. A model/host adapter may simplify prompts but cannot alter chemistry, gate requirements or native provenance.

## Machine-readable discovery supplement

`contracts/mcp-tools.json` contains the exact five input schemas for MCP discovery; the embedded run schema must stay byte-equivalent as parsed JSON to `run-request.schema.json`. `contracts/job-data.schema.json` defines the `data` payload returned by a successful job inspection. A successful inspection can report a failed job; tool `ok` and job `state` remain distinct.

For help, `topic` is recipe/error/style/capability/recovery; optional `item_id` requests one item, and an omitted item returns a short paginated index for that topic. Cursors are opaque, principal-scoped and bounded. `status` defaults to compact and `job.wait_ms` to zero. The native worker may remain uninitialized when status is read.

Artifact delivery with no destination ID uses the originating host artifact channel only if it is available and already authorized. Otherwise return `DESTINATION_DENIED` with a corrective action. A run's optional destination ID stores the requested delivery preference; it does not prove a transfer. The host calls `chemdraw_artifact(action=deliver)` after artifact availability, and records actual receipt separately. Retried delivery to the same destination is idempotent by artifact SHA-256 and delivery attempt ID; a different destination requires its own authorization.

Transport requests have an effective authenticated principal even when that field is absent from model-visible schemas. Never accept a principal supplied by the model as authority. `job-data.identity` is required once a job succeeds; before that it may be absent when application probing has not completed. All seven gates are always present, initially unverified/pending, so omitted evidence cannot look like a pass.

## Session commit and correction rules

Before native work, atomically reserve the session's parent revision for one job/worker generation. Commit requires compare-and-swap on that parent revision and reservation token. Only a verified successful output advances the session revision; a failed or stale output remains a diagnostic artifact. This session reservation is additional to the application write lane and does not solve native document identity by itself.

`needs_input` and `blocked` are quiescent stopped jobs with no automatic resume. The host obtains the missing input or resolves the blocker, then submits the corrected complete request under a new idempotency key, preserving the last committed revision for continuations. The old job remains auditable. `outcome_unknown` is an unresolved, fenced state, not proof of quiescence: no new session write may begin until reconciliation establishes native completion/quiescence. Reconciliation reads existing state and may finalize a proven completed operation; it does not replay the original native write. If proven not started, mark the old attempt stopped and allow a deliberate new submission. A timed-out `needs_input` wait is not user approval.

Keep the P0 compact idempotency ledger and tombstones; do not automatically forget old keys. When its configured safe capacity is reached, reject new work with `RESOURCE_LIMIT` rather than permitting a stale key to become a new mutation. A future expiration protocol must define wire-level age/replay protection before any retention change.

## State transitions and output style identity

| Current state | Event | Next state / authority |
| --- | --- | --- |
| queued | Worker owns session reservation and starts preflight | preflight |
| preflight | Valid request, capability and document binding | running |
| preflight | Missing chemical input or observed missing capability | needs_input or blocked; quiescent, release reservation |
| running | Native commands have known completion | verifying |
| verifying | Required automated gates pass and revision CAS succeeds | succeeded; publish immutable revision/artifacts |
| running/verifying | Known failure with native quiescence established | failed; retain diagnostic artifacts, no revision advance |
| active state | Cancel requested | Set cancellation_requested; cancelled only at verified safe/quiescent boundary |
| active state | Native reply lost, crash or write timeout with uncertain disposition | outcome_unknown; preserve journal and fence reservation |
| outcome_unknown | Reconcile proves write completed and worker quiescent | verifying without replaying native mutation; original job identity retained |
| outcome_unknown | Reconcile proves write never started and worker quiescent | failed with corrective action; release reservation, new deliberate request may proceed |
| outcome_unknown | Still indeterminate or in flight | outcome_unknown; no new write or automatic key change |
| needs_input/blocked/failed/cancelled/succeeded | Same idempotency key replay | Same job and current state/revision; no mutation or reset |

A recipe can collect diagnostic artifacts after failing, but those cannot become the committed scene revision. Owner review and host receipt can be appended as separate evidence after `succeeded`; neither rewrites a failed native result.

Before the first native dispatch, resolve every style value (font family/size, bond length/stroke, charges, arrowhead/curve settings, spacing, canvas units and render scale) into an immutable effective-style document and SHA-256. Include `style_sha256` in the job identity and artifact manifest; owner approval references this exact style plus artifact hashes. Once dispatched, changing those values requires a new style version and contract-reviewed profile ID, never silent mutation of `chembridge-review-v1`. The proposal defaults in QUALITY_GATES.md must be validated for native application before any passing fixture claim.
