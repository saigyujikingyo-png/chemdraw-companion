# Mechanism IR v0.2 phase receipt

13 September 2026. **Draft: contract, migration and bounded regression evidence complete; native candidate execution and hidden evaluation pending. This is not phase or product acceptance.**

The phase addresses the representation failures exposed by `flynn-aldol-055`. It does not expand the corpus, train a model or add MCP, installer, host or UI features. The original blind response and earlier failed Composer attempt remain immutable. No new inference was made for migration or these checks.

## Executed evidence

The new [IR contract](MECHANISM_IR_V0_2.md), [depiction semantics](DEPICTION_SEMANTICS_V1.md), [electron-flow compiler](ELECTRON_FLOW_COMPILER_V1.md) and [Python API](../contracts/ir_v02/API.md) separate complete chemical inventory from display intent. The element model represents 118 element identities; this is not 118-element chemical-validation or native-renderer coverage.

| Test group | Executed and passed | Scope |
|---|---:|---|
| Existing corpus | 28 | Archival corpus contracts and controls |
| Existing quality | 130 | Selected permitted quality/correction controls |
| Existing paired | 69 | Extraction, evaluator, metadata and API controls |
| Existing OS firewall | 8 | Actual restricted-process access controls |
| New IR v0.2 core | 57 | General elements, migration, graph/flow checks, depiction and capability diagnostics |
| New depiction evaluator | 43 | Qualified semantic subsets, display distinctions, correspondence and geometry-evidence negative controls |
| **Total** | **335** | **235 legacy + 100 new; eight protected-content tests deliberately excluded** |

The 235 selected legacy cases had zero unittest failures, errors or skips. Their initial audit wrappers returned exit 1 because they classified 22 denied import-cache probes as failures. Offline inspection identified all 22 as caches for approved modules, with no protected-fixture access. The wrapper classification was corrected without rerunning the tests; original logs were retained. Selected source hashes were identical before and after. Excluded tests are not counted as passes, and protected chemistry was neither read nor hashed.

The first combined new-suite invocation exposed a test import error. The test now supports package-relative imports and discovery; semantic code was unchanged. The final independent run passed 100 cases with exit 0 in 0.839 seconds. With the existing dependencies configured, the focused command is:

```text
python -B -m unittest contracts.ir_v02.test_ir_v02 contracts.paired.test_depiction_semantics
```

These tests establish bounded implementation behavior, not native output or complete chemical correctness.

## Isolated deterministic migration

The explicit `preserve_v01_display` policy was applied to the original PNG-only model response. It preserves chemical fields, graph/charge changes and all six electron-flow intents, with the documented `target` to `sink` key rename. It adds explicit component and depiction records without using target geometry or interpreting the author's conventions.

The first restricted worker attempt failed with `VALIDATOR_DEPENDENCY_UNAVAILABLE`: `jsonschema` was unavailable under its dependency access setup, so no syntax validation occurred. This dependency/ACL failure is retained. A separately manifested copy of 146 existing dependency files made them accessible to the worker. The second attempt, with the same code-manifest hash, completed migration, validation, flow compilation and depiction lowering; exit 0. Six synthetic hidden categories returned access-denied results. This establishes the worker's tested boundary, not isolation of the entire operator or host.

The migrated candidate still has 17 catalog atoms, three states, two transitions and six flows. Checked graph/reference invariants pass. Limited H/C/N/O/F inventory checks cover 45 atom-state occurrences; the six Br/K atom-state occurrences have unimplemented valence profiles. `chemical_validity` remains `not_established`. Flow coverage is `checked_relationships_only`, depiction is `intent_valid`, and native capability/visual quality are not yet measured by this evidence.

The compatibility depiction plan contains 51 visible atom occurrences, 42 visible bonds, 30 displayed LPs, five captions and six flows, with no hidden species. This intentionally preserves the old full-inventory display. It does not recover the author's selective LPs, omitted spectators or abbreviated conditions. Separate unrelated synthetic controls demonstrate those v0.2 representations.

| Immutable artifact | SHA-256 |
|---|---|
| Original blind IR bytes | `093048ab3fb1f5e3a92f2fe41b25b567d7c205550cdf1bcf64cde59197577efc` |
| Migrated IR bytes | `677d7a7685d7a73b633c681d7e9ccd07fd04fe69297132f2f2e78c0c96060a53` |
| Migrated candidate request | `77c0021772916bac9731a53a76f4833720249692ed141372b28a0fef6ec7395e` |
| Validation receipt | `0543732fe67e7d2ce01e2d1a603312eafb868f31c1eabf92e40a6420dbae90fc` |
| Electron-flow plan | `56eb444e2be02f222c7f27a0b7127225fde5284995f9eac12bc6cd7356117810` |
| Depiction plan | `c29f00d64f959242ec6389360be763f377fbe6d8310b76edaacfd3a9d5275f0c` |
| Isolated-worker code manifest | `3f3034fa25b2254765e85a692461bb0ce5c8ac032ee22e666c1f810a55c0ba06` |
| Executed core | `5c7ccfe89a1cb80ad64eee32abf6ba2365aab7738b94afb58ffaca013d5e1d8f` |
| v0.2 schema | `4c50013e774530315f90d4cd6d15309d3e72edca52ad58b61f0986c6fbb79e4d` |

File-byte hashes differ from canonical JSON/IR hashes by design; they are not interchangeable. Original bytes were preserved.

## Compatibility and evaluator limits

The previously executed supplier proton-transfer control uses the runtime v0.1 dialect. Its three atoms, two states, one transition and two flows migrated, validated, compiled and lowered without editing chemical intent. Its original wrapper SHA-256 remained `484ad2475f7f0982d78b9d4393789617fa8a748bf4fd8c5ed4812173b4e41549`. This compatibility check made no native or model calls.

No runtime-dialect M1 IR was available in the bounded safe inventory. The inspected M1-facing entries were recipe/SMILES inputs, not a runtime mechanism IR. M1 runtime migration compatibility is therefore **not established**. The separate archival corpus tests passing do not replace it; the two dialects are not interchangeable. No synthetic replacement was relabelled M1, and no new M1 visual PASS is claimed.

The evaluator separates chemical, depiction, omitted-by-design, condition-only, displayed-LP, flow-semantic and geometry findings. Target qualification and candidate IR validation remain separate. Without independently qualified target semantics and correspondence, the relevant result is unknown. LP ownership and arrow ports are not inferred from native proximity. Partial geometry reports must pass the existing evaluator contract and hash checks, but do not establish native visual PASS, authentic review or an IR-to-native provenance chain.

## Eight requested answers

| Question | Current evidence-bound answer |
|---|---|
| 1. Can v0.2 express the sample's complete chemical intent? | It expresses and preserves all chemical intent supplied in the original blind IR. Independent correctness of the source chemistry is not proved; validation coverage remains partial, including uncovered Br/K valence. |
| 2. Are chemical and depicted inventories separate? | Yes at the contract and lowering layers, with independent chemical/depiction hashes. **TODO/pending:** native materialization/readback evidence. |
| 3. Can selected LPs, counterions and abbreviations be expressed without changing chemistry? | Yes in unrelated synthetic contract controls. The real sample uses explicit compatibility display, not inferred author intent. **TODO/pending:** executed native capability results. |
| 4. Is bond-to-nonendpoint-atom flow handled generically? | Yes in the compiler and synthetic controls; the migrated sample's six flows compile without the old endpoint restriction. This is bounded graph-relationship checking, not complete electron-accounting proof. |
| 5. Are v0.1 fixtures compatible? | The receipted runtime proton-transfer control passes all four contract stages; 28 archival corpus tests pass separately. Runtime M1 compatibility remains unestablished. |
| 6. What is the furthest actual stage? | Isolated migration, validation, general flow compilation and depiction lowering completed. **TODO/pending:** the execution owner must insert the actual Composer, native save/reopen/render and evaluator outcomes. |
| 7. What is the new frontier blocker? | The migration dependency/ACL failure was resolved and retained. **TODO/pending:** actual integrated native/geometry attempt determines the next blocker; no native success or geometry failure is inferred here. |
| 8. Should work return to Composer geometry? | Proceed to the bounded existing native integration attempt. **TODO/pending:** its observed result determines whether integration work remains or geometry is the next frontier. Stop on the first geometry/route/collision limit; do not tune this sample toward its target. |

## Pending native evidence and gates

**TODO/pending for the execution owner:** record the implementation/input hashes; first attempt and any permitted general correction; candidate CDXML/CDX/render hashes; fresh-process reopen/readback results; target/candidate evaluator outcomes; unmeasured native ports/ink; and the precise stop-stage/blocker. No hidden target was read to prepare this draft.

ChemDraw overall = **not accepted**. M1 = exposed development, **no new visual PASS**. M2, descendants and future holdouts = **frozen, excluded and unscored**. Gold = **0**; active human correction time = **null**. No phase acceptance is claimed.

Private originals and detailed logs remain private. Sanitized evidence bindings:

| Receipt | SHA-256 |
|---|---|
| Independent contract review | `36ee95b52ec9e0035b11939a6d0aa0f4c6fd92be76d868aaff21dbe5e1a2e3c6` |
| Selected legacy regression summary | `e27f21fa28465576ac6790ec25ff723755f97c687e2847d458885a74c9298a21` |
| First migration failure | `1e7767827692b45a041a3a16404903a696228a4826c3419b56e3581fed41ef70` |
| Second migration success | `84b49534578319a53ab5a3cb07cf1e2dd44f48635fa9e45d8fe9e5723761e289` |
| Dependency-copy manifest, 146 files | `a046aa3e96422ef304b4efce98938db58179cdf834d8fdd97d1a4211c364e880` |
| Runtime legacy compatibility | `cbe55840690a3e3f27d9229af2e1a340c209e157dc10cf5a7368694f57ac472c` |
