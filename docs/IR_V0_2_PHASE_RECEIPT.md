# Mechanism IR v0.2 phase receipt

13 September 2026. **IN PROGRESS: migration and native fragment generation completed; composition is blocked at native hydrogen readback. One bounded generic hydrogen fallback investigation remains pending. This is not phase or product acceptance.**

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
| New runtime integration | 16 | Four atom-identity and twelve v0.2 runtime synthetic tests against frozen `c37fa926` |
| **Local total** | **351** | **235 legacy + 100 new contract/evaluator + 16 runtime; eight protected-content tests deliberately excluded** |

The 235 selected legacy cases had zero unittest failures, errors or skips. Their initial audit wrappers returned exit 1 because they classified 22 denied import-cache probes as failures. Offline inspection identified all 22 as caches for approved modules, with no protected-fixture access. The wrapper classification was corrected without rerunning the tests; original logs were retained. Selected source hashes were identical before and after. Excluded tests are not counted as passes, and protected chemistry was neither read nor hashed.

The first combined new-suite invocation exposed a test import error. The test now supports package-relative imports and discovery; semantic code was unchanged. The final independent run passed 100 cases with exit 0 in 0.839 seconds. With the existing dependencies configured, the focused command is:

```text
python -B -m unittest contracts.ir_v02.test_ir_v02 contracts.paired.test_depiction_semantics
```

The independent runtime run passed its sixteen cases with zero failures, errors or skips. It imported an inspected synthetic helper only for constructors, without running that helper's suite. All 24 frozen production code/schema files and the exported test/metadata blobs remained unchanged. The local total combines separately receipted runs; it does not mean the entire 351-case set was rerun at the final runtime revision. The supplier's separately reported 34-test result is not added to this local count. Supplier public runtime-control metadata was received, but its linked fresh native-control files have not been fetched and independently qualified here.

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
| Migration/contract-review core | `5c7ccfe89a1cb80ad64eee32abf6ba2365aab7738b94afb58ffaca013d5e1d8f` |
| v0.2 schema | `4c50013e774530315f90d4cd6d15309d3e72edca52ad58b61f0986c6fbb79e4d` |

File-byte hashes differ from canonical JSON/IR hashes by design; they are not interchangeable. Original bytes were preserved.

## First native attempt: readback blocker

The unchanged migrated request was submitted to runtime commit `c37fa926ac3aa33dfc2348dd3355c975595cb137`. Seed generation completed with exit 0, and the ChemDraw 26.0.0.6141 native fragment stage completed for all three states. Each per-state document had 17 atoms, 14 bonds and zero reported warnings. The independent receipt verified 55 artifact bindings and unchanged request/code bytes. Seed and compose workers each retained access-denied results for all six synthetic hidden categories; the hidden target was not accessed.

Composition exited 1 at `native_geometry_readback` with `NATIVE_HYDROGEN_UNVERIFIED`. The adapter required an explicit `NumHydrogens` value that native serialization omitted. This is a native identity/readback integration blocker, **not an observed Composer geometry, routing or collision frontier**. No full composed candidate, final native CDXML/CDX pair or hidden-target evaluation exists from this attempt. The first failure remains preserved.

A separate partial field review found that all 51 visible atom identity occurrences and 42 bond occurrences matched the declared plan in its checked fields. Eighteen atom occurrences retained an explicit `NumHydrogens` attribute, all with value zero; the other 33 omitted that attribute. This counts metadata observations, not eighteen hydrogen atoms. Missing values remained unknown, so complete native readback did not pass.

The initial field-review derivation mistakenly read `charge` instead of the plan's `formal_charge`, producing two spurious charge mismatches per state. The corrected v2 derivation removed those false mismatches without changing native artifacts or runtime code; the original v1 report remains preserved.

## Independent hydrogen observation

An unrelated local synthetic document supplied 21 atoms and 210 native property observations, with zero warnings, on the same ChemDraw build. All observed `NumImplicitHydrogens` values were zero, including familiar structures with hydrogens. `UnusedValences` also cannot serve as a universal hydrogen count: the chloride-anion control reported one unused valence while its saved label-hydrogen count was zero. These measurements disprove direct substitution of either field as a generally verified hydrogen observation.

The primary SDK description defines `NumHydrogens` as hydrogen content of an atom label and marks the property optional; when omitted, the format specifies the minimum count needed to satisfy valence. It is not a mandatory serialized total-hydrogen field. This format rule motivates a bounded, independently checked interpretation; it does not qualify the current adapter's implementation. [ChemDraw CDX SDK: Atom_NumHydrogens](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_NumHydrogens.htm).

The observation used a process bound to its native window with zero initial documents. There was no independent disk reopen. Close returned without error, but the subsequent document count was one; an empty application after close was not established. The first summary had a string/integer atom-reference join error and is retained beside corrected summary v2. The final artifact manifest binds both summaries and unchanged native originals. This was a raw property experiment, not a qualified fallback, a composed mechanism or native visual acceptance.

Two additional **selected-Formula** experiments retained separate first-attempt evidence. Attempt 01 used `Document.Selection.Formula` directly and failed with `PropertyNotFoundStrict` because that was the wrong interface member. No Formula value, FormulaHTML value or after-operation chemistry comparison was obtained. Its apparent `Selection.Count` was a PowerShell scalar count, not native `IChemDrawObjects.Count`; the independent selected-atom and selected-bond enumerations remain observations, but that count cannot establish exactly one selected native object. The original summary and eleven-entry artifact manifest are preserved.

Attempt 02 used typed `IChemDrawDocument.Selection` → `IChemDrawSelection.Objects` → `IChemDrawObjects.Formula/FormulaHTML`. Four carbon controls each had exactly one selected object and zero selected bonds. FormulaHTML retained contextual H counts 0/2/3/2 for acetone carbonyl carbon, ethene carbon, ethanol terminal carbon and ethanol middle carbon, respectively. Before/after atom and bond attributes and chemical SMILES were identical for all four controls. The output also adds radical superscripts for external bonds omitted from the selection: these are selected-fragment formulas, not complete formulas of the original atom states. Plain Formula strings had a corrupted bullet-marker encoding; the raw strings remain preserved, while FormulaHTML is unambiguous for these four observations.

The chloride-anion control then returned `Objects.Count = 2`, despite enumerating one selected atom and zero selected bonds. The extra object's identity was not inspected. The guard stopped **before reading its formula**, so chloride H capability was not measured and attempt 02 retains an overall failed-run status. Its sixteen-entry manifest binds the summary and original evidence; attempt 01's manifested assets remain unchanged. The four carbon observations establish a narrow native observation only. They do not qualify a general hydrogen fallback, and this local selection-formula route stops at that scope.

**TODO/pending:** the existing implementation task must complete production fallback implementation/qualification and report any authorized rerun of the unchanged original blind candidate. Neither outcome is established by these observations. Do not insert expected IR hydrogen values into native observations, change the blind input, or tune sample geometry.

## Compatibility and evaluator limits

The previously executed supplier proton-transfer control uses the runtime v0.1 dialect. Its three atoms, two states, one transition and two flows migrated, validated, compiled and lowered without editing chemical intent. Its original wrapper SHA-256 remained `484ad2475f7f0982d78b9d4393789617fa8a748bf4fd8c5ed4812173b4e41549`. This compatibility check made no native or model calls.

No runtime-dialect M1 IR was available in the bounded safe inventory. The inspected M1-facing entries were recipe/SMILES inputs, not a runtime mechanism IR. M1 runtime migration compatibility is therefore **not established**. The separate archival corpus tests passing do not replace it; the two dialects are not interchangeable. No synthetic replacement was relabelled M1, and no new M1 visual PASS is claimed.

The current adapter explicitly rejects abbreviations, non-automatic LP orientations, radicals and one-electron flows where native depiction is unsupported. Contract representation is broader than qualified native capability; the 118-element identity model is not full native element coverage.

The evaluator separates chemical, depiction, omitted-by-design, condition-only, displayed-LP, flow-semantic and geometry findings. Target qualification and candidate IR validation remain separate. Without independently qualified target semantics and correspondence, the relevant result is unknown. LP ownership and arrow ports are not inferred from native proximity. Partial geometry reports must pass the existing evaluator contract and hash checks, but do not establish native visual PASS, authentic review or an IR-to-native provenance chain.

## Eight requested answers

| Question | Current evidence-bound answer |
|---|---|
| 1. Can v0.2 express the sample's complete chemical intent? | It expresses and preserves all chemical intent supplied in the original blind IR. Independent correctness of the source chemistry is not proved; validation covers 45 atom-state inventories and leaves six Br/K valence occurrences uncovered. |
| 2. Are chemical and depicted inventories separate? | Yes at contract/lowering level, with independent hashes; the partial native fragment check agrees on 51 atom identities and 42 bonds. **Pending:** complete hydrogen readback and full native materialization. |
| 3. Can selected LPs, counterions and abbreviations be expressed without changing chemistry? | Yes in IR and unrelated synthetic plans. Runtime controls check selected LPs, hidden ions and captions, but abbreviations and non-auto LP orientations currently receive explicit unsupported diagnostics. The real sample retains compatibility display; author-specific omissions were not inferred. |
| 4. Is bond-to-nonendpoint-atom flow handled generically? | Yes in the compiler and synthetic runtime controls; the sample's six flows compile without the legacy endpoint rule. Complete native flow geometry has not been generated or evaluated. |
| 5. Are v0.1 fixtures compatible? | The receipted runtime proton-transfer control passes migration, validation, compilation and lowering; 28 archival corpus tests pass separately. Runtime M1 compatibility remains unestablished. |
| 6. What is the furthest actual stage? | Seed and all three native fragment stages completed. Compose then stopped at native geometry readback; no full candidate, final native pair or hidden evaluator run. **TODO/pending:** final bounded investigation outcome. |
| 7. What is the current blocker? | `NATIVE_HYDROGEN_UNVERIFIED`: required explicit H metadata is absent in native serialization. The local property experiment rules out naive COM-field substitutions. This is not yet a geometric-quality failure. **TODO/pending:** qualify or reject the bounded general fallback. |
| 8. Should work return to Composer geometry? | Resolve or explicitly stop at the native readback boundary first. Geometry has not yet become the observed frontier. **TODO/pending:** the final bounded outcome determines the next stage; no sample-specific layout repair is authorized by these results. |

## Pending outcome and gates

**TODO/pending for the execution owner:** record the bounded hydrogen fallback decision, any authorized implementation/input hashes and actual rerun result. Preserve the first failure. A full candidate, final fresh-process native pair, evaluator result and qualified port/ink measurements remain absent unless a later receipt explicitly establishes them. No hidden target was read to prepare this update.

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
| Independent first native attempt, 55 artifact bindings | `6e1c13e687c483464db91c36ee093a3f028e12f27df18dd86b190542b025163e` |
| Corrected native field coverage v2 | `b80fd69f246ceb178883dbea0f871ec7aba042e264fde3bacba3eac826139c2d` |
| Independent sixteen runtime tests | `a7d31e1d50a505c3f2f266d0f9372e4c101bf232d8f6c5a7f8418b018e289d35` |
| Local hydrogen observation summary v2 | `64b03c9a2bd6c4f58817f8bace68c6c6439b5b1296343ae3308c8ad2036d2212` |
| Local hydrogen final artifact manifest | `3d46f1e26a09d16ac2579e2e62847a4b313aafdfa879853375c4049a83cef068` |
| Selected-Formula attempt 01 summary, retained interface failure | `b588ee5e492c5e456f88373d8c3c50ac3054db9a5c705d3fa0576dc279d743a5` |
| Selected-Formula attempt 01 artifact manifest | `1e20c7fe7f1ac502e782d985f417e52bf6731ba28d16db9a04a76135d127992f` |
| Selected-Formula attempt 02 summary, four carbon observations | `2cfd96d4838f1c4184fc909ef6cea0c1576aa6373aca034b0e74ca12023d64be` |
| Selected-Formula attempt 02 artifact manifest | `ba084ee8a127ffe75d0b02c6d107f4e0d63fd772b0e5e2da447a228075980568` |
