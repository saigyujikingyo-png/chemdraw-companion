"""Synthetic calibration trust tests; no native run, pixel claims or human data."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from calibration import load_calibration


class CalibrationTrustTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="quality-calibration-unit-")
        self.base = Path(self.temporary.name).resolve()
        self.assertTrue(self.base.is_relative_to(Path(tempfile.gettempdir()).resolve()))
        self.assertTrue(self.base.name.startswith("quality-calibration-unit-"))
        self.style = {"font_family": "Arial", "font_pt": 8.0, "bond_pt": 14.4,
                      "stroke_pt": 0.6, "head_size": 650, "head_width": 163,
                      "head_center_size": 569, "head_type": "Solid", "head": "Full",
                      "tail": "None", "curve_type": "8"}
        self.build = "synthetic-unit-build/not-a-native-execution"
        self.payload = {"version": "quality-calibration/1.0", "id": "unit-calibration",
                        "native_build": self.build, "style": copy.deepcopy(self.style),
                        "measurement_status": "measured", "measurement_source": "synthetic",
                        "limits": {"head_extension_pt": 4.0, "uncertainty_pt": 0.1}}

    def tearDown(self):
        # Cleanup is confined to the verified temporary path created in setUp.
        self.temporary.cleanup()

    def write_bytes(self, data):
        (self.base / "calibration.json").write_bytes(data)
        return {"id": "unit-calibration-asset", "path": "calibration.json",
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "kind": "calibration"}

    def write(self, payload=None):
        return self.write_bytes(json.dumps(self.payload if payload is None else payload).encode("utf-8"))

    def load(self, asset, style=None, build=None):
        return load_calibration(asset, self.base, self.style if style is None else style,
                                self.build if build is None else build)

    def test_positive_binds_verified_bytes_and_preserves_limits(self):
        asset = self.write()
        result = self.load(asset)
        self.assertEqual(result["asset_id"], asset["id"])
        self.assertEqual(result["asset_sha256"], asset["sha256"])
        self.assertEqual(result["limits"], self.payload["limits"])
        self.assertAlmostEqual(result["conservative_forward_extension_pt"], 4.1)
        self.assertEqual(result["measurement_source"], "synthetic")

    def test_positive_utf8_bom_is_parsed_from_hashed_bytes(self):
        asset = self.write_bytes(b"\xef\xbb\xbf" + json.dumps(self.payload).encode("utf-8"))
        self.assertEqual(self.load(asset)["asset_sha256"], asset["sha256"])

    def test_million_point_extent_and_uncertainty_are_rejected(self):
        for key in ("head_extension_pt", "uncertainty_pt"):
            with self.subTest(key=key):
                payload = copy.deepcopy(self.payload)
                payload["limits"][key] = 1_000_000
                with self.assertRaises(ValueError):
                    self.load(self.write(payload))

    def test_nonfinite_limits_are_rejected_with_matching_file_hash(self):
        for key in ("head_extension_pt", "uncertainty_pt"):
            for bad in (float("nan"), float("inf"), -float("inf")):
                with self.subTest(key=key, value=repr(bad)):
                    payload = copy.deepcopy(self.payload)
                    payload["limits"][key] = bad
                    with self.assertRaises(ValueError):
                        self.load(self.write(payload))

    def test_valid_json_numeric_overflow_is_rejected(self):
        text = json.dumps(self.payload).replace('"head_extension_pt": 4.0', '"head_extension_pt": 1e999')
        with self.assertRaises(ValueError):
            self.load(self.write_bytes(text.encode("utf-8")))

    def test_negative_limit_and_boolean_are_rejected(self):
        for key in ("head_extension_pt", "uncertainty_pt"):
            for bad in (-0.01, True):
                with self.subTest(key=key, value=bad):
                    payload = copy.deepcopy(self.payload)
                    payload["limits"][key] = bad
                    with self.assertRaises(ValueError):
                        self.load(self.write(payload))

    def test_extent_bound_includes_uncertainty(self):
        payload = copy.deepcopy(self.payload)
        payload["limits"] = {"head_extension_pt": 14.0, "uncertainty_pt": 0.4}
        self.assertEqual(self.load(self.write(payload))["conservative_forward_extension_pt"], 14.4)
        payload["limits"]["uncertainty_pt"] += 0.000001
        with self.assertRaises(ValueError):
            self.load(self.write(payload))

    def test_scene_supplied_derived_allowance_is_not_a_calibration_field(self):
        payload = copy.deepcopy(self.payload)
        payload["conservative_forward_extension_pt"] = 1_000_000
        with self.assertRaises(ValueError):
            self.load(self.write(payload))

    def test_every_style_field_is_independently_bound(self):
        alternatives = {"font_family": "Times New Roman", "font_pt": 9.0, "bond_pt": 15.0,
                        "stroke_pt": 1.2, "head_size": 651, "head_width": 164,
                        "head_center_size": 570, "head_type": "Hollow", "head": "HalfLeft",
                        "tail": "Full", "curve_type": "9"}
        for key, value in alternatives.items():
            with self.subTest(field=key):
                payload = copy.deepcopy(self.payload)
                payload["style"][key] = value
                # The descriptor is intentionally recomputed. Independent
                # expected_style, not a stale checksum, must reject this.
                with self.assertRaisesRegex(ValueError, "style mismatch"):
                    self.load(self.write(payload))

    def test_requesting_a_different_stroke_rejects_unchanged_calibration(self):
        expected = {**self.style, "stroke_pt": 1.2}
        with self.assertRaisesRegex(ValueError, "style mismatch"):
            self.load(self.write(), style=expected)

    def test_missing_style_field_is_rejected_on_both_sides(self):
        for key in self.style:
            with self.subTest(field=key):
                payload = copy.deepcopy(self.payload)
                del payload["style"][key]
                with self.assertRaises(ValueError):
                    self.load(self.write(payload))
                expected = copy.deepcopy(self.style)
                del expected[key]
                with self.assertRaises(ValueError):
                    self.load(self.write(), style=expected)

    def test_nonfinite_and_boolean_expected_style_are_rejected(self):
        for bad in (float("nan"), float("inf"), True, 0, -1):
            with self.subTest(value=repr(bad)):
                with self.assertRaises(ValueError):
                    self.load(self.write(), style={**self.style, "stroke_pt": bad})

    def test_native_build_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "native build mismatch"):
            self.load(self.write(), build="different-native-build")

    def test_changed_build_and_recomputed_hash_still_rejected(self):
        payload = copy.deepcopy(self.payload)
        payload["native_build"] = "different-native-build"
        with self.assertRaisesRegex(ValueError, "native build mismatch"):
            self.load(self.write(payload))

    def test_uncertain_or_missing_measurement_never_passes(self):
        for status in ("uncertain", "unmeasured"):
            with self.subTest(status=status):
                payload = copy.deepcopy(self.payload)
                payload["measurement_status"] = status
                with self.assertRaisesRegex(ValueError, "unavailable or uncertain"):
                    self.load(self.write(payload))
        payload = copy.deepcopy(self.payload)
        del payload["limits"]["uncertainty_pt"]
        with self.assertRaises(ValueError):
            self.load(self.write(payload))

    def test_changed_bytes_of_same_length_reject_stale_hash(self):
        asset = self.write()
        path = self.base / "calibration.json"
        original = path.read_bytes()
        changed = original.replace(b'"head_extension_pt": 4.0', b'"head_extension_pt": 4.1')
        self.assertNotEqual(changed, original)
        self.assertEqual(len(changed), len(original))
        path.write_bytes(changed)
        with self.assertRaises(ValueError):
            self.load(asset)

    def test_wrong_hash_or_size_descriptor_is_rejected(self):
        for field, wrong in (("sha256", "0" * 64), ("bytes", 1)):
            with self.subTest(field=field):
                asset = self.write()
                asset[field] = wrong
                with self.assertRaises(ValueError):
                    self.load(asset)

    def test_missing_asset_or_file_and_wrong_kind_are_rejected(self):
        with self.assertRaises(ValueError):
            self.load(None)
        asset = self.write()
        with self.assertRaises(ValueError):
            self.load({**asset, "kind": "scene"})
        with self.assertRaises(ValueError):
            self.load({**asset, "path": "absent-calibration.json"})

    def test_remote_and_escaping_paths_are_rejected(self):
        asset = self.write()
        for path in ("https://example.invalid/calibration.json", "../outside-calibration.json"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    self.load({**asset, "path": path})

    def test_duplicate_json_key_is_rejected(self):
        text = json.dumps(self.payload).replace('"head_extension_pt": 4.0',
                                               '"head_extension_pt": 1e6, "head_extension_pt": 4.0')
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            self.load(self.write_bytes(text.encode("utf-8")))


if __name__ == "__main__":
    unittest.main()
