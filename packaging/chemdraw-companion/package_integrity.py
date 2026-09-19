"""Strict, standard-library verification of a ChemDraw Companion payload."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat

PRODUCT = "chemdraw-companion"
MANIFEST_VERSION = "chemdraw-package/0.1"
VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9][A-Za-z0-9.-]{0,48})?\Z")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
MAX_MANIFEST_BYTES = 8 * 1024 * 1024
MAX_FILES = 20000
MAX_FAILURES = 32
_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def read_json(path: Path, maximum: int = MAX_MANIFEST_BYTES):
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("JSON exceeds size bound")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("invalid JSON constant")))


def is_reparse(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def safe_directory(path: Path, *, existing: bool = True) -> Path:
    """Check the lexical path and all existing ancestors before resolving it."""
    path = Path(os.path.abspath(os.fspath(path)))
    for ancestor in reversed((path, *path.parents)):
        try:
            if is_reparse(ancestor):
                raise ValueError("reparse path refused")
            if not ancestor.is_dir():
                raise ValueError("directory expected")
        except FileNotFoundError:
            if existing:
                raise ValueError("directory is absent") from None
    return path


def safe_relative(value) -> bool:
    if not isinstance(value, str) or not value or len(value) > 240:
        return False
    if "\\" in value or ":" in value or any(ord(char) < 32 for char in value):
        return False
    parts = value.split("/")
    return all(part not in {"", ".", ".."} and not part.endswith((".", " "))
               and part.split(".", 1)[0].casefold() not in _RESERVED for part in parts)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_metadata(root: Path):
    """Call only after verify_package succeeds; no authenticity claim is implied."""
    return read_json(Path(root) / "package-manifest.json")


def verify_package(root) -> dict:
    failures = []
    checked = 0

    def fail(identifier):
        if len(failures) < MAX_FAILURES:
            failures.append(identifier[:280])

    try:
        root = safe_directory(Path(root))
        manifest_path = root / "package-manifest.json"
        if is_reparse(manifest_path) or not manifest_path.is_file():
            raise ValueError("manifest must be regular")
        manifest = read_json(manifest_path)
        if not isinstance(manifest, dict) or set(manifest) != {"manifest_version", "product", "version", "source_commit", "files"}:
            raise ValueError("manifest shape")
        if manifest["manifest_version"] != MANIFEST_VERSION or manifest["product"] != PRODUCT:
            raise ValueError("manifest identity")
        if not isinstance(manifest["version"], str) or not VERSION_RE.fullmatch(manifest["version"]):
            raise ValueError("manifest version")
        if not isinstance(manifest["source_commit"], str) or not HEX40.fullmatch(manifest["source_commit"]):
            raise ValueError("manifest source")
        records = manifest["files"]
        if not isinstance(records, list) or not 1 <= len(records) <= MAX_FILES:
            raise ValueError("manifest files")
        expected = {}
        folded = set()
        directories = set()
        for record in records:
            if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
                raise ValueError("file record")
            relative = record["path"]
            if not safe_relative(relative) or relative.casefold() == "package-manifest.json":
                raise ValueError("unsafe relative path")
            if relative.casefold() in folded:
                raise ValueError("duplicate file path")
            if type(record["bytes"]) is not int or record["bytes"] < 0:
                raise ValueError("file size")
            if not isinstance(record["sha256"], str) or not HEX64.fullmatch(record["sha256"]):
                raise ValueError("file hash")
            expected[relative] = record
            folded.add(relative.casefold())
            parts = relative.split("/")
            directories.update("/".join(parts[:i]) for i in range(1, len(parts)))
        if "build-info.json" not in expected:
            raise ValueError("build info absent")
        if folded.intersection(directory.casefold() for directory in directories):
            raise ValueError("file-directory collision")
    except (OSError, ValueError, TypeError, RecursionError, UnicodeError):
        return {"ok": False, "checked_files": 0, "failures": ["package-manifest.json:invalid_or_unsafe"]}

    observed = set()
    pending = [root]
    try:
        while pending:
            directory = pending.pop()
            with os.scandir(directory) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    relative = path.relative_to(root).as_posix()
                    if not safe_relative(relative):
                        fail("package:unsafe_entry")
                        continue
                    if is_reparse(path):
                        fail(relative + ":reparse")
                    elif entry.is_dir(follow_symlinks=False):
                        if relative not in directories:
                            fail(relative + ":unexpected_directory")
                        else:
                            pending.append(path)
                    elif not entry.is_file(follow_symlinks=False):
                        fail(relative + ":not_regular")
                    elif relative == "package-manifest.json":
                        continue
                    elif relative not in expected:
                        fail(relative + ":unexpected")
                    else:
                        observed.add(relative)
                        record = expected[relative]
                        if entry.stat(follow_symlinks=False).st_size != record["bytes"]:
                            fail(relative + ":size")
                        elif sha256_file(path) != record["sha256"]:
                            fail(relative + ":sha256")
                        checked += 1
        for relative in sorted(set(expected) - observed):
            fail(relative + ":missing")
        if not failures:
            build = read_json(root / "build-info.json", 65536)
            if not isinstance(build, dict) or any(build.get(key) != manifest[key] for key in ("product", "version", "source_commit")):
                fail("build-info.json:identity")
    except (OSError, ValueError, TypeError, RecursionError, UnicodeError):
        fail("package:read_failed")
    return {"ok": not failures, "checked_files": checked, "failures": failures}
