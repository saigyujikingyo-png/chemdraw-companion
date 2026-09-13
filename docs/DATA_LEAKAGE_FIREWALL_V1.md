# Data leakage firewall v1

This firewall implements [Issue #2](https://github.com/saigyujikingyo-png/chemdraw-companion/issues/2)'s generator boundary. Shared collaboration tasks are not isolated model generators: they share the filesystem. Source/custodian/evaluator tasks may inspect targets; their context must never be forwarded to the blind model.

## Executed boundaries

`contracts/paired/firewall.py` runs a process under the already configured elevated Windows Codex sandbox: deny filesystem root, permit only platform minimal runtime, explicit code/runtime files, neutral PNG/schema staging, and a fresh output directory. Explicit forbidden roots may not overlap grants. No installation, user creation, global configuration or credential-file reading is needed. The ordinary read-only sandbox protects writes but is not a read firewall; the unelevated limited-read attempt failed and is preserved.

Six synthetic sentinel categories were actually denied with `PermissionError`/errno 13: hidden CDXML, geometry, coordinates, object IDs, evaluator annotations and target-derived layout constraints. The allowed input remained readable. The generator broker uses the same restricted identity with network permitted solely for its transport function. Directory separation and a prompt saying not to read the answer are insufficient.

`firewall_broker.py` adds an API projection boundary. A normal-identity CLI acts only as the existing authentication custodian; it is not claimed to be OS-isolated. The restricted broker discards its incoming instructions, conversation history, tool definitions and metadata. It reconstructs the complete outgoing request from exactly the staged PNG bytes, the public runtime IR schema and fixed reaction-independent instruction. Model is GPT-5.6 Terra, reasoning max, tools empty, tool choice none. Only the already configured official ChatGPT/Codex responses endpoint is allowed; redirects and arbitrary API paths are rejected. Authentication stays in memory and is not logged or copied into evidence.

The model has no filesystem, evaluator API or tool handle. The output stream is buffered and checked for forbidden tool calls before it can reach the CLI. One initial request per immutable run directory is allowed. API tests inject hidden instructions, source IDs, paths and tool calls to ensure they cannot cross the projection. Shell sandbox tests and API projection tests are independent evidence; neither alone proves the other.

## Run receipt and threat boundary

Before inference, freeze PNG/schema hashes and exact projected request. Record run ID/time, complete generic prompt, requested/actual model and reasoning, payload hash, exposed assets, process profile and denial test receipt. Store original response/SSE, parsed output and parser version separately. A transport parser repair may reprocess the same saved response; it cannot silently invoke another model or change chemical content.

The trusted source/native custodian and developer still have access to their own authorized workspace. This design certifies the restricted broker plus remote no-tools model input boundary, not every process on the machine or a malicious account administrator. Never describe a shared-memory subagent or an ordinary CLI sandbox as a fully blind generator. Missing actual-model identity or unverifiable payload bytes prevents a completed-run claim.

## Input display and truth preservation

The first actual native reference is a transparent PNG with zero RGB values; shape exists in alpha. A consumer that discards alpha obtains a black image. Keep the original native PNG immutable. `normalize_native_png.py` can produce a deterministic fixed-white alpha composite with identical dimensions and no crop, resize, text, geometry or drawing changes. Record original/output hashes and code hash. This output is explicitly **native-derived display normalization**, not a direct ChemDraw export or a layout repair. It remains the same visible native ink under a declared white background. The native original remains the visual provenance root.

Changing exposed PNG bytes starts a new run. The owner separately authorized the original PNG request and the white-background diagnostic request; both are retained independently. The first failure must not disappear when the display issue is addressed. No target CDXML/CDX, source URL, reaction answer, hidden inventory, object IDs, coordinates or evaluation geometry is transmitted with either PNG.

## Exclusions and remaining gates

M2, all descendants and future holdouts remain frozen and excluded; M1 remains exposed development. Target source screening and a lineage registry are separate from access control. The metadata validator checks hashes and stage consistency but does not authenticate a model transport or a renderer merely because a JSON receipt exists.

Current local tests cover actual denial, protected-root grant overlap, payload projection, no-tools responses and stored SSE parsing. Final test counts and real inference outcomes belong in the pilot execution receipt. A malformed or unsupported IR is a preserved failure, never an invitation to copy hidden target chemistry or coordinates. No learned model, MCP expansion, installer, host support or product UI was added.
