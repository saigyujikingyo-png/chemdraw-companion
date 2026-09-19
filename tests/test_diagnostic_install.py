"""Installer integration checks using only temporary synthetic payloads and fake Codex."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

sys.dont_write_bytecode = True
PACKAGE_SOURCE = Path(__file__).resolve().parents[1] / "packaging" / "chemdraw-companion"
sys.path.insert(0, str(PACKAGE_SOURCE))
import package_integrity as integrity
import install as installer
import connect_codex as connector


def write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def freeze_manifest(package, version="0.2.0-preview.1", source_commit="a" * 40):
    records = []
    for path in sorted(package.rglob("*")):
        if path.is_file() and path.name != "package-manifest.json":
            data = path.read_bytes()
            records.append({"path": path.relative_to(package).as_posix(), "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest()})
    write_json(package / "package-manifest.json", {"manifest_version": "chemdraw-package/0.1",
               "product": "chemdraw-companion", "version": version,
               "source_commit": source_commit, "files": records})


def make_package(base, version="0.2.0-preview.1", *, marker="first", native_enabled=False):
    package = base / ("payload " + version)
    package.mkdir(parents=True)
    (package / "runtime").mkdir()
    (package / "runtime" / "python.exe").write_bytes(b"SYNTHETIC NONEXECUTABLE TEST MARKER")
    for name in ("install.py", "connect_codex.py", "package_integrity.py", "Install.cmd", "Connect Codex.cmd"):
        shutil.copyfile(PACKAGE_SOURCE / name, package / name)
    (package / "server.py").write_text("import json\nprint(json.dumps(" + repr({"ok": True, "native_execution_enabled": native_enabled}) + "))\n", encoding="utf-8")
    (package / "notice.txt").write_text(marker, encoding="utf-8")
    write_json(package / "build-info.json", {"product": "chemdraw-companion", "version": version, "source_commit": "a" * 40})
    freeze_manifest(package, version)
    return package


def fake_configuration(command, arguments):
    return {"name": "chemdraw-companion", "enabled": True, "disabled_reason": None,
            "transport": {"type": "stdio", "command": command, "args": list(arguments),
                          "env": None, "env_vars": [], "cwd": None},
            "startup_timeout_sec": None, "tool_timeout_sec": None,
            "enabled_tools": None, "disabled_tools": None}


class FakeCodex:
    """Models the CLI's documented get/add/remove boundary, including late effects."""
    def __init__(self):
        self.configuration = None
        self.other_plugins = {"chemdraw-agent": {"command": "ChemAIst remains unchanged"}}
        self.calls = []
        self.write_count = 0
        self.timeout_after_write = False
        self.fail_read_after_write = False
        self.fail_reads = False
        self.skip_write = False

    def __call__(self, command, **kwargs):
        self.calls.append(list(command))
        if kwargs.get("timeout") != 20:
            raise AssertionError("CLI calls must be bounded")
        if command[:2] != ["synthetic-codex", "mcp"]:
            raise AssertionError("Only the explicit fake CLI may be used")
        verb = command[2]
        if verb == "get":
            if self.fail_reads:
                raise subprocess.TimeoutExpired(command, kwargs["timeout"])
            if self.configuration is None:
                return subprocess.CompletedProcess(command, 1, "", "Error: No MCP server named 'chemdraw-companion' found.\n")
            return subprocess.CompletedProcess(command, 0, json.dumps(self.configuration), "")
        if verb not in {"add", "remove"} or command[3] != "chemdraw-companion":
            raise AssertionError("Unexpected write target")
        self.write_count += 1
        if self.skip_write:
            return subprocess.CompletedProcess(command, 2, "", "Synthetic write refused")
        if verb == "add":
            if command[4] != "--":
                raise AssertionError("Native command must follow the CLI separator")
            self.configuration = fake_configuration(command[5], command[6:])
        else:
            self.configuration = None
        if self.fail_read_after_write:
            self.fail_reads = True
        if self.timeout_after_write:
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        return subprocess.CompletedProcess(command, 0, "Configured", "")


class DiagnosticInstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="chemdraw-install-synthetic-")
        self.base = Path(self.temporary.name)
        self.source = make_package(self.base)
        self.root = self.base / "installed files \u5316\u5b66"
        self.actual_self_check = installer.run_self_check
        self.self_check_count = 0
        self.check_patch = mock.patch.object(installer, "run_self_check", side_effect=self.synthetic_self_check)
        self.check_patch.start()

    def tearDown(self):
        self.check_patch.stop()
        self.temporary.cleanup()

    def synthetic_self_check(self, payload):
        """Execute the benign synthetic script; never execute the marker named python.exe."""
        self.self_check_count += 1
        actual_run = subprocess.run

        def run_benign(command, **kwargs):
            self.assertEqual(command[0], str(Path(payload) / "runtime" / "python.exe"))
            self.assertEqual(command[1:3], ["-I", "-B"])
            self.assertEqual(command[-1], "--self-check")
            return actual_run([sys.executable, *command[1:]], **kwargs)

        with mock.patch.object(installer.subprocess, "run", side_effect=run_benign):
            return self.actual_self_check(payload)

    def install(self, source=None):
        return installer.install_package(source or self.source, self.root)

    def connect(self, fake, **kwargs):
        return connector.connect(self.root, cli=("synthetic-codex",), runner=fake, **kwargs)

    def test_integrity_accepts_every_listed_file_and_matching_build_metadata(self):
        report = integrity.verify_package(self.source)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["checked_files"], 9)
        self.assertEqual(report["failures"], [])

    def test_integrity_rejects_unexpected_modified_and_missing_files(self):
        for mutation in ("extra", "modified", "missing"):
            with self.subTest(mutation=mutation):
                package = self.base / mutation
                shutil.copytree(self.source, package)
                if mutation == "extra":
                    (package / "secret.txt").write_text("not a distributable file", encoding="utf-8")
                elif mutation == "modified":
                    (package / "notice.txt").write_text("bad!!", encoding="utf-8")
                else:
                    (package / "notice.txt").unlink()
                self.assertFalse(integrity.verify_package(package)["ok"])

    def test_integrity_rejects_traversal_case_collisions_boolean_size_and_duplicate_json(self):
        pristine = (self.source / "package-manifest.json").read_bytes()
        for mutation in ("traversal", "case", "boolean", "duplicate", "absolute", "reserved"):
            with self.subTest(mutation=mutation):
                manifest = json.loads(pristine)
                if mutation == "duplicate":
                    (self.source / "package-manifest.json").write_text('{"product":"chemdraw-companion","product":"other"}', encoding="utf-8")
                else:
                    if mutation == "traversal":
                        manifest["files"][0]["path"] = "../outside.txt"
                    elif mutation == "absolute":
                        manifest["files"][0]["path"] = "C:/outside.txt"
                    elif mutation == "reserved":
                        manifest["files"][0]["path"] = "nested/NUL.txt"
                    elif mutation == "case":
                        record = dict(manifest["files"][0])
                        record["path"] = record["path"].upper()
                        manifest["files"].append(record)
                    elif mutation == "boolean":
                        manifest["files"][0]["bytes"] = True
                    write_json(self.source / "package-manifest.json", manifest)
                report = integrity.verify_package(self.source)
                self.assertFalse(report["ok"], report)
                self.assertEqual(report["checked_files"], 0)
        (self.source / "package-manifest.json").write_bytes(pristine)

    def test_integrity_rejects_self_consistent_hashes_with_conflicting_build_identity(self):
        build = json.loads((self.source / "build-info.json").read_text())
        build["version"] = "9.9.9"
        write_json(self.source / "build-info.json", build)
        freeze_manifest(self.source)
        report = integrity.verify_package(self.source)
        self.assertFalse(report["ok"])
        self.assertIn("build-info.json:identity", report["failures"])

    def test_integrity_refuses_symbolic_link_without_reading_target(self):
        target = self.base / "external.txt"
        target.write_text("retain this unrelated file", encoding="utf-8")
        link = self.source / "notice.txt"
        link.unlink()
        try:
            os.symlink(target, link)
        except OSError as exc:
            self.skipTest("Symbolic-link privilege is unavailable: " + str(exc.winerror if hasattr(exc, "winerror") else exc.errno))
        self.assertFalse(integrity.verify_package(self.source)["ok"])
        self.assertEqual(target.read_text(), "retain this unrelated file")

    def test_actual_directory_reparse_is_rejected_without_traversing_it(self):
        target = self.base / "outside directory"
        target.mkdir()
        (target / "marker.txt").write_text("outside retained", encoding="utf-8")
        link = self.source / "external-link"
        if os.name == "nt":
            process = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
                                     capture_output=True, text=True, timeout=10, check=False,
                                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.assertEqual(process.returncode, 0, "Temporary junction creation failed")
        else:
            os.symlink(target, link, target_is_directory=True)
        try:
            self.assertTrue(integrity.is_reparse(link))
            report = integrity.verify_package(self.source)
            self.assertFalse(report["ok"])
            self.assertIn("external-link:reparse", report["failures"])
            self.assertFalse(integrity.verify_package(link)["ok"])
            self.assertEqual((target / "marker.txt").read_text(), "outside retained")
        finally:
            if os.name == "nt":
                link.rmdir()  # Remove only this junction, never its target tree.
            else:
                link.unlink()

    def test_fresh_install_current_readback_is_owned_and_no_host_connection_is_written(self):
        output = self.install()
        pointer, payload = installer.current_installation(self.root)
        self.assertEqual(output["status"], "completed")
        self.assertEqual(payload, self.root / "versions" / "0.2.0-preview.1" / "chemdraw-companion")
        self.assertTrue(integrity.verify_package(payload)["ok"])
        self.assertEqual(pointer["receipt_id"], output["receipt_id"])
        receipt = installer.regular_json(self.root / "receipts" / (output["receipt_id"] + ".json"))
        self.assertIsNone(receipt["previous_pointer"])
        self.assertEqual(receipt["status"], "completed")
        self.assertEqual(output["host_connection"], "unchanged_unverified")
        self.assertFalse((self.root / "connections").exists())
        self.assertFalse(list(payload.rglob("__pycache__")))

    def test_repeat_upgrade_and_file_rollback_preserve_versions_settings_and_raw_evidence(self):
        first = self.install()
        original_pointer = (self.root / "current.json").read_bytes()
        (self.root / "settings").mkdir()
        (self.root / "settings" / "user.txt").write_bytes(b"user settings stay")
        (self.root / "raw-evidence.bin").write_bytes(b"prior unknown effects")
        repeat = self.install()
        self.assertEqual(repeat["status"], "unchanged")
        self.assertEqual(repeat["receipt_id"], first["receipt_id"])
        self.assertEqual((self.root / "current.json").read_bytes(), original_pointer)
        second_source = make_package(self.base, "0.2.0-preview.2", marker="second")
        second = self.install(second_source)
        second_receipt = installer.regular_json(self.root / "receipts" / (second["receipt_id"] + ".json"))
        self.assertEqual(second_receipt["previous_pointer"], json.loads(original_pointer))
        rolled = installer.rollback(self.root, "0.2.0-preview.1")
        self.assertEqual(rolled["version"], "0.2.0-preview.1")
        self.assertEqual(rolled["rollback_scope"], "installed_files_only")
        self.assertTrue(installer.owned_version(self.root, "0.2.0-preview.2")[0].exists())
        self.assertEqual((self.root / "settings" / "user.txt").read_bytes(), b"user settings stay")
        self.assertEqual((self.root / "raw-evidence.bin").read_bytes(), b"prior unknown effects")

    def test_same_version_with_different_payload_is_refused_without_overwriting(self):
        self.install()
        old_pointer = (self.root / "current.json").read_bytes()
        (self.source / "notice.txt").write_text("changed", encoding="utf-8")
        freeze_manifest(self.source)
        with self.assertRaisesRegex(installer.InstallError, "different package contents"):
            self.install()
        self.assertEqual((self.root / "current.json").read_bytes(), old_pointer)
        self.assertEqual((self.root / "versions" / "0.2.0-preview.1" / "chemdraw-companion" / "notice.txt").read_text(), "first")

    def test_tampered_installed_version_blocks_status_rollback_and_upgrade(self):
        self.install()
        pointer, payload = installer.current_installation(self.root)
        (payload / "notice.txt").write_text("tampered", encoding="utf-8")
        with self.assertRaises(installer.InstallError):
            installer.status(self.root)
        with self.assertRaises(installer.InstallError):
            installer.rollback(self.root, "0.2.0-preview.1")
        with self.assertRaises(installer.InstallError):
            self.install(make_package(self.base, "0.2.0-preview.2"))
        self.assertEqual(installer.regular_json(self.root / "current.json"), pointer)

    def test_native_enabled_self_check_is_refused_before_pointer_change(self):
        unsafe = make_package(self.base, "0.2.0-preview.2", native_enabled=True)
        with self.assertRaisesRegex(installer.InstallError, "self-check failed"):
            self.install(unsafe)
        self.assertFalse((self.root / "current.json").exists())
        self.assertTrue(list((self.root / "staging").iterdir()))
        self.assertFalse((self.root / ".installation-lock").exists())

    def test_interrupted_pointer_receipt_requires_reconciliation_and_retains_evidence(self):
        atomic = installer.atomic_json

        def fail_completion(path, value):
            if Path(path).parent.name == "receipts" and value.get("status") == "completed":
                raise OSError("synthetic crash after pointer update")
            return atomic(path, value)

        with mock.patch.object(installer, "atomic_json", side_effect=fail_completion):
            with self.assertRaises(OSError):
                self.install()
        self.assertTrue((self.root / "current.json").exists())
        with self.assertRaisesRegex(installer.InstallError, "completed matching installation receipt"):
            self.install()
        receipts = list((self.root / "receipts").glob("*.json"))
        self.assertEqual(len(receipts), 1)
        self.assertEqual(installer.regular_json(receipts[0])["status"], "intent")

    def test_nonempty_unowned_root_and_stale_lock_are_preserved(self):
        self.root.mkdir()
        (self.root / "unrelated.txt").write_bytes(b"not owned")
        with self.assertRaisesRegex(installer.InstallError, "unowned installation root"):
            self.install()
        self.assertEqual((self.root / "unrelated.txt").read_bytes(), b"not owned")
        self.assertFalse((self.root / "installation-owner.json").exists())
        (self.root / "unrelated.txt").unlink()
        self.install()
        (self.root / ".installation-lock").mkdir()
        with self.assertRaisesRegex(installer.InstallError, "requires reconciliation"):
            self.install()
        self.assertTrue((self.root / ".installation-lock").exists())

    def test_status_of_absent_root_is_read_only(self):
        with self.assertRaises(ValueError):
            installer.status(self.root)
        self.assertFalse(self.root.exists())

    def test_concurrent_install_admission_has_one_attempt_and_one_final_receipt(self):
        entered = threading.Event()
        release = threading.Event()
        errors = []
        original_check = self.synthetic_self_check
        calls = 0

        def blocked_check(payload):
            nonlocal calls
            calls += 1
            if calls == 1:
                entered.set()
                if not release.wait(10):
                    raise AssertionError("test worker was not released")
            return original_check(payload)

        def first_client():
            try:
                self.install()
            except Exception as exc:
                errors.append(exc)

        with mock.patch.object(installer, "run_self_check", side_effect=blocked_check):
            thread = threading.Thread(target=first_client)
            thread.start()
            try:
                self.assertTrue(entered.wait(10))
                with self.assertRaisesRegex(installer.InstallError, "requires reconciliation"):
                    self.install()
            finally:
                release.set()
                thread.join(20)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(len(list((self.root / "receipts").glob("*.json"))), 1)
        self.assertEqual(len(list((self.root / "versions").iterdir())), 1)

    def test_codex_connect_is_idempotent_and_preserves_chemaist(self):
        self.install()
        fake = FakeCodex()
        old_plugins = copy.deepcopy(fake.other_plugins)
        first = self.connect(fake)
        again = self.connect(fake)
        self.assertEqual(first["status"], "connected")
        self.assertEqual(again["status"], "unchanged")
        self.assertEqual(fake.write_count, 1)
        self.assertEqual(fake.other_plugins, old_plugins)
        self.assertIn("installed files \u5316\u5b66", fake.configuration["transport"]["command"])
        self.assertEqual(fake.configuration["transport"]["args"][:2], ["-I", "-B"])
        self.assertEqual(first["host_tool_acceptance"], "unverified")

    def test_codex_refuses_unrelated_modified_and_disabled_entry_without_writing(self):
        self.install()
        desired = connector.descriptor(self.root, "0.2.0-preview.1")
        for mode in ("other", "disabled", "environment", "custom_timeout"):
            with self.subTest(mode=mode):
                fake = FakeCodex()
                fake.configuration = fake_configuration(desired["command"], desired["args"])
                if mode == "other":
                    fake.configuration["transport"]["command"] = str(self.base / "another.exe")
                elif mode == "disabled":
                    fake.configuration["enabled"] = False
                elif mode == "environment":
                    fake.configuration["transport"]["env"] = {"PRIVATE": "do-not-copy"}
                else:
                    fake.configuration["tool_timeout_sec"] = 120
                before = copy.deepcopy(fake.configuration)
                with self.assertRaises(installer.InstallError):
                    self.connect(fake)
                self.assertEqual(fake.configuration, before)
                self.assertEqual(fake.write_count, 0)
        self.assertFalse((self.root / "connections").exists())

    def test_cli_error_after_effect_is_reconciled_by_readback_without_replay(self):
        self.install()
        fake = FakeCodex()
        fake.timeout_after_write = True
        output = self.connect(fake)
        self.assertEqual(output["status"], "connected")
        self.assertEqual(fake.write_count, 1)
        self.assertFalse((self.root / "pending-connection.json").exists())

    def test_unknown_connection_effect_is_retained_then_reconciled_without_new_write(self):
        self.install()
        fake = FakeCodex()
        fake.fail_read_after_write = True
        unknown = self.connect(fake)
        self.assertFalse(unknown["ok"])
        self.assertEqual(unknown["status"], "outcome_unknown")
        self.assertTrue((self.root / "pending-connection.json").exists())
        again = self.connect(fake)
        self.assertEqual(again["status"], "outcome_unknown")
        fake.fail_reads = False
        reconciled = self.connect(fake)
        self.assertEqual(reconciled["action"], "reconcile")
        self.assertEqual(reconciled["status"], "completed")
        self.assertEqual(reconciled["receipt_id"], unknown["receipt_id"])
        self.assertEqual(fake.write_count, 1)
        self.assertFalse((self.root / "pending-connection.json").exists())

    def test_failed_cli_before_effect_retains_known_previous_configuration(self):
        self.install()
        fake = FakeCodex()
        fake.skip_write = True
        output = self.connect(fake)
        self.assertFalse(output["ok"])
        self.assertEqual(output["status"], "not_applied")
        self.assertIsNone(fake.configuration)
        self.assertFalse((self.root / "pending-connection.json").exists())

    def test_codex_upgrade_and_receipt_rollback_restore_owned_old_command(self):
        self.install()
        fake = FakeCodex()
        self.connect(fake)
        original = copy.deepcopy(fake.configuration)
        self.install(make_package(self.base, "0.2.0-preview.2"))
        upgraded = self.connect(fake)
        self.assertEqual(upgraded["version"], "0.2.0-preview.2")
        with self.assertRaisesRegex(installer.InstallError, "First use install.py --rollback"):
            self.connect(fake, rollback_receipt=upgraded["receipt_id"])
        installer.rollback(self.root, "0.2.0-preview.1")
        reverted = self.connect(fake, rollback_receipt=upgraded["receipt_id"])
        self.assertTrue(reverted["ok"])
        self.assertEqual(fake.configuration, original)
        self.assertEqual(fake.write_count, 3)

    def test_rollback_initial_connection_leaves_plugin_unconnected(self):
        self.install()
        fake = FakeCodex()
        connected = self.connect(fake)
        output = self.connect(fake, rollback_receipt=connected["receipt_id"])
        self.assertEqual(output["status"], "unconnected")
        self.assertIsNone(fake.configuration)
        self.assertEqual(fake.other_plugins["chemdraw-agent"]["command"], "ChemAIst remains unchanged")

    def test_codex_rollback_refuses_changed_connection(self):
        self.install()
        fake = FakeCodex()
        connected = self.connect(fake)
        fake.configuration["transport"]["command"] = str(self.base / "unrelated.exe")
        changed = copy.deepcopy(fake.configuration)
        with self.assertRaises(installer.InstallError):
            self.connect(fake, rollback_receipt=connected["receipt_id"])
        self.assertEqual(fake.configuration, changed)
        self.assertEqual(fake.write_count, 1)

    def test_codex_status_and_unavailable_read_do_not_write(self):
        self.install()
        fake = FakeCodex()
        status = self.connect(fake, read_only=True)
        self.assertEqual(status["status"], "unconnected")
        self.assertFalse((self.root / "connections").exists())
        fake.fail_reads = True
        with self.assertRaises(installer.InstallError):
            self.connect(fake)
        self.assertEqual(fake.write_count, 0)


if __name__ == "__main__":
    unittest.main()
