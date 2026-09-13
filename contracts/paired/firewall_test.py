"""Real six-category Windows denial tests; require an existing Codex sandbox.

Set PAIRED_FIREWALL_CODEX and optionally PAIRED_FIREWALL_PYTHON for this test
process only. Absent backend is a skip, never a passing leakage gate.
"""
import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
import shutil
sys.path.insert(0, str(Path(__file__).resolve().parent))
from firewall import sentinel_probe, CATEGORIES, confined_command


class FirewallDenialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.codex = os.environ.get("PAIRED_FIREWALL_CODEX")
        if os.name != "nt" or not cls.codex:
            raise unittest.SkipTest("requires explicit existing Windows sandbox executable")
        cls.scratch_root = Path(os.environ.get("PAIRED_FIREWALL_TEST_ROOT", tempfile.gettempdir())).resolve()
        cls.scratch_root.mkdir(parents=True, exist_ok=True)
        cls.base = (cls.scratch_root / ("paired-firewall-unit-" + uuid.uuid4().hex)).resolve()
        cls.base.mkdir()
        if not cls.base.is_relative_to(cls.scratch_root):
            raise RuntimeError("unexpected temporary root")
        cls.receipt = sentinel_probe(cls.codex, os.environ.get("PAIRED_FIREWALL_PYTHON", sys.executable), cls.base / "probe")
        if cls.receipt["process"]["returncode"] != 0:
            raise AssertionError(cls.receipt["process"]["stderr"])

    @classmethod
    def tearDownClass(cls):
        if not cls.base.is_relative_to(cls.scratch_root) or not cls.base.name.startswith("paired-firewall-unit-"):
            raise RuntimeError("refusing unsafe scratch cleanup")
        shutil.rmtree(cls.base)

    def denied(self, category):
        row = next(r for r in self.receipt["observation"]["attempts"] if r["category"] == category)
        self.assertTrue(row["denied"], row)
        self.assertEqual(row["exception"], "PermissionError")
        self.assertEqual(row["errno"], 13)

    def test_hidden_cdxml_denied(self): self.denied("hidden_cdxml")
    def test_target_geometry_denied(self): self.denied("target_geometry")
    def test_target_coordinates_denied(self): self.denied("target_coordinates")
    def test_target_object_ids_denied(self): self.denied("target_object_ids")
    def test_evaluator_annotations_denied(self): self.denied("evaluator_annotations")
    def test_layout_constraints_denied(self): self.denied("layout_constraints")

    def test_allowed_input_read_and_real_existing_sentinels(self):
        self.assertEqual(self.receipt["status"], "pass")
        self.assertEqual(len(self.receipt["sentinels"]), len(CATEGORIES))
        self.assertTrue(all(Path(s["path"]).is_file() for s in self.receipt["sentinels"]))
        self.assertFalse(self.receipt["model_called"])

    def test_parent_grant_cannot_include_hidden_root(self):
        with self.assertRaisesRegex(ValueError, "overlaps"):
            confined_command(self.codex, [sys.executable], self.base, [self.base],
                             forbidden=[self.base / "probe" / "hidden_target"])


if __name__ == "__main__":
    unittest.main()
