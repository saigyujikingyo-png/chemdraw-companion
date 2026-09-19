"""Install verified diagnostic files without changing any agent connection."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from package_integrity import (PRODUCT, VERSION_RE, is_reparse, package_metadata,
                               read_json, safe_directory, sha256_file, verify_package)

MARKER = "installation-owner.json"
POINTER = "current.json"
ID_KEYS = {"pointer_version", "product", "installation_id", "version", "source_commit", "manifest_sha256", "receipt_id"}


class InstallError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def default_root():
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise InstallError("ROOT_REQUIRED", "LOCALAPPDATA is unavailable; supply --root.")
    return Path(local) / "Chembridge" / "ChemDrawCompanion"


def atomic_json(path, value):
    """Replace one owned metadata file; retain an incomplete temp file on failure."""
    path = Path(path)
    safe_directory(path.parent)
    if path.exists() and (is_reparse(path) or not path.is_file()):
        raise InstallError("UNSAFE_METADATA", "An owned metadata path is not a regular file.")
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=True, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    if read_json(path) != value:
        raise InstallError("METADATA_READBACK", "Metadata readback did not match its receipt.")


def regular_json(path):
    path = Path(path)
    if is_reparse(path) or not path.is_file():
        raise InstallError("UNSAFE_METADATA", "An owned metadata path is not a regular file.")
    return read_json(path, 262144)


def owner_record(root):
    root = safe_directory(Path(root))
    record = regular_json(root / MARKER)
    if (not isinstance(record, dict) or set(record) != {"owner_version", "product", "installation_id"}
            or record.get("owner_version") != "chemdraw-installation/0.1"
            or record.get("product") != PRODUCT or not valid_id(record.get("installation_id"))):
        raise InstallError("UNOWNED_ROOT", "The installation root has no valid ChemDraw Companion owner record.")
    return record


def valid_id(value):
    return isinstance(value, str) and len(value) == 32 and all(char in "0123456789abcdef" for char in value)


@contextmanager
def root_lock(root, *, create=False):
    root = safe_directory(Path(root), existing=not create)
    if create:
        root.mkdir(parents=True, exist_ok=True)
    safe_directory(root)
    lock = root / ".installation-lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise InstallError("INSTALL_BUSY", "An existing installation attempt requires reconciliation; its lock was retained.") from None
    token = uuid.uuid4().hex
    try:
        atomic_json(lock / "owner.json", {"token": token})
        if not (root / MARKER).exists():
            if not create or any(item.name != lock.name for item in root.iterdir()):
                raise InstallError("UNOWNED_ROOT", "Refusing to adopt a nonempty or unowned installation root.")
            atomic_json(root / MARKER, {"owner_version": "chemdraw-installation/0.1", "product": PRODUCT, "installation_id": uuid.uuid4().hex})
        owner_record(root)
        yield root
    finally:
        try:
            if regular_json(lock / "owner.json") == {"token": token}:
                (lock / "owner.json").unlink()
                lock.rmdir()
        except (OSError, ValueError, InstallError):
            pass


def checked_payload(payload):
    report = verify_package(payload)
    if not report["ok"]:
        raise InstallError("PACKAGE_INVALID", "Package verification failed: " + ", ".join(report["failures"][:4]))
    for relative in ("runtime/python.exe", "server.py", "install.py", "connect_codex.py", "package_integrity.py"):
        if not (Path(payload) / relative).is_file():
            raise InstallError("PACKAGE_INCOMPLETE", "The diagnostic package is missing a required entrypoint.")
    metadata = package_metadata(payload)
    return metadata, sha256_file(Path(payload) / "package-manifest.json"), report


def owned_version(root, version):
    root = safe_directory(Path(root))
    owner = owner_record(root)
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        raise InstallError("INVALID_VERSION", "A valid package version is required.")
    directory = safe_directory(root / "versions" / version)
    record = regular_json(directory / "installation.json")
    payload = directory / PRODUCT
    metadata, digest, report = checked_payload(payload)
    expected = {"record_version": "chemdraw-installed-version/0.1", "product": PRODUCT,
                "installation_id": owner["installation_id"], "version": version,
                "source_commit": metadata["source_commit"], "manifest_sha256": digest}
    if record != expected or metadata["version"] != version:
        raise InstallError("UNOWNED_VERSION", "The installed version does not match its ownership receipt.")
    return payload, metadata, digest, report


def current_installation(root, *, allow_absent=False):
    root = safe_directory(Path(root))
    owner = owner_record(root)
    path = root / POINTER
    if not path.exists():
        if allow_absent:
            return None, None
        raise InstallError("NOT_INSTALLED", "There is no current installed version.")
    pointer = regular_json(path)
    if (not isinstance(pointer, dict) or set(pointer) != ID_KEYS
            or pointer.get("pointer_version") != "chemdraw-current/0.1"
            or pointer.get("product") != PRODUCT
            or pointer.get("installation_id") != owner["installation_id"]
            or not valid_id(pointer.get("receipt_id"))):
        raise InstallError("CURRENT_INVALID", "The current-version pointer is invalid.")
    payload, metadata, digest, _ = owned_version(root, pointer.get("version"))
    if pointer["source_commit"] != metadata["source_commit"] or pointer["manifest_sha256"] != digest:
        raise InstallError("CURRENT_INVALID", "The current-version pointer conflicts with the verified payload.")
    receipt = regular_json(root / "receipts" / (pointer["receipt_id"] + ".json"))
    if (not isinstance(receipt, dict) or receipt.get("status") != "completed"
            or receipt.get("new_pointer") != pointer or receipt.get("installation_id") != owner["installation_id"]):
        raise InstallError("RECONCILIATION_REQUIRED", "The pointer has no completed matching installation receipt.")
    return pointer, payload


def run_self_check(payload):
    try:
        process = subprocess.run([str(Path(payload) / "runtime" / "python.exe"), "-I", "-B",
                                  str(Path(payload) / "server.py"), "--self-check"],
                                 capture_output=True, text=True, timeout=20, check=False,
                                 cwd=str(payload), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if len(process.stdout) > 262144 or len(process.stderr) > 65536:
            raise ValueError("self-check output too large")
        result = json.loads(process.stdout)
        if process.returncode != 0 or not isinstance(result, dict) or result.get("ok") is not True or result.get("native_execution_enabled") is not False:
            raise ValueError("self-check did not confirm disabled native execution")
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        raise InstallError("SELF_CHECK_FAILED", "The non-native diagnostic self-check failed; no current-version pointer was changed.") from None
    return {"ok": True, "native_execution_enabled": False}


def result(action, status, *, version=None, receipt_id=None, root=None, error=None):
    return {"result_version": "chemdraw-install/0.1", "ok": error is None, "action": action,
            "status": status, "version": version, "receipt_id": receipt_id,
            "root": str(root) if root is not None else None,
            "native_execution_enabled": False, "host_connection": "unchanged_unverified",
            "rollback_scope": "installed_files_only", "error": error}


def _switch(root, version, previous, action):
    payload, metadata, digest, report = owned_version(root, version)
    run_self_check(payload)
    checked_payload(payload)
    if previous is not None and previous["version"] == version and previous["manifest_sha256"] == digest:
        return result(action, "unchanged", version=version, receipt_id=previous["receipt_id"], root=root)
    receipt_id = uuid.uuid4().hex
    owner = owner_record(root)
    pointer = {"pointer_version": "chemdraw-current/0.1", "product": PRODUCT,
               "installation_id": owner["installation_id"], "version": version,
               "source_commit": metadata["source_commit"], "manifest_sha256": digest, "receipt_id": receipt_id}
    receipt = {"receipt_version": "chemdraw-install-receipt/0.1", "product": PRODUCT,
               "installation_id": owner["installation_id"], "receipt_id": receipt_id,
               "action": action, "status": "intent", "observed_at": utc_now(),
               "previous_pointer": previous, "new_pointer": pointer,
               "checked_files": report["checked_files"], "native_execution_enabled": False,
               "host_connection": "unchanged_unverified"}
    receipts = root / "receipts"
    receipts.mkdir(exist_ok=True)
    safe_directory(receipts)
    receipt_path = receipts / (receipt_id + ".json")
    atomic_json(receipt_path, receipt)
    atomic_json(root / POINTER, pointer)
    receipt["status"] = "completed"
    receipt["completed_at"] = utc_now()
    atomic_json(receipt_path, receipt)
    current_installation(root)
    return result(action, "completed", version=version, receipt_id=receipt_id, root=root)


def install_package(source, root):
    source = safe_directory(Path(source))
    metadata, source_digest, _ = checked_payload(source)
    with root_lock(root, create=True) as root:
        previous, _ = current_installation(root, allow_absent=True)
        version = metadata["version"]
        version_dir = root / "versions" / version
        if version_dir.exists():
            _, _, installed_digest, _ = owned_version(root, version)
            if installed_digest != source_digest:
                raise InstallError("VERSION_CONFLICT", "That version is already installed with different package contents; it was preserved.")
        else:
            stage_id = uuid.uuid4().hex
            staging = root / "staging"
            staging.mkdir(exist_ok=True)
            safe_directory(staging)
            stage = staging / stage_id
            stage.mkdir()
            stage_version = stage / version
            stage_payload = stage_version / PRODUCT
            stage_payload.mkdir(parents=True)
            for relative in [entry["path"] for entry in metadata["files"]] + ["package-manifest.json"]:
                source_file = source / relative
                if is_reparse(source_file):
                    raise InstallError("PACKAGE_CHANGED", "A source file became a reparse point during installation.")
                target = stage_payload / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_file, target, follow_symlinks=False)
            staged_metadata, staged_digest, _ = checked_payload(stage_payload)
            _, current_source_digest, _ = checked_payload(source)
            if staged_digest != source_digest or current_source_digest != source_digest:
                raise InstallError("PACKAGE_CHANGED", "Package metadata changed while copying; the staging evidence was retained.")
            run_self_check(stage_payload)
            checked_payload(stage_payload)
            owner = owner_record(root)
            atomic_json(stage_version / "installation.json", {"record_version": "chemdraw-installed-version/0.1",
                        "product": PRODUCT, "installation_id": owner["installation_id"], "version": version,
                        "source_commit": staged_metadata["source_commit"], "manifest_sha256": staged_digest})
            versions = root / "versions"
            versions.mkdir(exist_ok=True)
            safe_directory(versions)
            os.rename(stage_version, version_dir)
        return _switch(root, version, previous, "install")


def rollback(root, version):
    with root_lock(root) as root:
        previous, _ = current_installation(root)
        return _switch(root, version, previous, "rollback")


def status(root):
    root = safe_directory(Path(root))
    pointer, payload = current_installation(root)
    _, _, _, report = owned_version(root, pointer["version"])
    output = result("status", "verified_files", version=pointer["version"], receipt_id=pointer["receipt_id"], root=root)
    output["checked_files"] = report["checked_files"]
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--status", action="store_true", help="Read installation metadata and verify files without mutation.")
    actions.add_argument("--rollback", metavar="VERSION", help="Switch verified files only; reconcile the Codex connection separately.")
    args = parser.parse_args(argv)
    action = "status" if args.status else "rollback" if args.rollback else "install"
    try:
        root = args.root or default_root()
        output = status(root) if args.status else rollback(root, args.rollback) if args.rollback else install_package(Path(__file__).parent, root)
    except (InstallError, OSError, ValueError, TypeError) as exc:
        code = exc.code if isinstance(exc, InstallError) else "INSTALL_IO_OR_METADATA_ERROR"
        message = str(exc) if isinstance(exc, InstallError) else "Installation metadata or file access failed; existing evidence was retained."
        output = result(action, "refused", error={"code": code, "message": message})
    print(json.dumps(output, ensure_ascii=True))
    return 0 if output["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
