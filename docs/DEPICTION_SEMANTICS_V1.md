# Depiction semantics v1

A chemical species can exist without appearing as a complete molecular drawing. Depiction semantics records that choice while preserving the chemical graph. This contract is part of [Mechanism IR v0.2](MECHANISM_IR_V0_2.md); it does not certify a native renderer.

## Species roles

| Role | Declared display intent |
|---|---|
| explicitly_drawn | Render the species as a chemical graph. |
| abbreviated | Render a named representation while retaining its complete chemical graph and explicit attachment binding where needed. |
| condition_caption | Represent the species in a condition caption. |
| reagent_caption | Represent the species in a reagent caption. |
| catalyst_caption | Represent the species in a catalyst caption. |
| counterion_hidden | Retain a chemically present counterion without a visible occurrence. |
| spectator_hidden | Retain a spectator without drawing it. |
| implicit | Preserve an explicitly declared implicit display choice. |
| omitted_by_convention | Preserve an explicitly supplied omission convention; never infer it from a hidden target. |

A DepictionState names chemical species through references. A visible caption may link several chemical species, for example a salt label describing an ion pair. Chemical presence is never implemented by deleting or inserting an atom because of a label.

An abbreviation has a label and, when electron-flow attachment requires it, an explicit chemical attachment atom. Lowering may not guess the reactive atom from a preferred heteroatom or decode an abbreviation into a replacement graph. A backend without a qualified abbreviation or caption port must return a capability/ambiguous-port diagnostic rather than silently expanding, hiding or rerouting it.

## Lone pairs

Chemical LP count belongs to ChemicalState. Displayed pairs and optional relative slot/orientation preferences belong to DepictionState. Displayed pairs cannot exceed the chemical inventory. A count of three with one visible pair is legal; zero visible pairs does not remove the donor's electrons.

ElectronFlow names a chemical LP donor and slot identity. A depiction policy explicitly decides whether a source pair must be visible, may use a virtual donor port, or is unsupported by the current backend. Undeclared hidden ports must not be fabricated from target geometry. Changing displayed pairs does not change formal charge or chemical valence.

## Typed text

Caption roles include condition, reagent, catalyst, solvent, temperature, time, workup, annotation, state_label and molecule_label. Text can bind species and a state/transition according to the schema. It is not a catch-all string whose position is guessed from state number.

Caption placement and abbreviation attachment use relative intent. Exact coordinates are calculated by Composer from intrinsic candidate geometry and a generic policy. Font/bond/style policy is separately frozen and cannot be altered to fit one screenshot.

## Lowering and native materialization

LoweredDepictionPlan is separate from the complete chemical IR. It records visible occurrences, expected visible atom/bond inventories, selected LP slots, typed captions, hidden reasons and resolved/unsupported flow-port requirements. It has no hidden-target geometry. Chemical and depiction plans have separate hashes.

Native seed generation uses the visible plan and candidate-derived intrinsic geometry. Native readback compares against the planned visible inventory, while chemical validation still uses the complete IR. Every generated native object maps back to its chemical/depiction reference. Abbreviated and caption objects are not falsely counted as missing chemical atoms.

General tests must show the same rules with multiple elements/counterions/reagents, arbitrary identities and different state counts. Unsupported display modes must fail by capability; a schema enumeration alone is not executed adapter support.

## Evaluation semantics

The hidden evaluator reports chemical mismatch, depiction mismatch, omitted-by-design, condition-only species, displayed-LP mismatch, electron-flow mismatch and geometry mismatch separately. An absent target counterion or unshown LP cannot by itself establish chemical error.

Target observations need qualified atom/state/species/port correspondence and explicit coverage. Native XML is useful object/geometry evidence, but does not automatically identify every chemical species, LP owner or condition role. Missing or partial annotations produce unknown/partial results. A target picture does not declare that everything unshown is chemically absent.

The original blind output can be migrated with preserve_v01_display and compared honestly as a literal full-inventory depiction. Matching the author's selective conventions is a separate task; no evaluator feedback is sent back to edit that candidate.
