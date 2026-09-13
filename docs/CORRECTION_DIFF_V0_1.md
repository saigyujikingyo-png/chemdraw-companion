# Correction diff semantics v0.1

Status: design for the Composer R&D / Dataset Phase, 2026-09-13. A correction record explains an observed change between immutable revisions. It does not implement editing, establish native success or authorize training. Apply the [corpus quality and split policy](CORPUS_QUALITY_AND_SPLITS.md); corpus contracts remain separate from runtime fixes.

## Identity and immutable evidence

Bind each record to its sample, base revision, resulting revision and before/after artifact hashes. Preserve original proposals, intermediate failures and corrected outputs. Never replace the first output with a corrected figure. Record the actor, execution method, status, intended operations, observed values, semantic check, timing and native readbacks.

For a new edit, persist intent against the exact base hashes before mutation. An imported historical pair may support a retrospective diff, but must be labelled retrospective: do not fabricate a prior intent, actor action or measured time. Proposed, executed and independently verified changes are different evidence states.

Correspondence maps stable chemical identities and state occurrences to the actual objects in each artifact. Native object IDs, XML order, filenames and matching labels alone are insufficient. Atom, bond, lone-pair and electron-flow targets must include the relevant occurrence; repeated atoms across mechanism states are distinct drawing occurrences.

Record ambiguous matching as unresolved. A symmetry exemption requires one verified, chemically valid correspondence over all affected states, not arbitrary per-state exchanges. Exclude unresolved pairs from correction gold and executable replay.

## Operation meaning

Each operation records its kind, target, before value, intended after value, observed after value and reason. Separate three kinds of change conceptually; exact field encodings belong to the correction-record schema:

- Chemistry: atom properties, hydrogen/isotope counts, bond order, charge, stereochemistry, participant roles, transitions and electron-flow source/target semantics.
- Geometry: component transforms, text anchors, curve control points, ports, grouping, spacing and page placement. Declare coordinate frame and physical units.
- Presentation: font, size, stroke, arrow appearance and explanatory text. Text that changes chemical meaning also requires a chemistry operation.

A change spanning categories records every affected operation. A layout-only correction must preserve chemical semantics. A chemical correction creates a new scientifically reviewed revision; it cannot silently rewrite the benchmark answer or become an automatic-success claim.

Keep byte differences separate from normalized semantic and drawable differences. Serializer ID renumbering, property order and declared rounding are not user corrections. A requested nonzero edit with no observed meaningful delta is a no-op failure, not editing proof.

## Verification and review

Verify base hashes, correspondence completeness, expected nonzero differences and preservation of unrelated objects. Reconstruct chemistry and ports from actual outputs, rather than copying intended values into the result. Reject truncated curve arrays, missing/extra objects and unexplained style or chemistry changes.

Native edit evidence requires saving and independently reopening the relevant corrected format, then comparing actual readback. Record CDX and CDXML evidence separately; one does not certify the other. Retain unsupported or failed readbacks explicitly.

An AI proposal or automated correction remains a proposal until an actual human review creates a distinct reviewed revision and audit. Chemistry and visual sign-offs are independent decisions; neither can be synthesized by an agent. `correction` gold additionally requires trustworthy correspondence and verified before/after evidence.

Record human active correction time separately from wall time and automated execution. Unknown values are `null`, never zero. An agent suggestion, unattended native cleanup or serializer rewrite is not a human edit.

## Leakage and scope

All correction descendants inherit their source family's split and exposure restrictions. M1/M2 corrections remain locked regression/evaluation evidence, excluded from further fitting and training even if corrected or gold. This document authorizes no new native repair attempt, holdout selection, collection or model training.
