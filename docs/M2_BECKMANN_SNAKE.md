# M2 Beckmann Snake architecture killer test

Status: frozen synthetic test design, not an executed native result. Internal IR version mechanism-ir-test/0.1; fixture M2-beckmann-snake.v1. Run after SaveAs repair, capability matrix, S1, R1 and M1. Do not wait for installer/MCP/multi-agent packaging. Missing native capabilities block dependent operations; IR/Composer implementation and diagnosis can proceed independently.

## Generalization requirement

The [anti-hardcoding and holdout gate](M2_GENERALIZATION_GATE.md) is normative. M2 must use general IR -> general Composer. No Beckmann template, sample coordinates, state-ID branching or per-screenshot patches. Seven states/six steps/fifteen arrows are reference expectations only. Base M2 is followed by implementation freeze and at least one untuned unsymmetrical-oxime holdout before packaging.

## Reference chemistry

Use acetophenone oxime with phenyl anti to the hydroxyl leaving group across C=N. Phenyl migrates; methyl remains on the original oxime carbon; product is acetanilide. Exclude E/Z isomerization and side reactions in this teaching fixture. Anti migration is source-supported; the seven-state acid/water representation is an explicit teaching expansion, not an experimental intermediate sequence or a concentrated-sulfuric-acid mechanism claim. See [sources](SOURCES.md).

Use the [complete mapped fixture](../examples/m2-beckmann-snake.json), validated against the [internal schema](../contracts/mechanism-test-case.schema.json). C1 is the oxime carbon, N2 the nitrogen, O3 original oxime oxygen, C4 methyl, C10..15 phenyl, O20 acid/base water, O21 attacking water. H30..35 are explicit transferred/heteroatom hydrogens. Carbon H remains implicit and conserved. Formal charge is zero unless listed; lone-pair inventory is explicit for N/O. Atom maps are validation data, not required visible labels.

| State | Main species | Next event / two-electron arrow count |
| --- | --- | --- |
| s0 | Ph-C(CH3)=N-OH; phenyl anti OH | O protonation / 2 |
| s1 | Ph-C(CH3)=N-OH2+ | Coupled phenyl migration, N-O cleavage, C-N bond-order increase / 3 |
| s2 | CH3-C≡N+-Ph | Water attacks carbon; one C-N pi pair returns to N / 2 |
| s3 | CH3-C(OH2+)=N-Ph | Water-assisted O deprotonation / 2 |
| s4 | CH3-C(OH)=N-Ph | N protonation / 2 |
| s5 | CH3-C(OH)=N+(H)-Ph | Water-assisted O deprotonation with C=O formation and C=N decrease / 4 |
| s6 | CH3-C(=O)-NH-Ph | Acetanilide plus regenerated hydronium |

Total: seven states, six transitions, fifteen curly arrows. All flows in a transition use the same pre-state and are simultaneous. s2/s5 N has no lone pair; protonated three-bond O has one pair. Do not add a free deficient N intermediate, attack nitrilium N, or draw an unassisted 1,3-H shift. Do not use ordinary step arrows between resonance contributors.

In the fixed mapping, O21 becomes carbonyl oxygen, O3 remains in leaving water, H35 becomes the amide H and hydronium is regenerated. This tracks one defined path, not experimentally unique oxygen/proton provenance. The displayed system remains charge +1; an unchanged spectator counterion is declared omitted.

## Composition contract

The diagram below is the reference traversal, not a row table for the generation input. Derive ordering from transition edges and layout from generic packing rules. The historical fixture's rows_left_to_right and expected fields stay in the test oracle. Use [m2-composer-request.json](../examples/m2-composer-request.json) at the general Composer boundary. Its dimensions/margins/font are provisional shared parameters; verify the resolved native font/style and freeze them without case-specific overrides.

Freeze the valid IR and effective style before native dispatch. Use a 170 mm x 230 mm canvas, 8 pt text, 14.4 pt nominal bonds, 0.6 pt strokes and at least 600 effective native DPI. Record the resolved font/template, margins and all effective values plus SHA-256. This is a provisional house test profile, not a publisher/university standard.

~~~text
s0 -> s1 -> s2
            |
s5 <- s4 <- s3
|
s6
~~~

The illustrated base reference has two outer row turns and six step connectors. The generation policy requests at least two outer row turns; actual row breaks follow general packing and measured geometry, not the reference row table. Six connectors follow this reference transition graph rather than a Composer constant. Curly arrows belong to the source panel; step connectors are distinct objects. Expand the phenyl ring, show the participating acid/water species, charges and all declared N/O lone pairs. Keep complete species inventory in the native figure and separate panels clearly. Do not swap phenyl/methyl, mirror a fragment, skip a state, crop auxiliaries, shrink fonts/bonds or flatten curves to make the snake fit.

Retain geometry criteria in QUALITY_GATES.md: zero unintended collisions/clipping; unrelated ink clearance at least 0.12 bond lengths, curve clearance 0.18 and port deviation at most 0.20. Check the anti relationship semantically and through opposite-side substituent geometry in s0/s1; not an assumed E/Z label. A target double-bond descriptor, where exposed, must agree. No claim of full 3D transition-state geometry is required.

Run one base composition and two fresh repeat runs with the same frozen input/style (three total), a finite predeclared deadline and at most two automatic repairs per run. All must preserve chemical/step topology and meet geometry limits; record coordinate variation. Do not demand byte-identical native files. Also run one internal stress variant with a rigidly rotated source fragment and one wider-turn-spacing constraint; each must preserve anti relation, mappings and donor/acceptor meaning. These are targeted stability checks, not an invitation to broaden chemistry.

## Native artifacts and editing

Keep each run's untouched first CDX/CDXML/PNG, source IR, composed geometry/ports, effective style, object mapping, validation report and hashes before repair.

Independently close/reopen the saved CDX and the saved CDXML from disk. Compare all seven state graphs, six connectors, fifteen editable electron curves, lone pairs, charges, text and mappings. On separate copies from each format, move a curve control point, edit a label, move a fragment and reroute its associated arrows. Exercise charge/lone-pair edits in a labelled diagnostic copy, not by silently changing accepted chemistry. Save and reopen edited copies again, comparing only declared changes. Opening the still-loaded original, valid SMILES, or an image object does not pass.

At 170 mm the native raster needs at least 4016 pixels across; check actual ink scale, not padded canvas dimensions. A 14.4 pt bond needs approximately 120 native pixels at 600 DPI. Preserve original low-quality output if this fails.

## Controls and failure attribution

Prepare a manually authored native reference of the SAME IR/style/size, with source mapping and concrete visual review. Reference preparation time is measured separately. Human review pending does not prohibit building/running the automated fixture; it prevents an acceptance claim.

| Control/result | Supported conclusion |
| --- | --- |
| Native reference itself cannot save/reopen/edit required objects | P0-A transport or P0-B native-object limitation on that exact route; distinguish by operation |
| Manual reference works; frozen golden geometry replay through adapter loses objects/control points | Adapter translation/import/roundtrip failure; native software incapability is not established |
| Golden geometry replays faithfully; automatic Composer collides, misroutes or breaks snake | Composer geometry/constraints failure |
| Input IR cannot express states/anti/ports, or generated graph/electron meaning is wrong before materialization | IR/semantic validation failure |
| Valid source IR/scene becomes semantically wrong only after import/reopen | Adapter mapping/roundtrip failure |
| Only an unattractive generated image exists, without controls | Undetermined; acquire the missing discriminating control |
| Several controls fail independently | Mixed; list each cause and evidence |

Golden replay is diagnostic only and can never count as a generated M2 pass. It must use the same adapter/app build/style as automatic composition and bypass only Composer. Preserve both geometric and native-reference hashes. A valid IR and missing Composer are an implementation gap; more installer/MCP/host engineering cannot remedy it.

## Human correction and acceptance

Record per run: first-output hash/time, automated checks, automatic repair count/time, human reviewer, manual active editing seconds, elapsed correction time, software/wait time, edit count by chemistry/geometry/object-control/text, corrected-output hashes and final decision. Use null/unavailable when not measured; zero means an observed zero-edit review. Do not include reference creation in output repair time or hide it.

First-attempt automated quality passes only if the untouched output meets every required check and concrete visual acceptance without human correction. A human-corrected file can separately pass usability/quality; it cannot backfill first-attempt automation. Report both first attempt and after bounded automatic repair. Manual-time targets are not yet empirically established; do not invent a speedup or silently waive the zero-manual-correction automation criterion.

M2 remains blocked/unrun until native execution occurs. Contract/semantic checks alone do not pass P0-B/C. A final P0-C decision requires actual geometry, native preservation, stability runs, the generalization gate including an untuned holdout, and owner visual review.
