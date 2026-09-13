# Composer R&D / Dataset Phase handoff

Effective 13 September 2026. This applies the user's new dataset instruction after the R2 acceptance review. Read DEVELOPMENT_PRINCIPLES.md, CHEMBRIDGE.md, CLOUD_STORAGE.md, MECHANISM_IR_V0_1.md and CORPUS_QUALITY_AND_SPLITS.md.

## Current deliverable and limits

The architecture branch contains five corpus schemas, a bounded validator, three ungraded semantic representation probes, an existing-native geometry/render annotation proposal, acquisition/rights policy, correction-diff design and a 40-gold / 200-total sample plan. No gold data was created, no model was trained, and no dataset was crawled. Native acceptance from R2 remains partial: M1 quality fails, base M2 is unscored and holdout is not started.

The corpus profile is separate from the existing runtime payload. Do not merge annotation coordinates, expected answers, native IDs or correction targets into Composer inputs. Runtime lowering is future explicit, feature-checked work; unsupported radical/single-electron cases must not be silently simplified.

## Immediate work

1. Review the schemas and validation receipt, including the three complete semantic examples. Resolve contract issues before collecting data or implementing a corpus platform.
2. Keep correcting general integrity defects identified by the R2 review: complete geometry inventories, actual native style fields, object-pair-scoped contact exemptions and current capability receipts. Use independent synthetic controls.
3. Develop general geometry and native measurement on independently authored development microfixtures. From this phase onward, M1/M2 inputs, outputs, corrections and descendants are locked evaluation material. Do not use their coordinates, masks, head metrics, failures or corrected files for new rule fitting, priors, critics, ranking or prompts. Retain already-exposed legacy code/history honestly; new policy cannot undo past contamination.
4. Prepare a small first-party native pilot and request real independent chemistry and visual review on concrete artifacts. AI proposals are ungraded/silver, never frozen truth. Capture before/after native files, actual nonzero edits, semantic changes, readback and measured manual time. Do not fill missing reviews or timing with invented values.
5. Expand toward 40 gold within 200 total only after the pilot's schema/rights/quality checks are operational. Keep per-family and stress coverage, unique lineage counts, checked failures and promotions separate. Do not start mass scraping or model training as a substitute for this proof.
6. Run locked S1/R1/M1/base-M2 regression/evaluation gates without fitting on them. Base success is still required before an immutable implementation/rules/style/adapter/cache freeze and independently selected untuned asymmetric-oxime perturbation. Known-family unseen-input evidence is distinct from family-disjoint generalization.

All benchmark-derived revisions remain outside fitting data. Same-semantics redraws/crops/ID changes inherit exposure. A genuinely new chemical perturbation may be selected by the independent evaluator after freeze inside the evaluation boundary; it does not become family-disjoint merely because its filename or atoms differ.

## Deferred work

Keep installer, MCP expansion, extra hosts, release work and a replacement editor deferred. Do not build an end-to-end CDXML predictor. Native ChemDraw remains the required adapter/output for present acceptance; the durable assets are semantic IR, general Composer constraints and aligned correction data.

Do not resume the archived computer-manager relay or the OpenAI frontend synchronization investigation. Origin's former coordination task is now independent; stop all cross-task updates to it. ChemDraw architecture/development coordination continues only within the existing ChemDraw tasks.

## Next receipt

Return the exact schema/code revision; representation and negative-test outcomes; any unsupported semantics; selected development candidates with provenance/rights; actual review status; original native artifacts and alignment; correction timing; evaluation exclusions; and remaining A/B/C gates. Distinguish schema-valid, chemically reviewed, natively verified and visually accepted. Unknown evidence stays unknown.
