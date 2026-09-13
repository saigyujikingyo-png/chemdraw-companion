# Mechanism IR v0.2 phase receipt

13 September 2026. **PARTIAL: the representation/compiler deliverables and three unchanged-input native attempts are recorded. The final attempt still stops at native hydrogen readback, before Composer layout. The required full candidate and native comparison gate was not met; no phase or product acceptance is claimed. This bounded phase is closed without another repair or rerun.**

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
| **Legacy/core/evaluator subtotal** | **335** | **235 legacy + 100 new contract/evaluator, from their separately receipted runs** |
| Latest runtime integration | 26 | Thirteen atom-identity and thirteen v0.2 runtime synthetic tests against frozen `bc428205`; 23 repeated cases and three added cases |
| **Local distinct-case total** | **361** | **335 + latest 26 runtime; earlier runtime cases are not added again; eight protected-content tests deliberately excluded** |

The 235 selected legacy cases had zero unittest failures, errors or skips. Their initial audit wrappers returned exit 1 because they classified 22 denied import-cache probes as failures. Offline inspection identified all 22 as caches for approved modules, with no protected-fixture access. The wrapper classification was corrected without rerunning the tests; original logs were retained. Selected source hashes were identical before and after. Excluded tests are not counted as passes, and protected chemistry was neither read nor hashed.

The first combined new-suite invocation exposed a test import error. The test now supports package-relative imports and discovery; semantic code was unchanged. The final independent run passed 100 cases with exit 0 in 0.839 seconds. With the existing dependencies configured, the focused command is:

```text
python -B -m unittest contracts.ir_v02.test_ir_v02 contracts.paired.test_depiction_semantics
```

The earlier `c37fa926` runtime checkpoint passed sixteen cases and remains retained. The intermediate independent run against `df00f5f64af2a58418d229e2ed73517ae98c24a9` executed all 23 cases in the same two modules once, with zero unittest failures, errors or skips. Sixteen case identities repeat the earlier checkpoint and seven are added. The inspected synthetic constructor helper is byte-identical to its previously reviewed Git blob; its own suite was not run. All 24 monitored code/schema files and all six exported test/helper/metadata blobs remained unchanged. Twenty-three monitored files match the runtime commit's exact Git blobs; the remaining architecture firewall helper is explicitly identified by the source manifest and was not imported by these tests.

The intermediate df00f5f wrapper returned exit 1 because it classified thirteen blocked optional `.pyc` cache probes as failures. Offline review mapped every denial to an allowed `.py` module that subsequently loaded successfully. The original failed wrapper receipt and log remain unchanged; no tests were rerun. The first offline provenance classifier also stopped when it assumed the architecture helper belonged to the runtime commit; the corrected classification preserves that failure and records the separate provenance. This is a Python audit-hook plus inspected-source boundary, not an OS isolation claim.

The final independent run against `bc428205a0066d7b544fe634910310d55fb3a893` executed 26 cases once, with zero failures, errors or skips and wrapper exit 0. These are the previous 23 case identities plus three cyclic-profile cases. All thirteen optional cache probes remained denied; the wrapper classified them against approved source paths and actual successful module loads, with zero boundary violations. All 24 monitored code/schema files and four exported Git blobs remained unchanged; 23 code/schema entries match this runtime commit and the separately manifested architecture firewall helper was not imported. The constructor helper suite was not run. This remains an audit-hook and inspected-source boundary, not OS isolation.

The 361-case total combines separately receipted runs; it does not mean all 361 were rerun against `bc428205`. Supplier-reported historical 34-, 41- and 44-case results are not added. Its public H-control metadata was retrieved as an exact Git blob, but its `chemdraw_cdxml.py` SHA-256 (`ab984b5d3a1c69286cc836e92668efb744060a07d972de285293715b7ad69646`) does not match that file in the frozen runtime (`46d5516c2880e454b48a2b4c6bb4309b2246ed5a3aa5fb69f32d991df30f95fd`), including ordinary LF/CRLF projections. Those supplier native claims are not thereby bound to this exact runtime; linked supplier native files were not retrieved for this review. The independently executed local production controls below are separate evidence. The later `bc428205` hash addendum reconstructs the old adapter hash using a specific 120-line mixed-ending transformation; independent review reproduced it. This explains the byte difference but does not retroactively authenticate the earlier execution bytes. The historical report is unchanged.

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

The primary SDK description defines `NumHydrogens` as hydrogen content of an atom label and marks the property optional; when omitted, the format specifies the minimum count needed to satisfy valence. It is not a mandatory serialized total-hydrogen field. This format rule motivates a bounded, independently checked interpretation; it does not by itself qualify an adapter implementation. [ChemDraw CDX SDK: Atom_NumHydrogens](https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_NumHydrogens.htm).

The observation used a process bound to its native window with zero initial documents. There was no independent disk reopen. Close returned without error, but the subsequent document count was one; an empty application after close was not established. The first summary had a string/integer atom-reference join error and is retained beside corrected summary v2. The final artifact manifest binds both summaries and unchanged native originals. This was a raw property experiment, not a qualified fallback, a composed mechanism or native visual acceptance.

Two additional **selected-Formula** experiments retained separate first-attempt evidence. Attempt 01 used `Document.Selection.Formula` directly and failed with `PropertyNotFoundStrict` because that was the wrong interface member. No Formula value, FormulaHTML value or after-operation chemistry comparison was obtained. Its apparent `Selection.Count` was a PowerShell scalar count, not native `IChemDrawObjects.Count`; the independent selected-atom and selected-bond enumerations remain observations, but that count cannot establish exactly one selected native object. The original summary and eleven-entry artifact manifest are preserved.

Attempt 02 used typed `IChemDrawDocument.Selection` → `IChemDrawSelection.Objects` → `IChemDrawObjects.Formula/FormulaHTML`. Four carbon controls each had exactly one selected object and zero selected bonds. FormulaHTML retained contextual H counts 0/2/3/2 for acetone carbonyl carbon, ethene carbon, ethanol terminal carbon and ethanol middle carbon, respectively. Before/after atom and bond attributes and chemical SMILES were identical for all four controls. The output also adds radical superscripts for external bonds omitted from the selection: these are selected-fragment formulas, not complete formulas of the original atom states. Plain Formula strings had a corrupted bullet-marker encoding; the raw strings remain preserved, while FormulaHTML is unambiguous for these four observations.

The chloride-anion control then returned `Objects.Count = 2`, despite enumerating one selected atom and zero selected bonds. The extra object's identity was not inspected. The guard stopped **before reading its formula**, so chloride H capability was not measured and attempt 02 retains an overall failed-run status. Its sixteen-entry manifest binds the summary and original evidence; attempt 01's manifested assets remain unchanged. The four carbon observations establish a narrow native observation only. On their own they did not qualify a production fallback. The later production controls below provide separate, bounded qualification.

## Production H profile and second native attempt

The next runtime was frozen at `df00f5f64af2a58418d229e2ed73517ae98c24a9`; its source-manifest SHA-256 is `8b1918625218c1fa39e7acc1e7abd276d935a9694989746da6c41e54d56d4949`. Its `native-carbon-selection-formula-h/0.1` profile reads strict one-carbon FormulaHTML after exactly one selected native object and atom, zero selected bonds, verified identity, unchanged whole-document chemical export, and exact before/after atom and bond attributes. It does not substitute expected IR H, `UnusedValences` or `NumImplicitHydrogens`. Its qualified scope excludes rings, charged/radical/isotopic carbon and standalone H4; at most one appropriately qualified directly bonded explicit H or D is allowed.

A separate local production-native batch used this frozen worker and ChemDraw 26.0.0.6141. Six controls passed the actual frozen readback APIs: ethene, ethyne, fluoromethane, tetrafluorocarbon, a C-F-H control and a C-F-D control. They supplied eight carbon observations covering H0/1/2/3; the last two returned implicit H2 while retaining the separate explicit H/D atom. Methane/H4 had one warning and two selected native objects, was stopped before FormulaHTML, and correctly remained `NATIVE_HYDROGEN_UNVERIFIED`. Its rejection is not an H4 capability pass. The generator's stale explicit-H/D eligibility flag was recorded but was not used to decide qualification; actual API checks governed. The qualification and 53-file manifest bind this one native batch, with zero retries and unchanged source/input bytes. **No independent disk reopen occurred**, and this is not complete mechanism or native visual acceptance.

The unchanged migrated request then underwent the second real integrated candidate attempt. Seed and native fragment stages completed; compose exited 1 at `native_geometry_readback` with `NATIVE_HYDROGEN_UNVERIFIED`. The driver records unchanged original/staged request, unchanged code, no model calls and no hidden-target access. Seed and compose used the restricted worker; the native custodian used candidate-only arguments outside that OS restriction, so whole-host isolation is not claimed.

The independent candidate-only audit verified all 61 artifact byte/hash bindings, 25 recorded code-file bindings and equal before/after code manifests, plus unchanged original/staged request bytes. It verified six actual denial controls in each of the seed and compose processes. All three native states had zero warnings and passed the full provenance/sidecar-0.4 binding API. Actual `read_explicit_geometry` passed the first two states, each with 17 atoms and 14 bonds; the third state remained rejected.

The same carbon had a one-object, one-atom, zero-bond selection and FormulaHTML H2 observations in all three states. Its open-chain occurrences satisfy the current neighborhood profile, whereas its final-state ring occurrence does not. This is the next **P0-B native atom-readback/profile capability blocker**, before layout: there is no observed Composer routing, collision or geometric-quality frontier from attempt 02. No full composed candidate, final native pair or hidden-target evaluator run was produced. The driver, diagnosis and independent audit are retained; the audit made no additional native call and did not override the ring exclusion.

## Final cyclic qualification and third native attempt

The final runtime was frozen at `bc428205a0066d7b544fe634910310d55fb3a893`, with source-manifest SHA-256 `090cf26d22f50c6c1f6e8ec8253709948ae6f1e8687cc44ed4ddbd6e0a3928eb`. Profile `native-carbon-selection-formula-h/0.2` preserves the earlier acyclic behavior. Its cyclic extension checks the entire connected native component: every atom is ordinary neutral, non-isotopic, non-radical carbon and every bond is single; removing terminal trees must leave one 3-8 member cycle containing the queried atom with degree two at each core node. Carbonyl or other heteroatom/multiple-bond components, fused/spiro/bridged/joined cycles, and other unqualified profiles remain rejected. This is a bounded capability qualification, not a general chemistry model. Strict FormulaHTML parsing and all selection, identity, source/hash and unchanged-graph checks remain required.

Six independently constructed generic cyclic controls were captured once, before final qualification, using the exact frozen native observer. They contained 28 atoms and 27 carbon observations, with zero warnings. The predeclared controls were saturated C3/C4/C6 rings, a carbonyl-bearing C4 ring, a C4 ring with one double bond, and a Kekule C6 contrast. No mechanism, protected example or target geometry was used. The old df00f5f consumer rejected all six; this observation was retained rather than relabelled a pass.

Independent offline re-evaluation with the actual bc428205 consumer verified 98 sealed artifact bindings across those six controls and the earlier seven production controls. The observer, bridge and native-common bytes matched their original executed bytes, so no new native control call was made. Saturated C3/C4/C6 now passed full atom/graph readback; carbonyl, unsaturated and Kekule rings remained rejected. All six earlier acyclic/H-D positives and the methane rejection were preserved. Thus 13 controls produced nine bounded passes and four expected refusals. Disk reopening and complete mechanism visual quality are outside this control evidence. Supplier cyclic-control claims remain separate, without independently retrieved supplier native originals.

A private alternative consumer was retained for review only. It was not installed, committed, used for candidate execution or substituted for bc428205; its 39 offline checks are not counted as production coverage or qualification.

The unchanged request underwent the final integrated attempt at 14:28 UTC on 13 September 2026. Seed completed in 0.688 s, native fragments in 4.484 s, and compose stopped after 0.656 s. All three native documents again had 17 atoms, 14 bonds and zero warnings. Independent audit verified all 61 artifact bindings, 25 code-file bindings, equal code manifests, unchanged original/staged request, and six actual denial controls in each restricted seed/compose process. The full native provenance API and all three sidecar-0.4 bindings passed. The original driver and its candidate-only native-custodian limitation remained unchanged.

Actual native readback passed the first two states completely. The final state failed with `NATIVE_HYDROGEN_UNVERIFIED` under profile 0.2. Its reported atom's connected cyclic component failed the **all-carbon** and **all-single-bond** requirements. The five-atom cycle core met the size and degree-two checks; this is not evidence of a fused or multiple-cycle topology problem. A correctly bound one-object/one-atom/zero-bond native CH2 observation does not override an unqualified component.

The first, second and third failures are preserved. There is still no full composed candidate, final candidate CDXML/CDX pair, fresh-process final reopen/render, or hidden-target evaluation. The evaluator wrapper was prepared but never executed, and target contents were not read. This remains a **P0-B native atom-readback capability blocker before layout**, not an observed Composer geometry/route/collision failure. No fourth attempt, further profile relaxation, target-derived edit or layout tuning was made.

## Compatibility and evaluator limits

The previously executed supplier proton-transfer control uses the runtime v0.1 dialect. Its three atoms, two states, one transition and two flows migrated, validated, compiled and lowered without editing chemical intent. Its original wrapper SHA-256 remained `484ad2475f7f0982d78b9d4393789617fa8a748bf4fd8c5ed4812173b4e41549`. This compatibility check made no native or model calls.

No runtime-dialect M1 IR was available in the bounded safe inventory. The inspected M1-facing entries were recipe/SMILES inputs, not a runtime mechanism IR. M1 runtime migration compatibility is therefore **not established**. The separate archival corpus tests passing do not replace it; the two dialects are not interchangeable. No synthetic replacement was relabelled M1, and no new M1 visual PASS is claimed.

The current adapter explicitly rejects abbreviations, non-automatic LP orientations, radicals and one-electron flows where native depiction is unsupported. Contract representation is broader than qualified native capability; the 118-element identity model is not full native element coverage.

The evaluator separates chemical, depiction, omitted-by-design, condition-only, displayed-LP, flow-semantic and geometry findings. Target qualification and candidate IR validation remain separate. Without independently qualified target semantics and correspondence, the relevant result is unknown. LP ownership and arrow ports are not inferred from native proximity. Partial geometry reports must pass the existing evaluator contract and hash checks, but do not establish native visual PASS, authentic review or an IR-to-native provenance chain.

## Eight requested answers

| Question | Current evidence-bound answer |
|---|---|
| 1. Can v0.2 express the sample's complete chemical intent? | It expresses and preserves all chemical intent supplied in the original blind IR. Independent correctness of the source chemistry is not proved; validation covers 45 atom-state inventories and leaves six Br/K valence occurrences uncovered. |
| 2. Are chemical and depicted inventories separate? | Yes at contract/lowering level, with independent hashes. In the final attempt, two states pass complete native readback of 17 atoms and 14 bonds each; the final cyclic state remains unqualified, so complete mechanism materialization is unestablished. |
| 3. Can selected LPs, counterions and abbreviations be expressed without changing chemistry? | Yes in IR and unrelated synthetic plans. Runtime controls check selected LPs, hidden ions and captions, but abbreviations and non-auto LP orientations currently receive explicit unsupported diagnostics. The real sample retains compatibility display; author-specific omissions were not inferred. |
| 4. Is bond-to-nonendpoint-atom flow handled generically? | Yes in the compiler and independently replayed synthetic runtime controls; the sample's six flows compile without the legacy endpoint rule. The real sample's full native flow geometry remains ungenerated and unevaluated. |
| 5. Are v0.1 fixtures compatible? | The receipted runtime proton-transfer control passes migration, validation, compilation and lowering; 28 archival corpus tests pass separately. Runtime M1 compatibility remains unestablished. |
| 6. What is the furthest actual stage? | Three real attempts completed seed and native fragment generation. The final attempt passes full readback of its first two states, then rejects the last cyclic component before layout. No full candidate, final native pair or hidden evaluator run exists. |
| 7. What is the current blocker? | `NATIVE_HYDROGEN_UNVERIFIED` in P0-B native readback: the final cyclic component is outside profile 0.2 because it contains non-carbon atoms and non-single bonds. Ring size and degree-two core checks pass. It is not a measured geometry/collision failure. |
| 8. Should work return to Composer geometry? | The observed frontier remains the native adapter. A future bounded phase must qualify a general, independently observed H/identity interpretation for realistic functionalized cyclic components before the unchanged input can establish Composer geometry behavior. The current evidence does not call for another sample-specific IR/compiler rule or any visual tuning. This phase stops here. |

## Final outcome and gates

**PARTIAL; minimum execution gate unmet.** The machine representation now carries all supplied blind intent through migration, validation and generic lowering. The real sample has not yet crossed the complete native atom-readback boundary, so the intended composition problem is not experimentally reached. Schema/test success, native fragment cleanup, full mechanism editability, visual quality and human acceptance remain distinct.

No further native API exploration, repair, inference, corpus expansion, learned training or peripheral product development was started after the final failed attempt. The next phase should address the bounded native adapter evidence gap without relaxing identity checks or changing the frozen blind input. M2 and holdouts stay outside that work.

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
| Historical independent sixteen runtime tests, superseded in current count | `a7d31e1d50a505c3f2f266d0f9372e4c101bf232d8f6c5a7f8418b018e289d35` |
| Local hydrogen observation summary v2 | `64b03c9a2bd6c4f58817f8bace68c6c6439b5b1296343ae3308c8ad2036d2212` |
| Local hydrogen final artifact manifest | `3d46f1e26a09d16ac2579e2e62847a4b313aafdfa879853375c4049a83cef068` |
| Selected-Formula attempt 01 summary, retained interface failure | `b588ee5e492c5e456f88373d8c3c50ac3054db9a5c705d3fa0576dc279d743a5` |
| Selected-Formula attempt 01 artifact manifest | `1e20c7fe7f1ac502e782d985f417e52bf6731ba28d16db9a04a76135d127992f` |
| Selected-Formula attempt 02 summary, four carbon observations | `2cfd96d4838f1c4184fc909ef6cea0c1576aa6373aca034b0e74ca12023d64be` |
| Selected-Formula attempt 02 artifact manifest | `ba084ee8a127ffe75d0b02c6d107f4e0d63fd772b0e5e2da447a228075980568` |
| Frozen df00f5f runtime source manifest | `8b1918625218c1fa39e7acc1e7abd276d935a9694989746da6c41e54d56d4949` |
| Intermediate independent 23-case runtime review, with cache-probe classification | `cac52b73f4cd9da0d3b228deb7d1e3aa1baf45000136854829ea6195e1e9bed7` |
| Intermediate raw runtime wrapper receipt, retained failed classification | `2f319e18ca87911ace676641beaad7d643dc19e6784daf47fd37dbac0853eeb1` |
| Supplier public H-control metadata, exact Git bytes only | `6a6b528808c931d5f34e552a0b2988c1c9fbd81943cd2b53078c7824ee11861a` |
| Independent local production H qualification, six positive controls | `c6098b6572a8e3ee4bdb627800fb74b877263be83c7eddc9bd95c1bb971a34cb` |
| Local production H artifact manifest, 53 files | `6d3cc35d373c63f4f5e94dfbbff1801c88d84eed10d5240689aa9428db7a7feb` |
| Second native candidate driver, retained failure | `8d5a6ebe3948f7a3798c7478f14b7fa258e4ff6bd6a237d48012ca7bc3742bd9` |
| Second native candidate-only diagnosis | `d59bd36776971c9ed56e18a62d33022dee8e07c4b98c57d7a67832cbec201b16` |
| Independent second native candidate audit, 61 artifact bindings | `31ce78ed74ce2c942a78fd6572c40274708e464a8b52f99186f253d0593b8dff` |
| Final frozen bc428205 runtime source manifest | `090cf26d22f50c6c1f6e8ec8253709948ae6f1e8687cc44ed4ddbd6e0a3928eb` |
| Final independent 26-case runtime review | `d1a35bbcf51393f8f7b49558b745f16fc1d25e7ab23ff5d6a3f5ee3d43d84a52` |
| Final runtime test execution receipt, exit 0 | `b4a4507c635ef8b3b9c1a99a54601535a456db17c122738d1b3895c926854a19` |
| Independent cyclic native observation, six controls | `28331ca1bc6136be58be6a70a9fdab5866f74dd2c5e28d08bee209fc345f1ad8` |
| Independent cyclic native artifact manifest, 45 files | `e0a00e71b5fe20df2e9ab06bb818e94fda70aec39f1cdc229ae56b54cee16478` |
| Final consumer re-evaluation, 13 controls / 98 artifact bindings | `e3ce9eeb862e9b28b1ed533788bbe1d29fd54c24aed0d1ab8930169d0163da6b` |
| Third native candidate driver, retained failure | `d7e3a0a22951f0bb6d57932649bb74e1f0d5c4dce349df5d52f3bd2724aa36e6` |
| Independent third candidate audit, 61 artifact bindings | `bbb08b8f01f09171df2f37759543ade7e90aa2ec79ab1445e584b2be5abde597` |
| Independent bc428205 code and hash-addendum review | `79970e1ecc0617948823d2146c5af9aff0c39a24528250aa1046a681a29ee972` |
