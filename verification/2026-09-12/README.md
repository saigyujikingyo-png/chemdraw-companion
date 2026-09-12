# Native P0 blocker evidence, 12 September 2026

**Decision: stop at native feasibility. Do not expand recipes, hosts or installation.** The implementation branch is based on architecture commit `394edf8b7b99b80827c79650c0a113808eb22ea1`; architecture-owned docs/contracts are unchanged. This directory is a diagnostic record, not a passing P0 bundle or software release.

## Observed application and entitlement boundary

The actual ASUS TX Gaming FA608FP_FA608FP execution device has x86 and x64 ChemDraw 26.0.0 registry entries. The validly signed x64 vendor executable was instantiated using the registered `ChemDraw_x64.Application` class and reported **ChemDraw Prime 26.0.0.6141**. This is fresh evidence from the implementation device, not the other computer's installation result.

The current accessibility tree has no Add-ins menu. Specific license validity, expiry and SDK entitlement remain **unverified**; no licensing, authentication, keys or security settings were changed. ChemScript files and signed COM interop metadata exist, but installed files are not entitlement. [Revvity ChemScript entitlement](https://support.revvitysignals.com/hc/en-us/articles/41816118840340-ChemDraw-ChemScript-is-missing) · [Add-in Manager product availability](https://support.revvitysignals.com/hc/en-us/articles/4408233119508-ChemDraw-I-didn-t-find-the-Add-in-Manager-under-ChemDraw-Add-in-menu-How-can-I-get-this-function)

The official JavaScript guide 1.6 was checked against its pinned SHA-256. No add-in was loaded and no API-version or paired-handshake success is claimed. The COM route is an observed official-interface candidate for architecture review, not a silent replacement of that contract. The vendor's published SaveAs example confirms MIME formats and physical units for its COM control, but its old tested version does not qualify today's Document automation behavior. [Official COM SaveAs example](https://support.revvitysignals.com/hc/en-us/articles/4408233346580-Is-there-an-example-of-the-Save-As-method-in-C-that-can-help-show-me-how-to-save-my-ChemDraw-structure-as-an-Enhanced-Metafile)

## What actually worked

At 17:59 UTC, an additional **ethanol smoke test** opened `CCO` via native SMILES import, called `Objects.Clean(deNovo=True)`, wrote CDXML/PNG/CDX, closed, reopened the disk CDX and exported fresh CDXML. These are the files under `native-smoke/`. The known C-C-O graph, net charge, 3 heavy atoms, 2 bonds and formula C2H6O agreed. Native chemical warnings were zero. Parsed chemical objects and coordinates agreed after reopening. Cleanup changed the input coordinates slightly; that does not establish an appreciable drawing-quality improvement.

The original native PNG is 335 x 131 pixels with transparency. This small diagnostic is not an 85 mm / 600 DPI final figure and was never S1. The CDX SHA-256 is `845aa45a92742733949378037ad16089eec4e19a077842c3fcfaf72021b21f8b`. The first successful run and later failures are both retained.

## N1 and the concrete save failure

The native probe required one fresh signed-vendor process with zero pre-existing documents. It created identical blank A/B documents. After activating B, an oxygen was created through the retained A reference: A had one oxygen and B remained empty. After activating A, a nitrogen was created through B: A retained its oxygen and B gained only nitrogen. This was observed again in a fresh diagnostic instance. Both documents assigned the same local atom ID, demonstrating why an object ID/content hash alone is not cross-document identity.

This is a narrow retained-COM-reference result within disposable instances. It does not certify arbitrary user documents, exclusive human access, add-in references, authenticated pairing, or a production lease protocol.

The next call, `Document.SaveAs(..., "text/xml", ...)`, returned without an exception but **did not create the requested `N1-A.cdxml`**. The native probe correctly stopped. A final reproduction with the committed probe path returned process exit code 1. Later read-only checks still found no expected CDXML. Additional controlled copies tried document Modified state and two output roots; neither produced its requested file. These failed writes were not blindly repeated against the original document.

The underlying vendor/edition cause is **unknown**. Do not infer an ACL, locked desktop, licensing defect, or universal ChemDraw failure. The observation is sufficient to block a reliable native-save/lifecycle claim. Result and event files retain the exact errors. No automatic Undo, retry, process kill, license activation or application patch was used. The diagnostic script is supervised; a production bounded-call supervisor, journal reconciliation and cancellation protocol have not been implemented.

Desktop UI input also failed with `GetCursorPos: 0x80070005` and `coordinate input geometry is unavailable`. Accessibility was readable; the screenshot was black. Thus license-dialog inspection and visual UI acceptance are incomplete. No OpenAI frontend, project-sync, cache, registration or security investigation/repair was performed.

## Gate disposition

| Gate | Evidence | Status |
| --- | --- | --- |
| Signed application and running edition | Native COM identity and signature hashes | OBSERVED |
| Legal entitlement / official add-in pairing | Prime observed; no Add-ins menu; no paired handshake | UNVERIFIED / BLOCKED |
| Retained A/B COM reference | Writes remained on intended disposable document in two probes | NARROW N1 RESULT ONLY |
| Ethanol native read/write/reopen | Initial native files and independent narrow graph checks | SMOKE PASS |
| Reliable native disk save | Later SaveAs returned without a file in repeated controlled tests | FAILED |
| S1 / R1 / M1 | Not run because the preceding gates remain blocked | NOT RUN |
| Fixed canvas, frozen effective style, final DPI | No representative fixture dispatched | NOT RUN |
| Copy edits, curves/conditions reopen, recovery/cancellation | Not qualified | NOT RUN |
| User final-figure acceptance | No three final figures submitted | PENDING |
| Five MCP tools, real hosts, Terra max, installer/rollback | Not implemented or tested in this diagnostic stage | NOT RUN |
| Artifact transfer | Repository files and archive bytes can be checked independently | No host receipt inferred |

Seven focused verifier tests passed: atom-ID renumbering, charge loss, wedge changes, dropped text, unsupported arrows, dangling bonds and duplicate IDs. PowerShell parsing passed. The verifier intentionally refuses broader scene/chemistry claims. These tests do not clear any blocked gate.

## Bounded next decision

Architecture/coordination should choose the qualified baseline before further implementation: confirm the current lawful ChemDraw entitlement and usable official add-in, or explicitly qualify the COM candidate after its silent-save failure is resolved. No new API key is requested; use the existing official license/account interface. Retain the current evidence and originals. Once the prerequisite route is reliable, continue S1 native generation/save/reopen/copy edit, then R1/M1 under the unchanged schemas and final-owner-review gate.

If this boundary cannot be resolved, the same device has a validly signed **MestReNova 17.0.1-41952**, Python 3.11 runtime files and vendor phase/peak/integral examples. A bounded alternative is a separately authorized 1D NMR workflow on copied public/synthetic data with explicit processing/reference choices, native save/export/reopen and numerical checks. Native execution and module entitlement remain untested; Mnova does not fulfill the ChemDraw drawing promise. [Mestrelab scripting](https://mestrelab.com/resources/mnova-python-the-holy-grail-of-automation.html)

The School of Chemistry's public table lists both applications for eligible student/personal use, including home computers; it does not establish this device's exact edition or modules. [University software table](https://chem.ed.ac.uk/cto/student-support/computing-software)

## Integrity and scope

The configured development model/effort remains GPT-6 Astra / max. This is not a Terra max benchmark; usage and charges are unavailable. Native calls in the initial smoke took 3.33 seconds of observed shell wall time; the final failing N1 command took 1.21 seconds. Neither is an end-to-end usability/efficiency benchmark.

The code checkout, probe state and logs remain outside sync. Existing Origin/ChemAIst, licenses and user files were preserved. Public evidence removes private paths and includes no vendor executables, authorization material, private tunnels, coursework or experimental data. `SHA256SUMS.txt` records every evidence file. The initial executed script is retained as text, and the current fail-closed probe is under `probes/`. No installer, stable release or product completion is claimed.
