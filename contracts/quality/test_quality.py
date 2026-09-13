"""Synthetic oracle regressions, not native ChemDraw execution or gold collection."""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_quality_fixtures import (build, digest, json_bytes, png_bytes, IR_FILE,
                                    METRICS, layer, plus, arrow, dots)
from common import read_json, parse_json_bytes, validate_schema
from validate_quality import evaluate, polyline_samples, main as oracle_main, port_ref, Unmeasured


class QualityOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed_temp = tempfile.TemporaryDirectory(prefix="quality-oracle-seed-")
        cls.seed = Path(cls.seed_temp.name) / "bundle"
        cls.index = build(cls.seed)

    @classmethod
    def tearDownClass(cls):
        cls.seed_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="quality-oracle-test-")
        root = Path(self.temp.name).resolve()
        self.assertTrue(root.is_relative_to(Path(tempfile.gettempdir()).resolve()))
        self.assertTrue(root.name.startswith("quality-oracle-test-"))
        self.base = root / "bundle"
        shutil.copytree(self.seed, self.base)
        self.select("tip-positive")

    def tearDown(self):
        # Only removes the verified TemporaryDirectory created by this test.
        self.temp.cleanup()

    def select(self, name):
        row = next(r for r in self.index["cases"] if r["name"] == name)
        self.value = read_json(self.base / row["case"])
        self.reference_path = self.base / row["reference"]
        self.reference = read_json(self.reference_path)
        return self.value

    def run_case(self):
        return evaluate(self.value, self.base, self.reference_path)

    def metric(self):
        return self.run_case()["metrics"][0]

    def write_reference(self):
        # Deliberately supplied external references for malformed-input unit tests;
        # these are never claimed as independent human/native records.
        data = json_bytes(self.reference)
        self.reference_path = self.base / "unit-external-reference.json"
        self.reference_path.write_bytes(data)
        self.value["reference_sha256"] = digest(data)

    def asset(self, ref):
        return next(a for a in self.value["assets"] if a["id"] == ref)

    def replace_asset(self, ref, data, suffix=".png"):
        item = self.asset(ref)
        relative = "assets/unit-" + digest(data) + suffix
        (self.base / relative).write_bytes(data)
        item.update(path=relative, bytes=len(data), sha256=digest(data))

    def rebuild_render(self):
        im = Image.open(self.base / self.asset(self.value["render_asset_ref"])["path"])
        result = Image.new("RGBA", im.size, "white")
        for obj in self.value["objects"]:
            with Image.open(self.base / self.asset(obj["asset_ref"])["path"]) as source:
                result = Image.alpha_composite(result, source.convert("RGBA"))
        self.replace_asset(self.value["render_asset_ref"], png_bytes(result))

    def test_eight_metric_positive_and_obvious_negative_families(self):
        observed = {status: set() for status in ("pass", "fail")}
        for row in self.index["cases"]:
            with self.subTest(case=row["name"]):
                self.select(row["name"])
                result = self.run_case()
                validate_schema("oracle-result.schema.json", result)
                metric = result["metrics"][0]
                self.assertEqual(metric["status"], row["expected_metric_status"], metric)
                if metric["status"] in observed:
                    observed[metric["status"]].add(metric["metric"])
                self.assertNotEqual(result["visual_quality"], "pass")
                self.assertFalse(result["actual_gold_collected"])
                self.assertEqual(result["evidence_mode"], "synthetic")
        self.assertEqual(observed["pass"], set(METRICS))
        self.assertEqual(observed["fail"], set(METRICS))

    def test_every_visual_case_preserves_exact_ir_bytes(self):
        expected = IR_FILE.read_bytes()
        for row in self.index["cases"]:
            self.select(row["name"])
            item = self.asset(self.value["ir_asset_ref"])
            self.assertEqual((self.base / item["path"]).read_bytes(), expected)
            self.assertEqual(item["sha256"], digest(expected))
            self.assertEqual(self.reference["ir_sha256"], digest(expected))
        self.assertEqual(self.index["chemical_ir_sha256"], digest(expected))

    def test_complete_asset_manifest_verifies(self):
        manifest = read_json(self.base / "manifest.json")
        declared = set()
        for row in manifest["files"]:
            data = (self.base / row["path"]).read_bytes()
            self.assertEqual(len(data), row["bytes"])
            self.assertEqual(digest(data), row["sha256"])
            declared.add(row["path"])
        actual = {p.relative_to(self.base).as_posix() for p in self.base.rglob("*") if p.is_file()}
        self.assertEqual(actual - {"manifest.json"}, declared)

    def test_builder_is_deterministic(self):
        second = Path(self.temp.name) / "second"
        build(second)
        self.assertEqual((second / "manifest.json").read_bytes(), (self.seed / "manifest.json").read_bytes())

    def test_builder_refuses_existing_output(self):
        with self.assertRaisesRegex(ValueError, "overwrite"):
            build(self.base)

    def test_visible_tip_is_pixel_apex(self):
        self.assertEqual(tuple(self.metric()["measurements"]["visible_point_px"]), (160, 70))
        self.select("tip-displaced")
        self.assertEqual(tuple(self.metric()["measurements"]["visible_point_px"]), (192, 70))
        self.assertEqual(self.metric()["status"], "fail")

    def test_rotated_pixels_preserve_tip_pass(self):
        self.select("tip-rotated")
        self.assertEqual(self.metric()["status"], "pass")

    def test_pixel_doubling_flat_apex_is_explicitly_unmeasured(self):
        self.select("tip-scaled")
        result = self.metric()
        self.assertEqual(result["status"], "unmeasured")
        self.assertIn("apex", result["reason"])

    def test_forged_tip_coordinate_field_is_rejected(self):
        self.value["measurements"][0]["tip"] = [160, 70]
        with self.assertRaises(ValueError):
            self.run_case()

    def test_main_cannot_move_locked_target(self):
        self.select("tip-displaced")
        self.value["measurements"][0]["target"]["point"] = [192, 70]
        with self.assertRaisesRegex(ValueError, "locked reference"):
            self.run_case()

    def test_reference_hash_is_bound(self):
        self.value["reference_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "reference hash"):
            self.run_case()

    def test_reference_ir_hash_is_bound(self):
        self.reference["ir_sha256"] = "0" * 64
        self.write_reference()
        with self.assertRaisesRegex(ValueError, "IR binding"):
            self.run_case()

    def test_candidate_cannot_select_reference_path(self):
        self.value["reference_file"] = "attacker-reference.json"
        with self.assertRaises(ValueError):
            self.run_case()

    def test_unqualified_reference_cannot_pass(self):
        self.reference["source"] = "unqualified"
        self.write_reference()
        self.assertEqual(self.metric()["status"], "unmeasured")

    def test_wrong_semantic_port_is_rejected_even_in_reference(self):
        self.value["measurements"][0]["target"]["entity_ref"] = "before:a2"
        self.reference["measurements"][0]["target"]["entity_ref"] = "before:a2"
        self.write_reference()
        with self.assertRaisesRegex(ValueError, "semantic port"):
            self.run_case()

    def test_unknown_flow_is_rejected(self):
        self.value["measurements"][0]["flow_ref"] = "missing-flow"
        self.reference["measurements"][0]["flow_ref"] = "missing-flow"
        self.write_reference()
        with self.assertRaisesRegex(ValueError, "unknown electron flow"):
            self.run_case()

    def test_unknown_metric_is_rejected(self):
        self.value["measurements"][0]["metric"] = "a-new-unsupported-metric"
        with self.assertRaises(ValueError):
            self.run_case()

    def test_wrong_state_arrow_and_head_are_rejected(self):
        for obj in self.value["objects"]:
            obj["state_ref"] = "after"
        for obj in self.reference["object_bindings"]:
            obj["state_ref"] = "after"
        self.write_reference()
        with self.assertRaisesRegex(ValueError, "wrong state"):
            self.run_case()

    def test_omitted_registered_layer_is_rejected(self):
        self.value["objects"].pop()
        with self.assertRaisesRegex(ValueError, "inventory mismatch"):
            self.run_case()

    def test_missing_object_asset_is_rejected(self):
        layer_ref = self.value["objects"][0]["asset_ref"]
        self.value["assets"] = [a for a in self.value["assets"] if a["id"] != layer_ref]
        with self.assertRaises((ValueError, KeyError)):
            self.run_case()

    def test_subset_ink_with_stale_hash_is_rejected(self):
        obj = self.value["objects"][0]
        item = self.asset(obj["asset_ref"])
        path = self.base / item["path"]
        with Image.open(path) as source:
            im = source.convert("RGBA")
        im.putpixel((40, 70), (255, 255, 255, 0))
        path.write_bytes(png_bytes(im))
        with self.assertRaisesRegex(ValueError, "byte count|SHA-256"):
            self.run_case()

    def test_layer_ink_absent_from_render_is_rejected(self):
        item = self.asset(self.value["render_asset_ref"])
        with Image.open(self.base / item["path"]) as source:
            im = source.convert("RGBA")
        im.putpixel((160, 70), (255, 255, 255, 255))
        self.replace_asset(item["id"], png_bytes(im))
        with self.assertRaisesRegex(ValueError, "absent from final render"):
            self.run_case()

    def test_uncovered_render_ink_never_becomes_complete_acceptance(self):
        item = self.asset(self.value["render_asset_ref"])
        with Image.open(self.base / item["path"]) as source:
            im = source.convert("RGBA")
        im.putpixel((5, 5), (0, 0, 0, 255))
        self.replace_asset(item["id"], png_bytes(im))
        result = self.run_case()
        self.assertEqual(result["uncovered_render_ink_pixels"], 1)
        self.assertEqual(result["visual_quality"], "unverified")

    def test_colour_partition_cannot_prove_nonoverlap(self):
        self.select("overlap-positive")
        self.value["evidence"]["object_layers"] = "visible_colour_partition"
        result = self.metric()
        self.assertEqual(result["status"], "unmeasured")
        self.assertIn("colour masks", result["reason"])

    def test_observed_overlap_still_fails_with_colour_partition(self):
        self.select("overlap-charge")
        self.value["evidence"]["object_layers"] = "visible_colour_partition"
        self.assertEqual(self.metric()["status"], "fail")

    def test_scene_allowance_injection_is_rejected(self):
        self.value["native_head_metrics"] = {"arrowhead_allowance_pt": 1e6}
        with self.assertRaises(ValueError):
            self.run_case()

    def test_metric_threshold_injection_is_rejected(self):
        self.value["measurements"][0]["maximum_distance"] = 1e6
        with self.assertRaises(ValueError):
            self.run_case()

    def test_policy_hash_mismatch_is_rejected(self):
        self.value["policy_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "policy hash"):
            self.run_case()

    def test_style_mismatch_is_rejected(self):
        self.value["style"]["stroke_pt"] = 1.2
        with self.assertRaisesRegex(ValueError, "style"):
            self.run_case()

    def test_native_build_mismatch_is_rejected(self):
        self.value["native_build"] = "unrelated-build"
        with self.assertRaisesRegex(ValueError, "native.build"):
            self.run_case()

    def test_missing_calibration_is_rejected(self):
        ref = self.value["calibration_asset_ref"]
        self.value["assets"] = [a for a in self.value["assets"] if a["id"] != ref]
        with self.assertRaises((ValueError, KeyError)):
            self.run_case()

    def test_million_point_calibration_allowance_is_rejected(self):
        ref = self.value["calibration_asset_ref"]
        item = self.asset(ref)
        calibration = read_json(self.base / item["path"])
        calibration["limits"]["head_extension_pt"] = 1e6
        self.replace_asset(ref, json_bytes(calibration), ".json")
        with self.assertRaises(ValueError):
            self.run_case()

    def test_large_polyline_is_rejected_before_sample_allocation(self):
        with self.assertRaisesRegex(ValueError, "workload limit before allocation"):
            polyline_samples([[0, 0], [16000, 0], [16000, 1]])

    def test_tip_interval_crossing_threshold_is_unmeasured(self):
        threshold = read_json(HERE / "policy-v1.json")["metrics"]["visible_tip_target"]["maximum_distance"]
        point = [160 + threshold * self.value["style"]["bond_pt"] * self.value["pixels_per_pt"], 70]
        self.value["measurements"][0]["target"]["point"] = point
        self.reference["measurements"][0]["target"]["point"] = point
        self.write_reference()
        result = self.metric()
        self.assertEqual(result["status"], "unmeasured")
        self.assertIn("uncertainty", result["reason"])

    def test_lp_quadrant_boundary_is_unmeasured(self):
        self.select("lp-positive")
        for m in (self.value["measurements"][0], self.reference["measurements"][0]):
            m["atom_point"] = [110, 82]
            m["expected_radial_deg"] = 270
        self.write_reference()
        self.assertEqual(self.metric()["status"], "unmeasured")

    def test_lp_slot_swap_is_rejected(self):
        self.select("lp-positive")
        self.value["measurements"][0]["lp_ref"] = "before:lp1:1"
        self.reference["measurements"][0]["lp_ref"] = "before:lp1:1"
        self.write_reference()
        with self.assertRaisesRegex(ValueError, "LP slot binding"):
            self.run_case()

    def test_closed_shaft_has_no_qualified_tail(self):
        self.select("tail-positive")
        loop = layer(lambda d: (d.ellipse((40, 40, 120, 100), outline="black", width=3),
                                d.line((120, 70, 140, 70), fill="black", width=3)))
        im = Image.alpha_composite(loop, arrow()["head"])
        self.replace_asset(self.value["objects"][0]["asset_ref"], png_bytes(im))
        self.rebuild_render()
        result = self.metric()
        self.assertEqual(result["status"], "unmeasured")
        self.assertIn("topologically ambiguous", result["reason"])

    def test_step_omitted_near_object_cannot_pass(self):
        self.select("spacing-positive")
        image = plus(115, 140)
        data = png_bytes(image)
        item = {"id": "unit-near-charge", "path": "assets/unit-near-charge.png", "kind": "object_layer",
                "sha256": digest(data), "bytes": len(data)}
        (self.base / item["path"]).write_bytes(data)
        self.value["assets"].append(item)
        binding = {"id": "near-charge", "kind": "charge", "state_ref": "before", "semantic_refs": ["before:q2"]}
        self.value["objects"].append({**binding, "asset_ref": item["id"]})
        self.reference["object_bindings"].append(binding)
        self.write_reference()
        self.rebuild_render()
        result = self.metric()
        self.assertEqual(result["status"], "unmeasured")
        self.assertIn("omits registered", result["reason"])

    def test_missing_measurements_are_not_pass(self):
        self.value["measurements"] = []
        self.reference["measurements"] = []
        self.write_reference()
        result = self.run_case()
        self.assertEqual(result["metric_verdict"], "unmeasured")
        self.assertEqual(set(result["missing_metric_families"]), set(METRICS))

    def test_nonfinite_observation_is_rejected(self):
        self.value["measurements"][0]["target"]["point"][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            self.run_case()

    def test_duplicate_json_keys_and_nonfinite_json_are_rejected(self):
        for data in (b'{"x":1,"x":2}', b'{"nested":{"x":1,"x":2}}', b'{"x":NaN}', b'{"x":1e999}'):
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    parse_json_bytes(data)

    def test_duplicate_measurements_are_rejected(self):
        self.value["measurements"].append(copy.deepcopy(self.value["measurements"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate metric"):
            self.run_case()

    def test_synthetic_cannot_be_promoted_by_claimed_human_acceptance(self):
        self.value["evidence"]["human_acceptance"] = "accepted"
        self.value["evidence"]["inventory_complete"] = True
        result = self.run_case()
        self.assertEqual(result["human_acceptance"], "unverified")
        self.assertEqual(result["visual_quality"], "unverified")
        self.assertFalse(result["actual_gold_collected"])
        self.assertEqual(result["native_layer_authenticity"], "not_authenticated")


    def test_native_label_cannot_promote_synthetic_assets(self):
        self.value["evidence_mode"] = "native"
        with self.assertRaisesRegex(ValueError, "native-render asset kind"):
            self.run_case()

    def test_native_asset_labels_cannot_promote_synthetic_calibration(self):
        self.value["evidence_mode"] = "native"
        self.asset(self.value["render_asset_ref"])["kind"] = "native_render"
        for obj in self.value["objects"]:
            self.asset(obj["asset_ref"])["kind"] = "native_object_render"
        with self.assertRaisesRegex(ValueError, "synthetic calibration"):
            self.run_case()

    def test_dangling_provenance_references_are_rejected(self):
        for field in ("native_receipt_asset_ref", "annotation_review_asset_ref"):
            with self.subTest(field=field):
                self.select("tip-positive")
                self.value["evidence"][field] = "missing-evidence"
                with self.assertRaisesRegex(ValueError, "dangling provenance"):
                    self.run_case()

    def test_asset_byte_budget_is_checked_before_read(self):
        self.value["assets"][0]["bytes"] = 100000001
        with self.assertRaisesRegex(ValueError, "asset budget"):
            self.run_case()

    def test_unsupported_port_helper_cannot_pass(self):
        with self.assertRaisesRegex(Unmeasured, "not implemented"):
            port_ref({"type": "prospective_bond"})

    def test_wrong_lp_state_cannot_pass(self):
        self.select("lp-positive")
        self.value["objects"][0]["state_ref"] = "after"
        self.reference["object_bindings"][0]["state_ref"] = "after"
        self.write_reference()
        with self.assertRaises(ValueError):
            self.run_case()

    def test_wrong_lp_object_kind_cannot_pass(self):
        self.select("lp-positive")
        self.value["objects"][0]["kind"] = "label"
        self.reference["object_bindings"][0]["kind"] = "label"
        self.write_reference()
        with self.assertRaises(ValueError):
            self.run_case()

    def test_cli_positive_and_negative_exit_codes_never_native_pass(self):
        for name, expected in (("tip-positive", 2), ("tip-displaced", 1)):
            with self.subTest(case=name):
                self.select(name)
                path = self.base / (name + ".case.json")
                with patch.object(sys, "argv", ["validate_quality.py", str(path), "--reference", str(self.reference_path)]):
                    with redirect_stdout(io.StringIO()) as stream:
                        code = oracle_main()
                self.assertEqual(code, expected)
                self.assertNotEqual(json.loads(stream.getvalue())["visual_quality"], "pass")

    def test_cli_requires_explicit_external_reference(self):
        with patch.object(sys, "argv", ["validate_quality.py", str(self.base / "tip-positive.case.json")]):
            with patch("sys.stderr", io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    oracle_main()
        self.assertEqual(caught.exception.code, 2)



    def test_scaffold_pixel_displacement_cannot_reuse_old_reference_pass(self):
        self.select("scaffold-positive")
        obj = next(o for o in self.value["objects"] if o["id"] == "after-a2")
        old_reference = self.reference_path.read_bytes()
        self.replace_asset(obj["asset_ref"], png_bytes(dots([(250, 120)])))
        self.rebuild_render()
        self.assertEqual(self.reference_path.read_bytes(), old_reference)
        try:
            result = self.metric()
        except ValueError:
            return  # An invalid pixel-to-reference binding is also a closed gate.
        self.assertIn(result["status"], ("fail", "unmeasured"), result)

    def test_native_scaffold_without_atom_extractor_is_unmeasured(self):
        self.select("scaffold-positive")
        # Deliberately forged native labels exist only in this temporary unit
        # input, never in delivered fixtures or claimed native/human evidence.
        self.value["evidence_mode"] = "native"
        self.asset(self.value["render_asset_ref"])["kind"] = "native_render"
        for obj in self.value["objects"]:
            self.asset(obj["asset_ref"])["kind"] = "native_object_render"
        ref = self.value["calibration_asset_ref"]
        calibration = read_json(self.base / self.asset(ref)["path"])
        calibration["measurement_source"] = "native_render"
        self.replace_asset(ref, json_bytes(calibration), ".json")
        result = self.metric()
        self.assertEqual(result["status"], "unmeasured")
        self.assertIn("extractor", result["reason"])

    def test_scaffold_mixed_or_same_states_are_rejected(self):
        for mutate_all in (False, True):
            with self.subTest(same_state=mutate_all):
                self.select("scaffold-positive")
                for m in (self.value["measurements"][0], self.reference["measurements"][0]):
                    targets = m["atom_pairs"] if mutate_all else m["atom_pairs"][:1]
                    for pair in targets:
                        pair["before_ref"] = pair["after_ref"]
                self.write_reference()
                with self.assertRaisesRegex(ValueError, "distinct states"):
                    self.run_case()

    def test_scaffold_non_atom_occurrences_are_rejected(self):
        self.select("scaffold-positive")
        for m in (self.value["measurements"][0], self.reference["measurements"][0]):
            m["atom_pairs"][0]["before_ref"] = "before:lp1:0"
            m["atom_pairs"][0]["after_ref"] = "after:lp1:0"
        self.write_reference()
        with self.assertRaisesRegex(ValueError, "atom occurrence"):
            self.run_case()


if __name__ == "__main__":
    unittest.main()
