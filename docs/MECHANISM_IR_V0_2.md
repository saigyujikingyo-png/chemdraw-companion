# Mechanism IR v0.2

Phase scope, 13 September 2026: separate chemical inventory, depiction intent and electron-flow semantics, then run the existing external blind IR through the existing native pipeline. This document defines the implementation contract; the rerun receipt, rather than this design, establishes executed capability. No corpus expansion, learned training, MCP/installer/host/UI work or new user-owned development task is part of this phase.

## Representation boundary

Mechanism IR contains chemistry, identity, state transitions, semantic electron flow, depiction intent and relative constraints. It contains no target CDXML IDs, answer-side coordinates, target Bezier curves or evaluator annotations. Complete chemical data remains immutable when a rendering policy hides a species.

The v0.2 family keeps atom_catalog, states, transitions and entry_state to support explicit version dispatch. The original mechanism-ir/0.1 schema, old examples and historical verification bytes remain intact. A new schema lives under contracts/ir_v02; it does not silently replace the old schema at its URI.

| Concept | Meaning |
|---|---|
| Atom identity | Stable map, valid element and isotope identity; no native object ID. |
| ChemicalState | Bond graph, formal charges, radicals, implicit hydrogen and chemical LP inventories. |
| ChemicalSpecies | A connected chemical component with explicit atom membership and state-local identity. |
| DepictionState | How that state is displayed, independently of whether its species exist chemically. |
| DepictedSpecies | A reference to a chemical species plus a declared display role and optional label/attachment binding. |
| ElectronFlow | Semantic donor and sink, electron count and optional declared effects; not a drawing spline. |
| Transition changes | Actual before/after bond and charge differences, retained independently of arrows. |

Species membership partitions a state's chemical inventory. References must resolve, IDs must be unique, and no bond may disappear because its species is hidden. Unsupported pathway or valence profiles are distinguished from malformed chemical data.

## Elements and state properties

The element model represents all 118 named elements with atomic numbers, using the [IUPAC periodic table](https://iupac.org/wp-content/uploads/2022/05/IUPAC_Periodic_Table_A3-04May22.pdf). It is not a permitted-element list tailored to a reaction. Element identity, chemically justified valence coverage and a backend's ability to depict an element are independent checks.

H/C/N/O, halogens, B/Si/P/S and Li/Na/K/Mg are naturally members of that model. A valid element with unqualified valence must report incomplete chemical-validation coverage, not an invented universal octet result. A renderer that cannot depict a valid atom raises a depiction capability error. Neither diagnostic authorizes changing the atom.

Isotope is part of stable atom identity. Formal charge, radical electrons and implicit hydrogen may have explicit state properties. State comparisons verify declared changes and conserved inventory; an unspecified property cannot be silently inferred from a target picture.

## API and validation layers

The executable contract exports:

    migrate_v01(ir, *, policy="strict", depiction_states=None)
    validate_mechanism(ir)
    compile_electron_flows(ir)
    lower_depiction(ir)
    validate_depiction_capabilities(ir, capabilities)

Errors expose a code, path, message and details through IRContractError. Syntax, referential/graph invariants, valence coverage, flow consistency and depiction validity are separate results. A syntactically valid model response is not full chemical approval.

The compiler and depiction lowering are pure operations on IR and declared policy. Their outputs retain chemical and depiction identities and independent hashes. The native adapter generates its own IDs; those mappings are output-side provenance, never an input answer key.

## Explicit migration

The default strict migration requires explicit depiction semantics when v0.1 cannot distinguish chemical inventory from intended display. It reports MIGRATION_DEPICTION_REQUIRED (migration requires explicit depiction semantics) rather than guessing hidden spectators or condition captions.

The explicitly chosen preserve_v01_display policy is a compatibility operation: it deterministically preserves the old Composer's full chemical inventory, all declared LPs and existing labels as visible content. It derives component identities from the graph and renames flow target to sink. It does not infer abbreviations, source-specific omissions or captions from hidden answers. Repeated migration of identical bytes/policy must produce identical semantic content.

This compatibility policy is used for the existing frozen PNG-only output. It preserves the original chemical intent but does not claim to recover the original author's display conventions. The migrated candidate therefore may show more species and LPs than the target. That is an exposed depiction difference, not permission to rewrite the original blind result.

A migration receipt binds original bytes, policy, schema/code hashes, migrated output and chemical-inventory/flow invariants. The original IR and prior failure receipts are immutable. If a requested conversion is ambiguous or unsupported, it fails explicitly.

## Regression and exclusion

Tests cover general elements, alternative halogen/counterion combinations, chemical/display separation, typed captions, selected LPs, bond-to-nonendpoint-atom and bond-to-bond flows, LP donors, migration and leakage. The receipted runtime-dialect proton-transfer control passed explicit migration, validation, compilation and lowering, and 28 archival corpus controls passed separately; runtime-dialect M1 compatibility is not established because no such IR was available in the bounded safe inventory. See the [API](../contracts/ir_v02/API.md) and [phase receipt](IR_V0_2_PHASE_RECEIPT.md) for scope and evidence; reproduce the focused contract controls with `python -B -m unittest contracts.ir_v02.test_ir_v02 contracts.paired.test_depiction_semantics`. Historical evidence is not relabelled.

M2 Beckmann Snake, all descendants and future holdouts are excluded from this entire phase, including design, debugging, fixtures, rule derivation and acceptance. Exclusion tests use metadata-only sentinels, not protected chemistry. M1 is exposed development and has no new visual PASS without an actual qualifying rerun.
