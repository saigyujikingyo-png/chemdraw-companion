# M2 generalization and holdout gate

Revision 2026-09-12.3. Required in addition to the original M2 native/quality/editability gates. No base-native or holdout pass has been observed by this architecture task.

## Generation rules

M2 MUST be generated from general Mechanism IR by a general Composer. Prohibit Beckmann-specific drawing/mechanism templates used to pass the benchmark, sample-specific absolute page/curve coordinates, state-number/name/atom-map dispatch, fixed 7-state/6-transition/15-curve algorithms, fixture/hash/name lookups, and patches tailored to individual screenshots. Moving those rules into configuration, an adapter, a prompt, generated code, a cache or a plugin does not make them general.

Allowed: reaction-independent packing, bounding boxes, alternating row direction, external row-turn lanes, collision avoidance, donor/acceptor ports, rigid fragment transforms, text/charge clearances and general chemical constraints. Rule parameters must be shared, versioned and frozen. Derive grouping from transition graph and measured geometry. Opaque IDs provide identity, not placement instructions. Reaction labels are display text, not algorithm switches.

Native generation may produce intrinsic fragment coordinates. Composer may transform measured fragments through general rules. This does not permit a stored whole-M2 layout or a structure-to-page-coordinate lookup. Cache reuse requires declared content-addressed keys, independently reproducible native generation and generic policies; no hidden benchmark assets.

Golden native references and golden geometry replay remain DIAGNOSTIC CONTROLS ONLY. Neither is a valid generated M2 entry. Keep their input path, output path and provenance separate from the scored generation path.

## Input and oracle boundary

The new [mechanism IR schema](../contracts/mechanism-ir.schema.json) and [Composer request](../contracts/composer-request.schema.json) define a reaction-neutral boundary. The [M2 Composer input](../examples/m2-composer-request.json) contains valid chemistry and generic layout policy, not an expected result, per-state row assignment or page coordinates. Native fragment measurements enter through the geometry service and retain provenance.

The old mechanism-test-case.schema.json, m2-beckmann-snake.json and validate_mechanism_fixture.py are a **reference oracle only**. Their fixed maps/counts/rows check the known sample. They are not a general IR or Composer implementation, must not be imported into production generation, and must not restrict holdouts to acetanilide or the sample's IDs/counts. Historical validation reports retain that limited scope.

Schema validation proves only syntax. A general semantic validator must verify graph/charge/electron accounting, atom and occurrence identity, transition continuity and stereo relationships without sample IDs. Composer must order through explicit transition edges and entry_state, not array order or lexical state names. Current implementation may explicitly reject branching/cyclic pathways; bounded linear support must still be independent of reaction identity and step count.

The 7/6/15 values describe the reference sample only. Holdout reports derive counts from their independently reviewed IR. General Composer tests must include other supported sequence lengths and flow counts; no dummy states/arrows may be inserted into scored chemical mechanisms.

## Evidence against hardcoding

Before claiming a base pass, inspect the generation call graph, imports, rules/configuration, prompts, templates and caches. Record source/build/config hashes and the audit result. Include tests that bijectively relabel state/transition/flow/atom identifiers, shuffle storage arrays while retaining explicit edges, and change chemically equivalent fragment orientation. Relationships and layout quality must survive; compare modulo the ID mapping, not native bytes.

Also exercise valid supported linear IRs of different lengths and different per-step flow counts. Such structural/metamorphic tests are distinct from the mandatory unseen chemical holdout. A source scan alone cannot prove absence of hidden special-casing; report both inspection and observed behavior.

## Holdout sequence and contamination rules

1. Complete the base M2 native, quality, editability, anti-hardcoding and owner-review gates. Before selecting the holdout, freeze the implementation commit/binary, dependencies, Composer/semantic rules, prompts, layout parameters, native style/build/adapter and cache policy. Record hashes and an immutable freeze receipt. No named holdout structure is selected or tuned in this revision.
2. After that freeze, an evaluation owner independent of tuning selects at least ONE previously unused **unsymmetrical oxime** within declared chemical scope. Change a substituent or migrating group sufficiently to alter fragment geometry; require a different migrating group identity/role from the reference by explicit anti configuration. A paired opposite-configurational or bulk/placement perturbation is recommended if the selected case alone does not distinguish a fixed phenyl preference. Merely renaming phenyl, atom IDs or labels is insufficient.
3. Independently establish the input's explicit configuration, anti relation, chemically justified expected migration/product and electron bookkeeping. Keep the expected-answer record outside the generation path. The sample must be scientifically well-defined before execution. Do not manufacture uncertain chemistry merely to stress layout.
4. Run the frozen pipeline for the first time on that input, with the same generic rule parameters and declared repair budget. Record input/expected hashes and disclosure time, initial output before any human edit, native artifacts, all failures/automatic repairs, manual active correction time and retained corrected copies. The evaluator may reveal semantic input IR required by Composer; do not reveal golden coordinates or use expected-answer fields as generation commands.
5. Verify BOTH chemistry selection and composition. The semantic stage must derive or validate the migrating group from substrate connectivity and explicit anti configuration, not a fixed aryl/phenyl preference. Preserve its trace and independently compare product and electron flow. Supplying a fully correct IR and rendering it can pass composition only; it cannot establish automatic anti-selection. For the latter run, withhold expected product/migrating-group labels and do not derive runtime IR by loading the oracle.
6. Apply the same native CDX/CDXML independent reopen/edit, semantic-anchor, snake topology, final-size quality and manual-time gates. Use counts from that case's IR. Holdout pass and base pass are separate records; one unseen case supports only bounded generalization, not arbitrary mechanisms.
7. No code/config/prompt/template/coordinate tweaks after disclosure may count toward that holdout's first unseen pass. A discovered defect may be fixed by a general rule, but retain the failure, reclassify that sample as a regression case, rerun the base suite, freeze a new build and choose a NEW unseen case. Exhaustive seeds/retries and selecting only a good-looking result must be disclosed and cannot count as first-attempt success.

The execution order is SaveAs -> capability matrix -> S1 -> R1 -> M1 -> base M2 -> freeze -> holdout/perturbation. Installer/MCP/host expansion remains after these gates. If base M2 is blocked, holdout stays not_started, never implicitly passed.

## Required receipt

Record base pass evidence; freeze time/commit/build and every relevant rule/style/config hash; evaluator independence; holdout selection/disclosure time; input and separate expected hashes; proof it was not used for tuning; declared chemical scope; semantic selection trace; actual state/transition/flow counts; untouched first artifacts; automatic repairs/retries; manual active/wall time; both native-format edit receipts; semantic/geometry/native verdicts; contamination status and final decision. Unknown fields remain unverified, not zero/pass.

Separate gate fields: base_m2, anti_hardcoding_audit, metamorphic_behavior, freeze_integrity, unseen_input, anti_selection, electron_flow, composition, native_roundtrip, manual_correction_measurement, owner_acceptance. Do not combine an audit or schema pass with a native benchmark pass.
