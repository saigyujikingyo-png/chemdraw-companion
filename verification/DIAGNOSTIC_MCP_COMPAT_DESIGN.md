# Diagnostic MCP compatibility repair

Design checkpoint: 2026-09-19. Target: 0.2.0-preview.2.
Baseline: c6cfa3ec398d4659a3e61a6e48460e689f84e530 (0.2.0-preview.1).

## Failure and outcome

Real Codex startup reaches tools/list but receives -32602 because the server
rejects every nonempty params object as a cursor. File integrity and registration
passed; fresh host discovery failed. The earlier hand-written stdio check used
empty params and did not cover this client boundary.

Accept standard request metadata separately from operation parameters. A
single-page catalog returns its complete one-tool list when no continuation cursor
is supplied, without nextCursor. Keep invalid metadata, unknown operation fields,
unsupported cursors, unknown tools and nonempty tool arguments as bounded -32602
errors. The tool still accepts exactly an empty argument object. The recorded official request is {"_meta":{"progressToken":0}}, without a
cursor. No issued continuation cursor exists; all supplied cursor values, including
null or empty strings, remain invalid. This follows the negotiated 2025-06-18
optional string cursor contract; metadata is a separate optional object.

## Scope and invariants

Change only the diagnostic server, its protocol regression tests and a bounded
official-client verification harness, the preview version/schema constants and
relevant release documentation. No native controller/worker change, native route,
new tool, permission expansion, dependency in the distributed runtime or schema
weakening. Metadata is neither an execution option nor reflected into tool output.
Keep producer validation, structured/text agreement, 64 KiB messages and EOF exit.

Use the supported local Codex client to capture and verify real discovery. Keep
this probe isolated from unrelated MCP/native servers through supported per-process
configuration. It must not create a user task, call a model, edit app internals,
change caches or use a remote host. An official-client protocol result remains
separate from an actual model tool call in the desktop task.

## Acceptance and delivery

1. Retain the failing baseline and the real client's nonempty request shape.
2. Test omitted/empty/metadata-bearing list requests and metadata-bearing calls,
   plus invalid cursor, metadata, extra fields, tool name and argument cases.
3. Run affected diagnostic/installer tests and the official-client discovery/call
   checks against the final candidate; preserve failures and EOF/process receipts.
4. Freeze a clean commit and deterministic immutable preview. Independently verify
   source mapping, complete package hashes and the unchanged official runtime.
5. Obtain the existing Governance exact-candidate review, then publish a new tag,
   release and PR without overwriting preview.1. Download and compare the asset.
6. Install preview.2 through the reviewed installer, retain preview.1 and receipts,
   update the owned official registration, read back every file/command and verify
   actual discovery. Report fresh desktop-model evidence separately; hand back a
   safe checkpoint if a normal host exit/refresh is needed.

References: [MCP request metadata](https://modelcontextprotocol.io/specification/2025-06-18/schema#jsonrpcrequest),
[MCP pagination](https://modelcontextprotocol.io/specification/2025-06-18/server/utilities/pagination),
[Codex app-server](https://learn.chatgpt.com/docs/app-server).
