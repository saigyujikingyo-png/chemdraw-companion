# ChemDraw Companion contributor instructions

Before design, implementation, tests or release, read DEVELOPMENT_PRINCIPLES.md (shared rule version 2026-09-12.4), then CHEMBRIDGE.md and CLOUD_STORAGE.md. User instructions override local guidance. Read docs/IMPLEMENTATION_HANDOFF.md and the architecture, interface and quality contracts before changes.

This independent repository is for the ChemDraw product. Preserve existing Origin and ChemAIst installations, repositories, credentials, user files and uncommitted changes. Do not embed this product in the Origin runtime or reuse rejected ChemAIst layouts without requalification. Reuse only individually verified infrastructure with licence review and attribution.

Keep active Git checkouts, runtimes, locks, databases, jobs and build output outside cloud sync. Machine-local paths belong in private receipts, not public source. Retain the active version and a working rollback version.

The architecture owner changes docs/ and contracts/ on codex/native-architecture-v1. The implementation owner uses a separate codex/native-p0 branch for runtime code and native evidence. Coordinate changes to contracts before merging. Do not write the other owner's branch or reset, clean or stash unrelated state.

Do not claim a capability from a method name, process exit, installed version or unit test. Native execution, chemical correctness, visual quality, editability, host delivery and installation each require their own evidence. P0-A transport, P0-B object control and P0-C composition are separate gates. Fix SaveAs, complete the ChemDraw 26 matrix, then S1 -> R1 -> M1 -> M2 Beckmann Snake before installer/MCP/multi-agent packaging. Prioritize independent IR/Composer and diagnose layout failures instead of expanding peripheral work.

The OpenAI frontend project-synchronisation bug is an external known issue. The user explicitly stopped investigation. Do not repair caches, registrations or the application for that issue.

Public content is English and sanitized. No accounts, licence material, tokens, tunnel configuration, private coursework or experimental inputs. Do not redistribute vendor binaries. Defaults remain one product entry, credential reuse, non-developer installation, thin host adapters, Terra max benchmarks and bounded resource use.
