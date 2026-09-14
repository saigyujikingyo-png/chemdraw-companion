# Output-schema coverage and next-version plan

Status: **documentation adopted; output-schema implementation and acceptance pending**.
Updated 2026-09-14 on the implementation branch `codex/native-p0`.

## Authority, source and freeze

Adopt [shared rule 2026-09-14.1, section 12](../DEVELOPMENT_PRINCIPLES.md#12-structured-tool-outputs-and-output-schemas).
The canonical source is Chembridge commit
[`9c916e5e542ccf34e66256516af4793d195c0d87`](https://github.com/saigyujikingyo-png/chembridge/blob/9c916e5e542ccf34e66256516af4793d195c0d87/DEVELOPMENT_PRINCIPLES.md).
The synchronized principles match ChemDraw main `29a6599` and the canonical
source byte for byte (SHA-256 `5ef21e5454370924eb7fa1a4afb14747695fe8a5308f12440cf4cfd0a11b08ae`).
Architecture `885b3b4` carries the same text with CRLF line endings; its contributor
and scope guidance is also adopted, with the current implementation freeze made explicit.

Runtime remains frozen at **`b9363abfce19481d33e8d6409cb3d8d7dd477310`**.
This update changes only shared guidance, coverage, version planning and the change
record. It does not change executable contracts, tool discovery, native workers,
fixtures or prior evidence. No native/UI execution is authorised here. Machine
Interface Only, M2/descendant/holdout isolation, no 055 rerun/H-profile expansion,
Gold=0 and historical PARTIAL results remain in force. The shared rule's general
GUI guidance does not override the stricter current user instruction.

The architecture owner retains `docs/` and `contracts/`; the implementation owner
maintains this plan and, after explicit unfreeze, the approved validator/adapter
work. Formal contract changes require coordination; this plan is not a new contract.

## Current inventory and coverage

Read-only inspection of the frozen source found five **design-only** public MCP
tools in [mcp-tools.json](../contracts/mcp-tools.json), `contract_version: 1.0`,
`status: design-unimplemented`. All five have input schemas; **0/5 have outputSchema**.
There is no public MCP server/dispatcher in this implementation. Matching
`structuredContent`, server-side output validation and actual host discovery/calls
are therefore **not implemented / not verified for all five**. JSON from the
developer CLI is not MCP structuredContent.

[job-data.schema.json](../contracts/job-data.schema.json) already describes a
successful job-inspection data payload, including failed-job states. The common
envelope and errors are described in [the draft interface](../docs/INTERFACE_CONTRACT.md).
Neither a payload schema nor prose establishes complete tool-output coverage.

The following is the complete current public-tool/dispatch inventory. **Every row
has output-schema implementation pending, result validation pending and host
acceptance unverified.** Existing native evidence does not change these statuses.

| Public tool | Dispatch variant | Planned output coverage / existing fragment |
| --- | --- | --- |
| `chemdraw_status` | `detail=compact` | Runtime/product identity, session/lease and queue state, unavailable native facts |
| `chemdraw_status` | `detail=capabilities` | Bounded capability evidence, supported/unsupported/unknown distinctions |
| `chemdraw_help` | `topic=recipe` | One versioned recipe/operation schema, supported versions and cursor semantics |
| `chemdraw_help` | `topic=error` | Stable error code, bounded meaning and safe recovery information |
| `chemdraw_help` | `topic=style` | Style identity/hash, properties with units, observed versus proposed values |
| `chemdraw_help` | `topic=capability` | One capability and evidence; missing interface remains unsupported/needs_interface |
| `chemdraw_help` | `topic=recovery` | Known operation disposition and recovery guidance; no automatic replay |
| `chemdraw_run` | `recipe=structure_sheet.v1` | Submission identity/current job state, refusal/error; no new recipe execution authorised |
| `chemdraw_run` | `recipe=reaction_scheme.v1` | Same submission envelope with this recipe's validated payload; qualification pending |
| `chemdraw_run` | `recipe=electron_flow_step.v1` | Same submission envelope; schema acceptance never implies chemistry support |
| `chemdraw_job` | `action=inspect` | Job-data fragment plus full envelope, pending/terminal/error branches, event cursor |
| `chemdraw_job` | `action=cancel` | Request acknowledged versus cancellation completed; retain job ID and actual disposition |
| `chemdraw_job` | `action=reconcile` | Observed known/unknown outcome and evidence; preserve uncertain writes without replay |
| `chemdraw_artifact` | `action=describe` | Artifact metadata, provenance, available preview/resource, missing/denied artifact |
| `chemdraw_artifact` | `action=deliver` | Destination/route status, receipt or delivery failure; retained native artifact metadata |

The existing local CLI dispatches the five actions below. Their result dictionaries
are implemented, but **all output schemas and producer-side schema validation are
pending**. Its observed failures/refusals differ in fields/types; preserve them
when defining compatible contracts instead of relabelling them as MCP results.

| Local CLI action / subcase | Existing output and verification context | Planned contract branches |
| --- | --- | --- |
| `open-copy` | Native copy/identity/baseline observations; bounded script and controller evidence | Source/hash failure, copy/open failure, initial derivation, stable baseline, deadline uncertainty |
| `inspect` | Current or last-verified observation and frozen-session refusal | Current/stale distinction, drift, source/session expiry, error and end-session result |
| `inspect` + `end_session` / `keep_open` | Script/controller lifecycle evidence; Close can leave processes | Unsaved refusal, final observation, confirmed detach, close-return versus verified exit |
| `relative-position` + `above-arrow` | Bounded native movement evidence, separate derived-association record | Candidates/ambiguity, unsupported scope, identity/token refusal, computed motion, protected diff |
| `relative-position` + `up-half-bond` | Uses actual native BondLength; chemistry remains unqualified | Same guard/error coverage, native units, collision refusal, exact target residuals |
| `save` | New CDXML/CDX artifacts; original preserved | Per-format partial output, IDs/hash/bytes, save error, known/unknown write disposition |
| `reopen` | Fresh native bindings and exact differences; outer ok is not equivalence | Hash/identity failure, preserved old state, normalization difference, new revision and lifecycle |

These seven rows cover all five CLI actions and applicable variants; no new public
tool or generic dispatcher is introduced. A future public adapter must validate
both its compact outer result and the selected operation payload using the same
definitions as its direct-call path. Recipe/help/schema discovery should return
one requested detailed schema with version/hash, rather than a default giant union.
If full/economy modes are added, both must preserve the same meanings; no such modes
are claimed for this frozen CLI.

## Required result semantics for the next implementation

- Define required/optional fields, stable identifiers and types, bounded lists,
  pagination/end-of-list semantics, observation time and producer provenance.
  Native geometry uses document points; half-bond motion uses the observed native
  BondLength. Record schema/operation versions independently from product versions.
- Keep tool action acceptance, job state, mutation outcome, content equivalence,
  native execution/render, desktop display, chemistry and delivery as separate
  facts. A successful inspection may report a failed job. Keep all current strict
  differences, unknown H and PARTIAL evidence; do not turn outer `ok` into fidelity.
- Define null versus omitted values and unavailable/unsupported/not-calculated
  states. Never substitute zero, empty success, invented values or a pass. Retain
  the draft envelope's `ok`, `data`, `warnings`, `error` meanings; explicitly cover
  `data=null` on tool failure and `error=null` where no tool error occurred.
- Cover success, argument refusal, execution/output-validation failure and
  applicable queued/preflight/running/verifying/needs-input/blocked/failed/cancelled/
  interrupted/outcome-unknown branches. Maintain stable errors consistent with
  MCP `isError`; code review must distinguish tool failure from job failure.
- Validate at the producing server/adapter before delivery, including dispatcher
  payloads and exception/timeout paths. A malformed backend result must not be
  emitted as success. If a write already happened, retain request/job/session/
  operation IDs and evidence and report the known or unknown disposition. Output
  repair must never repeat the native write or erase the first failure.
- Describe each file with artifact ID, filename, MIME type, byte size, hash when
  available, provenance, relation to the requested operation and delivery state.
  Unknown metadata needs explicit semantics. Keep binary/image bodies in native
  MCP content/resource blocks; do not duplicate them as JSON or large text blobs.
  Do not expose arbitrary private paths as a public file-read interface. Valid
  metadata alone does not establish receipt by the user.
- Generate schema and producer validation from shared typed definitions where
  practical; reuse dependencies. Keep a deterministic serialized JSON text fallback
  consistent with structuredContent for supported hosts. Preserve existing content
  blocks, IDs, field types and recovery behavior. Do not fabricate a separate
  contract for a different model or silently drop structured results.

## Next applicable version and ownership

| Version line | Current state | Planned next step; not released |
| --- | --- | --- |
| Shared rules | `2026-09-14.1`, adopted now | Policy version only; never used as a plugin product version |
| Agent Edit Loop | `v0.1`, runtime `b9363ab`, PARTIAL/frozen | Propose **v0.1.1** after explicit unfreeze for compatible output definitions/validation only; implementation owner records exact source and validation |
| Public MCP contract | `1.0`, design draft `0.1.0`, no installed public server | Architecture owner assigns the next documented output-contract revision and operation schema versions before implementation; preserve existing 1.0 meanings/inputs |
| Plugin distribution | No certified release/installer in this scope | No tag, package bump or published schema-compliance claim in this documentation update |

The v0.1.1 target is conditional on compatibility, not a release promise. Adding
an output schema does not justify changing an existing required field, null
meaning, unit, default, artifact shape or retry semantics. If an actual design
requires such a break, stop the compatible-release claim and specify a separately
reviewed next-version migration (for example v0.2); retain the old path until the
migration and applicable host checks are accepted. Public MCP work is scheduled
only when that interface is independently authorised; this notification does not
unfreeze packaging, native work or all historical recipes.

## Validation and completion plan

1. Architecture/implementation review fixes the per-tool and operation definitions,
   version/dialect policy and compatibility mapping. Account for all 5 tools,
   15 current public dispatch variants and 5 CLI actions (7 documented variants).
   Schema discovery must expose the selected operation's version and meaningful
   schema without an unconstrained object standing in for the payload.
2. After authorised implementation, run focused producer contract checks on
   success/error/refusal/pending/terminal/cancel/interrupted/unknown branches;
   missing/null/empty values; unsupported results; malformed result rejection;
   artifact/error/partial-save paths and a lost reply after a write. Exercise the
   actual producer and exception paths, not just hand-built passing JSON.
3. Verify direct and dispatch results against the same definitions, the outer
   MCP outputSchema and exact structuredContent/text-fallback consistency. Check
   actual host dialect/adapters and media blocks. Cover full/economy modes only
   if present; do not invent support or new tools for a checklist.
4. Record real schema discovery and tool calls separately for each advertised
   host. Keep untested ChatGPT Chat/Work local/cloud, Codex or other-host routes
   unverified; old CLI calls are not retroactive MCP acceptance. Test installation
   or packaging only under separately authorised scope.
5. Measure schema bytes/default discovery versus on-demand size, latency,
   calls/retries and actual usage when available. Retain the Terra max benchmark
   requirement without changing this task's model; unavailable measurements stay
   unavailable. Schema size alone is not proof of quota savings.
6. Preserve separate native/numerical/visual/editability/host-delivery gates. No
   native/UI execution is part of this frozen adoption. New contract tests do not
   rerun, supersede or relabel old failed/PARTIAL acceptance.

For each inventory row, maintain implementation commit, output schema ID/version,
validator path, direct/dispatch/text/media checks, actual host evidence and open
gaps. At adoption all those implementation/acceptance fields are pending, except
the existing design fragments and explicitly labelled CLI/native history above.
Close a row only with its own evidence; schema conformity is never overall product
acceptance. Update discovery/help and installation guidance when implementation is
actually available, preserving compact defaults and honest unsupported states.

## Pinned Origin reference - planning only

Read-only implementation reference: Origin Companion 0.2.11 at commit
`8bff772b6cb70019e19a13e97adef9568b569d20`:

- [Output-contract design and coverage](https://github.com/saigyujikingyo-png/origin-agent-bridge/blob/8bff772b6cb70019e19a13e97adef9568b569d20/origin-agent/docs/OUTPUT_CONTRACTS.md).
- [Typed output definitions](https://github.com/saigyujikingyo-png/origin-agent-bridge/blob/8bff772b6cb70019e19a13e97adef9568b569d20/origin-agent/src/origin_agent/output_types.py).
- [Schema generation and result validation](https://github.com/saigyujikingyo-png/origin-agent-bridge/blob/8bff772b6cb70019e19a13e97adef9568b569d20/origin-agent/src/origin_agent/output_contracts.py).

These are design references for the existing coverage rows, not imported code,
dependencies or ChemDraw acceptance. The following additions to the next-version
validation plan are all **pending implementation and unverified in ChemDraw**.

| Reference pattern | ChemDraw application / focused check after unfreeze |
| --- | --- |
| Shared strict output types and schema generation | Cover every direct tool and operation with common definitions; reject number/string coercion, non-finite numbers and integer substitutes for boolean evidence; preserve optional/null meanings |
| Validate a returned result without invoking the backend again | Inject a malformed result after a simulated completed write; retain only valid known ChemDraw request/job/session/operation IDs, report output-validation failure, assert the write count remains one |
| Compact discovery plus the selected operation's full schema | Keep the current five-tool design; verify each of the fifteen dispatch variants against its own payload contract, including explicit errors and unsupported branches |
| Artifact metadata checked against existing content blocks | Verify IDs, MIME types, lengths, block kinds and any declared content indices/page offsets; reject mismatches while preserving binary/text payloads and delivery distinctions |
| Structured result and serialized text fallback agree | Exercise direct/dispatch and intended host adapters; reject or repair the output representation without changing an operation's meaning or repeating it |
| Cached schemas and bounded structured results | Choose ChemDraw-specific depth/item/byte budgets from measured outputs; test limit failures and discovery overhead without duplicating media or claiming token savings |

Do not inherit Origin's operation names, state/error enums, contract version,
resource limits, artifact layout or private-path exposure. Its typed-model choice
is a candidate, not approval for a new ChemDraw dependency. Any eventual code
reuse needs licence/attribution review and approval within the existing ownership
and freeze boundaries. Its release, test, native, installation, GUI and account
results remain Origin evidence; they were not rerun or counted here. ChemDraw's
five public output schemas remain unimplemented, and the proposed v0.1.1 target,
Machine Interface Only, M2 isolation and historical PARTIAL status are unchanged.
