# Annotation pipeline and multimodal alignment v0.1

Status: proposed workflow with a partial, ungraded native-alignment example. No annotation service, OCR model, critic, gold dataset or new native execution is claimed.

## Ingestion and authority

Start from a sample registry, immutable revision, lineage/exposure group, per-asset permission record and task mode. Register every available CDX, CDXML, SVG, raster, render and supplementary record before annotation. Store byte hashes, source/version, producer and relationships. Missing formats remain missing. An accessible download or file extension does not prove producer, licence, editability or chemistry.

Treat evidence as different observations: reviewed semantic intent; actual native object/readback state; native rendered pixels; vector observations from a specified SVG producer; and human corrections. A CDX is paired with a separately reopened CDXML readback and execution receipt when available. CDX and CDXML reopen acceptance remain separate.

Frame definitions include page number, units, origin, axis direction, dimensions and calibrated affine transforms. CDXML points, SVG user units and raster pixels are never silently interchangeable. Record SVG viewBox/export scale and glyph transforms in the asset/annotation evidence. DPI metadata alone is insufficient. The schema permits uncertain calibration, but an unverified transform cannot support qualified geometric measurements.

Each correspondence binds semantic occurrences to asset ID + SHA-256 + frame + object locator. One atom may map to several text/charge glyphs, and one native object may render multiple ink regions. Native IDs are valid only within the bound artifact. Reopening or cleanup may require a new mapping; ambiguous graph/symmetry matches remain unresolved.

## Raster-only annotation, in dependency order

| Layer | Record and checks |
| --- | --- |
| Page and reading order | Page/panel/step regions, candidate traversal and explicit ordering relations; preserve competing readings when ambiguous. |
| Molecular graph | Skeleton, atom/bond proposals, element labels, bond order and stereo; use confidence and unresolved alternatives rather than guessing obscured atoms. |
| Participant roles | Bind reactant/intermediate/product/reagent/catalyst roles to molecule/species occurrences and steps. Page position alone is not chemistry. |
| Ordinary reaction arrows | Identify direction/type and associated step endpoints; distinguish these from curly electron-flow arrows. |
| Conditions | Exact OCR/manual text, region and step association; keep original text before normalization and mark uncertain temperatures, units and reagent names. |
| Electronic marks | Charge, radical and LP identity, count and attachment; distinguish absent, intentionally omitted, not visible and unresolved. |
| Electron flow | Detect full/fishhook arrow geometry, then resolve semantic donor/sink in the pre-state; explicitly represent prospective bonds and simultaneous groups. Coordinate-only arrows remain proposals, not valid IR. |
| Visual geometry | Capture native/raster/vector points, glyph bounds and ink masks, final size, arrow orientation, collisions and clearances, with intended contacts identified by object pair. |

A layer can be not_started, proposed, reviewed, ambiguous or not_applicable. Later layers do not erase earlier uncertainty. An obscured source port is a reason to retain a hypothesis or reject a training label. Chemical bond/electron accounting and human scientific review remain independent of OCR confidence.

AI can propose all layers, but its output stays ungraded/silver. Every proposal retains actor/model/tool version, evidence regions, confidence where meaningful and reviewer decisions. Human-reviewed gold is a distinct immutable revision, not a flag set by the same agent.

For native-plus-raster sources, populate the same layers jointly: use native atoms/bonds/marks and geometry directly, align rendered pixels, and use SVG/raster to confirm appearance and detect native import changes. Do not run a raster-only reconstruction merely because an image recognizer is available.

## Quality and use

Keep checks for semantic accounting, visible ink, annotation completeness, correspondence, native roundtrip and actual physical-size review separate. A failed or deliberately imperfect example may be valuable for a critic if it is accurately labelled and rights/split eligible. Count checked failures as failures, not accepted figures.

Correction records retain before/after native assets, whole-scene semantic and drawable diffs, intended operations, identity ambiguity and manual active time. Fragment motion/rotation, port/control changes, electronic-mark/caption displacement and step spacing have explicit units/frames. Exclude serialization-only ID changes and antialias rounding from human-edit counts. Chemical corrections require a scientific revision and cannot be silently relabelled as layout improvement.

The first uses are shared rule discovery, layout-prior/critic calibration and candidate ranking on development data. A critic score cannot override conservation, anti stereo, port binding or native collision checks. Preserve candidate count, seed, ranking, automatic repairs and first output so best-of-many selection does not masquerade as first-attempt success.

Under the current Quality Oracle phase policy, M1 may be used for exposed development. The fixed M2 lineage, its descendants and future reserved evaluation data are unavailable to feature fitting, rule parameter selection, prompts, training, reward/critic calibration and candidate-ranker tuning. The registry separates generation_asset_refs from oracle_asset_refs. Anti-selection permits only substrate_input assets in generation; a complete answer IR is not an anti-selection input.

## Acceptance of the pilot

All five schemas and the cross-file bundle must validate; missing points, references, hashes, frames and split mismatches must fail closed. The three semantic probes demonstrate representation only. The next gold pilot needs actual independent chemistry/visual decisions, native CDX/CDXML readback and a timed correction session when corrections occur. Unknown manual time is null. No human review or missing SVG/native output is synthesized to fill a schema.

Implementation limits: the current validator checks local example bytes and declared external bindings, not remote file retrieval, identity inside a native application, actual reviewer identity, an OCR pipeline, complete chemistry or a production diff engine. These remain explicit acquisition/qualification work.
