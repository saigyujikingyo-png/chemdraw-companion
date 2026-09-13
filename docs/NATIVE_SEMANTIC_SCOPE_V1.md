# Native semantic readback v1: hydrogen scope

Status: original synthetic evidence independently verified; only 19 measured branches admitted. The fixed-input stage remains PARTIAL; see [the new phase receipt](NATIVE_SEMANTIC_PHASE_RECEIPT.md).
This document supplements [the phase protocol](NATIVE_SEMANTIC_READBACK_V1.md); it does not replace an execution receipt or amend historical results.

## Basis and evidence status

The latest source-only review covers delivery [56ace468](https://github.com/saigyujikingyo-png/chemdraw-companion/tree/56ace46880bf946e058b31695791e358398fec87), with execution-source reference [2d6ac0d8](https://github.com/saigyujikingyo-png/chemdraw-companion/tree/2d6ac0d8a510d912f8e03157cf182cd6ce403683).
It retains the carbon-API/non-carbon-field restriction reviewed at b674580 and introduces profile native-semantic-readback/1.1 with measured-branch admission.
The approved [7633111 control matrix](https://github.com/saigyujikingyo-png/chemdraw-companion/blob/76331117248c54a314dcd566586b2f187f7d5756/verification/2026-09-13-p0b-semantic-readback/inputs/control-matrix.json) contains 20 synthetic inputs and 66 atom nodes.
Its roles are 14 qualification candidates, three observation candidates, two unsupported negatives, and one deliberate conflict negative.
Ammonium and chloride may establish their explicitly bounded branches after measurement; methane and the conflict input remain diagnostic-only.

The [r2 implementation report](https://github.com/saigyujikingyo-png/chemdraw-companion/issues/2#issuecomment-5654655325) reports 16 matching controls, two unsupported contrasts, and two diagnostic controls across 40 fresh process identities.
It reports, in each 66-atom phase, 37 carbon API observations with missing NumHydrogens, 20 non-carbon field decodes, and nine unresolved atoms.
The [r3 implementation report](https://github.com/saigyujikingyo-png/chemdraw-companion/issues/2#issuecomment-5654703017) reports the same 20-control outcome under the tightened implementation and 62 guarded software tests.
Those r2/r3 reports retain their historical, implementation-reported status; they are not reclassified as final qualification.
The final r4 delivery at 1bcca3bf was independently retrieved: all 739 content members and 57 frozen source/input Git byte bindings match. The delivered verifier and actual production adapter were independently replayed on both phases: 16 matching controls / 57 atoms, two refusals, two diagnostic controls, and 19 measured branches. The original pending proposal is preserved; a new bounded admission record and full evidence hashes are linked in the phase receipt.
Within each phase, selection preserves full nested labels, atom/bond attributes and native chemical export. Across cleanup and a fresh-process reopen, nine controls have 11 label BoundingBox changes of 0.01; four of those controls also have five label-anchor changes of 0.01. Text, style and chemical graph agree; original geometric values are preserved. This is not cross-process geometry byte equality or visual acceptance.

## What is being counted

`implicit_h` remains the compatibility key for H attached to an atom without an independent native atom node.
Label H, a serialized NumHydrogens value, and a selected formula can describe the same attached H; they are not additive.
An independent H/D node retains its own native ID, chemical map, isotope, and bond and is counted once in the graph inventory.
D is Element=1 with Isotope=2. An isotope on a heavy atom identifies that heavy atom, not its attached H.
The [legacy NumHydrogens specification](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_NumHydrogens.htm) distinguishes an explicit zero from omission and excludes separately drawn H nodes.
Omission has a valence-dependent format meaning; this implementation does not recover it with an H/C/N/O valence table or an expected IR value.
These preserved CambridgeSoft SDK pages explain the old format; they are not ChemDraw 26 behavior guarantees.

## Conditions, reasons, and bounded controls

The following table separates atom-local interpretation from component or document integrity. A control example is evidence to obtain and verify, not a universal chemical theorem.

| Condition | Why this scope is needed | Positive controls and unresolved boundaries |
|---|---|---|
| All 118 element identities remain representable; H capability is separate. | Element identity is atom-local. The H resolver supports a much smaller domain and cannot declare other elements chemically illegal. | Encoding checks cover element symbols; native H observations here concern C/N/O, terminal H/D, and isolated chloride. Other elemental environments remain unqualified. |
| The ordinary connected component contains neutral, non-isotopic C/N/O and terminal H/D, with no radical or abnormal-valence evidence. | The current conservative predicate inspects the whole actual component to detect unresolved connectivity and unsupported states. Its name `normal` is not an independent valence-validity test. | Ethanol, ethylamine, acetone, acetaldehyde, acetic acid, methyl acetate, acetamide, ethene, and acetonitrile. Other charge states, heavy isotopes, and radical contexts are not inherited from these examples. |
| Each independent H/D is neutral, singly bonded, and terminal; its non-node H remains separate. | This is local to that node and its incident bond; the component must retain the complete H/D inventory. A bridging or multiply bonded H cannot be counted as an ordinary attached substituent. | CH2D-OH and H-C(=O)-D distinguish one and two independent hydrogen neighbors. Nonterminal H, other isotopes, and malformed bonds remain unsupported. |
| Every resolved carbon requires selected FormulaHTML from exactly one object, one atom, zero selected bonds, and the matching native atom ID. | Selection is local: a fragment formula or another atom's formula cannot stand in for the selected carbon. | The ordinary carbon controls exercise multiple functional-group environments. Wrong selection counts/ID, charged or isotopic carbon, and missing or malformed API output must not resolve H. |
| The carbon formula has one C, an optional H term, and the bounded cut-bond suffix; the suffix equals actual incident bond-order sum and native UsedValences. | Incident graph data checks the interpretation of the selected formula. It never supplies H by subtraction from a presumed valence. | Ethene and acetonitrile distinguish multiple-bond cuts; carbonyl controls distinguish H0/H1. The parser's H4 ceiling does not qualify isolated methane, whose component remains observation-only. |
| Supported non-carbon atoms require an explicit, parseable NumHydrogens field. | This is a local format decode, not a native API observation and not an omitted-field default. | O roles in alcohol, acid, ester, ether ring and carbonyl controls; N in amine, amide, nitrile and ammonium; terminal H/D and chloride. Missing fields remain unknown even if a label or expected value supplies a plausible answer. |
| Parsed atom-label identity/H must agree with the other available evidence. Labels alone do not resolve H. | This is local to the bound node. Complete nested text/run evidence is also preserved across the entire document so label-only changes cannot hide behind unchanged n/b attributes. | The CH4-text versus field-H3 seed is deliberately conflicting. Compound or unsupported labels remain unresolved; page text is never an atom label. |
| Acyclic components may contain ordinary single, double, and triple bonds within the stated domain. | Topology is component-wide, but a remote carbonyl or heteroatom is not itself a format-defined ambiguity in local carbon H. | The acyclic functional-group controls above. This does not qualify every amine, tautomer, conjugated system, or other possible C/N/O graph. |
| A cyclic component has exactly one cycle; its pruned core is saturated C5, C6, or C4O five-membered. | Cycle number, core membership, and internal edge orders require the complete component. Ring size is an explicit coverage limit, not an atom-ID or coordinate rule. | Cyclohexane, tetrahydrofuran, and cyclopentanone. Internal unsaturation, other core sizes/elements, and fused/spiro/bridged or multiple cycles remain unqualified. |
| A carbonyl outside the cyclic core is permitted within the other conditions. | Only edges within the cycle core must be single. Rejecting every carbonyl in the whole component would unnecessarily exclude this independently chosen control. | Cyclopentanone supplies the ring-external C=O contrast. Benzene is a frozen unsupported contrast; it does not establish a general aromaticity classifier. |
| Isolated N+ and Cl- have separate field-decoding scope. | Their component is a single node, so they cannot inherit carbon selection semantics or general charged-species support. | NH4+ and Cl-; a zero chloride H observation cannot be derived from UnusedValences. Other charged components remain unknown. |
| Actual CDXML query fields trigger the unqualified boundary. | Query restrictions can change the graph's meaning even when its displayed atom and H fields look ordinary; the policy is component-wide refusal. | The reviewed final source explicitly includes FreeSites, RingBondCount, UnsaturatedBonds, SubstituentsUpTo, SubstituentsExactly and ImplicitHydrogens. Its new test starts from an API-complete matching ethane baseline, adds each real field, expects component-wide unverified, and restores the matching baseline. This is source-reviewed test design, not a native query qualification claim. |

The [FreeSites](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_RestrictFreeSites.htm) and [RingBondCount](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_RestrictRingBondCount.htm) pages distinguish CDXML field names from SDK constant names.
The legacy [ImplicitHydrogens query restriction](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_RestrictImplicitHydrogens.htm) is not an H-count field or an automatic translation of the native ImplicitHydrogensAllowed property.
The [AbnormalValence specification](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_AbnormalValence.htm) explicitly leaves normal-valence conventions application-dependent.

## Provenance and comparison gates

Nonzero or unavailable warning evidence prevents a resolved H acceptance; zero warnings alone proves neither correct chemistry nor supported scope.
Every observation requires complete, unique native node/map and bond coverage; expected atom identity and graph checks remain independent of H matching.
Source, native artifact, sidecar, and selection-after hashes bind the raw evidence to the exact observer, parser, profile, and build.
Selection must preserve complete atom/bond attributes, nested labels, and the native chemical export. Conflicting or incomplete evidence cannot be repaired by choosing the value closest to expected IR.
Fresh initially empty workers need PID, OS start time, HWND-derived PID, job identity and document-count bindings. Existing native instances are preserved.
Cleanup and saved-file reopening occur in different fresh processes; reopen has no second cleanup. Same-process document reopening is insufficient independent disk-readback evidence.
Neither graph equality nor cross-process agreement is independent chemical truth; comparison uses the frozen, separately constructed control expectations.
`observe_document` accepts no expected IR. Later comparison returns match, mismatch, or unverified without changing observations.

## What may be claimed after verification

All seed nodes explicitly contained NumHydrogens. Only actual native output bytes establish which fields disappeared and which resolution branches executed.
Carbon-field-only and label-only resolution are disabled; non-carbon omission does not silently select another source.
The reviewed branch key records component scope, source class/field, serialized-H and label presence, atomic number, charge, isotope, resolved H, and the sorted multiset of independent H-neighbor isotopes. Native IDs and coordinates are not qualification selectors.
Admission requires coverage of the same branch in both cleanup and reopen phases, drawn only from matching controls. Production retains raw evidence but resolves an unlisted branch to unknown; missing production admission is rejected.
The qualification loader rechecks the complete bound control evidence and re-derives the admitted keys. This limits resolution branches; it is not a complete functional-group classifier or independent proof of chemical validity.
Software tests prove their synthetic guard behavior; they are not additional native controls or native quality passes.
The current 20-control scope provides no general 118-element H decoder, universal ring support, mechanism correctness, visual acceptance, or Gold promotion.
No predicate, control, or exception is justified by 055 or any private candidate identity, layout, target annotation, or expected answer.
Protected M2/derived/holdout material remains unread and outside this work. Historical failures and prior freezes retain their original bytes and status.
Any missing capability remains unknown; this scope document does not authorize a private retry, source revision, or post-candidate expansion.
