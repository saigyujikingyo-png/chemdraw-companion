# ChemDraw Companion

> **Native execution is frozen.** The 0.2 diagnostic preview checks package integrity and reports capability limits. It cannot read, edit, render or close ChemDraw. See [the lifecycle record](LIFECYCLE_RECORD.md) and [diagnostic installation guide](packaging/chemdraw-companion/README.md). Historical native evidence below remains PARTIAL.

Diagnostic **0.2.0-preview.2** repairs the real Codex tools/list metadata startup failure in preview.1. See the [compatibility design and evidence](verification/DIAGNOSTIC_MCP_COMPAT_DESIGN.md) and [focused verification](verification/DIAGNOSTIC_MCP_COMPAT_VERIFICATION.md). Existing native limits remain unchanged.

Current shared rule: **2026-09-19.1**. The 0.2 diagnostic package implements a non-native installer and status MCP entry. Publication, installed readback and fresh host acceptance require their own dated receipts; native functionality remains frozen. See the [focused portable verification record](verification/DIAGNOSTIC_PREVIEW_0_2.md).

## Historical native milestone (2026-09-12 through 2026-09-14)

Historical implementation milestone: **Agent Edit Loop v0.1, PARTIAL**, with executable content frozen at `b9363ab`. The [controller receipt](https://github.com/saigyujikingyo-png/chemdraw-companion/blob/81e52337e669849c9d8284ce3c74719ef69ce52f/docs/AGENT_EDIT_LOOP_V0_1_RECEIPT.md) separates the bounded native result from outstanding display, lifecycle and roundtrip-classification gaps. At that historical checkpoint, shared rule **2026-09-14.1** was adopted for documentation and planning only; the present bounded repair adopts **2026-09-19.1**. See [per-tool/per-operation output-schema coverage and the next compatible version plan](runtime/OUTPUT_SCHEMA_COVERAGE_PLAN.md) and the [change record](CHANGELOG.md); that historical update did not implement or release output-schema compliance. The present diagnostic and lifecycle contracts are described separately in [the lifecycle record](LIFECYCLE_RECORD.md). The earlier research roadmap below remains historical until explicitly resumed.

ChemDraw Companion is a proposed independent Chembridge plugin for producing and revising editable structures, ordinary reaction schemes and bounded electron-flow diagrams through a user's licensed ChemDraw installation. It is not a Revvity or University of Edinburgh product.

Start with [the implementation handoff](docs/IMPLEMENTATION_HANDOFF.md), then [architecture](docs/ARCHITECTURE.md), [interface contract](docs/INTERFACE_CONTRACT.md) and [quality gates](docs/QUALITY_GATES.md). The [risk register](docs/RISK_REGISTER.md) tracks stop conditions. The [source ledger](docs/SOURCES.md) separates documented capabilities from tests that still need to run.

The first milestone separates P0-A transport, P0-B object control and P0-C mechanism composition. Execute SaveAs repair -> the [ChemDraw 26 capability matrix](docs/CHEMDRAW_26_CAPABILITY_MATRIX.md) -> S1 -> R1 -> M1 -> [M2 Beckmann Snake](docs/M2_BECKMANN_SNAKE.md), before installer/MCP/host packaging. The core asset is the independent [Chemical Mechanism IR and Mechanism Composer](docs/MECHANISM_IR_COMPOSER.md). All four fixtures require saved/reopened editable documents and owner-reviewed figures. M2 also requires the [generalization gate](docs/M2_GENERALIZATION_GATE.md): no sample-specific generation, then implementation freeze and an untuned asymmetric-oxime holdout. Open-source chemistry libraries may independently validate semantics. They must not silently replace promised native generation, cleanup, rendering or exports.

Use one host-neutral execution core and one product identity. ChatGPT Work cloud/local, Claude and WorkBuddy are targets until their actual workflows and artifact delivery have been tested. GPT-5.6 Terra with max reasoning is the acceptance benchmark; the development model is not benchmark evidence.

Public documentation and future GitHub Releases are in English. Ordinary use must not require a checkout, Git, a separately installed programming runtime or hand-edited JSON. The diagnostic preview implements versioned file installation and a separate reversible Codex connection. Native-product installation/acceptance remains outside this frozen slice.

## Composer R&D and dataset design

The [first corpus/annotation architecture](docs/MECHANISM_IR_V0_1.md) aligns chemical semantics, native objects, rendered geometry and corrections. It includes draft schemas and ungraded representation proofs, not a collected gold dataset or native acceptance. See [the phase handoff](docs/COMPOSER_RND_HANDOFF.md), [annotation workflow](docs/ANNOTATION_PIPELINE_V0_1.md), [quality and splits](docs/CORPUS_QUALITY_AND_SPLITS.md), [rights](docs/CORPUS_ACQUISITION_AND_RIGHTS.md) and [sample plan](docs/CORPUS_SAMPLE_PLAN.md).
