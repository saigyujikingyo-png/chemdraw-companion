# ChemDraw Companion

Architecture preview, 2026-09-12. No native execution, host acceptance, installer or release is certified by this repository yet.

ChemDraw Companion is a proposed independent Chembridge plugin for producing and revising editable structures, ordinary reaction schemes and bounded electron-flow diagrams through a user's licensed ChemDraw installation. It is not a Revvity or University of Edinburgh product.

Start with [the implementation handoff](docs/IMPLEMENTATION_HANDOFF.md), then [architecture](docs/ARCHITECTURE.md), [interface contract](docs/INTERFACE_CONTRACT.md) and [quality gates](docs/QUALITY_GATES.md). The [risk register](docs/RISK_REGISTER.md) tracks stop conditions. The [source ledger](docs/SOURCES.md) separates documented capabilities from tests that still need to run.

The first milestone is three native sample workflows with saved and reopened editable documents and owner-approved figures. Open-source chemistry libraries may independently validate semantics. They must not silently replace promised native generation, cleanup, rendering or exports.

Use one host-neutral execution core and one product identity. ChatGPT Work cloud/local, Claude and WorkBuddy are targets until their actual workflows and artifact delivery have been tested. GPT-5.6 Terra with max reasoning is the acceptance benchmark; the development model is not benchmark evidence.

Public documentation and future GitHub Releases are in English. Ordinary use must not require a checkout, Git, a separately installed programming runtime or hand-edited JSON. Installation and update behavior remain design requirements until implemented and tested.
