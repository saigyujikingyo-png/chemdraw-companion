# ChemDraw Companion contributor instructions

Before design, implementation, tests or release, read DEVELOPMENT_PRINCIPLES.md (shared rule version 2026-09-13.1), then CHEMBRIDGE.md and CLOUD_STORAGE.md. User instructions override local guidance. Read docs/COMPOSER_RND_HANDOFF.md, docs/QUALITY_ORACLE_V1.md and docs/GOLD_SILVER_HOLDOUT_V1.md, then docs/PAIRED_MECHANISM_CORPUS_SURVEY.md, docs/BLIND_RECONSTRUCTION_PROTOCOL_V1.md, docs/DATA_LEAKAGE_FIREWALL_V1.md and the architecture/interface contracts before changes. Issue #2 authorizes bounded actual external acquisition and blind reconstruction using existing tasks; no peripheral product expansion. Current policy permits exposed M1 development; M2 and its descendants plus future holdout remain locked against fitting/training.

This independent repository is for the ChemDraw product. Preserve existing Origin and ChemAIst installations, repositories, credentials, user files and uncommitted changes. Do not embed this product in the Origin runtime or reuse rejected ChemAIst layouts without requalification. Reuse only individually verified infrastructure with licence review and attribution.

Keep active Git checkouts, runtimes, locks, databases, jobs and build output outside cloud sync. Machine-local paths belong in private receipts, not public source. Retain the active version and a working rollback version.

The architecture owner changes docs/ and contracts/ on codex/native-architecture-v1. The implementation owner uses a separate codex/native-p0 branch for runtime code and native evidence. Coordinate changes to contracts before merging. Do not write the other owner's branch or reset, clean or stash unrelated state.

Do not claim a capability from a method name, process exit, installed version or unit test. Native execution, chemical correctness, visual quality, editability, host delivery and installation each require their own evidence. P0-A transport, P0-B object control and P0-C composition are separate gates. Fix SaveAs, complete the ChemDraw 26 matrix, then S1 -> R1 -> M1 -> M2 Beckmann Snake before installer/MCP/multi-agent packaging. Prioritize independent IR/Composer and diagnose layout failures instead of expanding peripheral work.

M2 must pass docs/M2_GENERALIZATION_GATE.md: no Beckmann-specific templates, sample coordinates, ID-based layouts or screenshot patches. General IR/Composer generation must be separate from reference oracles. After base M2 passes, freeze implementation/rules before selecting an untuned asymmetric-oxime holdout. Fixed 7/6/15 counts are sample expectations only.

The OpenAI frontend project-synchronisation bug is an external known issue. The user explicitly stopped investigation. Do not repair caches, registrations or the application for that issue.

Public content is English and sanitized. No accounts, licence material, tokens, tunnel configuration, private coursework or experimental inputs. Do not redistribute vendor binaries. Defaults remain one product entry, credential reuse, non-developer installation, thin host adapters, Terra max benchmarks and bounded resource use.
