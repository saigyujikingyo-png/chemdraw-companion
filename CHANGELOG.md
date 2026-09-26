# Change record

## 0.2.0-preview.2 (diagnostic MCP compatibility)

- Accept standard request metadata for tools/list and tools/call, including Codex progressToken=0. Keep the one-page catalog and empty diagnostic arguments strict.
- Reject malformed metadata, unknown operation fields, all unissued cursors and native/tool argument requests before the producer.
- Preserve a recorded official Codex discovery fixture, failing preview.1 evidence and an isolated official-client verification harness. No native capability or runtime dependency is added.

## 0.2.0-preview.1 (native-disabled diagnostic preview)

- Add durable versioned lifecycle receipts, startup deduplication, bounded same-attempt observation and owned exit semantics, verified through portable failure boundaries.
- Keep native dispatch frozen and preserve historical partial acceptance.
- Add a self-contained diagnostic status MCP package, versioned installation/rollback and MIT source licensing. Package, installed-host and native acceptance remain separate.

## 2026-09-14 - shared-rule adoption, documentation only

- Adopt shared principles **2026-09-14.1**, including section 12 on structured tool
  outputs, and synchronize contributor/product-scope guidance from the reviewed
  shared commits. The rule version is not a ChemDraw product version.
- Add [output-schema coverage, compatibility/version planning and validation
  requirements](runtime/OUTPUT_SCHEMA_COVERAGE_PLAN.md): all five design MCP tools,
  their fifteen dispatch variants and the existing five CLI actions. OutputSchema,
  matching structuredContent and producer-side validation remain pending.
- Propose Agent Edit Loop **v0.1.1** only for a future explicitly unfrozen,
  compatible output-contract change; no product release/tag/version bump occurs
  here. Breaking changes require a separately reviewed migration.
- Preserve executable source at **b9363ab**, Machine Interface Only, M2 isolation,
  the closed Agent Edit Loop v0.1 **PARTIAL** result and all historical failures.
  No native/UI run, MCP service, packaging or schema-conformance claim is added.
- Pin Origin Companion 0.2.11 source `8bff772` as an output-contract design
  reference, with ChemDraw-specific pending checks for strict typing, retained IDs
  without write replay, dispatch discovery, media blocks and text compatibility.
  No Origin code, dependency or test/native/installation acceptance is imported.

Earlier execution and acceptance records retain their exact source versions;
this change record does not recertify them.
