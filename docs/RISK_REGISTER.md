# P0 risk register: transport, object control and composition

Architecture revision 2026-09-12.3 supersedes the original risk ordering, not historical evidence. **The largest architectural uncertainty is P0-C: whether correct chemical meaning can consistently become a good editable mechanism figure.** SaveAs/COM reliability is a necessary P0-A engineering prerequisite.

Execution order: **repair SaveAs -> ChemDraw 26 capability matrix -> S1 -> R1 -> M1 -> M2 Beckmann Snake**. Severity and execution dependency are different. Run M2 through a direct developer harness, then freeze and run the untuned holdout in M2_GENERALIZATION_GATE.md, before installer, MCP, cloud or multi-agent packaging.

| Priority / ID | Risk | Discriminating evidence | Failure decision |
| --- | --- | --- | --- |
| P0-C / C01 | Correct chemistry cannot become readable multi-step geometry | M2 seven-state snake, editable electron curves, two row turns, consistent scale, first output and correction time | Diagnose IR vs Composer vs adapter using M2 controls; stop peripheral expansion |
| P0-C / C02 | No independent state identity, anti relation or simultaneous electron flow representation | Versioned Chemical Mechanism IR, atom provenance, state-scoped ports and graph differences | Fix IR/validator; do not encode chemistry as vendor coordinates/calls |
| P0-C / C03 | Native render conceals poor geometry or extensive manual repairs | Separate untouched first output, bounded automatic repairs and human-corrected copy at final size | Human repair cannot retrospectively pass automated quality |
| P0-C / C04 | Memorized M2/template/coordinate patches mimic a general Composer | Separate oracle/runtime; generic input boundary, ID relabeling/variable-length tests, frozen untuned chemical holdout | Reject benchmark claim; preserve first failure and consume disclosed holdout before retuning |
| P0-B / B01 | Atoms/bonds/charges/lone pairs flatten, disappear or cannot be controlled | Create/read/change/remove microfixtures and independent native CDX/CDXML reopen/edit | Qualify another adapter operation; images/method names are insufficient |
| P0-B / B02 | Curves are editable but chemical anchors are lost | Control-point edit plus donor/acceptor mapping through fragment motion and reopen | Separate geometry control from semantic anchors; Composer may explicitly maintain anchors |
| P0-B / B03 | Transform/cleanup detaches curves or changes stereo/anti relationships | Rigid transforms, cleanup/readback, mapping and rerouting; no silent reflection | Repair adapter mapping or Composer invalidation; reject semantic changes |
| P0-B / B04 | Reopened object IDs change or duplicated fragments are misidentified | IR occurrence -> native ID remapping; duplicate-fragment ambiguity refusal | Block unsafe object edits; hashes cannot replace identity |
| P0-A / A01 | SaveAs returns without a correct file; reopen/export unreliable | Immutable requested path, returned args, actual native errors, file bytes/readback, controlled comparisons | Fix transport first; dependent B/C tests remain blocked/unrun |
| P0-A / A02 | Wrong document/process receives mutation | Qualified binding and actual active-document readback during identical A/B/focus tests | Refuse unsafe writes; new PID alone is not isolation |
| P0-A / A03 | Required edition/entitlement/backend unavailable | Exact build/edition and operation-level matrix for permitted COM/Add-in/CDXML routes | Mark only the evidenced route unavailable |
| P0-A / A04 | Replay/stale revision/crash corrupts state | Durable intent, same-key reconciliation, disposable revision, reservation and CAS commit | Fence unknown outcomes; no blind retry, Undo or process kill |
| P0-A / A05 | Export has wrong scope, native scale or revision | Full inventory, physical ink scale, guarded fingerprints and wrong-selection tests | Fail export separately from file availability |
| Later / L01 | Peripheral work conceals unresolved drawing core | Four fixture bundles and separate A/B/C results before installer/host expansion | Pause breadth; keep core diagnosis active |
| Later / L02 | Installation/update loses credentials or rollback | Separate versions, drain jobs, preserve encrypted config and test recovery | Block deployment separately |
| Later / L03 | Local files/presets advertised as delivery/model acceptance | Receiver bytes/open receipts, actual host workflows and Terra max measurements | Keep host/delivery acceptance unverified |

## Failure disposition

A pass never implies B or C. A transport blocker makes dependent tests blocked/unrun, not a negative Composer result. Distinguish documented, detected, narrow_observed, native_verified, failed, unsupported and unverified, with exact operation/build/backend evidence.

M2 failure classes: transport, native_object_control, adapter_translation_or_roundtrip, ir_or_semantics, composer_geometry, mixed, undetermined. Correct supplied chemistry with failed geometry must not be blamed on a model without a reproducer. Do not switch products or add peripheral systems as a substitute for diagnosis. Mnova is only a separately authorized future product decision.

Reports include failed operation, build/edition, source, sanitized native error, controlled alternatives, hashes, unchanged first output, recovery and next decision. Owner silence is pending.

## Resource and retention policy

Retain one native write lane, queue cap 8, 30-minute idle lease and durable revision/idempotency fences. The initial 180-second deadline remains for S1/R1/M1 recipes. M2 is a separate developer experiment: declare a finite total deadline and per-call deadlines before execution and record actual timing; do not silently extend the public recipe contract. Keep the two-repair cap for a fixed-input composition job.

Scratch stays outside sync: 1 GiB/7 days for verified inactive diagnostics only. Never evict active/unknown jobs, current runtime, rollback version, selected deliverables or the sole verified artifact. P0 idempotency tombstones have no automatic expiry; at 16 MiB reject new jobs with RESOURCE_LIMIT pending an explicit retention decision. These are policies, not performance or automatic-cleanup claims.
