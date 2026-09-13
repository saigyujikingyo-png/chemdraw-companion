# Agent Edit Loop v0.1 - developer checkpoint

This is a small local CLI, not an installer or MCP service. Python (with Pillow)
and PowerShell 7 use the already installed licensed ChemDraw and existing native
adapter. A hidden bounded STA worker retains each owned COM document between
separate CLI calls. Default idle expiry is 20 minutes; maximum lifetime two hours.
All artifacts and receipts default to `.local/agent-edit-loop/<session_id>`.

**Checkpoint status: native script validation is still in progress. This commit
is for source review, not Agent, visual, chemical or human acceptance.**

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

Optional `request_id` is a UUID: never reuse it for a different action. Requests
are serialized. Timeout freezes mutation; inspect the retained late receipt and
log, do not replay an uncertain write. No original or saved artifact is overwritten.
Wrong session/document/revision/object tokens refuse. Missing/ambiguous selection
returns candidates. Only unrotated captions are currently supported; unsupported
or unresolved obstacle geometry refuses. The agent chooses IDs, never coordinates.

Position uses native caption bounds, arrow endpoints and BondLength. Above-arrow
uses a 0.25 BondLength initial gap, 0.10 BondLength obstacle margin and at most 16
additional upward steps of 0.25 BondLength. The second intent shifts exactly 0.5
BondLength upward or refuses a collision. It does not move structures/change fonts.

Full native CDXML structure and native text/style readback protect every other
object, without numeric tolerance. Only the target `t`'s `p`/`BoundingBox` may differ
for a movement; target native-coordinate residuals are checked at 1e-6 absolute.
Document name/date/aggregate bounds and page bounds are separately recorded
metadata. Save/reopen differences are reported in full, not hidden as a broad
normalization tolerance. Run a separate `role:"no-edit-control"` copy through
save/reopen first to observe normalization independently; this role blocks moves.

Control A in `edit-loop-controls/` is original ordinary workflow data, with roles
declared before native execution. No mechanism/holdout/055 input is used. Root's
independent control B is not included. Script checks do not count as actual Agent
workflow, native visual inspection, human acceptance or H-profile qualification.
