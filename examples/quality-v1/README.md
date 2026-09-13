# Reproducible Quality Oracle v1 controls

These 22 **partial synthetic** cases exercise eight metric families. They are not ChemDraw renders, complete chemical drawings, collected mechanisms, gold samples, M2 inputs or unseen holdout. The fixed proton-transfer IR is retained byte-for-byte across the cases to isolate a visual test. A Br-shaped caption is presentation-only and does not add a bromine atom to that IR.

The [archive](synthetic-controls.zip) contains an index, separately supplied references, requests, content-addressed PNG/IR/calibration assets and a full file manifest. There are 99 archive entries; the manifest covers the other 98 files. The independent run's [results](results.json) retain every metric, missing coverage and distinct evidence outcome. Archive size, SHA-256, source hashes and test versions are recorded in [the validation receipt](../../docs/QUALITY_ORACLE_V1_VALIDATION.json).

Unpack into an empty local directory. Run the validator from the repository with each case and its separate reference. For example:

```text
python contracts/quality/validate_quality.py LOCAL_CONTROLS/tip-positive.case.json --reference LOCAL_CONTROLS/tip-positive.reference.json
```

Synthetic positives exit 2 because overall native acceptance is unverified; measured failures exit 1. Neither result is gold or an integrated Composer qualification. To reproduce the controls from source:

```text
python contracts/quality/build_quality_fixtures.py --out NEW_LOCAL_DIRECTORY
python -m unittest discover -s contracts/quality -p "test_*.py"
```

The builder refuses an existing output directory. Python, jsonschema, NumPy and Pillow are development dependencies; this adds no end-user runtime, installer or host configuration.

Observed outcomes: eight standard positive controls plus a 90-degree tip rotation pass their target metric; twelve negative controls fail their target metric; the twofold nearest-neighbor enlargement has an ambiguous flattened apex and remains unmeasured. Every case is intentionally partial: the other seven metric families are not qualified on that image. Future native isolated-negative qualification must demonstrate their preserved behavior as specified in the [adversarial plan](../../docs/ADVERSARIAL_NEGATIVE_PLAN_V1.md).
