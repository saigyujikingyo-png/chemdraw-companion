# Native runtime integration for Mechanism IR v0.2

The runtime consumes the unchanged executable contract from architecture commit `ea8f6b7b324f9f0fd0091b52052486374de4f4e7`. It performs no migration or inference automatically. The custodian supplies a v0.2 mechanism and an explicit layout policy. Both `composer-request/0.1` and `composer-request/0.2` envelopes are accepted for a v0.2 mechanism; dispatch is by `mechanism.ir_version` and does not invoke the legacy HCNO semantic validator.

Use `probes/run_composer.py validate|seed|compose --request REQUEST --out NEW_DIRECTORY`. Compose also requires `--seed SEED_DIRECTORY --native NATIVE_FRAGMENT_DIRECTORY`. The existing `probes/run_paired_candidate.py` wraps seed, native cleanup, compose and independent CDX/CDXML reopening with immutable inputs and bounded workers. Existing output paths are rejected.

The seed and composition receipts retain `ir_sha256`, `chemical_inventory_sha256` and `depiction_plan_sha256`, plus the exact lowered plan and compiled flows. Native geometry receipts bind their input files, source hashes, visible atom manifest, style and native binary identity. A caller-supplied plan must equal deterministic lowering of its supplied IR. Chemical inventory remains complete even when its depicted subset is smaller. Original source/sink ports remain in each routed flow's `lowered_ports` record.

The adapter uses all 118 contract element identities to encode atomic numbers. This is an encoding capability, not native execution or chemical validity for every element. Native readback compares explicit serialized identity/H/charge/isotope fields and the depicted bond graph. **An omitted CDXML `NumHydrogens` produces `NATIVE_HYDROGEN_UNVERIFIED`; it is not inferred from a valence table or replaced with expected IR values.** A generic carbon-containing control currently reaches this boundary. COM `NumImplicitHydrogens` observations are optional raw evidence and are not a qualified total-H oracle.

| Depiction feature | Current bounded evidence/status |
| --- | --- |
| Selected LP with nonzero chemical pair index | Static water control draws one selected pair from a two-pair chemical inventory; explicit atom fields, one LP, caption and LP bounding vector retained in native import and independent CDX/CDXML readbacks |
| Virtual LP source | Lowering/composition preserves an undrawn source port; generic flow control stops at the existing arrow label-clearance frontier; no final native flow quality claim |
| Hidden counterion | Synthetic test preserves complete inventory while excluding the native atom occurrence |
| Condition-caption species alongside a visible species | Native control retains one visible atom, hidden chemical inventory and both typed caption texts through independent CDX/CDXML readbacks |
| Entirely caption-only state | `NATIVE_CAPTION_ONLY_STATE_UNSUPPORTED` diagnostic |
| Abbreviations | Explicit capability rejection; no expansion or guessed attachment geometry |
| LP orientations other than `auto` | Explicit capability rejection; orientation intent remains in the plan |
| Isotopes | Generic N/P/Na/Cl controls retained explicit isotope/H/charge fields after native cleanup/serialization; that control did not undergo independent disk reopening |
| Radical atoms / one-electron native arrows | Explicit capability rejection; never serialized as full two-electron arrowheads |
| Bond-to-nonendpoint atom | Contract and seed accept the general flow; original sink preserved. Native generic control stops at omitted carbon hydrogen metadata before layout |

The existing frozen route search constants are unchanged. A v0.2 composition that reaches a layout or route-clearance frontier records failure; if a scene was generated, its first scene/mapping/CDXML is retained and the paired runner does not continue to final native export. No reference-based layout correction or automatic retry is performed.

`stage-result.json` separates checked semantic invariants from native capability or geometry failure. A successful stage is not full chemical validity, physical-size visual acceptance, product acceptance or Gold. The legacy `verify_composition.py` has no v0.2 depicted-subset contract; do not use it to certify v0.2 output. The independent architecture evaluator remains a separate integration boundary.

Run `probes/run_ir_v02_regression.py --output NEW_RECEIPT` for the explicitly audited synthetic runtime subset. It records exclusions and unscheduled tests separately, with an additional protected-payload file-open guard. Its source selection does not establish protection against arbitrary renamed/embedded derivatives. The native control summary is in `verification/2026-09-13-ir-v02/runtime-controls.json`; all failed first outputs remain preserved privately. No protected evaluation chemistry, private blind IR, target image or new model inference was used for these controls.
