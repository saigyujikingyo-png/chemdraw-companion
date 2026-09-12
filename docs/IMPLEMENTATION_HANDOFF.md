# Implementation handoff: first native feasibility milestone

Read this page first, then ARCHITECTURE.md, INTERFACE_CONTRACT.md, QUALITY_GATES.md and SOURCES.md. Shared rules: DEVELOPMENT_PRINCIPLES.md, version 2026-09-12.4. This is a design handoff; it does not certify an implementation.

## Repository and ownership

- Dedicated repository: `saigyujikingyo-png/chemdraw-companion`. This product is separate from Origin and existing ChemAIst repositories and installations.
- Architecture branch: `codex/native-architecture-v1`; docs/contracts/examples only. The handoff message supplies the exact immutable commit.
- Implementation branch: `codex/native-p0`, created from the handoff commit on the implementation device in its verified non-synced directory. Keep runtime/jobs/builds outside OneDrive. Do not assume another computer's paths.
- Architecture owner changes docs/contracts; implementation owner changes runtime/native probes/tests/installer. Send contract questions/deltas to the architecture owner; do not force-push or concurrently edit the same branch. Merge agreed architecture updates explicitly.
- Start with a small native probe and fixture worker. No monorepo framework, replacement of installed ChemAIst, Origin-core chemistry module or broad renderer expansion.

The architecture owner publishes sanitized design only. Implementation owns actual app/licence discovery, code, native samples, installation packages and release evidence. No new developer task is needed beyond the already coordinated implementation task.

## Immediate implementation sequence

1. Report exact device/application build and edition evidence without licence values; load official add-in and establish paired handshake. ChemDraw detection alone does not pass.
2. Qualify safe disposable-document binding, including identical A/B and focus-switch tests. Verify the behavior of a retained Document reference. A hash/lease is not an identity guarantee. Refuse arbitrary document editing until safe.
3. Prove official structure input, native CDX bytes and PNG, then actual disk reopen and editable object readback for S1. Validate native generation/cleanup independently; do not silently use legacy open-source layouts.
4. Add R1 and M1 only within the typed contract, with fresh native geometry and bounded companion page layout. Require editable curves and conditions after reopen. Run the quality checklist on the actual final images.
5. Produce a continued revision in a new isolated document; preserve the prior artifact. Exercise lost-reply idempotency, revision conflict, cancellation/crash, wrong selection and stale identities.
6. Return three reviewable fixture bundles plus a compact capability matrix and blocker report. Owner visual review is a gate, not something the runtime can infer. Expand useful features/hosts/installers only after P0 native and quality gates pass.

The official Add-in guide includes `getCDXBase64Encoded`; native serialization is a viable probe candidate. It does not document open/save/replace/cleanup or reliable document identity. `Window.close` is not document close. Native desktop/other official adapters must be verified operation by operation for the missing steps. `addCDXML` appends and preserves supplied geometry/style, so it does not fix old layouts.

## Stable interface to implement

Five tool names: `chemdraw_status`, `chemdraw_help`, `chemdraw_run`, `chemdraw_job`, `chemdraw_artifact`.

Three immutable recipe IDs: `structure_sheet.v1`, `reaction_scheme.v1`, `electron_flow_step.v1`. The run schema, all five MCP input schemas, job-data schema and examples are under contracts/ and examples/. RISK_REGISTER.md records unresolved stop conditions and initial resource policies. All P0 jobs require native CDX plus PNG; additional native CDXML readback and quality/provenance files are mandatory. Unsupported capabilities block, never substitute a renderer.

Keep broker/add-in/manifest/contract/recipe/style versions separate. Persist idempotency and write intent before native dispatch. Terminal `outcome_unknown` requires reconciliation without replay. Job success, native editability, visual acceptance and host receipt are different statuses.

## Implementation return format

Send commit/branch, exact app/API/build versions, methods exercised, actual capability status, fixture IDs and input hashes. For each fixture attach/refer to received CDX/CDXML/PNG, scene/style, manifest, semantic/object comparisons, reopened-edit receipt and final-size visual evidence. Include actual failures, repairs, manual steps, timings and unresolved gaps. Do not publish private paths, account/activation/tunnel details or course data.

If blocked, identify the specific failing operation/licence/binding/quality test and official alternatives tried. Preserve diagnostics. Stop breadth and report the bounded Mnova 1D NMR alternative for a coordination decision; do not relabel its result as ChemDraw output.

The later default acceptance model is GPT-5.6 Terra + max in actual user hosts. Development using Astra does not establish that benchmark. Reuse existing encrypted connections; do not request new credentials without evidence. The known OpenAI frontend project-sync bug stays out of scope.

## Architecture review corrections before runtime implementation

The final architecture supplement adds per-session revision reservation and commit compare-and-swap, simultaneous SN2 graph validation with reactant-side anchors, and fixed physical canvas sizing without stretching molecular style. `needs_input`/`blocked` stop quiescently and require a corrected new request; `outcome_unknown` fences further writes until reconciled. Keep idempotency tombstones in P0 rather than implementing undefined expiry. These refine the existing contract; tool names and recipe IDs are unchanged.
