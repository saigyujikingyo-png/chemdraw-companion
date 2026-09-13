# Automatic target comparison v1

The target is a structured teacher candidate, not automatically correct chemistry or authenticated human gold. Only the evaluator can read its native files, inventory and geometry. Use the [blind protocol](BLIND_RECONSTRUCTION_PROTOCOL_V1.md) and existing [Quality Oracle v1](QUALITY_ORACLE_V1.md).

## Extraction implemented now

`contracts/paired/target_extract.py input.cdxml inventory.json` parses bounded CDXML without external entity declarations. It preserves native IDs, parent/page relationships, complete primitive attributes, atom/bond/fragment/text/graphic/arrow/curve/scheme/step records and explicit finite geometry. Duplicate native IDs are rejected. Unparsed values generate warnings rather than synthetic zeros.

Curly-arrow candidates include headed splines, legacy CurveType arrow bits, modern nonzero-angular arrows and headed legacy arcs. Superseded legacy graphics are deduplicated only against a resolvable modern arrow. A broken reference remains visible with a warning. The vendor [Curve_Type specification](https://chemapps.stolaf.edu/iupac/cdx/sdk/properties/Curve_Type.htm) defines the four full/half-head bits. Neither an arc nor a spline automatically establishes electron-flow chemistry.

Explicit charges/radicals/LP symbols and geometry are extracted where present. State order, condition roles, LP ownership, electron-flow source/sink, scaffold correspondence and step spacing remain null unless separately established. Text objects include atom labels; they are not all conditions or captions. CDX is converted through native ChemDraw; this XML prototype is not a substitute binary renderer.

## Four independent layers

| Layer | Required evidence | Current prototype limit |
|---|---|---|
| Chemical correctness | Atom/bond graph, charge/radical/LP, state sequence, roles/conditions, electron-flow ports and bond changes | Conservative explicit graph comparison only; no full chemical PASS |
| Native objects/editability | Source and candidate validity, complete object inventory, native save/reopen survival, editable arrows and semantic binding | XML inventory alone does not establish editability; use separate native journal and diagnostic edits |
| Geometry | Declared correspondence and proper rigid alignment, fragment movement/rotation, scaffold residuals, LP/charge/text/arrow changes and spacing | Unique explicit fragment-graph matching plus fragment/atom deltas; ambiguous/repeated/symmetric graphs stay unresolved |
| Native visual quality | Final native ink, visible head/tail ports, LP orientation, collision/clearance, curvature, head/glyph overlap, spacing/scaffold consistency | Requires measured, hash-bound Quality Oracle packet; spline endpoints are never visible tips |

`hidden_evaluate.py target.cdxml candidate.cdxml evaluation.json` is deliberately partial. It compares exact explicit atom element, charge, isotope, radical and AS fields, and bond order/BS, using a bounded unique graph-isomorphism search. Endpoint-sensitive wedge displays, dangling/self/duplicate/cross-fragment bonds, symmetric alternatives and multiple possible fragment matches are not silently mapped. Repeated intermediates may still require independently qualified state correspondence. Native IDs or object-list positions are never used as a target-to-candidate identity shortcut.

For unique matched fragments, the evaluator computes a 2D proper rigid fit without scale or reflection. It records rotation, origin translation, centroid displacement and residual RMSD. Emitted fragment translation is the centroid delta; atom displacement is separately reported in the unaligned native global frame. One-atom orientation is unmeasured. Per-fragment fitting is not a global scaffold-consistency pass.

The current evaluator contract forbids unsupported final PASS claims; all four qualification gates remain `unmeasured`. Partial measurements, native pairing receipts and an actual negative chemical/visual finding remain separate evidence. Empty dictionaries or matching object counts cannot confer acceptance.

## Correction deltas and correspondence limits

`correction-delta.schema.json` reserves fragment translation/rotation, atom displacement, LP displacement/angle, charge/caption displacement, arrow source/target anchors, control points, curve shape and step spacing. The executable validator accepts the implemented typed vectors/angles and rejects reserved-but-unimplemented delta types. It reports missing kinds explicitly; null is not zero.

Version 1 emits automatic fragment/atom measurements only where graph matching is unique. Arrow, LP, text and step correspondence still need a general semantic/object-binding extractor. A future extension must bind each semantic source/sink independently, compare native arrow geometry under a declared transform and include all control points without interpreting an XML endpoint as visible ink. Ambiguous symmetry and state identity must block the corresponding training label.

All generated deltas are **structured-target automatic correction, silver**. `actual_gold=false` and human active time remains null unless a real human record exists. Do not invent correction time, human identity or provenance. Automatic extraction can reduce repeated geometric annotation, but cannot yet replace target selection, ambiguous chemical interpretation, severe disagreements or aesthetic calibration.

## Validation

`validate_paired.py` checks schemas, exclusion lineage, rights consistency, original-to-asset hash binding, task-specific exposure, required run evidence, finite measurements, coordinate units and optional actual file hashes/PNG validity. Run records require byte verification of the payload and isolation receipt. Structural validity still does not authenticate a renderer, model transport or human reviewer; those claims require independent replay/evidence inspection.

Targeted tests exercise malformed graphs, symmetry, duplicate native IDs, dangling supersession, zero angular size, legacy curve heads, rigid rotation, hash mismatches, false qualification and leakage metadata. Synthetic negatives test the guardrails; only external native artifacts and the blind execution receipt establish pilot progress.
