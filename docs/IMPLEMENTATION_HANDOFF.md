# Implementation handoff: P0-A/B/C and M2

Read DEVELOPMENT_PRINCIPLES.md (2026-09-12.4), CHEMBRIDGE.md and CLOUD_STORAGE.md, then this page, ARCHITECTURE.md, QUALITY_GATES.md, CHEMDRAW_26_CAPABILITY_MATRIX.md, MECHANISM_IR_COMPOSER.md and M2_BECKMANN_SNAKE.md. Revision 2026-09-12.2 supersedes the three-fixture risk ordering.

## Ownership and compatibility

Dedicated repository: saigyujikingyo-png/chemdraw-companion. Preserve Origin/ChemAIst, credentials, user files and unrelated changes. Use each device's verified non-synced checkout. Architecture owns docs/contracts/examples on codex/native-architecture-v1; implementation owns runtime/probes/tests/evidence on codex/native-p0. Merge the communicated immutable commit; no force-push or cross-owner branch overwrite. Continue the existing developer task.

Five tool names and three recipe IDs remain unchanged: structure_sheet.v1, reaction_scheme.v1, electron_flow_step.v1. M2 has a separate internal IR fixture/direct harness; do not force it into M1 or wait for a new public recipe. Historical contract and native evidence retain their original scopes.

## Immediate sequence

1. **Repair SaveAs.** Preserve f111c36 ethanol success and later missing-file failure. Change one variable at a time from the successful baseline; keep requested path immutable and capture by-ref returns and actual native errors. Verify bytes/reopen. A new PID alone is not COM isolation; Activate without readback is not a complete inactive-document test.
2. **Complete the ChemDraw 26 capability matrix.** Record build/edition/backend and operation/create/read/change/remove/reopen evidence. Probe Add-in where available without making it a prerequisite to permitted COM/CDXML routes.
3. **S1 -> R1 -> M1.** Retain structure, reaction and elementary SN2 cases with real native objects, semantics, reopened edits and final-size evidence.
4. **M2 Beckmann Snake immediately next.** Frozen seven-state/six-transition IR, anti-phenyl migration, mapped proton transfers, curly arrows/electron objects, three-row snake, separate CDX/CDXML reopen/edit and manual correction time. Preserve first output.
5. **Classify failures.** Use semantic checks, object microfixtures, manual native reference, fixed geometry replay and automatic composition to separate native control, adapter translation, IR and Composer. A blocked A dependency leaves M2 blocked/unrun, not failed or passed.
6. Return four bundles with independent A/B/C results, capability receipts and blockers. Continue focused repair while owner review is pending; installer/MCP/host expansion follows the native/object/composition and owner quality gates.

SaveAs is necessary engineering; P0-C is the main architecture risk. Long-term assets are backend-replaceable Mechanism IR/Composer. COM/Add-in/CDXML remain adapters. Do not automatically pivot to Mnova or add peripheral engineering when M2 fails.

## Required return

Send branch/commit, app/API/interop versions, actual methods, matrix row statuses, input/style hashes, semantic/geometry reports, unchanged first output, bounded automatic repairs, final CDX/CDXML/PNG, both-format disk reopen/edit receipts and mappings. Record actual active manual correction seconds, wall time and edit counts; unavailable is null, not zero. Human-fixed output cannot overwrite automated failure.

Retain safe binding, durable intent, idempotency fencing, revision reservation/CAS, immutable artifacts, finite call deadlines and separate native/owner/host results. Native claims require native evidence. Later actual GPT-5.6 Terra + max host acceptance remains separate from Astra development.

No installer/release is claimed. Reuse encrypted connections. The known OpenAI frontend project-sync bug stays out of scope.
