# General electron-flow compiler v1

ElectronFlow describes electron movement. BondChange and ChargeChange describe differences between chemical states. The compiler retains all three rather than forcing a reaction template to derive every effect.

## Semantic ports

| Source | Sink | Interpretation and checks |
|---|---|---|
| LonePairRef | AtomRef | A chemical LP donates toward an atom; validate availability and related state changes. |
| LonePairRef | BondRef / FormingBondRef | A donor contributes to a bond; retain explicit endpoints and formation/order effects. |
| BondRef | AtomRef | A bond's electrons move toward an atom, which need not be one of the source bond endpoints. |
| BondRef | BondRef / FormingBondRef | Bond electrons contribute to another bond; state differences supply independent graph evidence. |
| AtomRef / RadicalRef | AtomRef / BondRef / FormingBondRef | Represent one-electron intent when specified; unsupported validation/rendering profiles remain explicit. |

A source bond identifies its atoms and sigma/pi intent. A sink forming bond identifies both endpoints, rather than relying on a preferred atom or reaction name. Source/sink references must resolve to the correct state occurrences. No native object IDs or Bezier coordinates are accepted.

A bond-to-nonendpoint-atom flow is not generally invalid. Its source electrons, sink atom and related graph changes are cross-checked. If compilation requires a prospective bond and the declared graph changes determine a unique compatible bond, a generic resolution may bind that bond while retaining the original sink. If multiple interpretations remain, report ambiguity; do not select one from a benchmark identity or screenshot.

## Cross-validation

The validator compares declared bond_changes and charge_changes against actual before/after state differences. Duplicate, dangling, contradictory or undeclared graph changes are rejected. Electron source availability, pair reuse, sink identity and optional effects are checked independently.

Flow/graph consistency is a declared validation profile, not a claim that every real mechanism has one universal arrow-to-charge template. Unsupported electron/valence profiles are reported with coverage. Loosening a template must not let clearly contradictory electron direction or effects pass. A supplied effect is checked against the real graph; it cannot override it.

The compiler emits semantic source/sink bindings, checked changes, diagnostics and provenance. Relative depiction requirements are lowered separately. It must not choose routes, copy target coordinates or infer display omissions. Geometry remains Composer's responsibility.

## Runtime integration

Version dispatch validates v0.1 using its unchanged schema and routes v0.2 to its own contract. Compatibility migration is explicit and independently receipted. Legacy runtime validation cannot be called afterward in a way that reinstates the old H/C/N/O or migrating-endpoint rejection.

The native adapter uses a general atomic-number model and a qualified visible-inventory plan. Its capability diagnostics distinguish isotope/radical, hydrogen/valence readback, abbreviation ports and unsupported representation from invalid chemistry. Readback must not silently infer missing hydrogens with the former four-element dictionary.

The existing candidate entry performs the same ordered stages: validation, lowering, candidate-derived native intrinsic geometry, Composer, native materialization and fresh-process save/reopen/render. No new product wrapper or model call is required.

## Bounded rerun and stop rule

The regression input is the unchanged original PNG-only response. An explicit deterministic migration is preferred over a new inference. Freeze original/migrated IR, code/schema, compatibility policy, layout policy and candidate-only input packet before execution. Preserve the first attempt and its stderr/artifacts.

Run at most one initial integrated candidate attempt, followed only by bounded, general implementation corrections justified by contract/integration defects. Stop when the candidate reaches geometry/route/collision limitations; do not change sample coordinates, style thresholds, labels or chemical/display intent to make that picture pass.

After a native candidate exists, the evaluator may join it with the hidden target. Its report separates semantic, depicted-object, geometry and native visual evidence. Visible arrowhead tips remain native pixel observations, not spline endpoints. Unqualified port/ink measurements stay unmeasured.

The final receipt answers the eight requested questions: full chemical intent, inventory separation, selected LP/counterion/abbreviation expression, nonendpoint flows, v0.1 compatibility, furthest real stage, new frontier blocker, and whether further IR work or Composer geometry now has priority. Overall ChemDraw remains unaccepted; M1 has no automatic new visual PASS; M2 is frozen/unscored; gold remains zero without genuine human evidence.
