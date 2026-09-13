# Native feasibility probes

These are supervised developer diagnostics, not the five MCP tools or an installable plugin. The P0 product remains blocked; do not infer a working recipe, legal entitlement, unattended isolation, or final-figure quality from these scripts.

`native-p0.ps1` discovers the registered x64 ChemDraw server, checks its Authenticode signature, and requires one fresh process with no pre-existing documents. It creates two disposable blank documents, deliberately changes the active document, writes through the retained references, and verifies that only the intended document changed. It then attempts native CDXML saves with file-existence, size and hash checks. A returned native call without its expected artifact fails the probe with a nonzero exit. It does not kill ChemDraw, change security settings, activate a license, enable add-ins, or edit user files.

Run it only in an authorized local diagnostic session:

```powershell
.\probes\native-p0.ps1
```

The default evidence folder is ignored `.local/native-probes` in this checkout. Each run gets a new directory and native instance; old receipts and artifacts are retained. A failed/uncertain native operation must be inspected, not replayed against its document. Native call supervision and timeouts are not a production job implementation yet. Do not advertise this probe as an unattended service.

`verify_smoke.py` verifies only the small, supplied ethanol evidence. It checks the known C-C-O graph, charges, native CDX header, PNG dimensions, and native graph/coordinate equivalence after reopening. It rejects arrows and other scene objects that need a separate comparator. This is not a general SMILES, stereo, reaction, mechanism, glyph, or quality validator.

```text
python probes/verify_smoke.py verification/2026-09-12/native-smoke
python -m unittest discover -s tests -v
```

See `verification/2026-09-12/README.md` for the initial successful smoke run, subsequent SaveAs failures, entitlement/UI limitations, exact source baseline, and the bounded next decision. Architecture-owned docs/contracts have not been changed by these probes.
