# R3: general verifier repairs and independent native geometry controls

This is an engineering checkpoint, **not P0 acceptance**. It responds to the review of `eb8b4c869a23237f726f8cf127be18743f573a14` in architecture commit `d12ec4e7830a0c9f60197a416886afba90ab20ff`, merged without replacing the implementation branch.

The newer corpus-phase instruction takes precedence: M1/M2 are **exposed_and_tuned regression references**. They are excluded from training/correction corpora and unseen benchmarks. No new holdout is selected, no training/crawling begins, and R2's exhausted two-repair allowance remains unchanged. This evidence archive is not a corpus ingestion.

## Implemented and verified

- Scene comparison now validates both scenes against the supplied IR before comparing geometry: complete identity bijections, state/atom/component/bond/LP/flow/connector inventories, duplicate identities, exact control/path lengths, finite coordinates, atom chemistry, aromatic valence and specified double-bond stereo. Actual bond rendering and atom label records are also compared. A single verified global symmetry remains allowed across all states; a state-local identity swap remains rejected.
- Colour-copy readback now checks actual `ArrowheadWidth`, `CurveType`, head/line/fill fields, effective run fonts with font-table mapping/inheritance, relevant document defaults, and text runs bound to their owning atom. Consistent font-ID renaming is allowed; changed fonts, defaults or ownership are rejected.
- Mixed-colour contact exceptions retain the permitted object pair and colour contributors. A third object cannot borrow a legitimate contact circle. Ambiguous colour-pair explanations fail closed. This is a conservative colour-mixture diagnostic with native object bounds; it is not a general proof against fully occluded objects or all raster ambiguities.
- The capability matrix now identifies tested native methods, mutation mode, formats, immutable evidence revisions and untested scope. It no longer presents the historical SaveAs/process-binding failures as the current result.

**47 tests pass.** Nine retained scene corruptions are rejected, including the four review counterexamples. Five colour-copy readback corruptions are rejected. These last five are defects and repairs of a subcheck; they do not establish a historical bypass of the entire mask gate.

The exposed historical M2 geometry replay still passes catalog/flow/bond-endpoint reorder, bijective identity relabel and 37-degree rotation comparisons. Maximum rotation displacement is approximately `3.36e-11 pt`. This is a deterministic regression, not fresh native M2 execution or an unseen chemical benchmark. No runtime IR interface, Composer rule or native adapter implementation changed in this checkpoint.

## Independent development experiment and regression result

The [predeclared experiment](experiment-plan.json) generated twelve independent procedural curves: four axis orientations and three terminal-handle lengths at Arial 8 pt, 14.4 pt bond scale and 0.6 pt stroke. ChemDraw natively imported and saved all twelve as CDXML and PNG, with zero chemical warnings. The owned process was verified through its HWND/PID. The worker completed in 2.375 seconds; no ChemDraw process was terminated.

Observed visible head extension was approximately **3.95–4.08 pt**. The declared half-pixel plus 0.02 pt uncertainty yields a conservative bound of **4.159696287964 pt** for this measured family. Source/native hashes, actual head fields, build/style and scale are retained in [development-arrow-metrics.json](development-arrow-metrics.json). A later reader check added native type/style assertions and reproduced exactly the same bound; it did not rerun native rendering or alter the measured pixels. These geometry controls are not gold chemical records and do not qualify all curve shapes.

The existing shared annotation rule was evaluated once with this independently measured bound. **M1 failed before native import** with `No backside attack route clears measured annotations`. S1/R1 input files written before the failure remain retained; the incomplete batch was then explicitly rejected by `native-pages.ps1` before native initialization. No new M1 native output or scored M2 run is claimed. No rules were adjusted from this regression result, and no development or exposed-reference repair was consumed. See [regression-receipt.json](regression-receipt.json).

Rechecking unchanged R2 native masks with the repaired verifier gives **S1 pass / R1 pass / M1 fail**. S1's legitimate mixed bond contacts remain accepted with recorded contributor pairs. M1's zero-gap pairs and visible departure-port failure remain rejected; unresolved mixed ink is also reported conservatively. Retained first outputs and failures are not overwritten.

| Layer | Result |
| --- | --- |
| General scene/mask guards | Repaired and fault-tested within the documented scope |
| Independent native curve controls | 12 completed; 24 original CDXML/PNG outputs |
| Retained S1/R1 | Automatic mask pass; owner physical-size review pending |
| Retained M1 | Native quality failed |
| New M1 regression | Route preflight failed; incomplete native batch refused |
| New scored M2 | Not run; prerequisite not passed |
| Dataset/correction corpus | Not started; architecture schema/gold contracts precede ingestion |
| Freeze / holdout / owner review | Not started / not selected / pending |
| Human active correction time | `null`; no measured human session |

## Evidence and reproduction

`raw-evidence.zip` is **604,147 bytes**, SHA-256 **71e6d8791b3a1c44be0bd82f6b27fe729e8ef2ebf82be3a6ad65a69aa59a6cac**. All **241 manifest entries** were read back and hashed; **24 native outputs** retain their exact original bytes. JSON/journal paths are sanitized with both original and public hashes in [evidence-manifest.json](evidence-manifest.json). No vendor binaries, licences or private academic data are included.

The archive separates `development-build-1/source` (actual source before the native batch), intermediate/final corruption controls, retained partial regression input, native refusal journal, measurement replays, and `final-source`. The final source audit is not substituted retroactively for the earlier executed source. Staged Git hashes are listed separately where line-ending normalization differs. The enclosing commit plus the delivery receipt binds this evidence to the delivered revision.

Read-only reproductions, after extracting the archive into a scratch folder and installing the repository's locked probe dependencies:

```text
python -m unittest discover -s tests -v
python probes/arrow_extent_controls.py measure --inputs <scratch>/native-core-r3/development-arrow-input --native <scratch>/native-core-r3/development-arrow-native --out <new-report.json>
```

Historical native replay inputs remain bound to the immutable [R2 evidence](https://github.com/saigyujikingyo-png/chemdraw-companion/tree/eb8b4c869a23237f726f8cf127be18743f573a14/verification/2026-09-12-r2). All fault controls are synthetic mutations of retained evidence; none is represented as native generation. Further layout development must use independent development inputs under the new corpus/gold contracts. The runtime IR/Composer remain the reusable core, with COM/CDXML as the adapter.
