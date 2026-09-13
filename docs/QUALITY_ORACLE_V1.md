# Quality Oracle v1

Phase: Quality Oracle + Gold Correction Corpus, 13 September 2026. Status: first protocol, schemas and bounded executable pixel-metric prototype. This is not a qualified production vision system, Composer acceptance, a native execution, gold collection or training. The accepted c92a918 R&D checkpoint remains a failed native-quality result; the current prototype does not patch its runtime call sites.

## Evidence hierarchy

Final ChemDraw native render is the visual observation to evaluate. Preserve its original bytes with CDX/CDXML and native readback, effective styles, execution journal and measured pixel scale. Abstract spline endpoints, intended coordinates and successful saving cannot replace visible pixels. Native geometry supplies object identity and chemical attachment; it is not independent chemical approval.

The implementation evaluates an observation request against a **separately supplied reference file**, an independently versioned policy and a hash-bound calibration. The candidate cannot select target coordinates, LP directions, scaffold positions, a larger tolerance or its own calibration allowance. Reference IR hash, frame and object/semantic bindings are checked; altered candidate reference fields are rejected. The caller must control reference selection and custody. Hash consistency alone does not authenticate a reviewer or prevent a caller from choosing an inappropriate reference.

Reference positions and allowed angular sectors must come from independently reviewed annotations or a qualified native readback/port extractor for this exact molecule occurrence. They must not come from an LLM guessing page coordinates or from the candidate's erroneous arrow. M1 is now allowed development data with retained exposure; this does not make a Composer-generated target its own reference truth. M2 and descendants remain locked.

## Eight separate measurements

Lengths are normalized by an independently established native bond scale B. Pixel and calibration uncertainties propagate conservatively. Each metric has its own threshold; a single weighted average or global tolerance cannot offset a failure.

| Metric | Measurement | Independent policy and no-pass cases |
| --- | --- | --- |
| Visible arrowhead tip to target port | Locate a unique actual apex in an observable complete head layer; measure to the semantically bound atom/bond/LP port for the correct source-state occurrence. Retain intended approach direction in the qualified extractor/reference. | Separate tip distance limit. Never add head extension to the acceptance limit. Ambiguous/clipped heads or unsupported ports are unmeasured. |
| Visible arrow tail to source port | Identify the other end of a connected, open, unbranched shaft; bind the particular donor LP slot or source bond. | Separate tail distance limit. A spline's first control point is not a visible-tail observation. Closed/branched/self-crossing shafts do not pass. |
| LP quadrant and orientation | Detect both dots; measure atom-to-pair direction and the two-dot axis independently, in the atom's local bond frame. | Separate radial and dot-axis angles plus allowed sectors. Whole-page rotation must not change the local quadrant. Single/merged dots or uncertainty crossing a sector boundary are unmeasured. |
| Ink clearance | Measure actual nearest ink between bond, label, charge, LP and arrow objects, with error bounds. | Arrow/arrowhead clearances and ordinary-object clearances are distinct. Any exception requires a specific semantic object pair and a bounded legal contact region; v1 does not implement general exceptions. Missing objects cannot improve the score. |
| Curve bend severity | On a pixel-supported centerline, report arc/chord ratio, maximum excursion/B and total turn separately; a later qualified extractor adds curvature-radius and stable smoothing diagnostics. | Each component has its own ceiling. The cached path must cover the visible shaft and be supported by its pixels; shortcuts, branches and loops cannot pass. No LLM-generated control-point score substitutes for ink. |
| Arrowhead/glyph overlap | Inspect complete independently observable head and glyph layers, intersection and signed/visible gap. | Zero visible-colour intersection is not evidence of zero hidden overlap. Mutually exclusive colour partitions remain unmeasured for absence of overlap; discovered overlaps fail. |
| Step spacing | Project complete state ink along the declared reading direction; measure gutters and row turns with connector ownership kept explicit. | Minimum/maximum step gap are independent. Registered state objects cannot be omitted. Complete native inventory, condition text and snake order still need qualification. |
| Common-scaffold consistency | Use one fixed identity mapping on an unchanged common subgraph; fit only proper rigid translation/rotation and report RMSD, maximum residual and orientation error. | No fitted scale, reflection or per-atom remapping. The prototype recomputes synthetic isolated-marker centers and rejects stale position caches; a qualified native atom-position extractor is still missing, so native scaffold observations remain unmeasured. Fewer than three non-collinear points are insufficient. Rotation fitting cannot conceal a required common orientation. |

The checked-in policy-v1.json contains **provisional engineering values**, not empirically validated aesthetics or universal chemistry conventions. Its hash is part of each request/result. Human-reviewed development references must qualify or revise a new policy version before automatic acceptance; evaluation data must never drive that selection. The eight policies remain separate even after calibration.

## Measurable does not mean acceptable

Report four independent outcomes: chemical correctness, native editability, visual quality, human acceptance. The corpus IR checker provides only its implemented closed-shell bookkeeping result; it does not establish scientific mechanism plausibility. Editability requires actual independent save/reopen and observed changes. A human visual rejection survives all automated passes. Missing active correction time stays null.

For an upper limit, an uncertainty interval entirely inside passes, entirely outside fails, and a straddling interval is unmeasured. Apply the dual rule for minimum clearances and both bounds for spacing. Missing/ambiguous observations cannot be averaged away. Known hard visual failures reject the candidate even if other measures are unavailable.

The minimal executable always leaves overall native visual acceptance unverified unless it has found a failure, in which case it records failed. It can return pass_measured_subset for synthetic or bounded metric controls. This is intentional: no trusted native object-layer exporter, receipt authentication, complete native inventory admission, full occlusion recovery or gold-qualified policy has yet been implemented. Native execution and real human approval are never created by this validator.

## Native measurement and annotation pipeline

1. Save immutable first and final native artifacts; bind IR, source occurrence IDs, native IDs, full document/readback hashes, effective style, measured scale and final PNG to the execution record.
2. Enumerate all drawable objects from native readback and reconcile them with the semantic graph. Detect additions, losses, duplicates, unknown objects and missing conditions/charges/LPs.
3. Obtain independently observable object layers, or native colour diagnostics with confirmed colour-only changes, registration and full silhouette checks. Pixels from a single colour partition cannot prove absence of occluded overlap. Preserve every unresolved attribution.
4. Recompute segmentation/features from authenticated native renders. Cache tips, tails, bounds and paths only with their source hashes and compare them with fresh extraction. The prototype recomputes pixels from object-layer PNGs and verifies their union against the final render, but does not authenticate how those layers were produced.
5. Supply the reference table separately from the candidate. Review target/source ownership, angular sectors, unchanged scaffold and native coordinate frame. Bind review to exact assets, policy and output revision; stale approvals cannot transfer to edited images.
6. Run per-metric checks and retain overlays, raw measurements, intervals, failures and missing coverage. Optimize Composer only against qualified development supervision. Re-run independent native output after a change; never overwrite the first failure.

The prototype has a bounded unique-apex detector, a shaft topology check, fixed pixel sampling/workload caps and exact reference/hash validation. Centerline-based bend metrics remain a constrained cache check, not a general raster skeleton/curvature solution. General legal-contact exemptions and prospective-bond target extraction are unsupported. A manifest claiming native origin or complete inventory cannot elevate these limits.

## Calibration trust and P2

calibration.py loads the exact bytes it hashes; it verifies finite values, declared native build and all eleven style fields, including stroke and complete head dimensions/type. It derives a bounded extent from measured size and uncertainty, but that extent is **never added to tip or tail thresholds**. The original c92 runtime/probe still needs the corresponding integration fix on its own branch. New prototype tests do not close that existing P2 by implication.

## Artifacts and use

- [Observation schema](../contracts/quality/oracle.schema.json), [independent reference schema](../contracts/quality/reference.schema.json), [result schema](../contracts/quality/oracle-result.schema.json), [per-metric policy](../contracts/quality/policy-v1.json), [calibration schema](../contracts/quality/calibration.schema.json).
- [Pixel validator](../contracts/quality/validate_quality.py), [adversarial plan](ADVERSARIAL_NEGATIVE_PLAN_V1.md).
- [Gold correction protocol](GOLD_CORRECTION_CORPUS_V1.md), [correction-record schema](../contracts/quality/correction-record.schema.json), [correction validator](../contracts/quality/validate_correction.py).
- [Current split policy](GOLD_SILVER_HOLDOUT_V1.md) and [20-50 sample strategy](GOLD_SAMPLE_STRATEGY_V1.md).

Development execution requires Python with jsonschema, NumPy and Pillow. Reuse the configured scientific runtime and isolated dependencies. No daemon, MCP, installer, host adapter, training service or user-facing programming setup is added.

Run the pixel validator with an independently supplied reference: python contracts/quality/validate_quality.py CASE.json --reference REFERENCE.json. Exit 1 records invalid evidence or a known visual failure; exit 2 records unverified/unmeasured native acceptance, including synthetic positives. It never exits 0 to certify a native figure in this version. Run correction validation as documented in the gold protocol. Tests run with python -m unittest discover -s contracts/quality -p 'test_*.py'.

Synthetic fixture generation is explicit and refuses an existing output directory. Test images and geometric annotations are never native ChemDraw renders, gold labels, M2 variants or training data. The adversarial receipt identifies which measurements were actually exercised and which native qualification gates remain outstanding.

The [first-delivery verification](QUALITY_ORACLE_V1_VALIDATION.md) records actual checks and remaining native gates; the [synthetic controls](../examples/quality-v1/README.md) are separately reproducible.
