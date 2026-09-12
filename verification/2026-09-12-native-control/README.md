# Native control and generic Composer checkpoint

**Diagnostic checkpoint, not a P0 pass or release.** Typed native saving is now reproducible on the tested ChemDraw build. M1 still fails a native charge check, and the generic Composer fails required identity-invariance/quality checks. Installer, MCP, host delivery benchmarks and holdout selection remain gated.

The previous [f111c36 evidence](../2026-09-12/README.md) remains unchanged. Architecture baselines c7037ff and caa8877 were merged into the implementation branch. Public records use English and redact local paths. This work used Astra/max for development; no Terra/max host benchmark or billing measurement is claimed.

## Environment and SaveAs result

Tested application: signed **ChemDraw Prime 26.0.0.6141 x64**, registered `ChemDraw_x64.Application`. Installed interop assembly/file version: **22.0.0.0**, recorded separately from the application version. Executable SHA-256: `F5383228898B6E6BE08ABDED9F6DB0909D0841A2F6A5BBEF50BA00F44AF8A084`; interop SHA-256: `ECAED777A648DF79927C79C3D7A33E1A813C6B027C4111396B7139FDDA81959A`. Python 3.12.14 and PowerShell 7.6.5 were used. Exact entitlement and Add-in availability remain unqualified; neither is inferred from this COM result.

In the controlled SaveAs run, PowerShell late binding still returned without a file after loading interop. Calling `IChemDrawDocument.SaveAs(ref object, ...)` through the installed strongly typed interop produced native CDX, CDXML, PNG and JPEG. Independently opened CDX/CDXML copies accepted a charge edit, saved and reopened. Requested paths are immutable, files are never overwritten by the save adapter, and callers verify nonempty bytes. Actual exception chains/HRESULTs are logged. The invalid MIME control also returned without a file: absence of a thrown exception is not success. No observed result establishes a licence or ACL failure.

The visible A/B test verifies the application's HWND-to-PID binding and compares canonical COM `IUnknown` identities after changing ActiveDocument. Mutations through the retained A reference remained in A while B was active. Earlier hidden-window/identity failures are retained. These are disposable-document controls; no arbitrary open user document, stale revision or multi-host concurrency qualification is claimed.

Key archive entries: `saveas-matrix/20260912-203751-f61d4ff6`, `native-probes/20260912-205152-41151b98`, `object-capabilities/20260912-204507-295422c5`.

## Gate status

| Gate | Observed result | Remaining limit |
|---|---|---|
| P0-A native transport | Typed saves, exact disposable A/B binding, both disk formats, native export exercised | Product idempotency/revision/CAS, N2/N4/N8/N9/N11 and host protocols unimplemented/unverified |
| P0-B object control | Atoms/bonds, editable spline points, captions, charges, electron symbols and rigid transforms exercised; both-format edit copies retained | Full CRUD/stereo/isotope surface, arbitrary-document identity, robust persistence remapping and complete quality qualification remain partial |
| S1 | Native graph/charges and one stereo wedge preserved through both formats | Independent absolute-CIP assignment, complete edit subset, rendered-mask and owner acceptance pending |
| R1 | Native participant graphs/charges, step arrow and annotations preserved through both formats | Preview plus sign touches the product OH label; condition-specific edit, full quality and owner acceptance unpassed |
| M1 | **Failed**: second repair still reads product methanol oxygen as formal charge +1 | Correct input has neutral product oxygen; native import/interpretation cause remains unresolved |
| Generic M2 diagnostic | Latest original/CDX/CDXML readback agrees: 126 mapped atoms, 111 bonds, 42 lone-pair symbols, 15 curves and 6 step arrows; zero native warnings; specified anti relation retained | Prerequisite M1 failed; curve clearance, complete rendered masks, identity invariance, owner acceptance and manual-time measurement fail/remain pending |
| Freeze / unseen holdout | **not_started** | Base prerequisites have not passed; no holdout structure was selected or tuned |

The [capability matrix](capability-matrix.json) separates each observed subset from full qualification. Unit tests, native chemistry, geometry, editability, owner review and host/installer acceptance are separate fields.

## Failure history and bounded experiments

- S1/R1/M1 initial output and two repairs are retained. The first repair adjusted the M1 diagnostic attack curve. Independent native checking later exposed three M1 charge mismatches. The second repair preserved native chemical text runs and translated them with atoms; two mismatches disappeared, but product oxygen remains +1. No third M1 repair was attempted. The most recent M1 image/file is explicitly a failed diagnostic.
- Visual review also finds the R1/M1 separator plus sign too close to the methanol OH label. R1's graph remains neutral despite this ambiguous appearance. The corresponding M1 native +1 could involve native text/charge interpretation, but that causal link has not been established by an isolated control. The report does not attribute it to licensing, permissions or a verified vendor defect.
- Legacy M2 specialized source, first output, two repairs, repeats, rotated inputs and geometry replay are archived under `M2-20260912`. Their source is quarantined as non-executable `.py.txt`. They are withdrawn from general Composer acceptance and never imported by runtime. Their native-control observations do not qualify composition or generalization.
- Generic M2 uses `examples/m2-composer-request.json` through the new generic IR boundary. The initial native seed failed the declared anti constraint and was rejected. One reaction-independent substituent-sector seed repair preserved it. The first composed native output then lost multiple bonds because CDXML `Order="2.0"` was interpreted as single. A serialization repair emits the enum token `2`. Counting seed and serialization changes, two automatic repair stages were used. No additional scored generic M2 repair or tuning was performed after the following failures were found.
- The independent verifier initially treated native step-arrow ID replacement as object loss. Native serialization explicitly writes `SupersededBy`; following the saved source's alias chain resolves all six arrows in both formats. The corrected report does not claim native IDs remain fixed. Production remapping remains incomplete.
- The latest generic figure has one native glyph-bounding-box clearance failure (2.458 pt versus required 2.592 pt). The router currently does not prove collision freedom against all bonds, electron symbols, captions and arrow masks. Visual congestion remains. A bbox result is not full rendered-mask acceptance.
- Bijective relabeling of state/transition/flow/atom IDs plus shuffled storage arrays preserves chemistry and counts but changes mapped atom positions by up to **84.3 pt**. Current component/candidate tie ordering is not invariant. This is a failed metamorphic result, not evidence of a passed generalization gate.
- Rotating intrinsic component geometry by 37 degrees preserves declared stereo and fits; valid path prefixes with two/four states produce two/seven flows. Independent small proton-transfer and ring-closure semantic tests exercise two/three flows, including empty charge changes. These are structural controls, not an unseen chemical holdout or final quality approval.

M2 was generated before the late independent M1 charge failure was identified. It is retained as **diagnostic-only**, never retroactively labelled a qualified successor to M1. The migration/product was supplied in complete IR; this does not establish automatic anti-substituent selection.

## Edit and raster evidence

On independent generic M2 CDX and CDXML copies, native fragment movement changed only the selected occurrence. Companion-owned endpoint displacement updates rerouted affected cubic controls; native lone-pair objects, caption and curve edits survived a second disk reopen. Deliberate charge changes and removal of one lone pair also survived in separately labelled diagnostic copies. Their altered chemistry is not accepted. See [edit comparison](generic-edit-verification.json).

Native PNG calibration exported a 144 pt line as 1,200 ink pixels for requested 72 and 600 DPI alike: observed ink scale is **600 DPI**, while embedded metadata is approximately **144 DPI**. Native pixels were not resampled or patched. The exported canvas includes margins; use measured content/canvas coordinates and explicit physical placement. JPEG is a preview, not high-resolution acceptance. See [calibration](pixel-scale-report.json). Native font/bond/stroke requests are 8/14.4/0.6 pt for M2; smaller S1/R1/M1 auxiliary captions are disclosed by their scene records. Physical print and owner acceptance remain unverified.

Worker receipts predeclare a 60-second disposable PowerShell deadline. A timeout stops only that worker, leaves the native process intact, marks `outcome_unknown`, and does not replay writes. It is not individually cancellable COM or proof that native mutation stopped. Worker timing is not total development time or manual correction time. Manual active correction seconds and manual edit counts remain **null**, not zero.

## Reviewable artifacts

| Sample | Native files | Preview | Verdict |
|---|---|---|---|
| S1 | [CDX](samples/S1/S1.cdx), [CDXML](samples/S1/S1.cdxml) | [PNG](samples/S1/S1.png), [JPEG](samples/S1/S1.jpg) | Native graph subset passed; quality pending |
| R1 | [CDX](samples/R1/R1.cdx), [CDXML](samples/R1/R1.cdxml) | [PNG](samples/R1/R1.png), [JPEG](samples/R1/R1.jpg) | Native graph subset passed; separator layout failed |
| M1 | [CDX](samples/M1/M1.cdx), [CDXML](samples/M1/M1.cdxml) | [PNG](samples/M1/M1.png), [JPEG](samples/M1/M1.jpg) | Failed product charge; diagnostic only |
| M2 | [CDX](samples/M2/M2.cdx), [CDXML](samples/M2/M2.cdxml) | [PNG](samples/M2/M2.png), [JPEG](samples/M2/M2.jpg) | Diagnostic only; composition/generalization unpassed |

[Raw evidence archive](raw-evidence.zip) contains 529 preserved files, including failed first attempts and edit copies. [Its manifest](evidence-manifest.json) records original/public bytes and hashes. Native CDX/CDXML/PNG/JPEG bytes are unchanged; text journals redact private paths and may normalize encoding. Originals remain in ignored local storage. No vendor runtime, licence, credentials or private academic input is redistributed.

[Native M2 comparison](generic-native-verification.json), [small-fixture comparison](small-fixture-verification.json), [metamorphic results](metamorphic-report.json), [source audit](source-audit.json), [dependency provenance](dependency-provenance.json), [17 focused tests](tests.txt) and [PowerShell parser results](powershell-parse.json) are separate records. The source audit inspected imports, rules, runtime paths and absence of benchmark assets; it is not an independent audit or substitute for failed behavioral evidence. Complete source snapshots were not captured for every historical attempt, so no historical build freeze is claimed.

## Developer-only reproduction

The prototype requires a separately installed, signed, licensed ChemDraw build and local Python/PowerShell. It is not an end-user installer. The hash-pinned `requirements-probes-win-py312.lock` covers the newly added generic-schema dependencies for Windows x64 Python 3.12; install into an ignored project-local target. Existing bundled image tooling is recorded separately and is not a complete frozen runtime.

`probes/run_composer.py seed` accepts only the generic Composer request and writes native fragment seeds. `probes/native-ir-fragments.ps1` imports/cleans/saves each seed under a finite worker deadline. `probes/run_composer.py compose` consumes those fresh measurements and produces editable CDXML plus semantic mappings. `probes/native-pages.ps1`, `verify_composition.py` and `verify_native_edits.py` perform native and independent checks. All output directories must be new. The test/oracle modules never feed production generation.

Next core work is to diagnose the minimal M1 native charge mutation and remove input-order-dependent packing ties, then run a newly declared bounded regression experiment. No installer, MCP facade, host expansion, frontend-sync repair, Mnova work, main-branch push or unseen-input tuning was performed in this checkpoint.
