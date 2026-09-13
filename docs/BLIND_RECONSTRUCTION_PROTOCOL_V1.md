# Blind reconstruction protocol v1

Effective 13 September 2026; executes [Issue #2](https://github.com/saigyujikingyo-png/chemdraw-companion/issues/2). This phase acquires bounded real external assets. It supersedes the previous handoff's no-collection instruction. It does not reopen the exhausted earlier pilot.

## Two distinct experiments

**Task A — PNG reconstruction:** a fresh model receives one byte-frozen ChemDraw native PNG, the public runtime IR schema and a reaction-independent instruction. It recovers reading order, molecular graphs, roles, reaction arrows, conditions, charge/radicals, lone pairs and semantic electron-flow source/sink. The output is `contracts/mechanism-ir.schema.json`, using `ir_version`, `atom_catalog`, `states` and `transitions`. The archival corpus IR has a different shape despite its similar version name; never silently substitute it.

**Task B — blind composition:** the model/Composer receives a supplied semantic IR or natural-language requirement and the public schema, with no reference image, native target or target-derived placement. Report it separately. This pilot's Task A result cannot qualify Task B.

No model-generated final CDXML coordinates bypass the IR. Schema validation does not establish chemical correctness. Missing, inconsistent or unsupported semantics are retained as failed attempts. A generic syntax-only repair, if authorized in a run plan, must receive only its own output and validator errors; it must never receive hidden reference hints.

## Custody and order

1. The source custodian records author/source, container and extracted-member hashes, retrieval time and rights. It checks exclusions without opening frozen benchmark answers. Raw third-party files stay private.
2. The native custodian opens the external CDX/CDXML in a fresh, PID/HWND-bound ChemDraw process with zero pre-existing documents, retains document references, saves new native CDX/CDXML/PNG and independently reopens each saved format in its own fresh zero-document PID/HWND instance. Same-process Close/Open can reuse cached COM identity and is not disk-read evidence. Journal source hashes, adapter/executable hashes, application build, save returns, output hashes and readback. Source bytes remain immutable.
3. Seal `generator_input/`, `hidden_target/`, `candidate/` and `evaluation/` according to `contracts/paired/hidden-split.schema.json`. Only the PNG and runtime schema cross the Task A input boundary. Author preview EMF/GDI images help source screening but are not substitutes for the native reference PNG.
4. Pass actual OS/API isolation checks in [DATA_LEAKAGE_FIREWALL_V1.md](DATA_LEAKAGE_FIREWALL_V1.md). Use a new model context. Record the exact prompt, requested/actual model, reasoning effort, run identifier, timestamp, exposed asset hashes, complete projected payload hash and isolation receipt hash. Terra with max reasoning is the default; do not silently substitute another model.
5. Preserve the unedited response and extract its IR without chemical or layout fixes. Record validation failures. Freeze all Composer inputs and the implementation/style hashes before candidate generation.
6. Feed accepted IR through the existing generic `run_composer.py seed` entry, native de novo fragment cleanup and `run_composer.py compose`. The fragment geometry must originate from candidate IR, never hidden target coordinates. The existing implementation branch owns this adapter; no new host/MCP/installer is needed.
7. Save/render the candidate using the existing retained-document adapter, then reopen each saved native format in a fresh process. Preserve failures and all intermediate artifacts. A process exit is not enough: verify files, hashes and readback.
8. Only the evaluator joins target and candidate. Produce separate semantic, object, geometry and native visual reports plus machine-readable correction deltas. Mark unsupported measurements unmeasured. No aggregate score can conceal a failed layer.

## Native pairing workflow

The existing `probes/native-common.ps1`, `NativeChemDraw.cs` and `native-snapshot.ps1` provide signed vendor loading, retained COM references, the corrected SaveAs call and readback. A bounded research driver calls these adapters for explicit external files. It refuses existing output directories and preserves the original bytes. Record explicit `chemical/x-cdx`, `text/xml`, `image/png` saves and both-format reopen events. Native JPEG is an additional human viewing export when PNG transparency is awkward; the original PNG remains native evidence. If its alpha-only ink is not interpreted, a separately authorized fixed-white alpha composite may become a new run's reference, with immutable original bytes, identical dimensions and a pixel-equivalence receipt.

Record PNG dimensions and metadata; requested export DPI does not prove effective DPI or calibrated native pixel-to-point scale.

Pairing does not itself prove full editability or visual quality. Native CDX import can expand abbreviations and create scheme objects; compare original-source inventory, imported objects and each reopen separately. Raw fragment/step-object counts are not semantic state/step counts. A nonzero retained-object edit and re-open test is a further editability gate; it must use a separate diagnostic copy, never the frozen teacher.

## Evidence and publication

The public repository contains code, protocols, citation/locator/hash manifests, source inventory and sanitized receipts. Private storage contains original assets, native exports, model packets/responses and detailed readback. Unknown redistribution rights do not block authorized internal discovery, but do not imply permission to publish raw files or train a model.

M1 is exposed development. M2 Beckmann Snake, all derivatives and future unseen holdouts remain excluded from acquisition examples, prompt/rule tuning, calibration, training, reconstruction and human reference. Source-family screening does not make an exposed sample unseen. There is no learned-model training in this phase.

A pipeline attempt can be useful even when chemical reconstruction, native composition or visual quality fails. Preserve the failure rather than patching a screenshot or hard-coding the target's coordinates. The execution receipt must state which stages actually ran and answer the seven Issue #2 questions with measured counts.

Current measured outcome: [Issue #2 execution receipt](reviews/2026-09-13-issue2-paired-pilot.md).

## Existing implementation entry

The implementation task published [402a31e](https://github.com/saigyujikingyo-png/chemdraw-companion/commit/402a31e2e5f36faaa088e4013e88eb99fa8bbdf5) on its existing branch. It adds only the two generic native-pair/candidate probes; runtime chemistry and schemas remain unchanged from c92a918. In that implementation checkout, with its qualified Python dependencies and PowerShell 7:

    python probes/run_paired_candidate.py --request REQUEST.json --sha256 REQUEST_SHA256 --out NEW_RUN_DIRECTORY --powershell POWERSHELL_7_EXE

An optional --inference-receipt argument binds a copied inference receipt. The runner does not execute a model or establish blindness by itself. It preserves the original request, stops on unsupported semantics, and retains failed-stage stderr. Its synthetic proton-transfer control is separate from this external pilot; supplier claims require recipient-side verification. See the execution receipt for the actual unchanged external-request result.
