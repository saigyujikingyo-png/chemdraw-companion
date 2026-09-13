# Agent Edit Loop v0.1 — operation receipt

Machine-interface execution is demonstrated on two independent development controls. This is a bounded caption-edit result, with outstanding desktop-display and automatic roundtrip-classification limitations. It is not overall ChemDraw acceptance.

Implementation: [b9363abfce19481d33e8d6409cb3d8d7dd477310](https://github.com/saigyujikingyo-png/chemdraw-companion/commit/b9363abfce19481d33e8d6409cb3d8d7dd477310), runtime branch `codex/native-p0`, existing PR #1. Architecture baseline was `e72ffaafc3b67f1d2fb1b7c309083220a946e865`. Both remote heads were refreshed before this receipt. No new development task/project was created.

## Actual Agent execution

The current Agent issued each one-operation CLI request after examining live native readback. The helper logs a single submitted operation; it does not select objects or contain a prerecorded editing sequence. No user-supplied object IDs or coordinates were needed. These are original workflow controls, not blind-reconstruction or mechanism benchmarks.

| Control | Live selected caption | Preserved style | Native bond length | Executed sequence |
|---|---|---|---|---|
| A | NaH, THF / 0 °C, 20 min | 12 pt; original mixed bold/regular runs | 18 pt | above-arrow; up 9 pt; fresh-process reopen; up 9 pt |
| B | PCC, CH2Cl2 | 10.5 pt; original regular run | 24 pt | above-arrow; up 12 pt; fresh-process reopen; up 12 pt |

Both used their own current document/revision. Both were saved as CDXML and CDX, reopened in distinct new owned processes, reread, edited using refreshed tokens, saved again and finally reopened in both formats. A and B had different source IDs, captions, text sizes/style runs, initial positions and bond lengths. B was independently authored before viewing A results.

There are 25 actual Agent calls on this exact source: 22 completed operations and 3 deliberate refusals. They include 6 caption moves, 4 saves, 8 fresh-process reopens, 2 opens and 2 final inspections. Wrong-document and stale-revision calls were refused. Passing an oxygen atom ID as the caption was refused. That last native test does not claim coverage of every independently identified atom-owned text representation.

[Actual call record](../verification/2026-09-13-agent-edit-loop-controller/actual-agent-calls.sanitized.json) retains original natural-language notes, structured requests, live bindings/revisions/tokens, results and hashes of private raw logs. Sanitized derivatives are labelled; originals are unchanged.

## Machine Interface Only

Read/write execution uses retained COM document objects: `Documents.Open`, `Document.Objects.get_Data(text/xml)`, native caption/arrow/atom/bond/settings properties, the selected `IChemDrawText.Position` setter, and `Document.SaveAs` for CDXML/CDX/PNG. The tool calculates relative placement from native bounds, arrow endpoints and BondLength. It does not derive object coordinates from screen pixels.

PID, process start time, HWND ownership, retained document identity and revision are checked; selection uses native object IDs and tokens from current readback. No current GUI Selection is read. Content execution used no mouse, keyboard, menus, UI Automation, clipboard or foreground-focus input. Missing capabilities must remain unsupported/needs_interface; no GUI fallback is permitted.

[Independent source audit](../verification/2026-09-13-agent-edit-loop-controller/machine-interface-review.sanitized.json) binds the exact four-file call chain. Native COM `Visible=true` / `Document.Activate()` and ActiveDocument identity checks remain environmental preconditions. This is not demonstrated headless operation. PNG export is currently mandatory in Observe; a native render failure and a desktop-window display failure are different events.

## Preserved content and serialization

All six moves passed strict protected-object comparisons; only the selected caption's position/bounds changed. Text/style runs, structures and chemical objects remained unchanged relative to native baseline. There was no Clean, atom/bond/charge/isotope/radical/LP/electron-arrow write or IR regeneration. Unknown H remains unknown; this establishes edit preservation, not correctness of the input chemistry.

Native derivations are retained separately: initial absent AS/BS to N changes are restricted to first export with a second stable observation; the first caption move can add its native step-above-arrow association. Root WindowSize changes are recorded as display metadata; page/object geometry remains strict. The earlier failures that motivated these narrow fixes remain failures.

CDX preserved the live caption coordinates. CDXML saved two-decimal position fields and produced an x displacement of -0.0009002685546875 pt in A and +0.0018310546875 pt in B after reopen. Integer-coordinate no-edit A/B controls reproduced native ID/Z/reference regeneration. A separate frozen three-caption fractional control, with no Position call, independently reproduced CDXML coordinate loss while CDX retained all six live anchor coordinates. These observations are bounded format evidence; no global tolerance or general precision contract was introduced. All strict `normalization.ok=false` results remain false.

**Remaining implementation limitation:** save/reopen outer `ok` reports operation completion, not preservation equivalence. The tool records but does not automatically classify all cross-reopen differences. Independent review of raw differences supports this narrow result; unexplained changes require review/refusal, not a general lossless-save claim.

## Visual and lifecycle evidence

The Agent examined native before/after PNGs for both controls. Final captions are above the main arrows, horizontally centered subject to the recorded CDXML quantization, at their original sizes, without observed structure collisions. Original alpha PNGs and labelled white composites are retained.

Desktop display is separate: A's final ChemDraw canvas was observed; B's initial canvas was observed, but the final read-only screenshot did not show the ChemDraw canvas. B final desktop display is **unverified**. No GUI fallback was used after the Machine Interface Only instruction. Earlier window activation and Alt+F4 cleanup of precisely owned retired windows were display/lifecycle diagnostics, never content editing; they are not counted as machine execution evidence.

Seven controller workers ended and have closure receipts. Twelve ChemDraw processes remained in the final read-only inventory: two intentionally retained final documents and ten residual processes after native Close/Quit. No unknown process was terminated. Residual-window cleanup lacks a qualified machine-interface recovery in this entrypoint and remains needs_interface.

## Scope and evidence

- Six focused synthetic tests were executed once on exact `b9363ab`, all passed: [static verification](../verification/2026-09-13-agent-edit-loop-controller/static-verification.sanitized.json). They are not native or visual tests.
- Controller no-edit A used `8c923c0`; no-edit B/fractional controls used `b9363ab`. The failed initial export used `406e643`; the failed first Agent A display-metadata attempt used `85f1d4a`. These runs are not relabelled as newer-source tests.
- The Windows implementation packet belongs to its individually bound script/source versions. Its 42 verified members include 34 native-classified files, 6 white previews and 2 source/role files; they are not 42 native controls. It is separate from these actual Agent calls.
- Original A/B hashes and all eight historical evidence files match the pre-stage baseline. Prior P0-B PARTIAL, three earlier native failures and failed offline prechecks are unchanged. Missing old observer fields were not rewritten or treated as new capability failures.
- M2/descendants/holdouts were not read or run; no 055 rerun or H-profile expansion occurred. M1, M2, Gold=0 and overall acceptance remain unchanged.
- Human acceptance, manual correction time and input chemical correctness are unmeasured. No model training, new frontend/service/MCP/installer or release packaging was performed.

Editable outputs, original before/after PNGs, display evidence, hashes and private raw trace are indexed by the local delivery README. Public machine-readable evidence is linked above and in [operation-evidence.json](../verification/2026-09-13-agent-edit-loop-controller/operation-evidence.json).
