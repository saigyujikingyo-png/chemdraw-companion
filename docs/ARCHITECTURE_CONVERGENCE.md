# ChemAIst to ChemDraw Companion: architecture convergence

Decision date: 2026-09-26. Status: bounded architecture decision; no runtime migration or new native acceptance. The existing local Product Max is the sole continuing product owner. Task identity, device checks, takeover acknowledgement and actual archive receipts are private; publication of this page does not prove takeover or archival.

## Product and source state

ChemDraw Companion is the only continuing ChemDraw native automation product. ChemAIst is a preserved technology source, not a second runtime controller. Do not merge the repositories wholesale, remove installations, rewrite history, change product identity or automatically merge historical PRs. Spectroscopy, data analysis, reports and other application integrations remain preserved outside Companion; their eventual owners should be the relevant specialist products or the shared Chembridge coordination layer, without creating a new general Agent platform.

The following refs were read from GitHub during this consultation, rather than inferred from old handoffs:

| Repository / ref | Exact commit / observation |
|---|---|
| Companion main | `29a65991c30532fd25e3e8f8e1e15a940af1e8e0` |
| Companion architecture, review base | `ae7ae011967b51e403dced71c948bd6a2e730dd1` |
| Companion native-p0 | `5a01ffc1230a8c06acb063a2ab8409879aed4fe5` |
| Companion lifecycle-receipts | `c6cfa3ec398d4659a3e61a6e48460e689f84e530` |
| Companion diagnostic-mcp-compat | `6949b139899ac44fe5e5200b76060b2535a5e145` |
| Companion open work | Issue #2; PRs #1, #3 and #4 remain unmerged |
| Companion releases | v0.2.0-preview.1 and v0.2.0-preview.2 exist; the latter points to 6949b139 |
| ChemAIst old main | `98e3c1079437735d0b79535f23826d98c4d9e4d0` |
| ChemAIst source archive | `archive/adobook-20260910/chymaistry/source/codex/chemaist-0121-cleanup` at `7724a940d402c84675af372bbaef0472231bc72a` |
| ChemAIst migration checkpoint | `migration/adobook-20260910` at `51c42370c643e28edac26ca1c41703ec90abc3b7` |

The two commits after the ChemAIst source archive change only the migration handoff and gitignore. The six mechanism modules named below have identical Git blobs at source and checkpoint. Their installed 0.12.20 package copies were independently hashed and match those source blobs. This proves those six files' provenance, not execution of the installed 53-tool catalog or acceptance of its outputs.

The current diagnostic branch already contains source lifecycle repairs, MIT licensing/third-party notices, and a native-disabled preview. Its single exposed tool is `chemdraw_companion_status`; the historical five-tool design is not the implemented catalog. The native controller's default/legacy paths refuse dispatch, and its opt-in draft.2 path does not provide a production native backend. The historical operational baseline remains `b9363abfce19481d33e8d6409cb3d8d7dd477310`. Neither claiming that all current runtime source is unchanged from b936 nor treating preview2 as native acceptance is correct.

## One authority and three capability boundaries

Target architecture, not the currently exposed diagnostic tool catalog:

External Agent -> Companion's existing small machine interface -> current operation contract or authoritative semantic/depiction plan -> selected pure checks and geometry -> qualified native adapter -> editable document, native render, save/reopen and continued edits.

- **Existing-document local editing:** native object snapshots, owned PID/document/revision, explicit target and operation receipt. Caption repositioning preserves text/style/chemistry and verifies geometric differences. It does not require whole-mechanism proof or regeneration through IR.
- **Mechanism generation:** current IR v0.2 in `contracts/ir_v02/core.py` is the chemical authority. Its immutable inventory, display roles, omission reasons, selected LP slots, state occurrences, ports and separated hashes feed lowering and Composer. Native observations retain their actual evidence sources and unknown values. Expected IR is comparison data, not a way to fill observed fields.
- **Blind reconstruction and research:** separate frozen input, exposure ledger and independent evaluation. Historical standards are unchanged; partial evaluation cannot award full visual PASS.

The `contracts/paired/depiction_semantics.py` implementation is evaluator-side code, not a second generator/compiler. Legacy Scene/sequence/parser classes must not become another authoritative chemical model. Any independent overall target must be supplied separately before generation; comparing a candidate to its own final state is not an independent target check.

Machine Interface Only remains mandatory. Content read/write uses native API/COM/object models or verified structured CDX/CDXML adapters, bound to real objects. No mouse, keyboard macro, menu/UI Automation, clipboard, screen-coordinate or foreground-focus fallback. Missing capability returns unsupported/needs_interface. Native exports may inform semantic feedback; executing that feedback still uses verified object references. Native render, desktop display, machine editing and true headless support are separate claims. Windows session/environment prerequisites remain explicit.

Read [the current lifecycle record](https://github.com/saigyujikingyo-png/chemdraw-companion/blob/6949b139899ac44fe5e5200b76060b2535a5e145/LIFECYCLE_RECORD.md) and its draft.2 output contract before implementing any later operation. Preserve intent-before-effect, exact binding, revision checks, timeout reconciliation, uncertain attempts and first failures. Do not replay relative moves after a timeout or treat closed.json as process-exit proof.

## Module inheritance decisions

All legacy source references in this table are relative to `src/mcp_chemdraw_agent/` at **7724a940d402c84675af372bbaef0472231bc72a** (also byte-identical at 51c42370 for the six main modules). Companion contracts are at **ae7ae011967b51e403dced71c948bd6a2e730dd1**, runtime/adapters at **6949b139899ac44fe5e5200b76060b2535a5e145**. Those commits are the precise comparison basis, not acceptance labels.

P0 means the next product reliability work; P1 means minimal semantic inheritance after that; P2 means optional later baseline work. License/provenance conditions in the following section apply to every row.

| Source / functions | Companion correspondence | Value, limitations and dependencies | Decision / priority | Minimum new verification |
|---|---|---|---|---|
| `mechanism_display_projection.py:12,39,86`: StateProjection, project_sequence, validate_projection | core.py `_depiction`, `lower_depiction`; immutable species inventory and omission reasons | Full ledger versus visible/omitted view is useful. Old selection uses changed non-H atoms, maximum heavy-atom principal and active-flow structures; it can override explicit depiction intent. Ledger uses Counter but visible/omitted checks use sets. Depends on legacy sequence/Scene keys. | **Adapt invariants / P1**; do not copy the model or automatic principal heuristic | Explicit intent wins; visible/omitted partition by species occurrence and multiplicity; no active endpoint silently omitted; input chemical hash unchanged |
| Same file `compact_formula:61`, `transition_products:74`; `mechanism_sequence_layout.py:_structure_key:72` | Existing typed identity, chemical/display hashes | Formula is not species identity; isotope/radical and LP are not complete in these keys. Mapping IDs are included, so distinct mapped species are not universally collapsed. Key/set logic still cannot independently prove multiplicity. | **Baseline only / P2** | Duplicate visible occurrence, missing occurrence, LP change, isotope/charge distinctions; never use formula as identity |
| `mechanism_sequence.py:state_signature:33,_overall_states:56,compile_mechanism_sequence:96` | core.py `_state_data`, `_flows`, `validate_mechanism`; optional independent sequence-target check | Adjacent-state continuity and caller-provided overall initial/final checks are useful. Old path has a restricted parser, 2–8 steps, 120 atoms/12 structures and explicit mapped-H rules. | **Adapt checks / P1**; no second sequence IR | Chemically continuous but wrong final target; wrong initial target; changed species count; reordered steps. Target provenance independent of candidate |
| `mechanism_compiler.py:44,168,238,295,346`; `native_chem.py:implicit_hydrogens:413` | core.py electron-flow compilation and current qualified native observers | Legacy compiler mixes semantics/coordinates; mapped bracket parser, limited elements, no aromatic/isotope/stereo coverage, inferred closed-shell LP, no general attached-H change. Python `native_chem` is not a native API observation. | **Do not migrate parser/H authority / P1 exclusion** | Preserve current 118-element identity separately from qualified chemistry/native coverage; unsupported stays explicit; no H profile expansion |
| `mechanism_scene.py:ElectronArrowGeometry:155`; `mechanism_layout.py:706–718` | core.py `compile_electron_flows`, `lower_depiction:418`; runtime `arrow_ports.py` | Useful separation of source_ref/sink_ref from source/start/control1/control2/tip/target. Legacy structure:index refs are not current state-occurrence identities. Geometry depends on old Scene/style. | **Adapt representation / P1** | Bind typed atom/bond/LP/formation ports first; wrong state/ref and duplicate LP spending reject; retain legal nonendpoint sinks and virtual LP cases |
| `mechanism_layout.py:509–518,561–568,879–923,1048–1119` | Selected LP slots and native port/glyph measurements; Quality Oracle | Old flow creates LP dots per atom source without independent selected-pair inventory. SVG marker triangle and estimated font/charge boxes are renderer-specific. Scene may force 8 pt. | **No migration as semantic inventory or visual oracle**; geometric ideas baseline / P2 | Preserve explicit visibility/pair intent; requested/effective styles separate; native visible head/LP/charge ink remeasured after authorized native capability work |
| `mechanism_continuous_layout.py:104–178,267–399`; `mechanism_sequence_layout.py:85–110,553–567` | Composer `prepare_components`, `pack_panel`, `compose` and rigid common-scaffold alignment | Reuse of shared-state coordinates is useful. Old layout chooses 4 columns for 7–8 panels, otherwise at most 3; grows canvas; auxiliary placement/order depends on indexes/first link. Current Composer preserves physical page/style and rejects overflow. | **Baseline only / P2**; adapt occurrence/reference auditing if missing | Permute IDs/input order; vary panel count/page size; overflow refusal; shared scaffold consistency without shared native object ownership |
| `mechanism_layout.py:_electron_arrow_geometries:464,_leaving_group_direction:854`; sequence layout `_clear_arrow:172,_route_arrows:316` | Composer `route_flows`, annotation geometry and independent verification | Collision rejection ideas useful; old routes include leaving-group/vertical-heterolysis assumptions, fixed angles/distances, 33-sample checking and greedy order. | **Adapt generic rejection only / P1**; route generation baseline / P2 | New ordinary synthetic negatives: text/bond/head overlap, degenerate bends, crossing and wrong port; order/rotation robustness; retain first rejected scene |
| Sequence layout `_segment_box:130–144` | No equivalent finite-segment/AABB clipping function found in inspected composer/annotation/ports/verification files | Small pure interval-clipping function; no SDK/RDKit/Scene dependency. Contact counts as collision; 1e-12 near-zero direction threshold needs explicit numerical contract. | **Direct reuse eligible, conditional / P2**; extract only if an actual gap requires it | Independently test finite/degenerate/parallel/touching/disjoint segments, scale behavior and non-finite refusal before adoption; no code copied this consultation |
| `mechanism_renderers.py:render_mechanism_cdxml:148`; `mechanism_sequence_renderers.py:52–289,356–552` | `adapters/chemdraw_cdxml.py:read_geometry,materialize` and native readback/reopen | Adjacent-state fragment references useful. Old step serializer omits layout LP and full SceneAtom H semantics, ignores charge glyph placement and rounds coordinates; self-XML parsing is not native roundtrip proof. | **Adapt reference integrity only / P2**; no drop-in serializer | Capability-specific LP/H/charge/arrow identity and fresh native reopen evidence after authorization; never infer omitted-field correctness |
| `tools.py:render_mechanism_step:1378,render_mechanism_sequence:1442 (artifact writes:1513–1547)`; `models.py:83–91` | Existing draft.2 operation receipts, status schema, artifact hashes | Hash/bytes/manifest-last ideas useful; old open-source-fallback result also says backend=native; plain dataclasses not output schemas; failure cleanup may delete first artifacts. | **Adapt manifest discipline / P0 as needed**; do not migrate 53-tool registry, AgentCore/REST/platform/launch helpers | Actual producer structured result and text fallback agree; native/per-stage evidence explicit; preserve failed output; exact artifact bytes and host delivery separately verified |

A bounded, newly constructed in-memory characterization extracted only three pure functions from the pinned source by AST; it imported no legacy package and read no old fixture bodies. One single-atom record passed normally, but a duplicate identical visible occurrence and a visible-only LP change also passed the old projection validator. This demonstrates those validator limitations, not failure of every old pipeline and not a chemistry/native acceptance test. No legacy suite was run.

## Port and geometry mapping

Map old source_ref/sink_ref to current flow ID plus state occurrence, molecule/atom or bond, selected LP index when applicable, and typed chemical port. Legacy source and target are computed geometric points, not semantic identities: source can be an LP-pair center; target can be an atom anchor or the midpoint of a depicted bond line. Legacy tip is the candidate cubic endpoint, alongside start/control1/control2. Preserve semantic references separately and distinguish this planned endpoint from the native-observed visible arrowhead tip. A renderer may place the visible head beyond its spline endpoint.

LP inventory, selected displayed slot and virtual LP are separate. Charge is chemical state; glyph position is depiction. Do not infer a displayed pair merely because a flow starts at an atom. Equivalent LP display numbering is not itself a chemical mismatch. Preserve unknown native H evidence instead of inferring it from legacy valence formulas.

All old SVG arrowhead dimensions, glyph/LP/charge boxes, font widths, clearance values and bend thresholds require native calibration. The continuous-layout validator's constant `minimum_curve_gap_pt=0.8` is not a measured minimum. Current native render is the visual measurement authority. Per-metric tolerances remain independent; no global tolerance relaxation.

## Rights, provenance and historical results

Pinned ChemAIst source is MIT; retain copyright/permission notices for substantial reused code and inspect its NOTICE obligations. Current Companion diagnostic source also has MIT/third-party notices. This consultation publishes decisions and symbol references, not private source files. MIT source licensing does not grant redistribution rights for private data, images, fonts, coursework, accounts, paths or protected examples. Review each proposed migration's source license and data provenance separately.

Do not import the complete optional RDKit/resvg/document/Origin/NMR dependency graph for a few pure functions. Spectroscopy/data/report code and legacy AgentCore/REST/catalog remain outside this migration.

The historical ChemAIst migration receipt reports a 549-test run with one failure and seven skips; that is neither all-pass nor current native proof. Its open-source fallback is not native execution. Existing user-rejected figures cannot become gold, a professional visual oracle or unseen tests. Companion Agent Edit Loop v0.1 remains PARTIAL; M1 visual acceptance has not passed, M2 is unscored/frozen, Gold remains 0. The 055/P0-B failures and offline-replay distinctions are retained. Source, synthetic tests, scripts, actual Agent calls, native execution, visual inspection and human acceptance remain separate.

Preview1 historical portable execution: 80 run, 79 passed, 1 skipped. Preview2's relevant rerun: 36 run, 35 passed, 1 skipped; earlier lifecycle evidence is not a new rerun. Installed-file integrity and official discovery do not establish an actual model tool call, native edit loop or human acceptance. This consultation ran no product regression suite, native operation, training or hidden evaluation.

## Optional Local Perceptual Critic boundary

This is a future replaceable ranking interface, not a product dependency or scheduled experiment:

1. Current IR/Composer generates candidates with immutable chemical/depiction hashes.
2. Hard semantic and geometric qualification rejects invalid candidates.
3. An authorized adapter produces native local patches with object/revision/render provenance.
4. A selected ranker scores only qualified candidates; it may abstain or reject all.
5. The owner rebinds the chosen semantic operation to current native objects/revision and executes it through the existing machine interface.

Minimum input: candidate IDs; source/revision, semantic/depiction/geometry hashes; qualified checks; native build/style/calibration; patch hash and document-to-patch transform; data-role/lineage/exposure; allowed resource budget. Minimum output: candidate ID/rank, score or null, reasons, uncertainty/abstention, backend/version and measured time/resource use. Images and patch coordinates never become a GUI write interface.

Geometry baseline, Gabor/orientation features, ordinary embeddings and FlyVis must share candidates, splits and evaluation. FlyVis is only one unproven backend. No valid candidate means refusal; a score cannot override chemistry or provenance. Stop on role uncertainty, missing native calibration, budget exhaustion or no measurable advantage over baseline. Start with one frozen model, small batch/short sequence; no automatic expansion to full-network training.

M2, descendants, unseen holdouts, 055 hidden target/IDs/geometry and hidden corrections are forbidden for migration tests, feature extraction, training, threshold selection and visual reference. Screen roles before content access. Unknown-origin examples are quarantined, not renamed into eligible data. No FlyVis/FlyForm installation, model download, training or experiment occurs in this consultation.

## Ownership, delegation and implementation order

The existing local Product Max owns product architecture, code, tests, releases, native execution and necessary bounded delegation, subject to the existing freezes. The Ultra is consultation-only and exits after verified takeover. The former remote Max exits after a safe checkpoint and takeover. Future remote tasks are temporary executors, never a second product owner. Shared Governance and unrelated products are untouched.

The user authorizes the local Product Max to create, track, review and archive bounded remote Max tasks when needed for frozen FlyVis inference, offline native-patch features, small ranking heads, common-baseline comparisons or a recorded small project GPU POC. This authorization survives the old tasks' archival. Each task needs exact objective/source/input, permitted directories, exposure scope, output/acceptance, budget and stop conditions; separate workdir/worktree; one unfinished task per experiment by default. Reconcile uncertain creation before retry. The executor may not delegate further.

This excludes paid cloud GPU, subscriptions, unlimited training, account/security changes, unrelated products, protected data, installed-product replacement and lifting native freeze. Supported tool confirmations still apply. Permission is not a working connection: exact remote device, task creation route and actual Max configuration must be verified. Current remote read/message capability was observed; new remote task creation was not tested and no such task was created.

Implementation order:

1. Finish the current machine-interface workflow's necessary reliability and actual host/model evidence. Preserve native freeze; the first narrow action may verify the existing diagnostic tool through a real Agent call, with a truthful separate receipt. Native requalification requires its own reviewed authorization; do not enable it through this architecture decision.
2. After that, add only missing projection/multiplicity invariants and independent sequence-target checks to current IR, with new ordinary controls. Then adapt typed port geometry where a concrete gap remains.
3. Consider legacy local geometry only against a demonstrated current gap and new generic tests. Do not migrate old Scene/compiler/serializer wholesale or change Composer thresholds to fit historical figures.
4. Consider perceptual ranking only when qualified native local candidates, data separation and a bounded baseline comparison exist.

No automatic PR merge, runtime migration, native resumption or experiment follows publication. Update current entrypoints to this decision while leaving old receipts and branch history intact. Actual takeover and archive results live in the private handoff record.
