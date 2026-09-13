"""Corpus contract negative controls; no native execution or dataset approvals.

Every mutation is in memory. Synthetic correction/freeze records are unit-test
fixtures only, never human records, native receipts, corpus data or holdouts.
Run: python -m unittest discover -s contracts/corpus -p test_corpus.py -v
"""
import copy
from contextlib import contextmanager
import json
from pathlib import Path
import sys
import shutil
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate_corpus as validator

EXAMPLES = HERE.parents[1] / "examples" / "corpus"


def fixture(name):
    return json.loads((EXAMPLES / (name + ".json")).read_text(encoding="utf-8"))


def entity(value, collection, identity):
    return next(row for row in value[collection] if row["id"] == identity)


def correction_fixture():
    """Structurally valid no-op, explicitly nonhuman and not native evidence."""
    return {
        "version": "correction-record/0.1", "id": "unit-test-correction",
        "sample_id": "unit-test-only", "record_kind": "design_fixture",
        "before_revision": "unit-before", "after_revision": "unit-after",
        "before_artifacts": [{"asset_ref": "unit-before", "sha256": "1" * 64}],
        "after_artifacts": [{"asset_ref": "unit-after", "sha256": "2" * 64}],
        "actor": {"id": "unit-test-tool", "kind": "tool"},
        "correspondences": [],
        "operations": [{"id": "unit-operation", "kind": "atom_displacement",
                        "entity_refs": ["unit-occurrence"], "intent_ref": None,
                        "before": [1, 2], "after": [1, 2], "observed_delta": [0, 0],
                        "reason": "in-memory no-op negative-control fixture",
                        "frame_ref": "unit-frame", "units": "pt"}],
        "claims": {"geometry_only": False, "nonzero_edit": False, "human_accepted": False},
        "semantic_equivalence": {"status": "unverified", "verifier": "not-run",
                                 "before_hash": "1" * 64, "after_hash": "2" * 64,
                                 "evidence_refs": []},
        "native_readbacks": [],
        "timing": {"manual_active_seconds": None, "wall_seconds": None,
                   "automatic_seconds": None, "measurement": "unmeasured", "evidence_refs": []},
        "review_refs": [],
    }


class CorpusMechanismTests(unittest.TestCase):
    def reject_integrity(self, value, message):
        # Prove the semantic guard, not an unrelated syntax failure, rejects it.
        validator.syntax("mechanism-ir", value)
        with self.assertRaisesRegex(ValueError, message):
            validator.mechanism(value)

    def test_three_representations_have_bounded_chemistry(self):
        for name in ("proton-transfer.ir", "M1.ir", "M2.ir"):
            with self.subTest(name=name):
                result = validator.mechanism(fixture(name))
                self.assertEqual(result["semantic_valid"], "bounded_pass")
                self.assertEqual(result["native_verified"], "unverified")
                self.assertEqual(result["runtime_projection"], "unverified")

    def test_dangling_electron_port(self):
        value = fixture("M1.ir")
        value["electron_flows"][0]["source"]["lone_pair_ref"] = "missing-lone-pair"
        self.reject_integrity(value, "unknown electronic port")

    def test_sink_cannot_refer_to_product_state(self):
        value = fixture("M1.ir")
        value["electron_flows"][0]["sink"] = {
            "type": "atom", "state_ref": "after", "atom_ref": "after:a2"}
        self.reject_integrity(value, "pre-transition state")

    def test_prestate_label_does_not_hide_product_occurrence(self):
        value = fixture("M1.ir")
        value["electron_flows"][0]["source"]["lone_pair_ref"] = "after:lp1:0"
        self.reject_integrity(value, "port occurrence scope")

    def test_prospective_bond_cannot_be_electron_source(self):
        value = fixture("M1.ir")
        value["electron_flows"][0]["source"] = {
            "type": "prospective_bond", "state_ref": "before",
            "atom_refs": ["before:a1", "before:a2"]}
        with self.assertRaisesRegex(ValueError, "schema:"):
            validator.syntax("mechanism-ir", value)

    def test_m2_prospective_sinks_include_new_bond_and_existing_bond_increment(self):
        value = fixture("M2.ir")
        bonds = {frozenset(b["atom_refs"]) for b in value["bonds"]}
        sinks = [f["sink"] for f in value["electron_flows"]
                 if f["sink"]["type"] == "prospective_bond"]
        self.assertTrue(any(frozenset(s["atom_refs"]) in bonds for s in sinks))
        self.assertTrue(any(frozenset(s["atom_refs"]) not in bonds for s in sinks))
        self.assertEqual(validator.mechanism(value)["semantic_valid"], "bounded_pass")

    def test_duplicate_lone_pair_slot_with_distinct_id(self):
        value = fixture("M1.ir")
        duplicate = copy.deepcopy(value["lone_pairs"][0])
        duplicate["id"] = "unit-duplicate-slot"
        value["lone_pairs"].append(duplicate)
        self.reject_integrity(value, "lone-pair slots")

    def test_same_lone_pair_cannot_be_spent_twice(self):
        value = fixture("M1.ir")
        duplicate = copy.deepcopy(entity(value, "electron_flows", "attack"))
        duplicate["id"] = "unit-second-spend"
        value["electron_flows"].append(duplicate)
        entity(value, "reaction_steps", "substitution")["electron_flow_refs"].append(duplicate["id"])
        self.reject_integrity(value, "same lone pair spent twice")

    def test_m1_bromide_charge_is_chemically_checked(self):
        value = fixture("M1.ir")
        entity(value, "charges", "after:q3")["value"] = 0
        self.reject_integrity(value, "electron/valence accounting")

    def test_m1_bromide_requires_four_lone_pairs(self):
        value = fixture("M1.ir")
        value["lone_pairs"] = [p for p in value["lone_pairs"] if p["id"] != "after:lp3:3"]
        # Removing the highest slot keeps slot contiguity valid.
        self.reject_integrity(value, "electron/valence accounting")

    def test_absolute_coordinates_cannot_enter_chemical_ir(self):
        for collection, key, data in (("atom_occurrences", "x", 10),
                                      ("states", "page_coordinates", [10, 20]),
                                      ("electron_flows", "bezier", [[0, 0]] * 4)):
            with self.subTest(collection=collection):
                value = fixture("M1.ir")
                value[collection][0][key] = data
                with self.assertRaisesRegex(ValueError, "schema:"):
                    validator.syntax("mechanism-ir", value)

    def test_anti_constraint_cannot_be_soft(self):
        value = fixture("M2.ir")
        next(c for c in value["layout_constraints"] if c["kind"] == "anti")["strength"] = "soft"
        self.reject_integrity(value, "chemical stereo cannot be soft")

    def test_anti_central_and_substituent_roles_are_checked(self):
        value = fixture("M2.ir")
        constraint = next(c for c in value["layout_constraints"] if c["kind"] == "anti")
        a, b, x, y = constraint["subjects"]
        constraint["subjects"] = [x, b, a, y]
        self.reject_integrity(value, "central bond or substituent roles invalid")

    def test_rich_radical_syntax_does_not_claim_bounded_chemistry(self):
        value = fixture("M1.ir")
        value["radicals"].append({"id": "unit-radical", "atom_ref": "before:a1",
                                  "unpaired_electrons": 1, "display": "shown"})
        validator.syntax("mechanism-ir", value)
        self.assertEqual(validator.mechanism(value)["semantic_valid"], "unsupported")

    def test_open_inventory_syntax_does_not_claim_bounded_chemistry(self):
        value = fixture("M1.ir")
        value["scope"]["atom_inventory"] = "open_declared"
        value["scope"]["omissions"] = ["unit-test deliberately open scope"]
        validator.syntax("mechanism-ir", value)
        self.assertEqual(validator.mechanism(value)["semantic_valid"], "unsupported")


class CorpusTrustAndSplitTests(unittest.TestCase):
    def test_manifest_and_split_positive_controls(self):
        self.assertEqual(validator.manifest(fixture("proof-manifest"))["gold_samples"], 0)
        self.assertEqual(validator.split(fixture("split-manifest"))["holdout_selection"], "not_started")

    def test_m1_m2_regression_cannot_be_used_for_training_or_tuning(self):
        for sample_id in ("M1", "M2"):
            for use in ("training", "rule_tuning"):
                with self.subTest(sample_id=sample_id, use=use):
                    value = fixture("proof-manifest")
                    sample = entity(value, "samples", sample_id)
                    sample["tier"] = "silver"
                    for right in sample["rights"]:
                        right["status"] = "approved"
                        right["permissions"]["train"] = True
                    sample["uses"][use] = True
                    with self.assertRaisesRegex(ValueError, "schema:"):
                        validator.manifest(value)

    def test_ai_review_cannot_promote_first_party_approved_rights_sample_to_gold(self):
        value = fixture("proof-manifest")
        sample = entity(value, "samples", "proton-transfer")
        sample["source"]["kind"] = "first_party"
        for right in sample["rights"]:
            right["status"] = "approved"
        sample["tier"] = "gold"
        sample["gold_scopes"] = ["semantic"]
        asset = next(a for a in sample["assets"] if a["id"] == sample["mechanism_asset_ref"])
        sample["reviews"] = [{"id": "unit-ai-review", "actor_id": "unit-ai",
                              "actor_kind": "ai", "independent_of_author": True,
                              "scope": "semantic", "revision_id": sample["revision_id"],
                              "reviewed_at": "2026-01-01T00:00:00Z",
                              "target_sha256": asset["sha256"], "decision": "accepted",
                              "evidence_refs": [asset["id"]]}]
        validator.syntax("corpus-manifest", value)
        with self.assertRaisesRegex(ValueError, "gold (needs|review)"):
            validator.manifest(value)

    def test_denied_rights_block_otherwise_eligible_uses(self):
        for use in ("training", "rule_tuning", "public_distribution"):
            with self.subTest(use=use):
                value = fixture("proof-manifest")
                sample = entity(value, "samples", "proton-transfer")
                sample["source"]["kind"] = "first_party"
                sample["tier"] = "silver"
                for right in sample["rights"]:
                    right["status"] = "denied"
                    right["permissions"]["train"] = True
                    right["permissions"]["redistribute"] = True
                sample["uses"][use] = True
                validator.syntax("corpus-manifest", value)
                with self.assertRaisesRegex(ValueError, "rights not cleared for " + use):
                    validator.manifest(value)

    def test_manifest_leakage_group_cannot_span_splits(self):
        value = fixture("proof-manifest")
        entity(value, "samples", "M1")["leakage_group_id"] = entity(value, "samples", "proton-transfer")["leakage_group_id"]
        validator.syntax("corpus-manifest", value)
        with self.assertRaisesRegex(ValueError, "leakage group spans splits"):
            validator.manifest(value)

    def test_split_leakage_group_cannot_span_splits(self):
        value = fixture("split-manifest")
        value["assignments"][1]["leakage_group_id"] = value["assignments"][0]["leakage_group_id"]
        validator.syntax("split-manifest", value)
        with self.assertRaisesRegex(ValueError, "leakage group spans splits"):
            validator.split(value)

    def test_holdout_selection_requires_a_started_freeze(self):
        value = fixture("split-manifest")
        value["freeze"]["selected_holdout_ids"] = ["unit-test-only-placeholder"]
        validator.syntax("split-manifest", value)
        with self.assertRaisesRegex(ValueError, "holdout selected before freeze"):
            validator.split(value)

    def test_frozen_holdout_selection_timestamp_must_follow_freeze(self):
        value = fixture("split-manifest")
        # No molecule is selected: this is only a synthetic event-order fixture.
        value["assignments"].append({"sample_id": "unit-test-only-placeholder",
                                     "leakage_group_id": "unit-test-only-group",
                                     "split": "evaluation_reserved", "exposure_status": "unseen",
                                     "assigned_at": "2026-01-01T00:00:00Z", "reason": "unit-test only"})
        value["freeze"] = {"status": "frozen", "commit": "unit-test-not-a-real-commit",
                            "bundle_sha256": "a" * 64,
                            "selected_holdout_ids": ["unit-test-only-placeholder"],
                            "generation": 1, "base_pass_receipt_sha256": "b" * 64,
                            "base_passed_at": "2026-01-01T00:00:00Z",
                            "frozen_at": "2026-01-02T00:00:00Z",
                            "selections": [{"sample_id": "unit-test-only-placeholder",
                                            "selected_at": "2026-01-03T00:00:00Z",
                                            "disclosed_at": None, "evaluator_id": "unit-test-tool",
                                            "independent_of_tuning": True,
                                            "freeze_bundle_sha256": "a" * 64}]}
        self.assertEqual(validator.split(value)["holdout_selection"], "frozen")
        value["freeze"]["selections"][0]["selected_at"] = "2026-01-01T12:00:00Z"
        with self.assertRaisesRegex(ValueError, "holdout chosen before freeze"):
            validator.split(value)


class CorpusAnnotationAndCorrectionTests(unittest.TestCase):
    def test_annotation_and_design_correction_positive_controls(self):
        self.assertEqual(validator.annotation(fixture("M1.annotation"))["gold_approval"], "not_conferred")
        result = validator.correction(correction_fixture())
        self.assertEqual(result["native_execution"], "not_performed")
        self.assertEqual(result["gold_approval"], "not_conferred")

    def test_cubic_bezier_requires_all_four_points(self):
        value = fixture("M1.annotation")
        observation = next(o for o in value["observations"] if o["geometry"]["kind"] == "bezier")
        self.assertEqual(len(observation["geometry"]["points"]), 4)
        observation["geometry"]["points"].pop()
        validator.syntax("annotation", value)
        with self.assertRaisesRegex(ValueError, "incomplete geometry points"):
            validator.annotation(value)

    def test_unmeasured_manual_time_cannot_be_zero(self):
        value = correction_fixture()
        value["timing"]["manual_active_seconds"] = 0
        validator.syntax("correction-record", value)
        with self.assertRaisesRegex(ValueError, "unmeasured manual time must be null"):
            validator.correction(value)

    def test_nonzero_claim_rejects_observed_noop(self):
        value = correction_fixture()
        value["claims"]["nonzero_edit"] = True
        validator.syntax("correction-record", value)
        with self.assertRaisesRegex(ValueError, "no observed nonzero edit"):
            validator.correction(value)

    def test_serialization_difference_is_not_a_nonzero_object_edit(self):
        value = correction_fixture()
        value["claims"]["nonzero_edit"] = True
        value["operations"][0].update(kind="serialization_only", after=[3, 4])
        validator.syntax("correction-record", value)
        with self.assertRaisesRegex(ValueError, "no observed nonzero edit"):
            validator.correction(value)


@contextmanager
def temporary_bundle():
    # Only small JSON fixtures are copied; context cleanup targets this verified
    # temporary directory and cannot address the source fixture directory.
    with tempfile.TemporaryDirectory(prefix="corpus-unit-") as temporary:
        directory = Path(temporary).resolve()
        assert directory.is_relative_to(Path(tempfile.gettempdir()).resolve())
        assert directory.name.startswith("corpus-unit-")
        for name in ("proton-transfer.ir", "M1.ir", "M2.ir", "M1.annotation",
                     "proof-manifest", "split-manifest"):
            shutil.copyfile(EXAMPLES / (name + ".json"), directory / (name + ".json"))
        yield directory


class CorpusBundleTests(unittest.TestCase):
    def test_bundle_positive_checks_local_bytes_without_native_execution(self):
        result = validator.bundle(EXAMPLES)
        self.assertEqual(result["status"], "pass")
        self.assertFalse(result["fresh_native_execution"])
        self.assertEqual(result["gold_samples"], 0)
        self.assertEqual(len(result["mechanisms"]), 3)

    def test_cross_manifest_disagreement_cannot_hide_in_individually_valid_files(self):
        for field, replacement in (("leakage_group_id", "unit-distinct-group"),
                                   ("split", "development"),
                                   ("exposure_status", "exposed")):
            with self.subTest(field=field), temporary_bundle() as directory:
                path = directory / "split-manifest.json"
                partitions = json.loads(path.read_text(encoding="utf-8"))
                row = next(a for a in partitions["assignments"] if a["sample_id"] == "M1")
                row[field] = replacement
                validator.split(partitions)
                path.write_text(json.dumps(partitions), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "split/registry disagreement"):
                    validator.bundle(directory)


if __name__ == "__main__":
    unittest.main()
