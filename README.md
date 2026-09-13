# ChemDraw Companion

Current phase: [Quality Oracle v1](docs/QUALITY_ORACLE_V1.md) and [Gold Correction Corpus](docs/GOLD_CORRECTION_CORPUS_V1.md). Native visual acceptance remains failed/unverified. M1 may be used for exposed development; M2 and unseen holdout remain locked. MCP, installer, host and product-surface expansion stay deferred.
Architecture preview, 2026-09-12. No native execution, host acceptance, installer or release is certified by this repository yet.

ChemDraw Companion is a proposed independent Chembridge plugin for producing and revising editable structures, ordinary reaction schemes and bounded electron-flow diagrams through a user's licensed ChemDraw installation. It is not a Revvity or University of Edinburgh product.

Start with [the implementation handoff](docs/IMPLEMENTATION_HANDOFF.md), then [architecture](docs/ARCHITECTURE.md), [interface contract](docs/INTERFACE_CONTRACT.md) and [quality gates](docs/QUALITY_GATES.md). The [risk register](docs/RISK_REGISTER.md) tracks stop conditions. The [source ledger](docs/SOURCES.md) separates documented capabilities from tests that still need to run.

The first milestone separates P0-A transport, P0-B object control and P0-C mechanism composition. Execute SaveAs repair -> the [ChemDraw 26 capability matrix](docs/CHEMDRAW_26_CAPABILITY_MATRIX.md) -> S1 -> R1 -> M1 -> [M2 Beckmann Snake](docs/M2_BECKMANN_SNAKE.md), before installer/MCP/host packaging. The core asset is the independent [Chemical Mechanism IR and Mechanism Composer](docs/MECHANISM_IR_COMPOSER.md). All four fixtures require saved/reopened editable documents and owner-reviewed figures. M2 also requires the [generalization gate](docs/M2_GENERALIZATION_GATE.md): no sample-specific generation, then implementation freeze and an untuned asymmetric-oxime holdout. Open-source chemistry libraries may independently validate semantics. They must not silently replace promised native generation, cleanup, rendering or exports.

Use one host-neutral execution core and one product identity. ChatGPT Work cloud/local, Claude and WorkBuddy are targets until their actual workflows and artifact delivery have been tested. GPT-5.6 Terra with max reasoning is the acceptance benchmark; the development model is not benchmark evidence.

Public documentation and future GitHub Releases are in English. Ordinary use must not require a checkout, Git, a separately installed programming runtime or hand-edited JSON. Installation and update behavior remain design requirements until implemented and tested.

## Composer R&D and dataset design

The [first corpus/annotation architecture](docs/MECHANISM_IR_V0_1.md) aligns chemical semantics, native objects, rendered geometry and corrections. It includes draft schemas and ungraded representation proofs, not a collected gold dataset or native acceptance. See [the phase handoff](docs/COMPOSER_RND_HANDOFF.md), [annotation workflow](docs/ANNOTATION_PIPELINE_V0_1.md), [quality and splits](docs/CORPUS_QUALITY_AND_SPLITS.md), [rights](docs/CORPUS_ACQUISITION_AND_RIGHTS.md) and [sample plan](docs/CORPUS_SAMPLE_PLAN.md).
