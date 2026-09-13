# Prospective P0-B native semantic readback implementation plan

Status: **preregistered; no native execution or qualification in this commit**. Runtime baseline is `bc428205a0066d7b544fe634910310d55fb3a893`. The architecture protocol is [c29af27](https://github.com/saigyujikingyo-png/chemdraw-companion/blob/c29af27d429a2e8c9fd4c4e94e0eb0def6071837/docs/NATIVE_SEMANTIC_READBACK_V1.md). Independent controller review of this frozen matrix is required before native execution. Existing failures, source-hash addenda and the preceding PARTIAL receipt remain unchanged.

## Observations and compatibility

The existing `implicit_h` key means attached H not represented as separate atom nodes. It remains an adapter compatibility key; earlier records are not relabelled historical errors. New evidence separately records serialized label-H fields, nested label tokens/runs, explicit H/D neighbor nodes, selected FormulaHTML, and the resolved non-node attached-H observation. Label H and attached H may refer to the same atoms and are never added together. Every explicit H/D node remains its own graph occurrence; D is Element=1, Isotope=2.

Each quantity has a value or null, source class (`explicit_native_field`, `native_api_observation`, `qualified_format_decode`, `unknown`), raw source/presence, exact artifact/node/map identity, qualification profile/scope and a reason for unknown/conflict. Expected chemistry is supplied only to a later comparison returning `match`, `mismatch` or `unverified`. Changing expected H cannot alter observations. Contradictory observations remain conflict/unverified, even if one value agrees with expected.

The preserved SDK [NumHydrogens definition](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_NumHydrogens.htm) concerns label-attached H, excludes independent H nodes, and gives omission a valence-dependent meaning. Omission is not zero. This first proposed implementation does **not** decode omission through a homemade valence table. The [Node definition](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/Node.htm) describes label/property redundancy and label-driven reading when Text exists. Label/field disagreements must therefore remain visible. These documents describe format semantics, not a ChemDraw 26 guarantee.

## Candidate rules for independent review

No rule below is qualified merely by being written here. Actual native results may narrow it; source/input revisions and failures must remain separate.

| Predicate or interpretation | Scope and protected ambiguity | Proposed positive/negative controls |
|---|---|---|
| Exact element-node identity, native ID/map, charge/isotope/radical and complete unique atom/bond inventory | Atom-local identity plus whole-document custody. Prevents observing a different atom or incomplete graph. All 118 element identities remain legal independently of H coverage. | All controls; unit negatives mutate identity, mappings and coverage. |
| Exact observer, bridge, parser, consumer and profile source bytes match an explicit frozen qualification manifest | Execution/provenance scope. Checking SHA syntax alone cannot establish a qualified implementation. Earlier observers are not automatically upgraded to a new scope. | Before/after source snapshots; wrong-source and stale-sidecar unit negatives. |
| Source and selection-after snapshots preserve atom/bond attributes **and complete nested atom-label evidence**, plus native chemical export | Whole-document integrity, not a carbon-neighbor whitelist. Detects label-only changes missed by an n/b-attribute-only comparison. | All native controls; unit mutation changes only nested H label text while n/b attributes remain identical. |
| FormulaHTML read for exactly one native object/atom, zero selected bonds, matching selected ID | Selection-local. Prevents parent-fragment/multiple-object formulas from being interpreted as an atom. | Ordinary controls; methane/ions can remain unknown when their selection is ambiguous. |
| Strict one-carbon FormulaHTML grammar; H term is the value, cut-bond suffix agrees with actual incident native bond orders and UsedValences | Local carbon API interpretation. The graph checks the meaning of the suffix; it does not calculate H. Normal neutral non-isotopic non-radical carbon only. | Alcohol, amine, ketone, aldehyde, acid, ester, amide, alkene, nitrile, carbon and heteroatom rings; grammar/count/charge/isotope/radical negatives. |
| Independent H/D neighbors retain their IDs, isotope and single-bond relation, separate from the selected atom's H term | Local counting boundary. Prevents counting graph H/D twice or treating heavy-atom isotope as attached D. | One explicit D in methanol; both explicit H and D in formaldehyde; malformed/nonterminal-H unit negatives. |
| Explicit NumHydrogens is first a raw label-H field; a bounded, independently qualified field/label interpretation may resolve non-node attached H | Local format decode, recorded as such. A missing field or unparseable/conflicting label does not supply a value. Initial candidates are normal C/N/O labels, isolated ammonium/chloride and terminal explicit H/D; admission is per demonstrated domain. | Neutral functional-group labels, NH4+, Cl-, explicit H/D and the deliberate CH4-text/field-H3 conflict. |
| No entire-component all-carbon/all-single-bond requirement merely because a carbon is cyclic | A remote carbonyl/heteroatom is not itself a format-defined H ambiguity. Actual native controls must qualify the selected formula interpretation in these environments. | Tetrahydrofuran, cyclopentanone and acyclic carbonyl/heteroatom cases; no reference geometry. |
| Aromatic/query/radical/abnormal or unresolved compound-label domains remain unknown/unsupported | A conservative capability boundary, not element illegality. Acyclic double/triple bonds and exocyclic carbonyls are distinct from unsaturated cyclic/aromatic scope. An initial conservative cyclic-unsaturation refusal is allowed, without calling it an aromaticity engine. | Benzene and methyl radical are frozen native contrasts. Query/abnormal flags and ambiguous labels are unit-only negatives and confer no native qualification. |

The native `ImplicitHydrogensAllowed` flag, if retained as a guard, is a recorded native condition and never an H count. It is not silently equated to the historical XML [query restriction](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_RestrictImplicitHydrogens.htm). [Abnormal valence](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_AbnormalValence.htm) remains unsupported; no universal normal-valence model is inferred from that property.

## Frozen control matrix

The generator contains literal per-atom expected chemistry, not an inferred valence engine. Its checked-in outputs under `verification/2026-09-13-p0b-semantic-readback/inputs/` are the frozen execution inputs. `control-matrix.json` supplies opaque maps, expected non-node attached H, explicit H/D neighbors, charge/isotope/radical and bonds separately from the eventual native observations. Native serialization may omit a field or change label representation; those are measured, not prefilled from expected values.

| Input | Distinction to observe |
|---|---|
| Methane | Isolated C/H4; ambiguous selection or warning leaves the corresponding capability unknown. |
| Ethanol | Saturated carbon, C-O adjacency and OH label. |
| Ethylamine | C-N adjacency and NH2 label. |
| Label/field conflict | Nested text CH4 versus scalar H3; no single expected H is selected to force a pass. |
| Acetone | Carbonyl carbon H0 and neighboring methyls. |
| Acetaldehyde | Carbonyl carbon H1. |
| Acetic acid | Carboxyl carbon and two distinct oxygen/H roles. |
| Methyl acetate | Ester linkage and O-bound methyl. |
| Acetamide | Carbonyl/N adjacency and NH2. |
| Ethene | Acyclic unsaturation. |
| Acetonitrile | Acyclic triple bond and nitrogen endpoint. |
| Cyclohexane | Saturated carbon ring baseline. |
| Tetrahydrofuran | Saturated ring with a heteroatom. |
| Cyclopentanone | Saturated ring bonds plus exocyclic carbonyl. |
| Carbon-deuterated methanol | Separate D node plus non-node C-H and O-H. |
| Explicit H/D formaldehyde | Two separate H/D neighbors; carbon non-node H0. |
| Benzene | Unqualified aromatic contrast; raw observations do not confer support. |
| Methyl radical | Unqualified radical contrast. |
| Ammonium | Explicit label H4 and positive charge; API ambiguity is independent. |
| Chloride | Explicit zero/negative charge; UnusedValences must never supply H. |

Some small synthetic chemistry types appeared in earlier exposed controls. This is not an unseen claim. Their old refusals and artifacts are not reclassified; most functional-group inputs and the new scope/label/reopen checks are prospective. Nothing is derived from 055, target images/geometry/IDs, M2, descendants, holdouts or evaluator corrections.

## Execution and evidence gate

1. Send this input/expectation freeze commit and source manifest through Issue #2. Await independent controller review before opening native software. Code and unit-test preparation may continue meanwhile.
2. Freeze the actual observer/bridge/consumer/parser/profile and required source/dependency bytes before execution. Use exact Git blob bytes and explicit existing qualification receipts; no retrospective newline explanation.
3. Recheck local process/job state. Preserve all existing instances. Create a new initially zero-document worker, bind native PID, OS start time, HWND and job/run ID, and retain owned document handles. Any competing/unbound instance fails isolation rather than being closed.
4. Execute open/cleanup/save against each frozen synthetic input. Preserve the original, warnings, raw fields/labels, failures and code/input bindings. The deliberate conflicting input is a diagnostic negative, not a chemistry qualification positive.
5. Reopen the saved native file in a different new initially zero-document process without another cleanup. Capture a new hash-bound snapshot and run the actual proposed semantic reader. Retain native-ID changes separately from the preserved chemical atom mapping; compare both native phases to the independent expected chemistry.
6. Require source/identity/graph/label/selection/hash integrity before admitting H. Different-process native agreement establishes consistency only; expected chemistry comes from the predeclared construction. Report raw observations, format/API-qualified values, conflict/unknown, warning exclusions and comparison results separately.
7. Preserve first errors and any reviewed corrections as new revisions. Final counts name the exact executed version; excluded/unscheduled tests are never added to PASS. Deliver the complete frozen runtime source/dependency file list to the controller.

No new dependency, service, model, platform or UI is proposed. Planned runtime work is a small scoped semantic-observation/parser module, exact source qualification binding, nested-label-aware invariance, and reuse/factoring of the existing observer with a fresh-process reopen probe. Final filenames and hashes will be enumerated after implementation; Composer geometry/routing/thresholds, IR v0.2 and installer/MCP surfaces are untouched.

Only the controller may replay retained candidate-side evidence, decide whether an old observer satisfies the new scope, and permit this phase's at-most-one unchanged blind request. Known replay rejection stops that run. No post-candidate profile extension or layout repair is authorized. Overall acceptance remains unestablished; M1 has no new visual PASS, M2/holdout stays frozen/unread/unscored, Gold=0.
