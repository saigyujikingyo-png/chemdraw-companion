# Issue #2 paired corpus and blind reconstruction execution receipt

13 September 2026. **Research delivery completed with an observed technical blocker. The full external reconstruction pipeline and ChemDraw product acceptance have not passed.**

This is an actual external acquisition and reconstruction attempt, not a synthetic demonstration. The [machine-readable receipt](../../verification/2026-09-13-paired-pilot/pilot-execution-receipt.json) binds the private artifacts. The [source survey](../PAIRED_MECHANISM_CORPUS_SURVEY.md) supplies citations and source coverage.

## Measured outcome

| Stage | Observed result |
|---|---|
| Acquisition | 77 unique CDX drawings with arc/curve objects, 64 exact author EMF pairs, 12 AI-screened mechanism candidates containing 114 electron-flow arrows. |
| Native targets | All 12 produced CDXML/CDX/native PNG/native JPEG in ChemDraw Prime 26.0.0.6141. All 72 original exported file hashes/sizes and 168 current manifest bindings, including fresh-process evidence checked. |
| Independent disk reads | Each saved format reopened in its own fresh zero-document PID/HWND instance: 24 instances, 24 verified input hashes, 24 verified new readbacks. Original outputs unchanged. |
| First PNG-only inference | Terra max returned no recoverable chemistry. Native PNG RGB is black; all shape information is in alpha. Failure retained. |
| Authorized white-background retry | Same dimensions/layout and zero changed ink-mask pixels. Terra max produced schema-valid IR: 17 catalog atoms, three states, two transitions, six electron flows. |
| Existing Composer | Unchanged IR actually submitted to the verified c92a918 seed entry. Exit 1: Element outside the declared semantic scope. Existing H/C/N/O support rejects Br and K. |
| Candidate comparison | No seed or candidate native artifact exists. Object, geometry and native visual comparisons remain unmeasured. Blind-candidate correction deltas = 0. |
| Semantic review | AI-assisted comparison supports the five-membered-ring scaffold, hydrogen transfer and intended six flows. Bounded state/bond/charge bookkeeping agrees; this is partial recovery, not full chemical PASS. |
| Prototype validation | 77 current paired tests pass, no skips. Twenty-four real native roundtrip controls produce 104 unique fragment matches and 1,042 fragment/atom deltas, solely as parser/evaluator controls. |
| Human and benchmarks | Active human correction time null; gold = 0. Task B not run. M1 not rerun; M2/derivatives/unseen holdouts excluded, frozen and unscored. |

Reopening is not lossless by default: IDs, small coordinates, text counts and one CrossingBonds property differ. Old same-process Close/Open evidence was downgraded after the existing developer found cached COM identity. Fresh-process evidence supersedes it. Native pairing alone does not prove object editing or visual quality. All twelve PNG headers encode approximately 191.9986 DPI despite requesting 600 DPI; calibrated effective physical scale is not established.

## Isolation and immutable evidence

The model received one PNG, the public runtime IR schema and a reaction-independent instruction in a fresh API context with no tools. A restricted broker plus allowlisted official API projection excludes hidden targets and prior task history. Actual OS probes denied six hidden categories; eight OS tests and fifteen projection/serialization tests passed. The custodian/evaluator can read targets, so this is not a claim of whole-host or operator isolation.

Both calls used GPT-5.6 Terra with max reasoning on the existing official backend and had separate explicit user approvals. The second projected request differs only in the PNG data URL. The fixed-white alpha composite is native-derived display normalization, not a direct native export or layout repair; all original native bytes remain immutable.

| Asset | SHA-256 |
|---|---|
| Original native PNG | 9c501f09c5ca98389cb970038dab84306356667ca43197894cbaa097075ebf27 |
| Authorized normalized PNG | 0f0fc8449049e785c4387f1908e9ddd78efeebd016d3c4254343fbee606f3538 |
| Runtime IR schema | 619e46a20c20e9e5906b2298041379a8a832e310632a8a6bdc05d9174e7b2d2c |
| Second candidate IR file | 093048ab3fb1f5e3a92f2fe41b25b567d7c205550cdf1bcf64cde59197577efc |
| Independent semantic review | 55937ff519634c00be7f483026418cfceb9577a66e18169ffbaf4c54d4129468 |

The first call consumed 5,041 tokens; the retry consumed 45,032, including 38,629 reasoning tokens. No further inference was made during parsing or review. The retry's original UTF-8 text SHA is 513fb32a0206a81e73c7741171268c18bbe0a4047118175670aeb20fd9f8c794; Windows LF-to-CRLF writing explains the stored-file hash difference. Both are retained, and the candidate was not rewritten. First-call parsing recovered completed SSE output-item text from the same response. Code snapshots are post-run, with an explicit parser/serialization addendum; no pre-run cryptographic code attestation is claimed.

## Latest implementation and supplier evidence

The existing implementation task subsequently published [402a31e](https://github.com/saigyujikingyo-png/chemdraw-companion/commit/402a31e2e5f36faaa088e4013e88eb99fa8bbdf5), adding only two generic probe entrypoints. The receiver retrieved its 213,022-byte private control ZIP and verified all 80 content-manifest entries; these are supplier synthetic controls, not external blind results. The receiver also verified 237 Git blobs in a separate execution snapshot and ran the same immutable external request through the new entry once. It again exited 1 at seed with the same element-scope error; no native fragment, compose or native candidate stage ran. No additional inference occurred. The [independent latest-interface check](../../verification/2026-09-13-paired-pilot/latest-interface-checks.json) records this result.

One receipt-field inconsistency remains in that new wrapper: input_semantic_validation says not_run on seed rejection, although stderr proves semantic validation was attempted and failed. The independent receipt records the observed rejection without rewriting the producer's original record. No acceptance claim relies on that field.

## Observed blockers and remaining uncertainty

The executed blocker is semantic support before geometry generation. Removing Br/K, changing the reaction or substituting a synthetic sample would invalidate this attempt. Executed runtime files were independently matched to their c92a918 Git blobs.

Static review additionally found a bond-to-nonendpoint-atom flow incompatible with the current migrating-bond rule. The intended new bond is declared elsewhere, but its compilation is unresolved. This second error was not executed past the element guard.

The model includes chemically reasonable K+, bromide, tert-butanol and full lone-pair inventories. The source omits some species, displays selected LPs, abbreviates fragments and uses KOtBu/HOtBu condition captions. Current runtime IR/Composer conflates chemical inventory with depicted visibility. A general representation for per-state visibility, displayed LPs, abbreviations and typed condition roles is needed; merely extending the element list will not solve this.

No candidate native render exists, so its greatest geometric error, visible port accuracy, ink clearance and human correction time are unknown. The evaluator currently implements unique fragment translation/rotation and atom displacement. Arrow/LP/text/spacing correspondence and calibrated native ink measurements are not integrated. Unit tests and roundtrip deltas cannot replace those missing measurements.

## Answers to the Issue #2 research questions

**Can professional CDXML/native renders teach Composer automatically?** They are feasible partial structured teachers: twelve real drawings were recovered and rendered, and object/geometry extraction is executable. Reliable end-to-end semantic and visual teaching is not yet established.

1. **Valuable structured samples:** 12 selected real mechanism candidates; the wider 77-file arc/curve pool is not 77 accepted mechanisms.
2. **Real curly electron arrows:** all 12 selected candidates, 114 AI-screened arrows; no human gold claim.
3. **CDXML/native PNG pairs:** 12 hash-bound pairs with fresh disk-read evidence and documented fidelity limits, not lossless-editability or quality certification.
4. **PNG-only semantics:** one sample recovered its main scaffold, hydrogen transfer, three states/two steps/six intended flows after authorized alpha normalization. Syntax and bounded bookkeeping pass; full chemical correctness/generalization remain unproven.
5. **Largest candidate differences:** native geometry/visual differences are unmeasured because composition failed. At IR level, chemistry support, flow compilation and chemical-completeness versus visual-depiction policy are the identified issues.
6. **Replace most manual correction:** not demonstrated. Extraction and limited deltas can reduce clerical work; ambiguous correspondence, semantic interpretation and native visual calibration remain unresolved.
7. **Expand corpus or modify Composer first:** modify the general IR/compiler/depiction and native-oracle integration in the existing implementation task. Use the twelve exposed targets for bounded development, then complete a real candidate comparison before expanding to 100+ samples. Keep M2 and holdouts isolated.

## Delivery and continuation

Delivered: four phase documents; registry/provenance/hidden-split/evaluator/correction-delta schemas; actual inventory/manifests; target extractor and partial hidden evaluator; deterministic alpha normalization; OS/API leakage tests; native pairing evidence and this execution receipt. Existing native adapters were reused. Research drivers and raw author/native/model assets remain private.

The existing developer task retains the native lifecycle and Composer implementation. No new user-owned development task, installer, MCP surface, host expansion or model training was introduced. Transport remains a prerequisite; explicit object control and high-quality mechanism composition/native visual supervision remain the unresolved architecture work.
