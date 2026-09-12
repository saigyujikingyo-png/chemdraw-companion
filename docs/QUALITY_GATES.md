# P0 native and quality gate

Status: acceptance design only. No fixture has been run or approved by this architecture task. Sample inputs are synthetic teaching specifications, not experimental claims. Native implementation owns fresh evidence; architecture review owns criteria and contract changes.

## Decision rule

Advance beyond P0 only after all three representative fixtures pass native execution, chemical correctness, layout checks, disk reopen/editability and explicit owner visual review. One fixture cannot compensate for another failing. CI, process exit, method presence, valid PNG or a library-generated CDXML is insufficient. Host/model, delivery and packaging have later separate gates; none inherits Origin acceptance.

First create a manually reviewed native reference for each proposed fixture, record its effective style and final size, and request owner quality approval on concrete images. Owner silence is pending. Work on probes and automated checks continues while references await review, but no visual acceptance claim is made. Do not fabricate a reference or repeatedly expand features while quality remains rejected.

## Representative fixtures

| ID / request | Minimum content | Required native/editable evidence |
| --- | --- | --- |
| S1 / `examples/structure-sheet.json` | One alanine zwitterion with specified stereo, NH3+ and COO- labels | Official structure insertion; stereo/charge/hydrogen readback; a visible wedge/hash assignment; CDX save to disk and reopen; atom/bond/label edit on a copy |
| R1 / `examples/reaction-scheme.json` | Hydroxide + bromomethane -> methanol + bromide; a conditions line and aligned reactants/products | Real molecule and text objects, reaction arrow, plus signs, conditions; complete atom/charge balance; native CDX reopen with those objects retained |
| M1 / `examples/electron-flow-step.json` | Same explicit elementary SN2 step; O lone-pair -> C and C-Br bond -> Br, with expected bond/charge changes | Two editable curved two-electron arrows with donor/acceptor relationship; native-rendered full scene; reopened arrows, lone-pair/charges/conditions preserved; move an arrow control point and save/reopen copy |

R1/M1 describe a deliberately small teaching case. No claims about arbitrary mechanisms, kinetics, temperature, experimental yield or every solvent condition. The structure fixture preserves the input stereo rather than assuming a CIP label without checking. Atom maps belong in validation data, not automatically in the visible figure.

## Checks for every fixture

1. **Environment and native execution:** actual OS/device alias, application build and edition/entitlement category, add-in/API version, broker/contract/build and recipe/style. Include exact native calls/commands and input/output hashes. Capture application readback; screenshots alone cannot establish API execution. `ChemDrawAPI.version` is API version, not application build.
2. **Chemical semantics:** compare graph identity, bond orders, isotopes, formal charge, explicit H and specified stereochemistry before/after native round trip, independently where possible. For reactions verify participant roles and mapping, total charge and complete balance or declared omissions. For M1 verify the two flows and declared graph changes. SMILES equality cannot check arrows or labels.
3. **Layout:** evaluate source and reopened drawable objects plus actual rendered glyph/arrow masks. Zero unintended collisions, clipping, missing glyphs, detached charges, or arrowhead overlap with labels. Exclude intended atom/bond contacts from collision checks, not arbitrary overlaps. Keep conditions associated with the reaction arrow, components aligned, and final margins nonzero.
4. **Editability:** save native CDX bytes, close/reopen through a verified native lifecycle, read again, then make a small native edit on a COPY. For M1 edit curve geometry; for R1 edit condition text; for S1 edit a label/bond on the test copy. Save and reopen the edited copy. Neither a flattened image object nor opening an already-loaded document counts.
5. **Visual inspection:** inspect full figure and focused difficult regions at actual 85 mm target size, plus high-resolution detail. Evaluate typography, charges/wedges, consistent bond length, line weight, arrow curvature/head direction and overall readability. Save annotated failures and subsequent fresh renders. Native PNG is documented as preview-capable: verify pixel count and effective DPI at final size, rather than assuming publication quality.
6. **Provenance and integrity:** produce complete manifest, effective scene/style, native CDX/CDXML/PNG, semantic/object comparison and reopen/edit receipts. Record byte SHA-256 for artifact transfer and normalized fingerprints for semantic/appearance comparison. Native XML ID/order changes need not equal a semantic difference.

Proposed pilot defaults (subject to concrete owner review): 85 mm width, 8 pt main text, 14.4 pt nominal bond length, 0.6 pt regular bond stroke, at least 600 effective DPI for final raster line art. The fixed 85 mm canvas requires at least 2008 pixels in width; a 170 mm canvas requires at least 4016. Do not stretch a small S1 structure to fill that width: retain the declared 8 pt text and 14.4 pt bonds. Independently verify native pixel scale on the ink/object geometry (a 14.4 pt bond is 0.2 inch and needs about 120 pixels at 600 DPI); padding alone cannot pass the resolution gate. Report canvas and ink bounding boxes in both pixels and physical units. Do not upsample a low-resolution image and claim new native detail. Probe the native scale option and record actual pixels; insufficient resolution is a quality failure or requires a separately verified native vector export.

Initial geometry diagnostics, measured against nominal bond length B: ordinary bond lengths within 10% of the declared style except explicitly justified cases; unrelated label/charge ink clearance at least 0.12 B; arrow-to-unrelated-object clearance at least 0.18 B; donor-tail/acceptor-port deviation at most 0.20 B. For M1, the incoming attack path approaches C opposite the leaving bond (within 30 degrees of the ideal backside direction). These are fixture engineering thresholds, not a universal scientific style standard. Correct intentional contacts require a named exemption with evidence. Passing numeric checks cannot override an owner's failed visual review.

## Required adverse cases

| ID | Injection | Pass behavior |
| --- | --- | --- |
| N1 | Identical blank documents A/B; switch after snapshot and before mutation; repeat while retaining a Document reference | No mutation to B or other user document; binding verified or refusal before action. Hash/lease alone cannot pass. |
| N2 | Drop reply after a native insertion succeeded; replay same idempotency key | Same job returned; `outcome_unknown` reconciled without duplicate append or blind Undo. |
| N3 | Export only structures as selection SVG from a mechanism page | Reject coverage as incomplete; arrows/conditions cannot disappear under a full-page claim. |
| N4 | Manual edit or second-host request changes revision | Reject stale revision; preserve edit and old artifacts; no silent merge. |
| N5 | Lose app/add-in, crash worker, or request cancellation during write | Bounded status and truthful mutation outcome; no killing unrelated application or claiming cancellation before quiescence. |
| N6 | Wrong stereo/charge, missing map, reversed electron flow or radical input | Correct field/semantic failure; no native success or substituted teaching scene. |
| N7 | Reopen loses curved arrows, conditions or editable object types | Fail native-editability even when molecular SMILES/PNG look valid. |
| N8 | Stale add-in or incompatible broker/tool manifest | Identity failure before mutation, understandable supported recovery. |
| N9 | Another principal guesses session/artifact ID; traversal or wrong destination | Denied without leaking files or private metadata. |
| N10 | Native file correct but host download/attachment route blocked | Native pass retained; delivery blocked separately, no false receipt. |
| N11 | Two continuations submit the same session/parent revision concurrently | One atomic reservation/commit; second job cannot overwrite or advance from a stale parent. |
| N12 | SN2 flows reordered, or anchor points to product component with the same map | Simultaneous pre-step validation remains correct under reordering; product-side anchor rejected. |
| N13 | Tiny native bitmap placed on a large padded/upscaled canvas | Fail effective native ink resolution even if overall pixel width meets the target. |

Do not broaden tests merely to increase a count. Native boundary tests and actual saved artifacts are the primary evidence here. Unit tests should target job/revision/idempotency/security/semantic failure logic; integration tests must exercise the vendor boundary and reopening.

## Later acceptance and efficiency

Actual host workflow matrix: ChatGPT Work cloud; ChatGPT Work local (known external project-sync issue may remain blocked/unverified); Claude; WorkBuddy. Verify each advertised surface with natural-language input, continued edit, invalid input/recovery and received editable file. Protocol compatibility or installed connector does not count. Do not investigate or patch the known OpenAI frontend sync bug.

Use GPT-5.6 Terra + max for the default benchmark when actually available. Record exact host/model/effort, app/plugin versions, device category/date, success on first attempt, human corrections, tool calls/retries, elapsed time, quality and receiver-side artifact evidence. Record actual input/cached/output/reasoning tokens and billed cost when provided; otherwise `unavailable`. Do not use schema byte estimates as billing or silently lower reasoning/switch models. Other models remain separately tested targets.

Installer gate: fresh user/device, upgrade, repeated install, paths with spaces/non-ASCII, existing valid credentials, file locks, interrupted update, backward-compatible migration/rollback and uninstall. Include actual manual steps, package size, startup and memory/CPU/disk/transfer measurements. No stable release until advertised gates pass; honest diagnostic preview may retain explicit gaps.

## Blocking report and Mnova alternative

Stop feature expansion when licence/API access is unavailable, document isolation is unsafe, native save/reopen fails, or fresh native figures still fail quality after the bounded repairs. The implementation returns a concrete report: device/app/edition, operation, official source, sanitized exact error, reproduction steps, last safe artifact, attempted official alternatives and what remains human-only or unknown. This is a blocked ChemDraw gate, not proof all ChemDraw versions lack the feature.

Consider Mnova as the next product only after that report and coordination decision. It cannot fulfill a ChemDraw drawing promise. The first alternative is one licensed 1D NMR workflow through official scripting: copy/import raw data, explicit processing/reference parameters, peak/integral table, native document, exported figure, disk reopen and independent numerical checks. Preserve FID, units, phase/baseline choices, solvent/nucleus and integral normalization. Treat qNMR, 2D and extra modules separately. The previously detected Mnova 17.0.41952 is a device-specific observation, not a campus version claim. Actual entitlement, invocation and results remain unverified. See the vendor links in SOURCES.md.
