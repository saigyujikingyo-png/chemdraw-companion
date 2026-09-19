"""Durable local edit receipts. Native execution remains operationally frozen.

The private backend argument is a portable process boundary used by tests. There
is deliberately no environment variable or CLI flag that enables native work.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import time
import uuid
from datetime import datetime, timezone
from functools import lru_cache

VERSION = "agent-edit-result/0.2-draft.2"
NATIVE_EXECUTION_ENABLED = False
BASE = {"action", "request_id", "session_id", "document_id", "revision"}
ACTIONS = {
    "open-copy": {"source", "expected_sha256", "role"},
    "inspect": {"end_session", "keep_open"},
    "relative-position": {"caption_id", "caption_token", "arrow_id", "arrow_token", "intent"},
    "save": {"stem"}, "reopen": {"artifact_id"},
}
ROLES = {"workflow-control", "script-safety-control", "no-edit-control", "development-copy"}
MAX_REPLY_BYTES = 8 * 1024 * 1024


def utc():
    return datetime.now(timezone.utc).isoformat()


def canonical(path):
    return Path(os.path.normcase(str(Path(path).resolve())))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def atomic(path, value):
    """Publish a completed file; failed temporary files remain diagnostic evidence."""
    path = Path(path)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


@lru_cache(maxsize=1)
def validator():
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
    base = Path(__file__).resolve().parents[1] / "contracts" / "output"
    common = read(base / "common.schema.json")
    schema = read(base / "edit-result-lifecycle.schema.json")
    registry = Registry().with_resource(common["$id"], Resource.from_contents(common))
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())


def checked(result):
    validator().validate(result)
    return result



def preflight_error(stage, message):
    """Separate checked pre-dispatch envelope; do not invent an operation for invalid input."""
    result = {"result_version": "edit-preflight-error/0.1", "dispatch": "not_started",
              "error": {"code": "INVALID_ARGUMENT", "message": (str(message) or "Invalid request")[:1024],
                        "stage": stage, "retryable": False}}
    if stage not in {"request_validation", "request_decode"}:
        raise ValueError("Invalid preflight stage")
    # The fixed, bounded construction implements this small schema without adding
    # a third-party requirement to malformed-input handling. CI cross-validates
    # actual CLI responses against the published JSON Schema.
    assert set(result) == {"result_version", "dispatch", "error"}
    assert set(result["error"]) == {"code", "message", "stage", "retryable"}
    assert isinstance(result["error"]["message"], str) and 1 <= len(result["error"]["message"]) <= 1024
    return result


def normalized(request, state):
    if not isinstance(request, dict) or request.get("action") not in ACTIONS:
        raise ValueError("One supported action is required")
    q = dict(request)
    action = q["action"]
    if set(q) - BASE - ACTIONS[action]:
        raise ValueError("Unknown request fields")
    q["request_id"] = str(uuid.UUID(q.get("request_id", str(uuid.uuid4()))))
    if action == "open-copy":
        if set(q) & {"session_id", "document_id", "revision"}:
            raise ValueError("open-copy cannot supply existing session tokens")
        q["source"] = str(canonical(q["source"]))
        q["expected_sha256"] = q["expected_sha256"].lower()
        if not re.fullmatch("[a-f0-9]{64}", q["expected_sha256"]) or q.get("role") not in ROLES:
            raise ValueError("An exact source SHA-256 and declared ordinary source role are required")
        if Path(q["source"]).suffix.lower() not in {".cdx", ".cdxml"}:
            raise ValueError("One ordinary CDX/CDXML source is required")
    else:
        for key in ("session_id", "document_id"):
            q[key] = str(uuid.UUID(q[key]))
        if type(q.get("revision")) is not int or q["revision"] < 0:
            raise ValueError("A nonnegative revision is required")
        if action == "inspect":
            if any(type(q[k]) is not bool for k in ("end_session", "keep_open") if k in q):
                raise ValueError("Session flags must be booleans")
            if q.get("keep_open") and not q.get("end_session"):
                raise ValueError("keep_open requires explicit end_session")
        elif action == "save":
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", q.get("stem", "")):
                raise ValueError("Use a new simple output stem")
        elif action == "reopen":
            q["artifact_id"] = str(uuid.UUID(q["artifact_id"]))
        elif action == "relative-position":
            if q.get("intent") not in {"above-arrow", "up-half-bond"}:
                raise ValueError("Unsupported relative intent")
            for key in ("caption_id", "arrow_id"):
                if type(q.get(key)) is not int or q[key] < 0:
                    raise ValueError("Current object identifiers are required")
            for key in ("caption_token", "arrow_token"):
                if not isinstance(q.get(key), str) or not 1 <= len(q[key]) <= 256:
                    raise ValueError("Current object tokens are required")
    return q, digest({"scope": str(state), "request": q})


def context(q, root, fingerprint):
    return {"request": q, "request_id": q["request_id"], "operation_id": str(uuid.uuid4()),
            "action": q["action"], "session_id": q.get("session_id"),
            "document_id": q.get("document_id"), "revision": q.get("revision"),
            "generation": None, "state_root": str(root), "fingerprint": fingerprint,
            "created_at": utc(), "stage": "validated", "dispatched": False,
            "worker_state": "absent", "session_state": "not_created", "quarantined": False, "evidence_ids": []}


def receipt(c, status, outcome, code=None, reason=None, session_state=None, details=None):
    evidence = c.get("evidence_ids", [])[-16:]
    recovery = "Observe this same attempt; never replay an uncertain operation."
    error = None if code is None else {
        "code": code, "message": reason[:1024], "stage": c["stage"], "retryable": False,
        "mutation_outcome": outcome, "evidence_ids": evidence, "next_action": recovery,
    }
    return {
        "result_version": VERSION, "operation": c["action"], "request_id": c["request_id"],
        "operation_id": c["operation_id"], "session_id": c["session_id"],
        "document_id": c["document_id"], "revision": c["revision"],
        "status": status, "mutation_outcome": outcome, "error": error,
        "session_state": session_state or ("unknown" if c["dispatched"] else "not_created"),
        "preservation": "unverified", "observed_at": utc(), "evidence_ids": evidence,
        "lifecycle": {"generation": c["generation"], "worker_state": c["worker_state"],
                      "dispatch_stage": c["stage"], "quarantined": c["quarantined"]},
        "artifacts": [], "observation_ref": None,
        "native_render": {"status": "unverified", "evidence_ids": [], "reason": "Native render acceptance is separate."},
        "desktop_display": {"status": "unverified", "evidence_ids": [], "reason": "Desktop display was not observed."},
        "details": details if details is not None else {
            "reason": (reason or "Attempt pending")[:512], "recovery_action": recovery,
            "candidates_ref": None,
        },
    }


def record(attempt, c, stage):
    c["stage"] = stage
    event = stage + "-" + uuid.uuid4().hex
    atomic(attempt / "events" / (event + ".json"), {"observed_at": utc(), **c})
    c["evidence_ids"] = (c["evidence_ids"] + [event])[-16:]
    atomic(attempt / "state.json", c)


def retain(attempt, c, result):
    # Never replace earlier timeout/validation evidence with a late response.
    checked(result)
    name = "receipt-" + uuid.uuid4().hex + ".json"
    atomic(attempt / "receipts" / name, result)
    c["result_file"] = name
    atomic(attempt / "state.json", c)
    return result


def error_result(attempt, c, code, reason):
    outcome = "known" if c.get("effect_known") else ("unknown" if c["dispatched"] else "none")
    if c["dispatched"]:
        c["quarantined"] = True
    if outcome == "known" and code == "NATIVE_OUTCOME_UNKNOWN":
        code = "OUTPUT_VALIDATION_FAILED"
    result = receipt(c, "outcome_unknown" if outcome == "unknown" else "failed", outcome, code, reason)
    return retain(attempt, c, result) if attempt is not None else checked(result)


def worker_state(c, backend):
    identity = c.get("worker")
    if not identity:
        return "unknown" if c["dispatched"] else "absent"
    observation = backend.observe(identity)
    if observation is None:
        return "dead"
    if observation == identity:
        return "ready" if c.get("ready") else "not_ready"
    return "stale"


def binding(observation):
    raw = observation["binding"]
    # Do not synthesize omitted scope or process identity from untrusted output.
    return {"pid": raw["pid"], "start_utc": raw["start_utc"],
            "hwnd": str(raw["hwnd"]), "document_id": observation["document_id"]}


def decode_reply(raw, c, folder):
    """Select this operation only. Identity/readiness checks precede mapping."""
    if not isinstance(raw, dict) or type(raw.get("ok")) is not bool:
        raise ValueError("Worker reply must contain a boolean ok")
    for key, expected in (("action", c["action"]), ("request_id", c["request_id"]),
                          ("operation_id", c["operation_id"]), ("session_id", c["session_id"]),
                          ("generation", c["generation"])):
        if raw.get(key) != expected:
            raise ValueError("Worker identity mismatch: " + key)
    # A failed legacy payload cannot establish effects from native_write=false.
    if not raw["ok"]:
        return receipt(c, "outcome_unknown", "unknown", "NATIVE_OUTCOME_UNKNOWN",
                       str(raw.get("reason", "Worker failed after dispatch")))
    ready = raw["readiness"]
    ending = c["action"] == "inspect" and c["request"].get("end_session")
    expected_ready = "not_ready" if ending else "ready"
    if (not isinstance(ready, dict) or set(ready) != {"state", "document_bound", "observations_complete"}
            or ready["state"] != expected_ready or ready["document_bound"] is not True
            or ready["observations_complete"] is not True):
        raise ValueError("No current document-bound readiness proof")
    observation = raw["observation"]
    document_id = str(uuid.UUID(raw["document_id"]))
    revision = raw["revision"]
    if type(revision) is not int or revision < 0:
        raise ValueError("Invalid returned revision")
    if observation.get("session_id") != c["session_id"] or observation.get("document_id") != document_id or observation.get("revision") != revision:
        raise ValueError("Observation scope mismatch")
    q = c["request"]
    if c["action"] not in {"open-copy", "reopen"} and document_id != c["document_id"]:
        raise ValueError("Unexpected document identity")
    expected_revision = 0 if c["action"] == "open-copy" else q["revision"] + (c["action"] != "inspect")
    if revision != expected_revision:
        raise ValueError("Unexpected revision transition")
    bound = binding(observation)
    native_binding = observation["binding"]
    if not isinstance(native_binding.get("executable"), str) or not native_binding["executable"]:
        raise ValueError("Native executable identity is missing")
    if c["action"] == "open-copy":
        if raw["source_sha256"] != q["expected_sha256"] or raw["baseline_stability"].get("ok") is not True:
            raise ValueError("Opening baseline was not established")
        if file_hash(q["source"]) != q["expected_sha256"]:
            raise ValueError("Original changed before receipt validation")
        details = {"source_sha256": q["expected_sha256"], "original_unchanged": True, "binding": bound}
    elif c["action"] == "inspect":
        details = {"binding": bound, "closure_receipt_id": None, "candidates_ref": None}
    elif c["action"] == "relative-position":
        motion = raw["detail"]["motion"]
        if raw["detail"]["verification"].get("ok") is not True:
            raise ValueError("Move comparison failed")
        details = {"caption_ref": q["caption_token"], "arrow_ref": q["arrow_token"], "intent": q["intent"],
                   "delta_pt": motion["delta"], "bond_length_pt": motion["native_bond_length"],
                   "comparison_evidence_id": q["request_id"] + "-check"}
    elif c["action"] == "save":
        if raw["detail"]["normalization"].get("ok") is not True:
            raise ValueError("Save comparison failed")
        details = {"saved_revision": revision, "comparison_evidence_id": q["request_id"] + "-save-normalization"}
    else:
        if raw["detail"]["normalization"].get("ok") is not True:
            raise ValueError("Reopen comparison failed")
        previous = {**raw["detail"]["previous_binding"], "document_id": c["document_id"]}
        details = {"previous_binding": binding({"binding": previous, "document_id": previous["document_id"]}),
                   "current_binding": bound, "reopened_artifact_id": q["artifact_id"],
                   "comparison_evidence_id": q["request_id"] + "-reopen-normalization"}
    # Only verified reply data may advance the trusted current binding.
    proposed = {**c, "document_id": document_id, "revision": revision}
    ending = c["action"] == "inspect" and q.get("end_session")
    result = receipt(proposed, "pending" if ending else "completed", "known",
                     reason="Session ending; document close and process exit remain separately observed" if ending else None,
                     session_state="ending" if ending else "active", details=None if ending else details)
    checked(result)
    c["document_id"], c["revision"], c["ready"] = document_id, revision, not ending
    c["session_state"] = "ending" if ending else "active"
    c["last_binding"] = bound
    c["native_binding"] = native_binding
    c["effect_known"] = True
    c["worker_state"] = result["lifecycle"]["worker_state"] = "not_ready" if ending else "ready"
    return result


def inspect_reply(attempt, c, backend):
    folder = Path(c["state_root"]) / c["session_id"]
    path = folder / "replies" / (c["request_id"] + ".json")
    c["worker_state"] = worker_state(c, backend)
    if not path.exists():
        return None
    if c["worker_state"] in {"dead", "stale", "unknown"}:
        return error_result(attempt, c, "STALE_OBJECT", "Reply cannot establish a live current worker generation")
    if path.stat().st_size > MAX_REPLY_BYTES:
        raise ValueError("Worker reply exceeds bounded size")
    data = path.read_bytes()
    reply_hash = hashlib.sha256(data).hexdigest()
    if c.get("validated_reply_sha256") == reply_hash and c.get("result_file"):
        return read(attempt / "receipts" / c["result_file"])
    if c.get("validated_reply_sha256"):
        raise ValueError("An already published worker reply changed; both attempts remain quarantined")
    raw_name = "raw-" + reply_hash + ".json"
    raw_path = attempt / "receipts" / raw_name
    if not raw_path.exists():
        with raw_path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    c["evidence_ids"] = (c["evidence_ids"] + [raw_name])[-16:]
    try:
        result = decode_reply(json.loads(data.decode("utf-8-sig")), c, folder)
    except Exception as exc:
        return error_result(attempt, c, "OUTPUT_VALIDATION_FAILED", str(exc))
    c["validated_reply_sha256"] = reply_hash
    if result["mutation_outcome"] == "unknown":
        c["quarantined"] = True
    if c["quarantined"]:
        result["session_state"] = "unknown"
    return retain(attempt, c, result)



def reconcile_closure(attempt, c, backend):
    """Observe one retained attempt. Close/Quit returns alone never release ownership."""
    path = Path(c["state_root"]) / c["session_id"] / "closed.json"
    if not path.is_file() or not c.get("result_file"):
        return None
    if path.stat().st_size > MAX_REPLY_BYTES:
        raise ValueError("Closure receipt exceeds bounded size")
    data = path.read_bytes()
    raw = json.loads(data.decode("utf-8-sig"))
    if (raw.get("generation") != c["generation"] or raw.get("session_id") != c["session_id"]
            or raw.get("operation_id") != c["operation_id"]):
        raise ValueError("Closure scope/generation/operation mismatch")
    state = raw.get("session_state")
    if state not in {"closed", "detached"}:
        return None
    applications = raw.get("applications")
    if not isinstance(applications, list) or not applications:
        raise ValueError("Terminal closure lacks owned application evidence")
    detached = 0
    matched_current = 0
    for app in applications:
        if not isinstance(app, dict) or app.get("generation") != c["generation"]:
            raise ValueError("Application closure generation mismatch")
        owned = app.get("owned_binding")
        if (not isinstance(owned, dict) or type(owned.get("pid")) is not int or owned["pid"] <= 0
                or not all(isinstance(owned.get(k), str) and owned[k] for k in ("start_utc", "executable"))):
            raise ValueError("Closure lacks exact owned process identity")
        current = c.get("native_binding", {})
        if all(owned[k] == current.get(k) for k in ("pid", "start_utc", "executable")):
            if app.get("document_id") != c["document_id"] or app.get("revision") != c["revision"]:
                raise ValueError("Closure document scope mismatch")
            matched_current += 1
        if app.get("session_state") == "closed" and app.get("observed_process_exit") is True:
            continue
        if (app.get("session_state") == "detached" and app.get("ownership_transferred_to_user") is True
                and app.get("ownership_verified") is True and app.get("saved_revision_verified") is True):
            detached += 1
        else:
            raise ValueError("An owned application remains unresolved")
    if matched_current != 1:
        raise ValueError("Closure does not identify exactly one current owned document")
    if state == "closed" and (detached or raw.get("observed_process_exit") is not True):
        raise ValueError("Quit return is not process exit proof")
    if state == "detached" and (detached != 1 or raw.get("ownership_transferred_to_user") is not True
            or not c["request"].get("end_session") or not c["request"].get("keep_open")):
        raise ValueError("Detach was not explicitly requested and verified")
    name = "closure-" + hashlib.sha256(data).hexdigest()
    if c.get("closure_evidence") == name and c.get("terminal") is True:
        return read(attempt / "receipts" / c["result_file"])
    if c.get("closure_evidence") and c["closure_evidence"] != name:
        raise ValueError("Published closure changed; do not replace original evidence")
    retained = attempt / "receipts" / (name + ".json")
    if not retained.exists():
        with retained.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    c["evidence_ids"] = (c["evidence_ids"] + [name])[-16:]
    historical = read(attempt / "receipts" / c["result_file"])
    c["ready"], c["session_state"] = False, state
    c["worker_state"] = worker_state(c, backend)
    c["closure_evidence"] = name
    if historical["mutation_outcome"] == "known":
        if c["action"] == "inspect":
            result = receipt(c, "completed", "known", session_state=state,
                             details={"binding": c["last_binding"], "closure_receipt_id": name, "candidates_ref": None})
        else:
            result = {**historical, "session_state": state, "observed_at": utc(),
                      "evidence_ids": c["evidence_ids"], "lifecycle": {
                          "generation": c["generation"], "worker_state": c["worker_state"],
                          "dispatch_stage": c["stage"], "quarantined": c["quarantined"]}}
        checked(result)
        terminal = Path(c["state_root"]) / ".lifecycle-v02" / "terminal-sessions"
        terminal.mkdir(exist_ok=True)
        atomic(terminal / (c["session_id"] + ".json"), {
            "session_id": c["session_id"], "generation": c["generation"],
            "state": state, "closure_evidence": name, "request_id": c["request_id"]})
        c["terminal"] = True
        return retain(attempt, c, result)
    # Exit can resolve ownership without resolving an earlier operation's effects.
    result = receipt(c, "outcome_unknown", "unknown", "NATIVE_OUTCOME_UNKNOWN",
                     "Ownership ended but the operation effect remains unknown", session_state=state)
    return retain(attempt, c, result)


def restore_attempt(attempt, fallback):
    """Recover assigned identity from immutable intent; unreadable state is never no-effect proof."""
    for name in ("state.json", "intent.json"):
        try:
            c = read(attempt / name)
            required = {"request", "request_id", "operation_id", "action", "session_id", "document_id", "revision",
                        "generation", "state_root", "fingerprint", "created_at", "stage", "dispatched", "worker_state",
                        "session_state", "quarantined", "evidence_ids"}
            if not isinstance(c, dict) or not required <= set(c):
                raise ValueError("Incomplete stored attempt contract")
            if (not isinstance(c["request"], dict)
                    or not all(isinstance(c[k], str) for k in ("request_id", "operation_id", "session_id", "generation", "state_root", "fingerprint", "stage"))
                    or type(c["dispatched"]) is not bool or type(c["quarantined"]) is not bool
                    or not re.fullmatch("[a-f0-9]{64}", c["fingerprint"])
                    or c["action"] not in ACTIONS or c["request"].get("action") != c["action"]
                    or c["request"].get("request_id") != c["request_id"]
                    or not isinstance(c["evidence_ids"], list)
                    or any(not isinstance(item, str) for item in c["evidence_ids"])):
                raise ValueError("Invalid stored attempt contract")
            if digest({"scope": c["state_root"], "request": c["request"]}) != c["fingerprint"]:
                raise ValueError("Stored request fingerprint mismatch")
            if c["request_id"] != fallback["request_id"] or canonical(c["state_root"]) != canonical(fallback["state_root"]):
                raise ValueError("Stored attempt scope mismatch")
            for key in ("request_id", "operation_id", "session_id", "generation"):
                if str(uuid.UUID(c[key])) != c[key]:
                    raise ValueError("Stored identity is not canonical")
            if name == "intent.json":
                c.update(dispatched=True, worker_state="unknown", ready=False, quarantined=True,
                         stage="registry_unreadable", recovery_error="State unreadable; identity recovered from retained intent")
            return c
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            continue
    c = {**fallback, "operation_id": None, "session_id": None, "generation": None,
         "dispatched": True, "worker_state": "unknown", "quarantined": True,
         "stage": "registry_unreadable", "recovery_error": "Existing attempt identity is unreadable; no replay or new identity"}
    return c


def prior_attempt(attempt, fingerprint, backend, boundary):
    c = restore_attempt(attempt, boundary["current"])
    boundary["current"] = c
    if c.get("recovery_error"):
        return error_result(None, c, "OUTPUT_VALIDATION_FAILED", c["recovery_error"])
    if c["fingerprint"] != fingerprint:
        return checked(receipt(c, "refused", "none", "IDEMPOTENCY_CONFLICT",
                               "Request ID is already bound to different input"))
    try:
        closed = reconcile_closure(attempt, c, backend)
        if closed is not None:
            return closed
        if c.get("result_file"):
            historical = read(attempt / "receipts" / c["result_file"])
            current = worker_state(c, backend) if c["dispatched"] else "absent"
            if historical["mutation_outcome"] == "known" and current in {"dead", "stale", "unknown"}:
                c["worker_state"], c["ready"], c["quarantined"] = current, False, True
                # Liveness loss invalidates tokens, not the completed operation's evidence.
                return retain(attempt, c, receipt(c, "failed", "known", "STALE_OBJECT",
                    "Historical operation result remains known; current worker binding is unusable", session_state="unknown"))
        if c["dispatched"]:
            result = inspect_reply(attempt, c, backend)
            if result is not None:
                return result
        if c.get("result_file") and not c["dispatched"]:
            return read(attempt / "receipts" / c["result_file"])
        return error_result(attempt, c, "NATIVE_OUTCOME_UNKNOWN" if c["dispatched"] else "INTERRUPTED",
                            "Accepted attempt has no completed response; reconciliation never redispatches")
    except Exception as exc:
        return error_result(attempt, c, "OUTPUT_VALIDATION_FAILED", str(exc))



def terminal_sessions(control):
    accepted = set()
    for path in (control / "terminal-sessions").glob("*.json"):
        try:
            marker = read(path)
            sid = str(uuid.UUID(marker["session_id"]))
            rid = str(uuid.UUID(marker["request_id"]))
            if path.stem != sid:
                continue
            attempt = control / "attempts" / rid
            owner = read(attempt / "state.json")
            name = marker["closure_evidence"]
            if not re.fullmatch("closure-[a-f0-9]{64}", name):
                continue
            raw_path = attempt / "receipts" / (name + ".json")
            raw = read(raw_path)
            if (owner.get("terminal") is True and owner["session_id"] == sid
                    and owner["generation"] == marker["generation"] == raw["generation"]
                    and raw["operation_id"] == owner["operation_id"]
                    and owner["session_state"] == marker["state"] == raw["session_state"]
                    and owner["closure_evidence"] == name and file_hash(raw_path) == name[8:]):
                accepted.add(sid)
        except (OSError, ValueError, TypeError, KeyError):
            continue
    return accepted


def _submit(request, state, *, timeout=50, _backend=None, _checkpoint=None, _boundary=None):
    """Submit once or observe the same attempt. Portable doubles are not native acceptance."""
    started = time.monotonic()
    root = canonical(state)
    q, fingerprint = normalized(request, root)
    c = context(q, root, fingerprint)
    _boundary["current"] = c
    checkpoint = _checkpoint or (lambda stage, current: None)
    # Fail closed before copying a source or inspecting historical session data.
    validator()
    if _backend is None:
        return checked(receipt(c, "refused", "none", "CAPABILITY_UNVERIFIED",
                               "Native execution is frozen. This build supports portable lifecycle verification and diagnostics only."))
    if isinstance(timeout, bool) or not isinstance(timeout, (float, int)) or not math.isfinite(timeout) or not 0 < timeout <= 60:
        raise ValueError("Timeout must be finite and between zero and sixty seconds")
    root.mkdir(parents=True, exist_ok=True)
    control = root / ".lifecycle-v02"
    control.mkdir(exist_ok=True)
    attempts = control / "attempts"
    attempts.mkdir(exist_ok=True)
    attempt = attempts / c["request_id"]
    lock = control / "controller.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        # Do not reclaim a stale lock, inspect a half-written reply, or dispatch.
        if attempt.is_dir():
            prior = restore_attempt(attempt, c)
            _boundary["current"] = prior
            if prior.get("recovery_error"):
                return error_result(None, prior, "OUTPUT_VALIDATION_FAILED", prior["recovery_error"])
            if prior["fingerprint"] == fingerprint:
                return checked(receipt(prior, "outcome_unknown" if prior["dispatched"] else "pending",
                                       "unknown" if prior["dispatched"] else "none",
                                       "NATIVE_OUTCOME_UNKNOWN" if prior["dispatched"] else None,
                                       "Another controller holds this same attempt; no additional dispatch"))
        return checked(receipt(c, "refused", "none", "RESOURCE_LIMIT", "Controller claim is occupied or unreconciled"))
    persisted = False
    try:
        if attempt.exists():
            return prior_attempt(attempt, fingerprint, _backend, _boundary)
        active_path = control / "active.json"
        active = read(active_path) if active_path.exists() else None
        if q["action"] == "open-copy":
            terminal_ids = terminal_sessions(control)
            legacy = any(p.is_dir() and p.name != ".lifecycle-v02" and p.name not in terminal_ids for p in root.iterdir())
            active_unresolved = active and active["session_id"] not in terminal_ids
            if active_unresolved or legacy:
                return checked(receipt(c, "refused", "none", "DOCUMENT_BINDING_UNSAFE",
                                       "An active or legacy session is unreconciled; a new request cannot bypass it"))
            c["session_id"], c["generation"] = str(uuid.uuid4()), str(uuid.uuid4())
        else:
            if not active or active["session_id"] != q["session_id"]:
                return checked(receipt(c, "refused", "none", "DOCUMENT_BINDING_UNSAFE", "No current owned session"))
            owner = read(attempts / active["request_id"] / "state.json")
            if owner["quarantined"] or owner.get("session_state") != "active" or not owner.get("ready") or worker_state(owner, _backend) != "ready":
                return checked(receipt(c, "refused", "none", "STALE_OBJECT", "Session is not ready, stale, or quarantined"))
            if (owner["document_id"], owner["revision"]) != (q["document_id"], q["revision"]):
                return checked(receipt(c, "refused", "none", "REVISION_CONFLICT", "Current document/revision does not match"))
            c["generation"], c["worker"], c["ready"] = owner["generation"], owner["worker"], True
        attempt.mkdir()
        (attempt / "events").mkdir()
        (attempt / "receipts").mkdir()
        atomic(attempt / "intent.json", c)
        record(attempt, c, "intent_persisted")
        persisted = True
        atomic(active_path, {"request_id": c["request_id"], "session_id": c["session_id"], "generation": c["generation"]})
        checkpoint("intent_persisted", c)
        folder = root / c["session_id"]
        wire = {**q, "session_id": c["session_id"], "operation_id": c["operation_id"], "generation": c["generation"]}
        if q["action"] == "open-copy":
            source = Path(q["source"])
            if not source.is_file() or file_hash(source) != q["expected_sha256"]:
                raise ValueError("Source hash required and must match before creating a copy")
            folder.mkdir()
            for name in ("inbox", "replies", "evidence", "saved"):
                (folder / name).mkdir()
            copied = folder / ("source" + source.suffix.lower())
            shutil.copyfile(source, copied)
            if file_hash(copied) != q["expected_sha256"]:
                raise ValueError("Copy hash changed")
            atomic(folder / "init.json", {"request": wire, "source": str(source), "copy": str(copied),
                                         "source_sha256": q["expected_sha256"], "max_idle_seconds": 1200,
                                         "generation": c["generation"], "operation_id": c["operation_id"]})
            checkpoint("prepared", c)
            # Persist possible dispatch BEFORE invoking the process boundary.
            c["dispatched"], c["worker_state"] = True, "spawning"
            record(attempt, c, "spawn_intent")
            checkpoint("spawn_intent", c)
            identity = _backend.spawn(folder)
            checkpoint("spawn_returned", c)
            if not isinstance(identity, dict) or set(identity) != {"pid", "start_utc", "executable"}:
                raise ValueError("Worker creation identity was not established")
            c["worker"] = identity
            atomic(folder / "worker.json", {"identity": identity, "generation": c["generation"]})
            record(attempt, c, "worker_persisted")
            checkpoint("worker_persisted", c)
        else:
            c["dispatched"] = True
            record(attempt, c, "enqueue_intent")
            checkpoint("enqueue_intent", c)
            atomic(folder / "inbox" / (q["request_id"] + ".json"), wire)
            checkpoint("enqueued", c)
        deadline = started + timeout
        while time.monotonic() < deadline:
            result = inspect_reply(attempt, c, _backend)
            if result is not None:
                return result
            if c["worker_state"] in {"dead", "stale", "unknown"}:
                return error_result(attempt, c, "NATIVE_OUTCOME_UNKNOWN", "Worker exited, changed identity, or became unobservable before reply")
            time.sleep(min(.02, max(0, deadline - time.monotonic())))
        atomic(folder / "UNCERTAIN.json", {"request_id": c["request_id"], "operation_id": c["operation_id"],
                                          "generation": c["generation"], "reason": "Frontend deadline; worker was not cancelled or terminated"})
        return error_result(attempt, c, "JOB_TIMEOUT", "Frontend deadline expired; retain and observe this same attempt")
    except Exception as exc:
        return error_result(attempt if persisted else None, _boundary.get("current", c), "OUTPUT_VALIDATION_FAILED", str(exc))
    finally:
        # Only the live controller releases its own short-lived claim. Abrupt
        # process death leaves the claim for explicit observation, never replay.
        try:
            lock.rmdir()
        except OSError:
            # An unreleased claim blocks further dispatch; never override a receipt.
            pass


def submit(request, state, *, timeout=50, _backend=None, _checkpoint=None):
    """Last producer boundary retains trusted identity even if receipt storage fails."""
    boundary = {}
    try:
        return _submit(request, state, timeout=timeout, _backend=_backend,
                       _checkpoint=_checkpoint, _boundary=boundary)
    except Exception as exc:
        c = boundary.get("current")
        if c is None:
            return preflight_error("request_validation", str(exc))
        c["quarantined"] = bool(c["dispatched"])
        outcome = "known" if c.get("effect_known") else ("unknown" if c["dispatched"] else "none")
        return receipt(c, "outcome_unknown" if outcome == "unknown" else "failed", outcome,
                       "OUTPUT_VALIDATION_FAILED", str(exc))
