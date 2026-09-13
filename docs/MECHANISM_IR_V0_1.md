# Mechanism IR v0.1: corpus and annotation profile

Status: first design submission, 13 September 2026. This delivers schemas and executable representation checks, not a collected gold corpus, a trained model, a new Composer, or native acceptance. M1 remains a native-quality failure at reviewed checkpoint eb8b4c8.

## Purpose and boundary

Build an aligned record of chemical meaning, native object geometry, final rendered appearance and correction work. The intended execution remains: validated semantic IR -> general deterministic/constraint Composer -> ChemDraw adapter -> native render and measured feedback. A learned prior or critic can propose/rank candidates; semantic checks, constraints and native feedback determine whether a candidate is acceptable. No end-to-end target of guessing CDXML or page coordinates from text is introduced.

The existing mechanism-ir/0.1 and composer-request/0.1 runtime contracts are unchanged. The new corpus-mechanism-ir/0.1 is an archival/annotation profile under contracts/corpus/. It normalizes state-scoped occurrences and semantic marks needed for training labels, provenance and corrections. It is not a second production API. An explicit future projection may lower its supported subset into the current runtime; it must reject unsupported features and whitelist inputs. No runtime currently imports this profile or its examples.

In particular, the current runtime contract fixes two-electron flows and stores implicit H in a global catalog. The corpus profile can describe radicals, one-electron arrows and state-scoped H, but this does not establish runtime or native support. The included chemical checker returns unsupported for single-electron/radical, open-inventory and other unimplemented cases.

## Semantic entities

| Entity | Identity and meaning |
| --- | --- |
| State | A graph snapshot with species membership; order comes from explicit ReactionStep edges and entry_state. |
| Species | A state-scoped chemical participant with role, stoichiometry and molecule membership; a salt may group disconnected molecules. |
| Molecule | One connected component occurrence. Splitting/merging creates new occurrences; atom identity supplies continuity. |
| Atom | Stable element/isotope identity across states. AtomOccurrence binds it to one state/molecule and explicit implicit-H count. Moving protons need stable explicit H atoms. |
| Bond | A state-scoped edge between atom occurrences, with order and specified stereo. |
| Charge / Radical / LonePair | Separate marks bound to an atom occurrence. Chemical presence and visible display are separate. LP slots identify port slots, not distinguishable physical electron pairs. |
| ReactionStep | Source/target states, simultaneous electron-flow group and associated conditions. Composite/unresolved steps are representable but outside the initial chemical checker. |
| ReactionArrow | The ordinary step arrow, distinct from an electron-flow arrow. |
| ConditionText | Exact text and step association with a typed role and evidence status. Unknown units or conditions are not invented. |
| ElectronFlow | Electron count and semantic source/sink. Ports refer to the source-state atom, bond, LP or radical; a prospective bond sink identifies both source-state endpoints. |
| LayoutConstraint | General reading order, snake traversal, spacing, alignment, orientation and chemical geometric requirements. It contains relationships and shared parameters, never per-sample page positions. |

All entity IDs are opaque and globally unique within a record. A native object ID is never a semantic identity. Charge/LP/radical fields reference AtomOccurrence, not an unscoped element or catalog entry.

Anti/syn constraints have ordered roles: central_A, central_B, substituent_on_A, substituent_on_B. They are hard chemical requirements in one state; the central bond must be double and both substituent attachments must exist. A numerical state name has no layout meaning. The M2 example's minimum-turn requirement comes from the existing declared layout policy; state/step/flow counts are not runtime constants.

## Meaning versus observations

The supplied/reviewed scientific record states intended chemistry. CDX/CDXML native readback records what the application actually serialized, including wrong values. Native render records what is visible. SVG can supply additional vector geometry and object locators, but its producer and correspondence must be verified. None automatically overrides the others: the observed M1 charge corruption is why native readback is not an infallible chemistry oracle.

When these assets coexist, ingestion registers all of them together with byte hashes, producer/execution receipts and coordinate frames. Correspondences can be one-to-many and uncertain. Preserve original files; store mappings and measurements as sidecars. Do not rasterize away available native object information or postpone native alignment until after image annotation.

Golden geometry, human corrections, oracle answers and critic labels are outputs/evaluation data. The generation projection cannot load them as page coordinates, fixture lookups, prompts, cached layouts or expected-product commands. A complete correct IR tests composition only. Anti-selection needs substrate-only input and a separate hidden answer record.

## First executable proof

The three files in examples/corpus/ are ungraded schema probes, excluded from corpus targets and fitting:

| Probe | States / steps / flows | Purpose |
| --- | --- | --- |
| proton-transfer.ir.json | 2 / 1 / 2 | Explicit proton transfer between hydroxide and ammonium; water/ammonia products and matching LP/charge changes. |
| M1.ir.json | 2 / 1 / 2 | OH- + CH3Br -> CH3OH + Br-; O LP 3 -> 2 and Br LP 3 -> 4, reaction arrow and aqueous condition. |
| M2.ir.json | 7 / 6 / 15 for this reference | Existing mapped Beckmann pathway, explicit acid/water/protons, hard anti relation and snake constraint. |

The reference validator checks syntax, identity/membership, state-scoped ports, stereo roles and bounded closed-inventory H/C/N/O/Br electron accounting. It checks that simultaneous pair moves explain complete bond and LP differences and that represented charge is conserved. This is bookkeeping, not independent chemical plausibility, experimental mechanism proof, anti-selection or native rendering.

The M1 annotation example binds a proposed semantic attack flow to actual archived native curve 31 and its observed control points. Its CDXML, CDX and native PNG references retain original hashes. Pixel-to-page alignment uses recorded mask calibration. The alignment is still a proposal, with no human sign-off. SVG is unavailable for this example and is not fabricated.

## Delivered contracts and checks

- [IR schema](../contracts/corpus/mechanism-ir.schema.json)
- [Annotation schema](../contracts/corpus/annotation.schema.json)
- [Corpus/provenance schema](../contracts/corpus/corpus-manifest.schema.json)
- [Correction schema](../contracts/corpus/correction-record.schema.json)
- [Split/freeze schema](../contracts/corpus/split-manifest.schema.json)
- [Bounded validator](../contracts/corpus/validate_corpus.py) and [tests](../contracts/corpus/test_corpus.py)
- [Validation receipt](CORPUS_SCHEMA_VALIDATION.json)

Developer checks use Python plus the existing jsonschema development dependency: python -m unittest discover -s contracts/corpus -p test_corpus.py. Individual validation is python contracts/corpus/validate_corpus.py mechanism-ir examples/corpus/M2.ir.json. Exit 0 means the named bounded check passed; 1 means invalid; 2 means representable chemistry outside the implemented semantic profile. No command implies gold or native acceptance.

build_schema_probes.py is test-data migration tooling, not generation code. Rebuilding its native-alignment proposal requires the immutable R2 evidence directory through --native-evidence; it never starts ChemDraw or obtains remote assets.

## R&D sequence

Approve these data contracts, then commission a small independently authored gold pilot. Use [the annotation workflow](ANNOTATION_PIPELINE_V0_1.md), [quality/split rules](CORPUS_QUALITY_AND_SPLITS.md), [correction design](CORRECTION_DIFF_V0_1.md), [rights strategy](CORPUS_ACQUISITION_AND_RIGHTS.md) and [sample plan](CORPUS_SAMPLE_PLAN.md). Corpus acceptance requires real reviewers, native files, measurements and provenance. Schema completion does not reset repair budgets or authorize collection at scale.

M1/M2 are locked exposed regression benchmarks from this phase onward and cannot supply further tuning/training or correction-prior data. Independent development examples drive general rules. After the base gates and an immutable implementation freeze, an independent evaluator selects the previously unused asymmetric-oxime holdout. Continue to keep MCP, installer, extra hosts and release expansion behind the core gates.
