# Agent Edit Loop v0.1 - developer checkpoint

This is a small local CLI, not an installer or MCP service. Python (with Pillow)
and PowerShell 7 use the already installed licensed ChemDraw and existing native
adapter. A hidden bounded STA worker retains each owned COM document between
separate CLI calls. Default idle expiry is 20 minutes; maximum lifetime two hours.
All artifacts and receipts default to `.local/agent-edit-loop/<session_id>`.

**Checkpoint status: source review and script checks, not Agent, visual, chemical
or human acceptance.** The initial strict failure is retained: the native
serializer added the target caption to `step/@ReactionStepObjectsAboveArrow`.
The controller subsequently authorised the narrow derived-association rule below;
the original failure, control A and earlier receipts are unchanged.

Run one action per invocation. Provide a UTF-8 JSON request file:

```powershell
python probes/native_edit_loop.py --request request.json --powershell <path-to-pwsh.exe>
```

`--powershell` is needed only for `open-copy` when `pwsh` is not on PATH. JSON on
stdin is also supported. One JSON response goes to stdout; exit 2 means refusal,
failure or an uncertain deadline. Use UTF-8 when saving stdout. Every successful
action returns `observation`: the live revision, document ID, candidate captions
and arrows with tokens, complete native XML file, native geometry and native PNG
plus a labelled white-background alpha-composite preview. Read that response and
preview before selecting the next action. Atom text is excluded by XML ownership;
the full XML text runs are authoritative text alongside raw native API values.

1. `{"action":"open-copy","source":"<absolute CDXML or CDX path>","expected_sha256":"<actual source hash>","role":"workflow-control"}`
2. `{"action":"inspect","session_id":"<returned>","document_id":"<returned>","revision":0}`
3. `{"action":"relative-position","session_id":"...","document_id":"...","revision":0,"caption_id":<live ID>,"caption_token":"<live token>","arrow_id":<live ID>,"arrow_token":"<live token>","intent":"above-arrow"}`
4. Submit another `relative-position` using the **new** revision/tokens and
   `"intent":"up-half-bond"`. The tool computes half of actual native BondLength.
5. `{"action":"save","session_id":"...","document_id":"...","revision":<current>,"stem":"edited-a"}` saves new CDXML and CDX; retain returned artifact IDs.
6. `{"action":"reopen","session_id":"...","document_id":"...","revision":<current>,"artifact_id":"<one returned ID>"}` opens those exact hashed bytes in a different fresh process; returns a new document ID/revision. Inspect the new live IDs/tokens before another relative edit. Reopen the other saved format separately when required.
7. End an owned session with an `inspect` request containing `"end_session":true`.
   Add `"keep_open":true` to detach the exact current saved revision for the user
   to continue viewing. Unsaved or poisoned revisions cannot use this option.

Optional `request_id` is a UUID: never reuse it for a different action. Requests
are serialized. Timeout freezes mutation; inspect the retained late receipt and
log, do not replay an uncertain write. No original or saved artifact is overwritten.
Wrong session/document/revision/object tokens refuse. Missing/ambiguous selection
returns candidates. Only unrotated captions directly on a known single physical
page are supported. The caption and arrow must be on that same page, and all four
page edges are checked. Fragment/group captions refuse. Unsupported
or unresolved obstacle geometry refuses. The agent chooses IDs, never coordinates.

Position uses native caption bounds, arrow endpoints and BondLength. Above-arrow
uses a 0.25 BondLength initial gap, 0.10 BondLength obstacle margin and at most 16
additional upward steps of 0.25 BondLength. The second intent shifts exactly 0.5
BondLength upward or refuses a collision. It does not move structures/change fonts.

Full native CDXML structure and native text/style readback protect every other
object, without numeric tolerance. Only the target `t`'s `p`/`BoundingBox` may differ
for a movement; target native-coordinate residuals are checked at 1e-6 absolute.
One explicit exception is separately returned as `derived_association`: the
target caption ID may be added/removed from Above/BelowArrow lists of the unique
step bound only to the selected arrow's exact native/modern ID aliases. Removing
the target ID must leave the same ordered list. All other step attributes,
reactants/products, atom maps, object associations, geometry and styles still
compare strictly. This code never edits these association attributes in ChemDraw;
it only records native output and applies the narrow comparison rule. This is
not called no-edit normalization or an unchanged-all-fields result.
Document name/date/aggregate bounds and page bounds are separately recorded
metadata. Save/reopen differences are reported in full, not hidden as a broad
normalization tolerance. Run a separate `role:"no-edit-control"` copy through
save/reopen first to observe normalization independently; this role blocks moves.
Reopen validates a temporary new process/document before committing its context,
then rechecks the old complete fingerprint immediately before closing the old
document. External/uncertain old changes are preserved, including at worker exit.
Tool-source hashes are returned, and source drift blocks further mutations.

Initial open has one narrowly observed normalization allowance: native export
may add `AS="N"` to an atom or `BS="N"` to a bond when that attribute was absent.
Exact additions are returned as `initial_native_normalization`; other object or
metadata differences refuse. A second PNG/read and a baseline comparison must
then pass the ordinary strict check. This allowance never applies to subsequent
edits, renders, saves or reopens. The controller's initial failure is retained;
the implementation machine previously observed no such initial additions.

Control A in `edit-loop-controls/` is original ordinary workflow data, with roles
declared before native execution. No mechanism/holdout/055 input is used. Root's
independent control B is not included. Script checks do not count as actual Agent
workflow, native visual inspection, human acceptance or H-profile qualification.
