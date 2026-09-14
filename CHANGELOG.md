# Change record

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

Earlier execution and acceptance records retain their exact source versions;
this change record does not recertify them.
