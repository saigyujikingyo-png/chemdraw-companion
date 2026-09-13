# ChemDraw Companion: Codex cloud development

Part of the [Chembridge cloud workspace](https://github.com/saigyujikingyo-png/chembridge). Read [shared principles](DEVELOPMENT_PRINCIPLES.md) and [contributor instructions](AGENTS.md) first.

The current main branch is an architecture preview. This environment checks its JSON Schema contracts and bounded M2 fixture. It does not execute ChemDraw, verify native layouts or accept the separate implementation branch.

## Environment configuration

Select this repository in Codex Web and name the environment **Chembridge / ChemDraw Companion**. Use the universal image with Python 3.12 and caching. Use the same setup and maintenance command:

```bash
bash scripts/setup_codex_cloud.sh
```

The setup uses a repository-local `.venv`; it does not combine this product's dependencies with another plugin. No OpenAI API key, campus session, tunnel secret or vendor licence is required for these checks.

## Verification commands

```bash
.venv/bin/python contracts/validate_mechanism_fixture.py examples/m2-beckmann-snake.json
```

Record the tested commit, runtime, command output and failures/skips. A setup or protocol pass is not native-software, account, host/model or final-artifact acceptance. Keep those results in this product's own records. Environment configuration does not change source ownership or authorise edits to another task's branch.

See the [Chembridge catalog and cloud guide](https://github.com/saigyujikingyo-png/chembridge) for the shared entrypoint and future-plugin process. Environment creation and real test results are recorded separately; this setup document does not claim a completed native release.
