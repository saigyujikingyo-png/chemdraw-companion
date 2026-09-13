# Implementation handoff: P0-A/B/C and M2

Current phase update (2026-09-13): read [COMPOSER_RND_HANDOFF.md](COMPOSER_RND_HANDOFF.md) and [MECHANISM_IR_V0_1.md](MECHANISM_IR_V0_1.md). The corpus profile is separate from the runtime contract. Current Quality Oracle phase: M1 may be used for exposed development; M2 and all descendants remain locked against tuning/training. Read QUALITY_ORACLE_V1.md and GOLD_SILVER_HOLDOUT_V1.md. This supersedes the older M1 restriction. Native gates and prior failed repair history remain in force.

Read DEVELOPMENT_PRINCIPLES.md (2026-09-12.4), CHEMBRIDGE.md and CLOUD_STORAGE.md, then this page, ARCHITECTURE.md, QUALITY_GATES.md, CHEMDRAW_26_CAPABILITY_MATRIX.md, MECHANISM_IR_COMPOSER.md and M2_BECKMANN_SNAKE.md. Revision 2026-09-12.3 retains P0-A/B/C and adds the mandatory M2_GENERALIZATION_GATE.md.

## Ownership and compatibility

Dedicated repository: saigyujikingyo-png/chemdraw-companion. Preserve Origin/ChemAIst, credentials, user files and unrelated changes. Use each device's verified non-synced checkout. Architecture owns docs/contracts/examples on codex/native-architecture-v1; implementation owns runtime/probes/tests/evidence on codex/native-p0. Merge the communicated immutable commit; no force-push or cross-owner branch overwrite. Continue the existing developer task.

Five tool names and three recipe IDs remain unchanged: structure_sheet.v1, reaction_scheme.v1, electron_flow_step.v1. M2 has a separate internal IR fixture/direct harness; do not force it into M1 or wait for a new public recipe. Historical contract and native evidence retain their original scopes.

## Earlier native sequence

Historical native-gate context only. The current work order is in COMPOSER_RND_HANDOFF.md; this older sequence does not authorize a new repair run during the Quality Oracle protocol delivery.

1. **Repair SaveAs.** Preserve f111c36 ethanol success and later missing-file failure. Change one variable at a time from the successful baseline; keep requested path immutable and capture by-ref returns and actual native errors. Verify bytes/reopen. A new PID alone is not COM isolation; Activate without readback is not a complete inactive-document test.
2. **Complete the ChemDraw 26 capability matrix.** Record build/edition/backend and operation/create/read/change/remove/reopen evidence. Probe Add-in where available without making it a prerequisite to permitted COM/CDXML routes.
3. **S1 -> R1 -> M1.** Retain structure, reaction and elementary SN2 cases with real native objects, semantics, reopened edits and final-size evidence.
4. **M2 Beckmann Snake immediately next.** Frozen seven-state/six-transition IR, anti-phenyl migration, mapped proton transfers, curly arrows/electron objects, three-row snake, separate CDX/CDXML reopen/edit and manual correction time. Preserve first output.
5. **Freeze and hold out.** Follow M2_GENERALIZATION_GATE.md. No Beckmann/template/coordinate/state-ID/screenshot special cases. Use general mechanism-ir.schema.json and composer-request.schema.json; legacy M2 validator is an external reference oracle only. Base M2 pass -> immutable implementation/rule freeze -> evaluator chooses at least one untuned asymmetric-oxime variant -> anti-selection/electron-flow/snake/native/edit/time evidence. Do not preselect or tune the holdout. A post-disclosure fix consumes the case and requires a new unseen sample.
6. **Classify failures.** Use semantic checks, object microfixtures, manual native reference, fixed geometry replay and automatic composition to separate native control, adapter translation, IR and Composer. A blocked A dependency leaves M2 blocked/unrun, not failed or passed.
7. Return the four base-fixture bundles plus separate freeze and holdout receipts with independent A/B/C results, capability receipts and blockers. Continue focused repair while owner review is pending; installer/MCP/host expansion follows native/object/composition, anti-hardcoding, untuned holdout and owner quality gates.

SaveAs is necessary engineering; P0-C is the main architecture risk. Long-term assets are backend-replaceable Mechanism IR/Composer. COM/Add-in/CDXML remain adapters. Do not automatically pivot to Mnova or add peripheral engineering when M2 fails.

## Required return

Send branch/commit, app/API/interop versions, actual methods, matrix row statuses, input/style hashes, semantic/geometry reports, unchanged first output, bounded automatic repairs, final CDX/CDXML/PNG, both-format disk reopen/edit receipts and mappings. Record actual active manual correction seconds, wall time and edit counts; unavailable is null, not zero. Human-fixed output cannot overwrite automated failure.

Retain safe binding, durable intent, idempotency fencing, revision reservation/CAS, immutable artifacts, finite call deadlines and separate native/owner/host results. Native claims require native evidence. Later actual GPT-5.6 Terra + max host acceptance remains separate from Astra development.

No installer/release is claimed. Reuse encrypted connections. The known OpenAI frontend project-sync bug stays out of scope.
