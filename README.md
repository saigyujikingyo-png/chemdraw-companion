# ChemDraw Companion

Current phase: [Agent Edit Loop v0.1](docs/AGENT_EDIT_LOOP_V0_1_RECEIPT.md), PARTIAL. Bounded native caption editing has evidence; desktop display and automatic roundtrip classification retain gaps. Runtime is frozen. The [output-contract draft and next-version plan](docs/OUTPUT_CONTRACTS_V1.md) adopt shared rule 2026-09-14.1 without claiming server-side implementation. M2 and unseen holdouts remain locked; mechanism research, MCP/service/host/installer expansion and release remain deferred.

Architecture preview. Current native evidence does not certify general mechanism generation, end-user host acceptance, installation or release.

ChemDraw Companion is a proposed independent Chembridge plugin for producing and revising editable structures, ordinary reaction schemes and bounded electron-flow diagrams through a user's licensed ChemDraw installation. It is not a Revvity or University of Edinburgh product.

Start with [the implementation handoff](docs/IMPLEMENTATION_HANDOFF.md), then [architecture](docs/ARCHITECTURE.md), [interface contract](docs/INTERFACE_CONTRACT.md) and [quality gates](docs/QUALITY_GATES.md). The [risk register](docs/RISK_REGISTER.md) tracks stop conditions. The [source ledger](docs/SOURCES.md) separates documented capabilities from tests that still need to run.

The paused mechanism research milestone separates P0-A transport, P0-B object control and P0-C mechanism composition. Execute SaveAs repair -> the [ChemDraw 26 capability matrix](docs/CHEMDRAW_26_CAPABILITY_MATRIX.md) -> S1 -> R1 -> M1 -> [M2 Beckmann Snake](docs/M2_BECKMANN_SNAKE.md), before installer/MCP/host packaging. The core asset is the independent [Chemical Mechanism IR and Mechanism Composer](docs/MECHANISM_IR_COMPOSER.md). All four fixtures require saved/reopened editable documents and owner-reviewed figures. M2 also requires the [generalization gate](docs/M2_GENERALIZATION_GATE.md): no sample-specific generation, then implementation freeze and an untuned asymmetric-oxime holdout. Open-source chemistry libraries may independently validate semantics. They must not silently replace promised native generation, cleanup, rendering or exports.

Use one host-neutral execution core and one product identity. ChatGPT Chat, Work cloud/local, Codex, Claude and WorkBuddy are targets until their actual workflows and artifact delivery have been tested. GPT-5.6 Terra with max reasoning is the acceptance benchmark; the development model is not benchmark evidence.

Public documentation and future GitHub Releases are in English. Ordinary use must not require a checkout, Git, a separately installed programming runtime or hand-edited JSON. Installation and update behavior remain design requirements until implemented and tested.

## Composer R&D and dataset design

The [first corpus/annotation architecture](docs/MECHANISM_IR_V0_1.md) aligns chemical semantics, native objects, rendered geometry and corrections. It includes draft schemas and ungraded representation proofs, not a collected gold dataset or native acceptance. See [the phase handoff](docs/COMPOSER_RND_HANDOFF.md), [annotation workflow](docs/ANNOTATION_PIPELINE_V0_1.md), [quality and splits](docs/CORPUS_QUALITY_AND_SPLITS.md), [rights](docs/CORPUS_ACQUISITION_AND_RIGHTS.md) and [sample plan](docs/CORPUS_SAMPLE_PLAN.md).
