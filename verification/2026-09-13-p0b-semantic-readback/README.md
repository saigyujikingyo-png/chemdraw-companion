# P0-B native semantic readback: implementation handoff

Final implementation: **2d6ac0d8a510d912f8e03157cf182cd6ce403683**.
Final source-freeze commit: **56ace46880bf946e058b31695791e358398fec87**.
The preregistered 20-input matrix at 7633111 remains unchanged.

The final native batch qualifies **19 measured observation branches** for
independent controller review. It does not qualify the entire proposed profile
or establish overall ChemDraw, native visual or human acceptance. The supplied
admission proposal remains pending and is intentionally refused by production.

| Final r4 check | Observed result |
|---|---|
| Native cleanup and independent CDXML reopen | 20 controls, 66 atoms, 40 distinct initially empty PID/start/HWND-bound processes |
| Independent expected comparison and delivered adapter | 16 controls / 57 atoms match in both phases |
| Unsupported native contrasts | Benzene and radical controls remain unverified/refused |
| Diagnostic-only controls | Methane retains warning 1; native-normalized H3/CH4 conflict remains outside positive qualification |
| Reopened H source branches | 37 selected native formulas, 20 explicit noncarbon fields, 9 unknown |
| Actual serialized H presence | 22 present, 44 missing; all original seeds had explicit NumHydrogens |
| Source/label integrity | Exact code/profile/build/sidecar hashes and full nested atom-label invariance checked |
| Guarded runtime tests | 67 passed; 12 excluded and 21 unscheduled are not passes |
| Complete-evidence admission checks | Valid evidence accepted for a private test; missing member, wrong hash, invented branch and two-key summary refused |
| Native worker duration | 35.328 seconds for final r4; no user-owned native process was changed |

The query tests first establish an API-bound ordinary baseline that matches,
then change only a real CDXML query property and require query-specific refusal.
Production admission is derived from actual cleanup **and** reopen coverage and
rechecked from the complete 161-file native/comparison evidence inventory.
Uncovered field/source/scope/atom/H branches remain unknown. Production compares
cleanup and reopened semantics against the same declared visible chemistry and
requires their consistency, preserving native ID remapping separately.

`source-freeze-r4.json` lists all 33 source/dependency files and 24 frozen
input/manifest files, exact raw hashes, installed dependency identities and
executor binary hashes. No dependency was added and no vendor binary is shipped.
The deadline wrapper's historical inventory also names `native-snapshot.ps1`;
the new semantic executor does not import or execute that legacy snapshot helper.

## Evidence and independent reproduction

- [Control receipt](control-receipt-r4.json), [implementation receipt](implementation-receipt-r4.json), [guarded regression](regression-r4.json), [admission checks](admission-checks-r4.json).
- [Complete synthetic package](native-controls-r4.zip): **1,422,192 bytes**, SHA-256 **33dfe5fc4d07ca02cfe7f82e65e52d05abc29f061625594b3281068954a5a76a**. All **739 content members** were read back and hash-checked; the ZIP also contains its member manifest.
- [Pending admission proposal](qualification-proposal-r4.json). Extract the package into `native-controls-r4/` beside this proposal. Only an independently approved qualification record should set `status` to `qualified`; retain the same bound source/control receipt and complete evidence directory.
- [Qualification implementation and limits](../../runtime/NATIVE_SEMANTIC_QUALIFICATION_V1_1.md).

The package contains exact latest and historical source trees, original
synthetic native CDXML/sidecars and comparison records. Machine-local prefixes
are removed only from explicitly labelled event/execution-receipt derivatives;
the sanitation manifest preserves original and derived hashes. Full original
machine journals and all first-failure evidence are retained in the owner's
local delivery archive. None of the native CDXML or sidecar bytes was edited.

For offline reproduction, use the extracted `source-tree` and run the documented
`verify_native_semantic_controls.py` command in the package README. This invokes
the delivered reader and comparisons without opening native software. The
full repository remains the source for the guarded runtime regression suite.

## Preserved history and remaining gate

r1 stopped after closing the first document because the initial probe required
its live HWND to survive Close. r2 corrected only that lifecycle boundary. r3
removed unexercised label-only and carbon-field-only H fallbacks. Independent
review then identified real query-name and incomplete qualification-admission
gaps; r4 corrects those. All prior sources, freezes, outputs and preliminary
computed receipts remain separately labelled. Their results are not silently
reclassified as final qualification.

The private candidate was not read, replayed or run here. The controller owns
independent verification, offline fixed-input preflight and this phase's
at-most-one attempt. New 0.5 evidence cannot qualify old 0.4 sidecars; a known
preflight refusal stops without a redundant native run. Composer geometry,
routing, thresholds, IR bytes and earlier visual failures are unchanged. M2,
descendants and holdouts remain unread/unexecuted/unscored. Gold remains zero.
