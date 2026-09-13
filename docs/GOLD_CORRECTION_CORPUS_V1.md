# Gold correction corpus v1

Status: evidence contract and workflow design, 2026-09-13. This delivery collects no samples, authenticates no humans, runs no native software and trains no model. The schema version is `gold-correction-record/1.0`; it is separate from the existing runtime and `contracts/corpus` profiles. Apply the current [split policy](GOLD_SILVER_HOLDOUT_V1.md) and [sample plan](GOLD_SAMPLE_STRATEGY_V1.md).

## What one eligible correction record contains

Preserve the first proposal and a distinct final revision. Each snapshot binds its Mechanism IR, CDX, CDXML and at least one native render by immutable path, byte count and SHA-256. Every native render carries `render_provenance`: `native_asset_ref`, `native_sha256`, `revision_id` and timezone-aware `rendered_at`. Its single declared native parent must belong to that snapshot. First/final render IDs and resolved file paths cannot overlap; gold also requires distinct first/final render bytes. Relabelling or reusing the first image does not prove a new native render. Different metadata or hashes alone do not authenticate a real native original. Both native formats must have different first/final bytes for correction eligibility; a serializer difference alone is insufficient. No final output overwrites the first attempt or earlier failures.

Four format-specific readback assets describe first/final CDX and CDXML after disk reopen. Each embeds its source native hash, revision, format, common coordinate frame and complete object inventory. The record's typed readback payload must equal the hash-checked JSON file. The coordinate unit is points; upstream normalization and native-to-page transforms must be evidenced by the producer, not guessed by this validator.

Object correspondence covers every recorded native object exactly once in all four inventories. Stable semantic references identify state occurrences; captions may have separate presentation identities. Native numeric IDs alone are locators, not chemical identities. Within each stage and native format, primary objects are injective by `(kind, semantic_ref)`; two primary atoms cannot claim the same state occurrence. Separate LP slots need separate LP occurrence references, although atom, charge and LP objects may share an anchor. Captions may have no chemical reference. `representation_role` defaults to `primary`. An `auxiliary` graphic must name its same-kind, same-occurrence primary through native `primary_object_ref` and correspondence `primary_entity_ref`; every auxiliary still requires complete mapping and field deltas. This supports explicit compound graphics without treating their parts as duplicate primary occurrences. Unresolved or ambiguous mapping prevents gold eligibility. A future symmetry exemption requires independently verified mechanism-wide equivalence; v1 does not silently choose a mapping or claim automatic matching.

Every applicable field has a before value, after value and calculated delta, including unchanged zero deltas. Rotation deltas use the shortest signed difference in [-180, 180) degrees; a full turn is not counted as a correction. Required coverage is derived from inventories:

| Object or relationship | Recorded fields |
| --- | --- |
| Fragment | Translation and rotation in degrees |
| Atom, lone pair, charge, caption | Position displacement |
| Bond | Endpoint geometry |
| Electron-flow/reaction arrow | Two anchors and two interior control points |
| Consecutive reaction steps | Step spacing in points |

Missing or extra differences, truncated arrays, double-mapped objects and disagreement between the two formats are rejected. Categories with no applicable object are explicitly `not_applicable`; they are never counted as measured corrections. The declared ordered `step_ids` requires one spacing measurement per adjacent pair. A single-step example legitimately has no interstep spacing.

## Actual review and time

Maintain separate chemical, editability, visual and human-review statuses, their target hashes and evidence. A passed status needs an uncontested independent review of its required assets. Automated review can support silver. Gold eligibility additionally requires human evidence for all four scopes, independent of both proposal author and corrector, and four successful native reopen records. One reviewer may make separately recorded chemical and visual decisions; a chemical pass never substitutes for visual approval. A recorded relevant rejection cannot be omitted from the status references. Review timestamps are compared as timezone-aware events and must follow their required native reopen/readback and render evidence, as well as correction completion. A 2026 decision cannot qualify a readback or render recorded in 2030.

Use actual human correction sessions: start/end timestamps with timezones, active seconds and bound timing logs. Sessions cannot overlap; their decimal active durations must sum exactly to the recorded manual total, fit within wall time and identify the human corrector. Geometry tolerances never apply to time sums. A zero-activity or aborted session can remain in silver evidence, but gold requires an actually positive sum from positive sessions; a positive summary field cannot manufacture activity. Automatic execution time is separate and may overlap wall-clock human activity. Unknown timing is `null`, not zero. A geometry correction reference needs positive measured human active time and a nonzero geometric change. An unchanged figure may be useful elsewhere but is not a correction pair.

Preserve source description/revision, producing software, creation time and license evidence covering every asset. Storage, annotation, training and redistribution permissions are independent. Approved storage and annotation are required for gold eligibility; neither implies training or publication permission. Rights and reviewer identity remain externally verified process facts.

## Validator boundary

Run `python contracts/quality/validate_correction.py path/to/record.json`; local asset paths resolve inside that record's directory. The checker verifies strict field types, finite numbers, file hashes, references, inventory completeness, numerical deltas, scope evidence and timing consistency. Both Mechanism IR assets must satisfy the existing mechanism-ir/0.1 schema; this is schema validation only, not a chemical review or a verified native-to-IR correspondence. A requested gold label fails if prerequisites are absent. `gold_eligible_by_record` means only that supplied records satisfy these rules. The result always reports `identity_authenticated: false` and `actual_gold_collected: false`.

This is not a native parser, automatic correspondence engine, chemistry oracle, full style comparator or production correction-diff engine. It cannot detect a convincingly fabricated source log or human identity from self-declared metadata. An external collection custodian must authenticate the session/review provenance and verify native extraction, IR semantics and publication-size visual quality before adding a gold sample to the corpus ledger. Synthetic tests intentionally manufacture bytes and identities to exercise that boundary; they are never collection evidence. Unsupported objects or geometry require a future profile, not discarded native inventory entries.
