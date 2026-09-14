"""Offline output-contract checks only; no MCP server, native calls or specimens."""
import copy
import hashlib
import json
import math
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

HERE = Path(__file__).resolve().parent
CONTRACTS = HERE.parent
PREFIX = "urn:chembridge:chemdraw:output:"


def load():
    index = json.loads((HERE / "registry.json").read_text())
    resources = {
        row["id"]: json.loads((HERE / row["path"]).read_text())
        for row in index["resources"]
    }
    catalog = json.loads((CONTRACTS / "mcp-tools.json").read_text())
    for tool in catalog["tools"]:
        schema = tool["outputSchema"]
        resources[schema["$id"]] = schema
    registry = Registry().with_resources(
        (key, Resource.from_contents(value)) for key, value in resources.items()
    )
    return catalog, resources, registry


def validate(value, schema, registry):
    def finite(item):
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("Non-finite JSON value")
        if isinstance(item, dict):
            for entry in item.values():
                finite(entry)
        elif isinstance(item, list):
            for entry in item:
                finite(entry)
    finite(value)
    Draft202012Validator(schema, registry=registry,
                         format_checker=FormatChecker()).validate(value)


def validate_mcp(result, schema, registry):
    """Contract test helper, not a wired production/server validator."""
    payload = result["structuredContent"]
    validate(payload, schema, registry)
    if result["isError"] != (not payload["ok"]):
        raise ValueError("isError contradicts operation ok")
    fallbacks = [c["text"] for c in result["content"] if c["type"] == "text"]
    if not fallbacks or json.loads(fallbacks[0]) != payload:
        raise ValueError("JSON text fallback differs from structuredContent")


def main():
    catalog, resources, registry = load()
    for schema in resources.values():
        Draft202012Validator.check_schema(schema)
    outcomes = []

    def check(name, fn, accepted=True):
        try:
            fn()
            actual = True
        except (ValueError, KeyError, TypeError) as error:
            actual = False
        except Exception as error:
            # ValidationError is expected only for deliberately invalid examples.
            if type(error).__name__ != "ValidationError":
                raise
            actual = False
        if actual != accepted:
            raise AssertionError(name)
        outcomes.append({"case": name, "expected_valid": accepted,
                         "result": "pass"})

    def payload(data):
        return {"contract_version": "1.0", "request_id": "request-control",
                "ok": True, "data": data, "warnings": [], "error": None}

    def error(outcome="none"):
        return {"code": "OUTPUT_VALIDATION_FAILED", "message": "Invalid result",
                "stage": "result_validation", "retryable": False,
                "mutation_outcome": outcome, "evidence_ids": [],
                "next_action": "Inspect existing operation; do not repeat write",
                "operation_id": "operation-control"}

    def mcp(value):
        return {"structuredContent": value, "isError": not value["ok"],
                "content": [{"type": "text", "text": json.dumps(value)}]}

    schemas = {t["name"]: t["outputSchema"] for t in catalog["tools"]}
    run = payload({"job_id": "job-control", "session_id": "session-control",
                   "state": "queued", "revision": None, "poll_after_ms": 100})
    for state in ["queued", "running", "blocked", "cancelled", "outcome_unknown"]:
        sample = copy.deepcopy(run)
        sample["data"]["state"] = state
        check("run-current-state-" + state,
              lambda s=sample: validate_mcp(mcp(s), schemas["chemdraw_run"], registry))
    failure = payload(None)
    failure.update(ok=False, error=error("unknown"))
    for tool, schema in schemas.items():
        check(tool + "-error-with-known-operation",
              lambda s=schema: validate_mcp(mcp(failure), s, registry))
        bad = copy.deepcopy(failure)
        bad["data"] = {}
        check(tool + "-error-data-not-null",
              lambda s=schema, b=bad: validate(b, s, registry), False)
    check("missing-structuredContent",
          lambda: validate_mcp({"content": [], "isError": False},
                               schemas["chemdraw_run"], registry), False)
    bad = mcp(run); bad["isError"] = True
    check("isError-mismatch",
          lambda: validate_mcp(bad, schemas["chemdraw_run"], registry), False)
    bad = mcp(run); bad["content"][0]["text"] = "{}"
    check("text-fallback-mismatch",
          lambda: validate_mcp(bad, schemas["chemdraw_run"], registry), False)
    bad = copy.deepcopy(run); del bad["data"]["revision"]
    check("omitted-revision", lambda: validate(bad, schemas["chemdraw_run"], registry), False)
    bad = copy.deepcopy(run); bad["data"]["state"] = "succeeded"
    check("success-null-revision", lambda: validate(bad, schemas["chemdraw_run"], registry), False)
    bad = copy.deepcopy(failure); bad["error"]["retryable"] = True
    check("unknown-mutation-not-retryable",
          lambda: validate(bad, schemas["chemdraw_run"], registry), False)
    bad = copy.deepcopy(failure)
    bad["error"].update(code="NATIVE_OUTCOME_UNKNOWN", mutation_outcome="none", retryable=True)
    check("native-unknown-code-is-not-no-write",
          lambda: validate(bad, schemas["chemdraw_run"], registry), False)
    status = payload({"product_id": "chembridge.chemdraw-companion",
                      "runtime_state": "uninitialized", "observed_at": "2026-09-14T00:00:00Z",
                      "identity": {"product_version": None, "broker_version": None,
                                   "addin_version": None, "application_build": None,
                                   "unavailable_reason": "Not initialized"},
                      "queue": {"pending_count": None, "state": "unavailable"},
                      "capabilities": [], "next_cursor": None})
    check("status-uninitialized-no-invented-version",
          lambda: validate_mcp(mcp(status), schemas["chemdraw_status"], registry))
    bad = copy.deepcopy(status); bad["data"]["next_cursor"] = "undispatchable"
    check("status-does-not-invent-cursor-input",
          lambda: validate(bad, schemas["chemdraw_status"], registry), False)
    help_result = payload({"topic": "capability", "items": [
        {"item_id": "output:save", "summary": "On-demand output schema",
         "schema_id": PREFIX + "edit-result:0.2-draft.1"}], "next_cursor": None})
    check("help-on-demand-schema", lambda: validate_mcp(mcp(help_result), schemas["chemdraw_help"], registry))
    artifact = {"artifact_id": "artifact-control", "file_name": "control.png",
                "media_type": "image/png", "bytes": 0, "sha256": None,
                "unavailable_metadata": ["sha256"], "role": "native_render",
                "producer": "synthetic metadata control; not native evidence",
                "source_artifact_id": None, "delivery_status": "available",
                "evidence_ids": []}
    artifact_result = payload({"artifact": artifact, "delivery_attempt_id": None,
                               "destination_id": None, "next_action": "Request delivery"})
    check("artifact-zero-is-distinct-from-null",
          lambda: validate_mcp(mcp(artifact_result), schemas["chemdraw_artifact"], registry))
    bad = copy.deepcopy(artifact_result)
    bad["data"]["artifact"]["unavailable_metadata"] = []
    check("unknown-hash-needs-explicit-status",
          lambda: validate(bad, schemas["chemdraw_artifact"], registry), False)
    bad = copy.deepcopy(artifact_result)
    bad["data"]["artifact"]["delivery_status"] = "receipt_verified"
    check("delivery-needs-evidence",
          lambda: validate(bad, schemas["chemdraw_artifact"], registry), False)
    gates = {k: {"status": "unverified", "evidence_ids": [], "reason": "Not measured"}
             for k in ["native_execution", "chemical_semantics", "layout_geometry",
                       "native_editability", "visual_review", "owner_acceptance", "host_receipt"]}
    job = payload({"job_id": "job-control", "session_id": "session-control",
                   "state": "failed", "stage": "preflight", "event_cursor": "event-control",
                   "revision": None, "cancellation_requested": False, "artifacts": [],
                   "gates": gates, "error": error()})
    # Existing job-data/1.0 has its original error fields; do not rewrite it.
    del job["data"]["error"]["operation_id"]
    check("successful-inspection-of-failed-job",
          lambda: validate_mcp(mcp(job), schemas["chemdraw_job"], registry))
    bad = copy.deepcopy(job); bad["data"]["error"] = None
    check("failed-job-needs-error", lambda: validate(bad, schemas["chemdraw_job"], registry), False)
    bad = copy.deepcopy(job); bad["data"]["gates"]["native_execution"]["status"] = "pass"
    check("job-pass-needs-evidence", lambda: validate(bad, schemas["chemdraw_job"], registry), False)
    bad = copy.deepcopy(job)
    bad["data"]["error"].update(code="NATIVE_OUTCOME_UNKNOWN", mutation_outcome="unknown", retryable=True)
    check("job-unknown-cannot-hide-as-failed-retry",
          lambda: validate(bad, schemas["chemdraw_job"], registry), False)
    bad["data"]["error"]["retryable"] = False
    check("job-unknown-needs-unknown-state",
          lambda: validate(bad, schemas["chemdraw_job"], registry), False)
    good_unknown = copy.deepcopy(bad); good_unknown["data"]["state"] = "outcome_unknown"
    check("job-unknown-preserves-stable-job", lambda: validate(good_unknown, schemas["chemdraw_job"], registry))
    edit_schema = resources[PREFIX + "edit-result:0.2-draft.1"]
    gate = {"status": "unverified", "evidence_ids": [], "reason": "Not measured"}
    edit = {"result_version": "agent-edit-result/0.2-draft.1",
            "operation": "relative-position", "request_id": "request-control",
            "operation_id": "operation-control", "session_id": "session-control",
            "document_id": "document-control", "revision": 2, "status": "completed",
            "mutation_outcome": "known", "error": None, "session_state": "active",
            "preservation": "target_change_verified", "native_render": gate,
            "desktop_display": gate, "observed_at": "2026-09-14T00:00:00Z",
            "evidence_ids": ["evidence-control"], "artifacts": [],
            "observation_ref": "observation-control",
            "details": {"caption_ref": "caption-control", "arrow_ref": "arrow-control",
                        "intent": "up-half-bond", "delta_pt": [0, -9],
                        "bond_length_pt": 18, "comparison_evidence_id": "evidence-control"}}
    check("edit-relative-document-units", lambda: validate(edit, edit_schema, registry))
    bad = copy.deepcopy(edit); bad["details"]["delta_pt"] = [0, float("nan")]
    check("nonfinite-coordinate", lambda: validate(bad, edit_schema, registry), False)
    bad = copy.deepcopy(edit); bad["details"]["screen_x"] = 12
    check("screen-coordinate-not-contract", lambda: validate(bad, edit_schema, registry), False)
    unknown = copy.deepcopy(edit)
    unknown.update(status="outcome_unknown", mutation_outcome="unknown", error=error("unknown"),
                   preservation="unverified", details={"reason": "Malformed backend after dispatch",
                   "recovery_action": "Reconcile existing operation", "candidates_ref": None})
    check("bad-backend-preserves-operation-identity", lambda: validate(unknown, edit_schema, registry))
    bad = copy.deepcopy(unknown); bad["status"] = "completed"
    check("unknown-not-success", lambda: validate(bad, edit_schema, registry), False)
    bad = copy.deepcopy(unknown); bad["mutation_outcome"] = "none"
    check("unknown-outcome-consistent", lambda: validate(bad, edit_schema, registry), False)
    bad = copy.deepcopy(unknown); bad["operation_id"] = None
    check("unknown-keeps-assigned-operation", lambda: validate(bad, edit_schema, registry), False)
    pending = copy.deepcopy(unknown)
    pending.update(status="pending", mutation_outcome="none", error=None, session_state="ending")
    check("pending-close-is-not-error-or-closed", lambda: validate(pending, edit_schema, registry))
    binding = {"pid": 101, "start_utc": "2026-09-14T00:00:00Z", "hwnd": "1001",
               "document_id": "document-control"}
    completed_details = {
        "open-copy": {"source_sha256": "a" * 64, "original_unchanged": True, "binding": binding},
        "inspect": {"binding": binding, "closure_receipt_id": None, "candidates_ref": None},
        "save": {"saved_revision": 2, "comparison_evidence_id": "comparison-control"},
        "reopen": {"previous_binding": binding,
                   "current_binding": {**binding, "pid": 102, "document_id": "document-new"},
                   "reopened_artifact_id": "artifact-control", "comparison_evidence_id": "comparison-control"},
    }
    for operation, details in completed_details.items():
        sample = copy.deepcopy(edit); sample.update(operation=operation, details=details)
        check(operation + "-bounded-details", lambda s=sample: validate(s, edit_schema, registry))
        bad = copy.deepcopy(sample); bad["details"] = {}
        check(operation + "-empty-details-refuse", lambda b=bad: validate(b, edit_schema, registry), False)
    for state, count in [("observed", None), ("unavailable", 0)]:
        bad = copy.deepcopy(status); bad["data"]["queue"] = {"state": state, "pending_count": count}
        check("queue-null-semantics-" + state,
              lambda b=bad: validate(b, schemas["chemdraw_status"], registry), False)
    bad = copy.deepcopy(status)
    bad["data"]["capabilities"] = [{"id": "caption", "status": "native_verified", "scope": "control", "evidence_ids": []}]
    check("native-capability-needs-evidence", lambda: validate(bad, schemas["chemdraw_status"], registry), False)
    # Input schemas and the historical job-data artifact must not change.
    check("run-input-schema-still-original",
          lambda: (_ for _ in ()).throw(ValueError()) if
          next(t["inputSchema"] for t in catalog["tools"] if t["name"] == "chemdraw_run") !=
          json.loads((CONTRACTS / "run-request.schema.json").read_text()) else None)
    print(json.dumps({"scope": "offline synthetic contract checks; no server/native/host execution",
                      "checks": outcomes, "passed": len(outcomes),
                      "schema_bytes_utf8": {k: len(json.dumps(v, separators=(",", ":")).encode())
                                             for k, v in resources.items()},
                      "billed_tokens": None, "billing_status": "unavailable"}, indent=2))


if __name__ == "__main__":
    main()
