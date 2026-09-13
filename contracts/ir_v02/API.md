# Mechanism IR v0.2 contract API

This package separates complete chemical inventory from drawing intent. It neither reads hidden targets nor emits absolute coordinates or native object IDs. It does not establish native quality or full chemical validity.

```python
from contracts.ir_v02 import (
    IRContractError, migrate_v01, validate_mechanism,
    compile_electron_flows, lower_depiction, validate_depiction_capabilities,
)
result = migrate_v01(old_ir, policy="preserve_v01_display")
report = validate_mechanism(result)
flows = compile_electron_flows(result)
plan = lower_depiction(result)
```

`migrate_v01(ir, *, policy="strict", depiction_states=None)` returns an independent JSON-compatible v0.2 object. Strict migration requires explicit depiction states and fails with `MIGRATION_DEPICTION_REQUIRED` otherwise. The explicitly selected `preserve_v01_display` policy draws every old chemical component, preserves every declared chemical lone pair as displayed, and retains state/transition labels as typed captions. It preserves legacy behavior; it does not infer the author's intended depiction. Both policies preserve chemical intent and rename flow `target` to `sink`. Migration records the policy and canonical SHA-256 of its v0.1 input; it is deterministic and has no target argument.

The old `atom_catalog`, `states`, `transitions`, `stereo_constraints` and `entry_state` remain. Catalog atoms have `map`, `element`, `implicit_h`, and optional `isotope` and `radical_electrons`. Isotope is immutable atom identity. State `atom_properties` may override implicit H or radical count, but never isotope. State `formal_charges`, `lone_pairs` and `bonds` are chemical inventories. Each state's `chemical_species: [{id, atoms: [map]}]` must exactly partition its graph into connected components, including isolated ions.

`depiction_states` contains exactly one record per chemical state:

```json
{
  "state_ref": "s0",
  "species": [{"species_ref": "component-id", "role": "explicitly_drawn"}],
  "lone_pairs": [{"atom_ref": 1, "displayed_pairs": 1,
    "slots": [{"pair_index": 0, "orientation": "auto"}]}],
  "captions": [{"id": "caption-id", "role": "state_label", "text": "Initial state"}]
}
```

Species roles are `explicitly_drawn`, `abbreviated`, `condition_caption`, `reagent_caption`, `catalyst_caption`, `counterion_hidden`, `spectator_hidden`, `implicit`, and `omitted_by_convention`. Abbreviations require `label`; optional `attachment_atom_ref` identifies their chemical attachment port. Captions have typed roles and optional `species_refs` (multiple disconnected species may share a caption) or `transition_ref`. Caption roles are condition, reagent, catalyst, solvent, temperature, time, workup, annotation, state_label and molecule_label. Absent LP display entries mean zero displayed pairs, not zero chemical pairs. Slots use chemical pair indices and qualitative orientations; omitted slots are deterministically expanded in index order with `auto` orientation.

Flow sources are `lone_pair`, `bond`, `atom`, or `radical`; sinks are `atom`, `bond`, or `forming_bond`. `electron_count` is 1 or 2. `effect`, when supplied, contains explicit bond/charge changes and cannot override the graph difference. Bond-to-nonendpoint-atom flows are valid ports; the compiler checks their relationship to the declared graph changes without imposing a reaction template. One-electron and atom-source profiles retain explicit unsupported coverage diagnostics. The current contract does not claim a complete electron-accounting proof.

`validate_mechanism(ir)` returns separate checked-invariant, chemical-validity, valence-coverage and depiction results or raises `IRContractError(code, path, message, details)`. Legal element symbols cover all 118 IUPAC elements; an uncovered valence is not an invalid element. `compile_electron_flows(ir)` returns normalized ports, actual graph/charge deltas and coverage diagnostics, without coordinates. `lower_depiction(ir)` returns `lowered-depiction/0.2`, the canonical chemical-IR hash, complete chemical inventory, visible atom/bond occurrences, selected LP slots, caption/abbreviation occurrences, hidden species with reasons and flow ports. Undisplayed LP sources use an explicit atom-associated virtual port; hidden/unanchored endpoints remain typed unresolved depiction diagnostics. Consumers must not replace diagnostics with guessed geometry.

`validate_depiction_capabilities(ir, capabilities)` accepts explicit capabilities (elements, isotope/radical support, roles, flow electron counts and virtual LP ports) and reports unsupported/unknown requirements separately. It never changes chemical validity. Native IDs are adapter-local occurrence mappings, not chemical identity.

CLI: `python -m contracts.ir_v02 {validate,migrate,compile,lower} INPUT --output NEW_JSON`, with migration `--policy strict|preserve_v01_display` and optional `--depiction JSON`. Successful output or a typed failure receipt is written to a new output path; existing files are never overwritten. There is no implicit version dispatch.

Element-symbol source: [IUPAC periodic table, 4 May 2022](https://iupac.org/wp-content/uploads/2022/05/IUPAC_Periodic_Table_A3-04May22.pdf). The source establishes element identity, not this prototype's valence coverage.
