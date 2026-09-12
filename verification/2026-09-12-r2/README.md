# Native core regression checkpoint R2

Execution started on 12 September and continued on 13 September 2026. This checkpoint implements the corrections requested by architecture review `2abac34977dabdc67e3e5b186980713c23f5d892`, retaining `2cc659771817f9968b8ed09b40b2335e32b0fdc7` and every earlier failure. **This is a diagnostic engineering checkpoint, not P0 completion, a qualified general Composer, a release or a holdout freeze.** PR #1 remains a draft.

## Decision and evidence

| Area | Observed result | Evidence |
| --- | --- | --- |
| Native H, mappings, geometry and style guards | Actual native H/valence, isotope, semantic flow bindings, LP attachment, control ports, containment and text-run sizes are checked. Corruption controls fail. | `historical-m2-new-guards.json`, tests and raw evidence |
| Exact native editing | Fresh CDX and CDXML runs preserve the declared nonzero fragment, curve, LP and caption edits. Complete captured non-target atom/bond/H/stereo/head/type/style fields are checked. | `native-edit-verification.json` |
| Edit false-pass controls | All seven actual-journal mutations rejected: no-op curves/symbols/captions, changed H, changed bond stereo, missing head, and a 0.01 charge change. | `native-edit-negative-controls.json` |
| Native geometry provenance | Native `Clean(true)` receipts bind IR/style/manifest, input/before/output bytes, the exact qualified executable/interop and owned PID/HWND. All seven corruption controls rejected, including a changed text run with a matching forged output hash. | `native-provenance-controls.json` |
| Ordering and geometry replay | Catalog-only, flow-only, reversed bond endpoints, bijective IDs plus shuffled arrays: zero displacement of atoms, LPs, curve controls, connectors or captions. Rigid 37-degree intrinsic rotations differ by at most 3.36e-11 pt. | `metamorphic-report.json` |
| Independent native regeneration | Two-state proton transfer (two flows) and electrocyclization (three flows) each passed fresh native intrinsic-geometry readback and Composer fit. Renamed/shuffled proton transfer was independently regenerated natively and gives zero scene displacement. These are disclosed controls, not holdouts or complete native-page quality tests. | `independent-ir-results.json`, `native-regeneration-comparison.json` |
| S1 | Native graph, H/isotope, input tetrahedral stereo, 8 pt runs, bond scale, exact native edits, containment and full native masks pass. Owner physical-size review remains pending. | `small-native-verification.json`, `small-native-mask-verification.json` |
| R1 | Native chemistry, 8 pt runs, spacing, exact condition-text edits, containment and full native masks pass. Owner review remains pending. | Same |
| M1 | Product O is now neutral and graph/H/edit/reopen checks pass. Full quality fails: attack curve touches a plus caption; a visible departure head touches the Br glyph. Repair 2 was rejected by Composer preflight before native M1 execution. | Same; `repair-budget-receipt.json` |
| CLI failures | Actual no-op editing, default full quality verification and an incomplete small-fixture batch all return exit code 1. The incomplete batch is refused before native isolation or opening. | `cli-controls.json` |
| M2 / freeze / holdout | No new scored M2. M1 quality prerequisite fails. Owner acceptance, freeze and independent unseen-input selection remain not started/pending. Historical M2 remains diagnostic. | `acceptance.json` |

39 logic/regression tests pass on the recorded Python 3.12 environment. PowerShell syntax checks pass. These checks do not substitute for the native execution and preserved files above. Installation, MCP, host integrations, model benchmarks and backend replacement were not expanded.

## Changes to the verification boundary

The semantic checker no longer reads intended IR hydrogen counts as if they were actual native values. It reconstructs H from native explicit counts or the supported native valence representation, binds flows to their pre-transition occurrence, reconstructs native LP/bond/atom ports, checks isotope and containment, and detects native run sizes that override a document default. The generic readback checker still cannot establish final visible arrowhead acceptance without a native mask; its default full gate therefore remains nonzero when required quality evidence is missing. An explicit `--scope readback` selects only the narrower readback gate.

Native editing now records an immutable intent before mutation and checks before -> intended nonzero difference -> independently reopened saved copy. Snapshots include atom H/isotope/radical/stereo, bonds, curve heads/types, symbol types, caption anchor/font/style and step-arrow geometry. Unchanged step arrows may be compared as complete drawable multisets when native serialization changes their IDs; this does not qualify arrow identity or arrow editing. A changed caption may recompute its glyph top, but its anchor and style must remain fixed and the complete edited readback must survive disk reopening. Diagnostic charge/LP deletion copies remain intentionally invalid chemistry.

Receipt verification trusts the executed local worker and journal. It is not cryptographic attestation against an actor able to replace both the executor and its evidence. Raw seeds without a completed matching native receipt are rejected. Native font checks include each text run, not just root defaults. The supported binary scope remains **ChemDraw Prime 26.0.0.6141**, installed interop **22.0.0.0**, with the precise native binary hashes in the receipts.

## General layout ordering and symmetry

Composer 0.2 uses whole-pathway chemical roles and intrinsic labelled geometry to settle component/candidate/routing ties. It does not sort numeric atom IDs for placement. Numeric tolerance settles floating-point angular ties for LP placement. Chemical role refinement is shared by seed generation and Composer; generation imports no benchmark oracle.

The scene comparator checks atoms, LPs, all curve controls, connectors, caption positions and semantic relationships. Equal role hashes alone do not grant an equivalence exemption. A permutation must be one verified graph/charge/H/LP/flow/stereo automorphism across every state. Tests accept a true global spectator exchange and reject an inconsistent state-local exchange. The retained M2 replay passes the strict supplied ID bijection without using a symmetry exemption. Replay of historical geometry and fresh native regeneration are explicitly separate results.

## M1 controlled diagnosis and repair limit

All five initial ablations have the same molecular nodes, bonds, positions and label fingerprint. The original and the case with only curves removed both produce product O(+1) and one warning. Removing separators, or removing both curves and the lone-pair symbol, produces neutral O and zero warnings. This narrows the interaction in this reproducer; it does not establish a vendor-internal parser cause or a universal chemical rule. Original input hashes and all native round trips are in `m1-control-results.json` and the archive.

The first spacing revision corrected chemistry but exposed a separate font defect: native fragments retained 10 pt label runs under an 8 pt document default. **Repair 1** restyled and natively cleaned the fragments at 8 pt and then recomposed them from freshly measured glyph extents. Chemistry and exact edits pass, while full native masks reveal the two M1 contacts described above.

**Repair 2** added measured arrowhead reach compensation and annotation obstacles. Composer rejected the M1 route before writing it. The then-current batch runner nevertheless exported the available S1/R1 files; its `complete` event is not acceptance of the missing M1. That partial batch is retained. The runner now rejects incomplete S1/R1/M1 input before entering native execution. The generic minimum-gap algebra was subsequently corrected and unit checked, but **no further native M1 was run** in this bounded experiment. Two automatic repairs have been consumed. This source therefore contains an unqualified M1 layout change; it must not be described as a demonstrated M1 fix.

## Full native masks and physical review

Each diagnostic CDXML copy changes only primitive colours and is rendered by ChemDraw. Original black PNG/CDX/CDXML/JPEG files are untouched. Chemical/drawable readback must agree (0.02 pt serialization tolerance), every primitive must have native ink, and every silhouette difference must remain within one pixel of counterpart ink. Mask distances use actual nontransparent raster ink, not label bounding boxes. Native bounds constrain colour decoding only. Mixed colours are permitted only inside named intended contacts such as a bonded atom or the declared donor tail. Mask development failures and all earlier reports are retained.

Unrelated label/ink clearance is 0.12 B; arrow-to-unrelated-object clearance is 0.18 B. A head approaching its own label must still have a positive ink gap, and its actual visible tip must satisfy the 0.20 B port tolerance. The M1 mask control demonstrates why the spline control endpoint cannot stand in for the visible head tip. Intrinsic arrowhead extent varies with curvature and must be checked on the final native render; the metrics cache contains no page/state/atom placement coordinates.

`physical-review.pdf` assembles the latest complete S1/R1/M1 native batch on explicitly sized 85 x 42 mm canvases. It labels the M1 failure. Its native source PNGs are 2044 x 1028 pixels with approximately 144 DPI metadata. Placement uses measured native geometry, and the independent 600 DPI ink/ruler calibration from `../2026-09-12-native-control/pixel-scale-report.json` is retained. No padding-only resolution claim, resampling or pixel repair is used. This assembled PDF is not a native ChemDraw PDF export. Print at **Actual size / 100%**; owner and physical-print acceptance remain unverified. Active human correction time is **null**, never zero or automated worker time.

S1 chirality preservation is independently checked for the explicitly supported acyclic SMILES subset using graph matching and local neighbour-order parity, including the virtual H position. Unsupported syntax fails closed. This is not an absolute CIP assignment or a general chemical toolkit. Primary convention source: [Daylight Theory, section 3.3.3](https://www.daylight.com/dayhtml/doc/theory/theory.smiles.html).

## Reproducibility and remaining limits

- `raw-evidence.zip` retains 502 manifest entries, including 186 native output files and exact final execution-source snapshots. All entries were read back and SHA-256 checked; all 12 published native samples byte-match their source files. Fault-injection copies are explicitly classified separately from native outputs.
- `source-audit.json` records final worktree and staged Git bytes. Some earlier R2 workers lack per-attempt execution source hashes; this gap is disclosed, not backfilled. Final object-edit and independent-IR workers capture their executor/helper/bridge hashes. Source inspection is by the implementation owner, not an independent anti-hardcoding audit.
- The full quality verifier is intentionally nonzero for historical M2: native semantics pass, but a retained bounding-box clearance failure and missing full quality/owner evidence prohibit acceptance. No new M2 page was scored.
- Native P0-A transport evidence is retained from the previous checkpoint. Full product isolation/recovery, the remaining object matrix, owner acceptance and host delivery capabilities remain separate unqualified gates.
- Direct architecture-task notification was unavailable from this execution host. The archived relay was not reopened or used. The immutable commit and draft PR are the handoff route.
