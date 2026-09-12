# Chemical Mechanism IR and Mechanism Composer

Architecture revision 2026-09-12.2. These are long-term assets; COM, Add-in and CDXML are replaceable adapters. The first required output remains licensed native ChemDraw CDX/CDXML and native rendering. Backend independence does not permit a silent renderer substitution or claim a second implemented backend.

## Responsibilities

1. Chemical Mechanism IR stores graphs, persistent atom maps, state occurrences, charges/lone pairs, specified stereochemistry, anti/syn relations, elementary transitions, simultaneous electron flows, graph differences and explanatory labels. No COM handles, CDXML IDs or device coordinates belong in this chemical layer.
2. Semantic validation checks every state/transition, mapping/provenance, donor/acceptor eligibility and fixture-specific chemistry. Syntax validation alone cannot establish chemical correctness.
3. Mechanism Composer consumes valid IR, versioned style, measured fragment geometry and layout constraints. It places panels, reserves labels/charges/electrons, routes step connectors separately from curly arrows, and resolves collisions deterministically. Snake traversal is explicit.
4. Backend adapters obtain native fragment geometry when qualified, materialize the composed scene as editable objects, maintain IR/native mappings, save/reopen/render/read back and report unsupported/lossy operations.
5. Verification compares source semantics, composed geometry, native readback and reopened edits, with separate A/B/C and first-output results.

Start with a few modules and a direct probe; no framework, service or full SDK is needed.

## Identity and transitions

An atom map identifies an atom across states. An occurrence such as s2:atom:10 identifies its drawing in one state; native IDs are adapter associations. Bond references are state-scoped endpoint pairs; lone-pair ports use state/atom/pair index. Pair indices are slots, not physical identity claims about indistinguishable electrons.

All arrows for one elementary transition refer to its source-state graph and act simultaneously. Bond donors identify sigma/pi electrons. A migrating bond targets the explicitly identified new bond (for M2, C1-C10 -> N2-C10), whose endpoints both exist in the pre-state; its geometry is a prospective bond port, not a claimed pre-existing bond object. This prevents ambiguity about which end migrates. Compare complete before/after graphs; never treat arrow-array order as sequential chemistry. Proton transfers require explicit mapped H and acid/base species. No hidden proton teleportation.

Geometry uses physical units, object-local ports and chemical occurrence references. Fragment cleanup/transform invalidates port positions and triggers recomputation. Native fragment cleanup is not a multi-step page composer.

## Proof before packaging

The [internal schema](../contracts/mechanism-test-case.schema.json) and [M2 fixture](../examples/m2-beckmann-snake.json) test this boundary without MCP. Version mechanism-ir-test/0.1 is an internal draft, not a supported public recipe. Keep five tools and existing three recipe IDs unchanged. M2 remains mandatory for P0.

A developer harness freezes input/style, obtains native fragments, invokes Composer and native adapter, then produces native/reopen evidence. It does not require installer, MCP, host adaptation or a model call. Missing Composer code is an implementation gap, not an interface limitation.

Use a reviewed manual native reference and frozen-geometry replay to isolate object control from composition. Future backends consume the same IR/scene boundary; a mock serializer only tests contracts, not equivalent native/scientific behavior.

The bounded contract checker is [validate_mechanism_fixture.py](../contracts/validate_mechanism_fixture.py). It checks graph/flow accounting and logical snake order, not native geometry. See [current validation evidence](M2_CONTRACT_VALIDATION.json); the earlier CONTRACT_VALIDATION.json remains unchanged historical evidence for the public schemas.
