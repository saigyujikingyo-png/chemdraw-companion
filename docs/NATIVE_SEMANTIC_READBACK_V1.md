# P0-B native semantic readback v1

This is a new bounded phase after the immutable [IR v0.2 PARTIAL receipt](IR_V0_2_PHASE_RECEIPT.md), authorized on 13 September 2026 and coordinated through [Issue #2](https://github.com/saigyujikingyo-png/chemdraw-companion/issues/2#issuecomment-5654370273). The preceding three failures retain their original status and bytes. This document declares evidence requirements; the phase receipt establishes what actually ran.

Live baseline inspection found architecture `3c63347d5cc0ba717f10dddf16115013995ab3dc`, runtime `bc428205a0066d7b544fe634910310d55fb3a893`, and open PR #1. Recheck heads before integration. Architecture owns docs/contracts and independent integration; the existing Windows task owns runtime/probes. The gray-window and page-clipping task has a separate synthetic display-repair receipt and is not mechanism acceptance. Native workers must be idle and exactly PID/HWND-bound before use.

## Meaning of hydrogen observations

`implicit_h` remains the existing IR/runtime compatibility key. For this adapter it denotes attached H not represented by separate atom nodes. Do not change blind IR or its depiction policy to accommodate an adapter limitation.

| Representation | Meaning and counting boundary |
|---|---|
| Atom label H | H expressed in an atom's label, such as CH3 or OH. Preserve the label and its binding to the actual atom; ordinary page text is not an atom. This may describe the same H as the attached-H observation. |
| Independent H/D node | A separate native Element=1 node with its own ID, isotope and bond. D has isotope 2; isotope on a heavy atom does not relabel its attached hydrogen. Preserve and count each node once. |
| Attached non-node H | Hydrogen associated with the atom without an independent native node. A qualified label, NumHydrogens or selected native formula can refer to this same quantity. These representations are not additive. |
| Explicit serialized field | Preserve its exact presence, string, parsed value and source hash. Explicit zero differs from a missing field. |
| Native API observation | Preserve raw API text/value, selector/counts, exact selected identity, process/build and before/after evidence. The API name alone does not establish semantics. |
| Format decode | A versioned interpretation of actual native fields/graph, qualified by independent controls for the declared native build and domain. It is not an API-observed value or an expected-IR substitute. |
| Unknown/conflict | Retain absent, unsupported, malformed, contradictory or unqualified evidence. Do not silently choose the value that agrees with IR. |

The [legacy NumHydrogens definition](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_NumHydrogens.htm) excludes independently drawn H atoms and defines omission through minimum hydrogen needed for valence, not as zero. The [legacy Node definition](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/Node.htm) describes redundant label/property information and label-based reading when Text is present. Conflicting label and scalar evidence therefore requires a diagnostic. [Isotope](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_Isotope.htm) preserves isotope identity; [AbnormalValence](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_AbnormalValence.htm) says normal valence can depend on the application. [RestrictImplicitHydrogens](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_RestrictImplicitHydrogens.htm) is a query restriction, not a general H-count field.

These are preserved CambridgeSoft SDK documents hosted by IUPAC, not current ChemDraw 26 behavior guarantees. Document interpretation and actual version-bound native outcomes remain separate evidence. No complete periodic-table valence engine is introduced; all 118 element identities remain representable while chemistry and native capability coverage are reported separately.

## Observation and comparison boundary

Every readback value retains at least its quantity, value or null, source class, source field/API/decode rule, artifact and atom identity, qualification scope/version, and reasons for unknown or conflict. Use these source classes consistently:

- `explicit_native_field`: the value is present in actual serialized native bytes.
- `native_api_observation`: a bound native call supplied the value, with the exact grammar/selection interpretation qualified.
- `qualified_format_decode`: a documented bounded rule decodes actual native evidence for the tested version and scope. Explicitly record defaults and any computation.
- `unknown`: no qualified observation. This is not a zero, an expected value, or a pass.

Raw evidence can coexist even when no resolved value is admitted. Preserve label H, independent H/D-node inventory and attached-H evidence separately; their potential overlap is explicit. Summing label H plus attached H is invalid. Independent H/D nodes cannot supply both their own graph occurrence and an additional attached-H increment.

Only after observation is complete may a separate comparison use expected IR. Comparison records are `match`, `mismatch` or `unverified`. Unknown/conflict yields unverified even when an expected value exists. Expected IR cannot generate, fill or overwrite observations; changing expected H in a negative test must not alter the measured value. Native identity, mapping, complete atom/bond graph, charge, isotope and radical checks remain required independently of H matching.

## Qualified rule requirements

Prefer the existing native CDXML fields, `Document.Selection.Objects.FormulaHTML`, and existing graph/selection readback. Do not enumerate unrelated COM properties or reopen the ChemScript route. FormulaHTML superscript bullets from a single-atom selection describe cut bonds under the separately tested grammar; they are not the original atom's radical state.

Each predicate must state the protected ambiguity, why it is local or component-wide, and the positive/negative controls supporting it. Local checks cover exact Element-node identity, incident bonds, charge/isotope/radical state, explicit H/D neighbors, label consistency and selected formula syntax. Component-wide checks cover complete/unique graph mapping, unresolved abbreviations/query/connectivity and any justified topology restriction. A distant heteroatom or carbonyl is not by itself a format-defined reason to reject a local carbon; removing the former whole-component guards still requires prospective native qualification. General cycle/aromatic coverage must not be inferred from a few accepted rings.

Keep exact source/sidecar/after-selection hashes, complete observation coverage, selected Objects=1/Atoms=1/Bonds=0 and selected ID, unchanged atom/bond attributes and label evidence, unchanged whole-document chemical export, warning classification, and precise process identity. Source and provenance failures are not bypassable H-coverage limitations.

## Independent controls before the candidate

Predeclare approximately 12-20 controls unrelated to 055, M2, their descendants and other reserved inputs. Define expected chemistry independently from simple constructed molecules, not from candidate readback. Include the variables the rule actually depends on: acyclic/cyclic environments, functional groups, carbonyls, heteroatom adjacency, saturated/unsaturated bonds and explicit H/D. Retain aromatic/query/radical/abnormal or other unqualified domains as unknown/unsupported. A historical negative renamed as a new positive is insufficient evidence.

Freeze raw source bytes, control inputs, expected definitions and a manifest before running. For every claimed native qualification execute open/cleanup/save, reopen the saved file in a different fresh initially empty native process, and invoke the actual delivered readback function. Compare graph and atom/H meanings against the predeclared control definition. Distinct-process native agreement proves consistency; the independent construction supplies the expected chemistry. Preserve first failures, classifications and any source/input revisions before a later run. Do not retroactively authenticate source via newline normalization.

Use existing receipts. Test counts belong to their exact executed version; excluded/unscheduled tests are not passes. Do not transfer the preceding no-independent-reopen cyclic control claim into this new required reopen gate.

## Fixed-input integration and stopping

After the declared control scope qualifies, freeze the complete runtime production tree and required compiler/probe dependencies, using exact Git blob bytes. Re-evaluate only retained candidate-side artifacts offline with the delivered API and all existing source/hash checks. Label this replay explicitly; it is not a new native run and cannot manufacture evidence for a changed observer. If a known capability rejection remains, record it and stop without a redundant candidate invocation.

A passing offline preflight permits this phase's one formal attempt with the unchanged migrated request: v0.2 validation/compiler/lowering, native fragments, every state's full semantic readback, the frozen Composer, final candidate native files/render, then the independent evaluator only if a complete candidate exists. No inference, manual IR edit, depiction change, sample replacement, hidden answer access or post-candidate profile expansion.

On readback failure, record exact field, qualification scope and first cause; close PARTIAL. On geometry/routing/collision failure, retain the first scene, mapping, candidate file and diagnostics without changing coordinates or thresholds. If chemical identity and provenance checks have passed and the file is safe to open, one diagnostic-only native render of the unchanged rejected candidate is allowed, outside the accepted registry. A source/identity failure cannot be bypassed to obtain a picture.

A complete candidate requires actual native save, independent fresh-process CDX and CDXML reopen, native PNG and actual object/editability evidence. Partial evaluator coverage never confers final visual PASS. File generation, zero warnings, reopenability and renderability are separate facts from visual acceptance.

## Deliveries and unchanged gates

Deliver precise implementation/test commits, a short new phase receipt linked to machine evidence, the predeclared control matrix and native reopen/source bindings, the fixed request's actual furthest stage and first blocker, any first Composer artifacts, and an Issue #2 handoff. Do not rewrite the prior phase receipt.

Chemical correctness, native visual quality, active manual correction time and human acceptance stay unmeasured where no corresponding independent evidence exists. Overall ChemDraw remains unaccepted, M1 has no new visual PASS and Gold stays zero. M2 and descendants/holdouts remain frozen, unread, unexecuted, untuned and unscored. No Composer geometry/routing/layout changes, corpus expansion, model training, MCP/installer/host/front-end work or new product task is authorized by this phase.
