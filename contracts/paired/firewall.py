"""Windows process read firewall for paired reconstruction research.

This confines spawned processes, not the authentication custodian which starts
Codex. The separate projection broker gives the remote model PNG/schema only.
No setup/install, account creation, credential reading or hidden-target reading.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

CATEGORIES = ("hidden_cdxml", "target_geometry", "target_coordinates", "target_object_ids",
              "evaluator_annotations", "layout_constraints")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, allow_nan=False, sort_keys=True) + "\n").encode("utf-8")


def toml(value):
    if isinstance(value, dict):
        return "{" + ",".join(json.dumps(k) + "=" + toml(v) for k, v in value.items()) + "}"
    return json.dumps(value)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def confined_command(codex, command, cwd, readable, writable=(), forbidden=(), network=False):
    """Exact allowlist plus platform runtime baseline. Never grants the repo root.

    Callers must supply only approved code/runtime paths and staged PNG/schema.
    Model-generated arguments never become permission rules. The caller is the
    trusted custodian; this function is not itself an ACL enforcement substitute.
    """
    require(os.name == "nt", "this backend requires existing native Windows Codex sandbox")
    codex = Path(codex).resolve(strict=True)
    cwd = Path(cwd).resolve(strict=True)
    require(command and Path(command[0]).is_absolute(), "absolute executable required")
    deny = [Path(p).resolve(strict=True) for p in forbidden]
    grants = [(Path(p).resolve(strict=True), access) for paths, access in ((readable, "read"), (writable, "write")) for p in paths]
    for path, access in grants:
        require(not any(path == d or path.is_relative_to(d) or d.is_relative_to(path) for d in deny),
                "read/write grant overlaps forbidden root")
        require(path != Path(path.anchor), "cannot grant a filesystem root")
    profile = {":root": "deny", ":minimal": "read"}
    profile.update({str(p): access for p, access in grants})
    profile.update({str(p): "deny" for p in deny})
    return [str(codex), "sandbox", "-P", "paired-firewall",
            "-c", "permissions.paired-firewall.filesystem=" + toml(profile),
            "-c", "permissions.paired-firewall.network.enabled=" + toml(bool(network)),
            "-c", 'windows.sandbox="elevated"', "-C", str(cwd), *map(str, command)]


def run_confined(codex, command, cwd, readable, writable=(), forbidden=(), network=False, timeout=45):
    args = confined_command(codex, command, cwd, readable, writable, forbidden, network)
    proc = subprocess.run(args, input="", capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
    return {"command": args, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr,
            "network_enabled": bool(network), "backend": "existing_codex_elevated_windows"}


def sentinel_probe(codex, python, out):
    """Real denial attempts against files created here; never accepts target paths."""
    out = Path(out).resolve()
    require(not out.exists(), "refusing existing probe output")
    out.mkdir(parents=True)
    inp, hidden, code = (out / name for name in ("generator_input", "hidden_target", "probe_code"))
    for p in (inp, hidden, code):
        p.mkdir()
    approved = b"APPROVED_SENTINEL_INPUT"
    (inp / "allowed.txt").write_bytes(approved)
    sentinels = []
    for category in CATEGORIES:
        path = hidden / (category + ".sentinel")
        data = ("SYNTHETIC_ONLY_" + category + "_" + uuid.uuid4().hex).encode()
        path.write_bytes(data)
        sentinels.append({"category": category, "path": str(path), "bytes": len(data), "sha256": sha(data)})
    script = code / "sentinel_reader.py"
    script.write_text("import pathlib,json,hashlib\nrows=[]\n" +
        "allowed=pathlib.Path(" + repr(str(inp / "allowed.txt")) + ").read_bytes()\n" +
        "for item in " + repr(sentinels) + ":\n" +
        " try:\n  pathlib.Path(item['path']).read_bytes();rows.append({'category':item['category'],'denied':False})\n" +
        " except PermissionError as e:\n  rows.append({'category':item['category'],'denied':True,'exception':'PermissionError','errno':e.errno})\n" +
        " except OSError as e:\n  rows.append({'category':item['category'],'denied':False,'exception':type(e).__name__,'errno':e.errno})\n" +
        "print(json.dumps({'allowed_sha256':hashlib.sha256(allowed).hexdigest(),'attempts':rows}))\n", encoding="utf-8")
    python = Path(python).resolve(strict=True)
    result = run_confined(codex, [python, "-B", script], inp,
                          [inp, script, python.parent], forbidden=[hidden], network=True)
    observation = json.loads(result["stdout"]) if result["returncode"] == 0 else None
    passed = bool(observation and observation["allowed_sha256"] == sha(approved) and
                  len(observation["attempts"]) == len(CATEGORIES) and
                  all(a.get("denied") and a.get("exception") == "PermissionError" and a.get("errno") == 13
                      for a in observation["attempts"]))
    receipt = {"version": "paired-firewall-probe/1.0", "timestamp": datetime.now(timezone.utc).isoformat(),
               "synthetic_only": True, "model_called": False, "status": "pass" if passed else "failed",
               "scope": "Observed OS denial in this existing sandbox; not a full generator inference receipt.",
               "sentinels": sentinels, "observation": observation, "process": result}
    (out / "receipt.json").write_bytes(json_bytes(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = sentinel_probe(args.codex, args.python, args.out)
    print(json.dumps({"status": result["status"], "receipt": str(args.out / "receipt.json"),
                      "denial_classes": len(CATEGORIES), "model_called": False}))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
