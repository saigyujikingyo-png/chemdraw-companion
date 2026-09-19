"""Connect an installed diagnostic payload using the official Codex CLI only."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from install import (InstallError, atomic_json, current_installation, default_root, owner_record,
                     owned_version, regular_json, root_lock, utc_now, valid_id)
from package_integrity import PRODUCT, safe_directory

NAME = "chemdraw-companion"
PENDING = "pending-connection.json"


def _run(cli, arguments, runner):
    try:
        process = runner([*cli, "mcp", *arguments], capture_output=True, text=True,
                         timeout=20, check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if len(process.stdout or "") > 1048576 or len(process.stderr or "") > 65536:
            raise InstallError("CLI_OUTPUT_INVALID", "The Codex CLI returned an oversized response.")
        return process
    except (OSError, subprocess.SubprocessError):
        raise InstallError("CLI_UNAVAILABLE", "The bounded Codex CLI operation did not complete; inspect its existing receipt before retrying.") from None


def _get(cli, runner):
    process = _run(cli, ["get", NAME, "--json"], runner)
    if process.returncode:
        if (process.stderr or "").strip() == "Error: No MCP server named 'chemdraw-companion' found.":
            return None
        raise InstallError("CLI_READ_FAILED", "The Codex CLI could not establish the named connection state.")
    try:
        value = json.loads(process.stdout)
    except (ValueError, TypeError):
        raise InstallError("CLI_OUTPUT_INVALID", "The Codex CLI returned invalid connection JSON.") from None
    if not isinstance(value, dict) or value.get("name") != NAME:
        raise InstallError("CLI_OUTPUT_INVALID", "The Codex CLI returned an unexpected connection identity.")
    return value


def _path_key(value):
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise InstallError("UNOWNED_CONNECTION", "An existing connection does not use an absolute owned executable.")
    return os.path.normcase(os.path.abspath(value))


def descriptor(root, version):
    payload, _, digest, _ = owned_version(root, version)
    return {"version": version, "manifest_sha256": digest,
            "command": str(payload / "runtime" / "python.exe"),
            "args": ["-I", "-B", str(payload / "server.py")]}


def _owned_config(root, value):
    if value is None:
        return None
    transport = value.get("transport")
    if (value.get("enabled") is not True or value.get("disabled_reason") is not None
            or not isinstance(transport, dict) or transport.get("type") != "stdio"
            or transport.get("env") not in (None, {}) or transport.get("env_vars") not in (None, [])
            or transport.get("cwd") is not None):
        raise InstallError("UNOWNED_CONNECTION", "The named connection has non-owned settings or is explicitly disabled; it was preserved.")
    permitted_transport = {"type", "command", "args", "env", "env_vars", "cwd"}
    permitted_root = {"name", "enabled", "disabled_reason", "transport", "startup_timeout_sec", "tool_timeout_sec", "enabled_tools", "disabled_tools"}
    if set(transport) - permitted_transport or set(value) - permitted_root:
        raise InstallError("UNOWNED_CONNECTION", "The named connection contains unsupported settings; it was preserved.")
    for key in ("startup_timeout_sec", "tool_timeout_sec", "enabled_tools", "disabled_tools"):
        if value.get(key) is not None:
            raise InstallError("UNOWNED_CONNECTION", "The named connection has user customizations; it was preserved.")
    command = transport.get("command")
    arguments = transport.get("args")
    if not isinstance(arguments, list) or len(arguments) != 3 or arguments[:2] != ["-I", "-B"]:
        raise InstallError("UNOWNED_CONNECTION", "The named connection is not an owned diagnostic launch command.")
    executable = Path(os.path.abspath(command))
    try:
        relative = executable.relative_to(Path(os.path.abspath(root)))
    except ValueError:
        raise InstallError("UNOWNED_CONNECTION", "The named connection belongs to another installation root.") from None
    parts = relative.parts
    if len(parts) != 5 or parts[0] != "versions" or parts[2:] != (PRODUCT, "runtime", "python.exe"):
        raise InstallError("UNOWNED_CONNECTION", "The named connection is outside a verified owned version.")
    expected = descriptor(root, parts[1])
    if _path_key(command) != _path_key(expected["command"]) or _path_key(arguments[2]) != _path_key(expected["args"][2]):
        raise InstallError("UNOWNED_CONNECTION", "The named connection does not match its verified installed payload.")
    return expected


def _same(first, second):
    return first == second


def result(action, status, *, version=None, receipt_id=None, error=None):
    return {"result_version": "chemdraw-connection/0.1", "ok": error is None, "action": action,
            "status": status, "version": version, "receipt_id": receipt_id,
            "native_execution_enabled": False, "host_tool_acceptance": "unverified", "error": error}


def _receipt_path(root, receipt_id):
    if not valid_id(receipt_id):
        raise InstallError("INVALID_RECEIPT", "A connection receipt identifier must be 32 lowercase hexadecimal characters.")
    return root / "connections" / (receipt_id + ".json")


def _read_receipt(root, receipt_id):
    receipt = regular_json(_receipt_path(root, receipt_id))
    if (not isinstance(receipt, dict) or receipt.get("receipt_version") != "chemdraw-connection-receipt/0.1"
            or receipt.get("product") != PRODUCT or receipt.get("receipt_id") != receipt_id
            or receipt.get("installation_id") != owner_record(root)["installation_id"]):
        raise InstallError("INVALID_RECEIPT", "The connection receipt does not belong to this installation.")
    return receipt


def _verify_descriptor(root, value):
    if value is None:
        return None
    if not isinstance(value, dict) or value != descriptor(root, value.get("version")):
        raise InstallError("INVALID_RECEIPT", "An owned connection receipt no longer matches its preserved package.")
    return value


def _finish(root, receipt, status, observed):
    receipt["status"] = status
    receipt["observed_at"] = utc_now()
    receipt["observed"] = observed
    atomic_json(_receipt_path(root, receipt["receipt_id"]), receipt)
    if status != "outcome_unknown":
        pending = regular_json(root / PENDING)
        if pending != {"receipt_id": receipt["receipt_id"]}:
            raise InstallError("RECONCILIATION_REQUIRED", "The connection pending marker changed; no new CLI mutation was attempted.")
        (root / PENDING).unlink()


def _reconcile(root, cli, runner):
    pending = regular_json(root / PENDING)
    if not isinstance(pending, dict) or set(pending) != {"receipt_id"}:
        raise InstallError("RECONCILIATION_REQUIRED", "The pending connection marker is invalid.")
    receipt = _read_receipt(root, pending["receipt_id"])
    before = _verify_descriptor(root, receipt.get("before"))
    after = _verify_descriptor(root, receipt.get("after"))
    try:
        observed = _owned_config(root, _get(cli, runner))
    except InstallError:
        return result("reconcile", "outcome_unknown", receipt_id=receipt["receipt_id"],
                      error={"code": "RECONCILIATION_REQUIRED", "message": "The same connection attempt remains unresolved; no command was replayed."})
    if _same(observed, after):
        _finish(root, receipt, "completed", observed)
        return result("reconcile", "completed", version=after["version"] if after else None, receipt_id=receipt["receipt_id"])
    if _same(observed, before):
        _finish(root, receipt, "not_applied", observed)
        return result("reconcile", "not_applied", version=before["version"] if before else None, receipt_id=receipt["receipt_id"])
    return result("reconcile", "outcome_unknown", receipt_id=receipt["receipt_id"],
                  error={"code": "RECONCILIATION_REQUIRED", "message": "The named connection changed outside the recorded attempt; it was preserved."})


def _change(root, before, after, cli, runner, *, action, original_receipt=None):
    receipt_id = uuid.uuid4().hex
    folder = root / "connections"
    folder.mkdir(exist_ok=True)
    safe_directory(folder)
    receipt = {"receipt_version": "chemdraw-connection-receipt/0.1", "product": PRODUCT,
               "installation_id": owner_record(root)["installation_id"], "receipt_id": receipt_id,
               "action": action, "status": "intent", "observed_at": utc_now(),
               "before": before, "after": after, "original_receipt": original_receipt,
               "native_execution_enabled": False}
    atomic_json(_receipt_path(root, receipt_id), receipt)
    atomic_json(root / PENDING, {"receipt_id": receipt_id})
    arguments = ["remove", NAME] if after is None else ["add", NAME, "--", after["command"], *after["args"]]
    try:
        _run(cli, arguments, runner)
    except InstallError:
        pass  # A CLI error may follow a completed write. Read the same attempt back.
    try:
        observed = _owned_config(root, _get(cli, runner))
    except InstallError:
        _finish(root, receipt, "outcome_unknown", None)
        return result(action, "outcome_unknown", receipt_id=receipt_id,
                      error={"code": "RECONCILIATION_REQUIRED", "message": "Connection write outcome is unknown; its receipt was preserved and will be reconciled without replay."})
    if _same(observed, after):
        _finish(root, receipt, "completed", observed)
        return result(action, "connected" if after else "unconnected", version=after["version"] if after else None, receipt_id=receipt_id)
    if _same(observed, before):
        _finish(root, receipt, "not_applied", observed)
        return result(action, "not_applied", receipt_id=receipt_id,
                      error={"code": "CLI_CHANGE_FAILED", "message": "Readback confirms the previous connection was preserved."})
    _finish(root, receipt, "outcome_unknown", observed)
    return result(action, "outcome_unknown", receipt_id=receipt_id,
                  error={"code": "RECONCILIATION_REQUIRED", "message": "Connection readback conflicts with the recorded change; no command will be replayed."})


def connect(root, *, cli=("codex",), runner=subprocess.run, rollback_receipt=None, read_only=False):
    root = safe_directory(Path(root))
    pointer, _ = current_installation(root)
    desired = descriptor(root, pointer["version"])
    if read_only:
        current = _owned_config(root, _get(cli, runner))
        return result("status", "connected" if current == desired else "unconnected" if current is None else "different_owned_version",
                      version=current["version"] if current else None)
    with root_lock(root) as root:
        pointer, _ = current_installation(root)
        desired = descriptor(root, pointer["version"])
        if (root / PENDING).exists():
            return _reconcile(root, cli, runner)
        current = _owned_config(root, _get(cli, runner))
        if rollback_receipt:
            old = _read_receipt(root, rollback_receipt)
            if old.get("status") != "completed" or old.get("action") != "connect":
                raise InstallError("INVALID_RECEIPT", "Only a completed connection change can be rolled back.")
            prior = _verify_descriptor(root, old.get("before"))
            target = _verify_descriptor(root, old.get("after"))
            if prior is not None and desired != prior:
                raise InstallError("ROLLBACK_FILES_FIRST", "First use install.py --rollback for the receipt's previous version, then restore its connection.")
            if current == prior:
                return result("rollback", "unchanged" if prior else "unconnected", version=prior["version"] if prior else None)
            if current != target:
                raise InstallError("CONNECTION_CHANGED", "The connection no longer matches that receipt; it was preserved.")
            return _change(root, current, prior, cli, runner, action="rollback", original_receipt=rollback_receipt)
        if current == desired:
            return result("connect", "unchanged", version=pointer["version"])
        return _change(root, current, desired, cli, runner, action="connect")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--codex", help="Path to the official Codex executable; defaults to PATH discovery.")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--status", action="store_true")
    actions.add_argument("--rollback", metavar="RECEIPT_ID", help="Restore a prior owned connection or remove the initial connection.")
    args = parser.parse_args(argv)
    action = "status" if args.status else "rollback" if args.rollback else "connect"
    try:
        command = args.codex or shutil.which("codex")
        if not command:
            raise InstallError("CLI_UNAVAILABLE", "Install or open Codex so its official CLI is available; the package remains unconnected.")
        if os.name == "nt" and Path(command).suffix.casefold() != ".exe":
            raise InstallError("CLI_UNSUPPORTED", "Supply the official Codex .exe with --codex; shell wrappers are not supported.")
        output = connect(args.root or default_root(), cli=(command,), rollback_receipt=args.rollback, read_only=args.status)
    except (InstallError, OSError, ValueError, TypeError) as exc:
        code = exc.code if isinstance(exc, InstallError) else "CONNECTION_IO_OR_METADATA_ERROR"
        message = str(exc) if isinstance(exc, InstallError) else "Connection metadata or file access failed; existing configuration was preserved."
        output = result(action, "refused", error={"code": code, "message": message})
    print(json.dumps(output, ensure_ascii=True))
    return 0 if output["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
