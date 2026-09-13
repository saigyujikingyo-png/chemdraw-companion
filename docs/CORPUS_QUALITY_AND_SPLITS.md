# Corpus quality and split policy v0.1

Status: design for the Composer R&D / Dataset Phase, 2026-09-13. This policy does not establish collected data, training permission, a working corpus service, or native acceptance. Follow [DEVELOPMENT_PRINCIPLES.md](../DEVELOPMENT_PRINCIPLES.md). The corpus contracts are separate from the existing runtime IR.

## Quality and evidence

Every immutable sample revision records its source, asset hashes, lineage, authorship, review evidence, exposure, rights and split. Use these tiers:

| Tier | Meaning |
| --- | --- |
| `ungraded` | Received or proposed; applicable checks remain incomplete. |
| `silver` | Useful candidate with recorded checks and limitations; not an approved reference. |
| `gold` | Explicitly reviewed revision, qualified only for its listed `gold_scopes`. |
| `quarantined` | Unresolved rights, identity, chemistry, leakage or integrity prevents use. |

The allowed `gold_scopes` are `semantic`, `native_geometry`, `visual` and `correction`. Each requires its own evidence. A native save does not establish chemistry, publication quality or human approval.

An AI-authored proposal cannot become gold through self-review or a metadata-only tier change. Preserve it and create a distinct human-reviewed revision with an audit linking the proposal, reviewed assets and actual decisions. Record reviewer identity, role, timestamp and evidence; never invent a person or sign-off. Chemistry and visual approval are separate human decisions, independent of proposal authoring. A finished gold figure needs both. Geometry additionally needs qualified native execution/readback; correction additionally needs verified before/after evidence. Unapproved scopes remain unqualified.

## Immutable families and exposure

Assign a `leakage_group_id` before partitioning. One family includes an original document and its native formats, images, crops, annotations, corrections, redraws, paraphrases and derived examples. Versioned duplicate checks combine byte hashes, chemical graph/mechanism comparisons and visual similarity. Unresolved near-duplicates are quarantined. File renaming or atom relabelling cannot establish independence.

Use exposure values `exposed_and_tuned`, `exposed`, `unseen` and `not_assessed`. Record `lineage_relation` as `root`, `same_semantics` or `chemical_perturbation`. A same-semantics crop, redraw, reformatting or ID rename inherits its parent's exposure and cannot become unseen. Append disclosure events identifying what was seen, by whom and when. Missing disclosure history means `not_assessed`, not `unseen`. The split manifest records policy version, family membership, assignment reason and immutable revision hashes.

## Locked benchmarks and reserved evaluation

Use splits `development`, `fixed_regression`, `evaluation_reserved` and `quarantined`. Both `fixed_regression` and `evaluation_reserved` belong to the evaluation bucket. A family cannot cross the development/evaluation boundary; evaluation relatives may use different evaluation subtypes when their lineage and exposure support the assignment.

M1 and M2 are now locked evaluation/regression benchmarks: assign `fixed_regression` and `exposed_and_tuned`. Preserve earlier failures, repairs and first outputs. From this phase onward, do not fit them again or use their scores/corrections to select prompts, rules, parameters, coordinates or training examples. This instruction supersedes earlier permission to keep repairing those samples. Their corrected, augmented and otherwise derived records remain excluded from training, including gold revisions.

Keep future unseen evaluation distinct. `evaluation_reserved` may remain empty; this phase selects no holdout. After the required implementation/rule freeze, an independent evaluator may create or select a genuine M2 chemical perturbation within the held-out evaluation lineage, independently establish its semantics, check duplicates and record disclosure. It may share the known reaction family and benchmark ancestry. Such evidence can support an unseen-input claim, never family-disjoint novelty; all benchmark descendants remain excluded from training. Relabelling a known answer or drawing does not qualify. Post-disclosure tuning consumes its unseen status; retain the failure and follow the existing [generalization gate](M2_GENERALIZATION_GATE.md).

## Rights and acceptance

Record separate `store`, `annotate`, `train` and `redistribute` permission flags with their evidence. Unknown permission is not affirmative permission; accessibility, university access, silver/gold status and human correction grant no additional rights. Split exclusions override a permissive training right.

Keep answer annotations and golden geometry outside generation inputs. Complete-IR rendering assesses composition; withheld-product tasks assess chemical selection separately.

Acceptance must reject development/evaluation leakage, falsely unseen same-semantics derivatives, fabricated review, unsupported gold scopes, missing lineage/hashes, benchmark-to-training promotion and oracle fields entering Composer. These requirements need semantic checks beyond JSON Schema; schema validity alone grants no use or acceptance.
