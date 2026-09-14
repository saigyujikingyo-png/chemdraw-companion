# Structured output contracts and release plan

Rule adopted: **2026-09-14.1**, section 12. This is an architecture-only draft on the existing architecture branch. Executable runtime remains frozen at `b9363abfce19481d33e8d6409cb3d8d7dd477310`. The implementation branch advanced to documentation-only `9d0dd55517796fba1c308911dd4d64d7a031149f` during this work; its six-file diff contains no executable changes. Its [implementation coverage plan](https://github.com/saigyujikingyo-png/chemdraw-companion/blob/9d0dd55517796fba1c308911dd4d64d7a031149f/runtime/OUTPUT_SCHEMA_COVERAGE_PLAN.md) remains owned by that task. Agent Edit Loop v0.1 remains PARTIAL. No MCP service, installation, host, GUI or chemical capability is implemented by this change.

## Current and proposed surfaces

[contracts/mcp-tools.json](../contracts/mcp-tools.json) remains `design-unimplemented`. Its five existing tool names now declare output schemas; all input schemas are unchanged. The [registry](../contracts/output/registry.json) identifies shared schemas and **20 individual tool/operation rows**: 15 MCP mode/recipe/action rows and 5 CLI operations. Each row separates declaration, implementation, server validation, host verification and owner.

| Surface | Output contract | Current implementation / evidence |
| --- | --- | --- |
| chemdraw_status, compact/capabilities | product/runtime identity, timestamp, bounded evidence-backed capabilities, explicit unavailable queue/versions | Design only; no MCP server or schema-qualified native call |
| chemdraw_help, five existing topics | bounded item metadata, optional schema IDs/resource IDs, opaque cursor | Design only; runtime schema discovery pending |
| chemdraw_run, three existing recipes | existing job/session/state/revision/poll response, including current-state replay | Design only; submission/idempotency integration pending |
| chemdraw_job, inspect/cancel/reconcile | original job-data plus output-only lifecycle/evidence constraints | Design only; cancel/reconcile need operation-specific semantic checks |
| chemdraw_artifact, describe/deliver | artifact identity/MIME/size/hash/provenance and delivery state | Design only; real content/resource blocks and receiver evidence pending |
| CLI open-copy | immutable source hash, actual binding, source protection | Legacy native implementation exists; new output adapter not implemented |
| CLI inspect | native binding, observation/candidate reference, closure evidence | Legacy response may precede resource closure; ending is not closed |
| CLI relative-position | caption/arrow references, intent, delta in pt, native bond length, comparison evidence | Legacy native operation exists; new result validation pending |
| CLI save | saved revision, artifacts and comparison evidence | Legacy outer ok is not preservation equivalence |
| CLI reopen | previous/new bindings, actual artifact and comparison evidence | Legacy native reopens exist; automatic equivalence classification pending |

The 15 MCP rows are status (2), help (5), run (3), job (3), artifact (2); no full/economy implementation exists. Existing status compact/capabilities is not evidence of a full/economy mode. No generic MCP dispatcher is currently implemented. The CLI action switch is the actual dispatcher; its five payload schemas are selected by operation and status. Shared payload shapes do not waive request/action-specific validation.

## Wire semantics and compact discovery

The draft MCP output profile is `output-contracts/1.0.0-draft.1`. The existing six envelope fields retain their meanings: `contract_version=1.0`, `request_id`, `ok`, `data`, `warnings`, `error`. Successful tool actions have structured data and null error; failed tool actions have null data and structured error. Successful job inspection may report a failed or interrupted job without becoming a tool execution error. `isError = !structuredContent.ok` applies to handled tool results; unknown tool/malformed JSON-RPC requests remain protocol errors.

The new job-data output overlay references the original schema without modifying its bytes. It requires error details for failed/blocked/needs_input/unknown jobs and evidence for pass/fail gates. The historical full-mechanism job success gates **must not become caption-edit prerequisites**. Caption-only results use the separately versioned edit adapter profile below.

MCP result metadata is carried once in `structuredContent`, with an equivalent serialized JSON TextContent fallback for supported legacy hosts. Images/binaries remain image/resource/content blocks, referenced by artifact metadata. Do not duplicate PNG base64 or files in JSON. Metadata validity, native image export and actual host receipt are separate claims. An observed zero-byte file is 0; unknown bytes/hash is null with the corresponding `unavailable_metadata` entry. Null version fields require a reason. Empty item lists mean the bounded query returned no items, not unavailable data.

Identity/reference fields are opaque; do not coerce the existing public string revision to the CLI's integer revision. CLI deltas and bond lengths are native document points, never screen pixels. Capability claims and measured pass/fail gates require evidence IDs; presence of an ID does not authenticate evidence. Server checks must bind actual timestamps, file hashes, producer, subject, version and authority.

Schemas use JSON Schema 2020-12, matching the existing repository dialect. Repository URNs resolve through the explicit registry; they are **not a promise that a host can resolve a local path or URN**. Before serving tools/list, the implementation must bundle only each tool's referenced definitions into a self-contained schema, reuse shared typed definitions, and test host dialect support. Do not publish one giant union of unrelated operations.

For on-demand detail, reuse `chemdraw_help(topic=capability,item_id=output:<tool-or-operation>)` and its existing cursor; schema resources are returned through resource/content metadata. Status cannot accept a cursor, so its output cursor is always null; detailed capability pagination belongs to help. This is planned discovery, not a newly installed tool. Skills/help must explain result meanings and unsupported host combinations before interface acceptance.

## Frozen CLI migration and side effects

`agent-edit-result/0.2-draft.1` is a **future opt-in normalized output**, not a schema claimed for the old raw CLI responses. Do not relabel or backfill historical receipts. Keep legacy response bytes/meaning available through a documented compatibility mode; introduce the new profile only after implementation is authorized. Direct CLI calls and any later dispatch route must use the same per-operation validator.

The new profile separates operation status, mutation outcome, preservation, native render, desktop display and resource state. `completed` means operation completion; preservation may still be needs_review and desktop display unverified. Normal pending work has null error; known failure/refusal/interruption has a bounded stable error. `outcome_unknown` and unknown mutation disposition agree in both directions and prohibit automatic retry. A refused write has mutation_outcome=none; post-write verification failure is failed/known or outcome_unknown, never refused/none.

Before any dispatch, allocate/persist operation identity using the existing receipt mechanism. Preserve all known operation/request/job/session IDs and already produced artifacts in error results. Error detail must come from trusted operation context if the backend payload is malformed. A bad JSON reply or schema mismatch after dispatch becomes OUTPUT_VALIDATION_FAILED with accurate known/unknown mutation disposition and recovery instruction; it must not fall through to native_write=false or lose assigned IDs. Validate the failure envelope too. Never retry the write to obtain a nicer response.

Current legacy gaps from frozen source:

- open-copy returns native_write as a string; other responses use bool, native_write_started or omit it. No single bool faithfully describes this history.
- native_edit_loop.py reads backend JSON without result schema validation. Generic exceptions can report native_write=false and omit known identity after dispatch.
- inspect(end_session) replies before finally writes the closure receipt. Report ending/pending until actual release evidence exists; detach and closed are different.
- save/reopen retain strict normalization differences but do not classify equivalence. Unknown differences require review/refusal; automatic ID reassignment is neither a loss nor an acceptance proof.
- native previews are file paths with hashes. Those paths are not yet schema-qualified MCP media delivery.

Do not retrofit a large transaction framework. Add the minimum trusted-context adapter/validation boundary after unfreeze. Machine Interface Only remains mandatory: use native COM/document interfaces or verified structural adapters, never GUI/clipboard/focus fallback. This contract work does not resolve residual windows, enable headless use or authorize native execution.

## Version plan and acceptance gates

| Identity | Decision |
| --- | --- |
| Shared rule | Adopted 2026-09-14.1; not the product version |
| Product | Existing 0.1.0 is an architecture draft. Reserve **0.1.1-dev.1** for the next output-contract preview only if implementation and compatibility checks justify it; no package/tag/release created here |
| MCP | Keep public contract major 1 and current input shapes; output draft has its own profile ID and manifest hash |
| CLI | Opt-in 0.2 result profile is an explicit migration of output shape; do not silently replace the frozen legacy format |
| Release | No output-schema compliance, host support or product-release acceptance until implementation evidence exists |

Next authorized implementation order: shared typed result definitions and server checks; per-operation normalization preserving side-effect context; consistent structuredContent/text fallback/media mapping; bounded discovery/bundling; direct/dispatch compatibility tests; actual host and artifact checks. Do not change the execution core's chemistry, layout or H qualification for these tasks.

Required evidence for each registry row:

1. Validate success, ordinary pending, invalid arguments, unsupported/needs_interface, known failure, cancellation/interruption and uncertain native outcomes where applicable. Preserve assigned IDs after effects and do not fabricate null replacements.
2. Reject malformed backend results, contradictory error/outcome pairs, omitted required fields, non-finite geometry, false pass evidence, bad artifact metadata and response/action mismatches. Validate partial-save errors without discarding produced files.
3. Test direct and dispatch routes, old/new response opt-in, equivalent JSON text fallback, actual media content/resource blocks, authorized delivery, schema discovery and local reference bundling. Report unavailable modes, not skipped passes.
4. Test each advertised host separately: ChatGPT Chat, local Work, cloud Work, Codex, Claude, WorkBuddy and others remain unverified for this new profile. Preserve ordinary use without a coding workspace; these local development checks are not end-user-host acceptance.
5. Record exact versions, schema bytes, calls/retries, latency and available actual usage for a future real Terra max benchmark. Schema size is not billed tokens or quota savings. Contract validation never replaces native reopen, preservation, numeric/visual quality or human acceptance.

## Change and verification record

2026-09-14: added draft outputSchema declarations, bounded per-operation registry, output-only job overlay and future CLI adapter; retained five public tool names, all inputs, old job-data, frozen runtime and previous evidence. Corrected the README's current-phase description without rewriting past receipts.

Run `python contracts/output/check_contracts.py` with the repository's existing JSON Schema dependency available. This isolated synthetic checker verifies result/schema branches and fallback semantics; it is not production validation. The [phase check receipt](OUTPUT_CONTRACTS_V1_CHECKS.json) binds the executed checker/schema bytes, actual outcome and implementation gaps: 54 isolated synthetic cases passed on the final draft. All five input schemas and the original job-data file remained unchanged. No server, host or native call was run. The receipt also discloses one source-discovery scope deviation: a generic-named validator fragment was read before recognizing it as M2-specific, then excluded without execution or reuse.

[Shared rule source](https://github.com/saigyujikingyo-png/chembridge/blob/9c916e5e542ccf34e66256516af4793d195c0d87/DEVELOPMENT_PRINCIPLES.md#12-structured-tool-outputs-and-output-schemas) and [MCP output specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools#output-schema). No private native artifact or retained benchmark is needed for this contract work.
