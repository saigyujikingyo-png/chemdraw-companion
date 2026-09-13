"""PNG-only API projection broker; CLI is an authentication custodian.

The custodian may run with the user's normal identity and is not claimed to be
OS-isolated. It receives only a neutral staged PNG, public IR schema and generic
prompt. This broker runs under the separate read-restricted Windows identity.
It discards all CLI context/tool definitions and emits one immutable API request.
Authentication headers are passed in memory only, never logged or persisted.
"""
import argparse
import base64
from datetime import datetime, timezone
import http.server
import io
import json
import math
from pathlib import Path
import queue
import secrets
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from firewall import confined_command, json_bytes, sha, toml, require

MODEL = "gpt-5.6-terra"
EFFORT = "max"
UPSTREAM = "https://chatgpt.com/backend-api/codex/responses"
PROMPT = ("Reconstruct the chemistry visible in the attached diagram as Mechanism IR JSON conforming to the supplied schema. "
          "Recover the visible molecular graphs, states, transitions, charges, lone pairs and electron-flow semantics. "
          "Use fresh opaque identifiers. Base chemical content only on the image; do not invent invisible structures. "
          "Return the IR JSON only. Do not return CDXML, drawing coordinates or an explanation.\n\nMechanism IR JSON schema:\n")
INSTRUCTIONS = "Interpret the supplied chemistry diagram and produce the requested JSON representation."
LIMIT = 25000000


def parse(data):
    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result, "duplicate JSON key")
            result[k] = v
        return result
    def nonfinite(value): raise ValueError("nonfinite JSON")
    return json.loads(data.decode("utf-8-sig"), object_pairs_hook=pairs, parse_constant=nonfinite)


def project(png, schema):
    require(png.startswith(b"\x89PNG\r\n\x1a\n") and len(png) <= LIMIT, "bounded PNG required")
    # The source PNG is delivered byte-identically. Pixel/CRC validation is done
    # by the custodian without exposing any sibling target data.
    schema_value = parse(schema)
    require(isinstance(schema_value, dict), "schema object required")
    return {"model": MODEL, "instructions": INSTRUCTIONS,
            "input": [{"role": "user", "content": [
                {"type": "input_text", "text": PROMPT + json.dumps(schema_value, sort_keys=True)},
                {"type": "input_image", "image_url": "data:image/png;base64," + base64.b64encode(png).decode(), "detail": "high"}]}],
            "tools": [], "tool_choice": "none", "parallel_tool_calls": False,
            "reasoning": {"effort": EFFORT}, "text": {"format": {"type": "json_object"}},
            "store": False, "stream": True, "include": ["reasoning.encrypted_content"]}



def project_incoming(png, schema, incoming):
    """Incoming CLI instructions/history/tools cannot affect the approved payload."""
    require(incoming.get("model") == MODEL and incoming.get("reasoning", {}).get("effort") == EFFORT,
            "model/effort mismatch")
    return project(png, schema)


def inspect_stream(data):
    events, completed, done_items = [], None, {}
    for line in data.decode("utf-8").splitlines():
        if not line.startswith("data:"):
            continue
        raw = line[5:].strip()
        if not raw or raw == "[DONE]":
            continue
        event = parse(raw.encode())
        events.append(event)
        def check(value):
            if isinstance(value, dict):
                kind = str(value.get("type", ""))
                require(not ("tool_call" in kind or "function_call" in kind or "custom_tool_call" in kind), "tool call in no-tools response")
                for child in value.values(): check(child)
            elif isinstance(value, list):
                for child in value: check(child)
        check(event)
        if event.get("type") == "response.output_item.done":
            index = event["output_index"]
            require(index not in done_items or done_items[index] == event["item"], "conflicting completed output item")
            done_items[index] = event["item"]
        if event.get("type") == "response.completed":
            completed = event["response"]
    require(completed is not None, "no completed model response")
    require(completed.get("model") in (None, MODEL), "actual model differs from requested model")
    # Codex SSE may omit output from the final response envelope while
    # delivering completed items in earlier events. Preserve both separately.
    output = completed.get("output") or [done_items[i] for i in sorted(done_items)]
    text = "".join(c["text"] for item in output if item.get("type") == "message"
                   for c in item.get("content", []) if c.get("type") == "output_text")
    require(text, "empty model output")
    return {"actual_model": completed.get("model", "unavailable"), "response_id": completed.get("id"),
            "usage": completed.get("usage"), "candidate_text": text, "response": completed,
            "stream_output_items": output, "reasoning_reported": completed.get("reasoning")}


def write_candidate(path, text):
    """Preserve model UTF-8 bytes without platform newline translation."""
    data = text.encode("utf-8")
    with Path(path).open("xb") as stream:
        stream.write(data)
    on_disk = Path(path).read_bytes()
    require(on_disk == data, "candidate serialization changed model bytes")
    return {"model_text_utf8_sha256": sha(data), "candidate_file_sha256": sha(on_disk),
            "candidate_file_bytes": len(on_disk), "candidate_sha256": sha(on_disk)}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("upstream redirects forbidden")


def serve(config_path):
    config = parse(Path(config_path).read_bytes())
    base = Path(config["base"])
    output = Path(config["output"])
    png = (base / "reference.png").read_bytes()
    schema = (base / "mechanism-ir.schema.json").read_bytes()
    require(sha(png) == config["png_sha256"] and sha(schema) == config["schema_sha256"], "staged asset hash changed")
    payload = project(png, schema)
    projected = json_bytes(payload)
    (output / "projected-request.json").write_bytes(projected)
    receipt = {"version": "paired-generator-receipt/1.0", "status": "prepared", "model_requested": MODEL,
               "reasoning_requested": EFFORT, "actual_model": "unavailable", "timestamp": datetime.now(timezone.utc).isoformat(),
               "model_called": False, "projected_request_sha256": sha(projected),
               "exposed_assets": [{"name": "reference.png", "bytes": len(png), "sha256": sha(png)},
                                  {"name": "mechanism-ir.schema.json", "bytes": len(schema), "sha256": sha(schema)}],
               "generic_prompt": PROMPT, "instructions": INSTRUCTIONS,
               "custody": "CLI authenticates but its context is discarded. Sandboxed broker forwards only frozen PNG/schema/generic prompt; remote model receives no tools.",
               "auth_persisted": False, "calls_allowed": 1}
    (output / "generator-receipt.json").write_bytes(json_bytes(receipt))
    state = {"claimed": False}
    gate = threading.Lock()
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def reply(self, status, data, kind="application/json"):
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        def do_GET(self):
            # Never forwards discovery, history, account or arbitrary API reads.
            self.reply(404, b'{"error":{"message":"projection broker has no discovery API"}}')
        def do_POST(self):
            try:
                require(self.path == "/" + config["ticket"] + "/responses", "unknown broker endpoint")
                length = int(self.headers.get("Content-Length", "0"))
                require(0 < length <= LIMIT, "bounded request body required")
                incoming = parse(self.rfile.read(length))
                require(json_bytes(project_incoming(png, schema, incoming)) == projected, "projection changed")
                with gate:
                    require(not state["claimed"], "one initial inference only")
                    state["claimed"] = True
                # No source text, tool definitions, paths, history or metadata
                # from incoming is copied into the outgoing request.
                receipt["incoming_context_discarded"] = True
                receipt["authorization_present"] = bool(self.headers.get("Authorization"))
                receipt["projected_tool_count"] = len(payload["tools"])
                if config["dry_run"]:
                    receipt.update(status="projection_dry_run_pass", model_called=False)
                    (output / "generator-receipt.json").write_bytes(json_bytes(receipt))
                    self.reply(400, b'{"error":{"message":"projection dry run complete; no upstream model called","type":"invalid_request_error"}}')
                    return
                authorization = self.headers.get("Authorization")
                require(authorization and authorization.startswith("Bearer "), "existing CLI authentication missing")
                headers = {"Authorization": authorization, "Content-Type": "application/json", "Accept": "text/event-stream"}
                # These operational headers are custody-only, never model input.
                for name in ("ChatGPT-Account-Id", "OpenAI-Beta", "originator", "User-Agent"):
                    if self.headers.get(name): headers[name] = self.headers[name]
                require(config["upstream"] == UPSTREAM, "non-allowlisted upstream")
                receipt.update(status="upstream_requested", model_called=True)
                (output / "generator-receipt.json").write_bytes(json_bytes(receipt))
                request = urllib.request.Request(UPSTREAM, data=projected, headers=headers, method="POST")
                opener = urllib.request.build_opener(NoRedirect())
                try:
                    with opener.open(request, timeout=600) as response:
                        data = response.read(LIMIT + 1)
                        require(len(data) <= LIMIT, "response budget exceeded")
                except urllib.error.HTTPError as exc:
                    data = exc.read(100000)
                    (output / "upstream-error-body.txt").write_bytes(data)
                    receipt.update(status="upstream_failed", http_status=exc.code)
                    (output / "generator-receipt.json").write_bytes(json_bytes(receipt))
                    self.reply(exc.code, data)
                    return
                # Buffer and inspect before the CLI sees any response, so a
                # hallucinated tool request is never executed by the custodian.
                (output / "response.sse").write_bytes(data)
                observed = inspect_stream(data)
                candidate_binding = write_candidate(output / "candidate.ir.json", observed["candidate_text"])
                (output / "response.json").write_bytes(json_bytes(observed["response"]))
                (output / "response-output-items.json").write_bytes(json_bytes(observed["stream_output_items"]))
                receipt.update(status="model_response_received", actual_model=observed["actual_model"],
                               response_id=observed["response_id"], usage=observed["usage"],
                               reasoning_reported=observed["reasoning_reported"],
                               response_sha256=sha(data), **candidate_binding,
                               candidate_validation="not_yet_validated")
                (output / "generator-receipt.json").write_bytes(json_bytes(receipt))
                self.reply(200, data, "text/event-stream")
            except Exception as exc:
                # Authentication is never included in exceptions or receipts.
                receipt.update(status="blocked", error_type=type(exc).__name__, error=str(exc))
                (output / "generator-receipt.json").write_bytes(json_bytes(receipt))
                self.reply(400, json_bytes({"error": {"message": str(exc), "type": "invalid_request_error"}}))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    print(json.dumps({"ready": True, "port": server.server_port}), flush=True)
    server.serve_forever(poll_interval=.2)


def launch(codex, python, png, schema, out, forbidden=(), dry_run=True):
    out = Path(out).resolve()
    require(not out.exists(), "refusing existing output")
    # This function receives one PNG path; it never lists that path's siblings.
    png_data = Path(png).read_bytes()
    schema_data = Path(schema).read_bytes()
    from PIL import Image
    with Image.open(io.BytesIO(png_data)) as image:
        require(image.format == "PNG", "reference must be PNG")
        image.verify()
    project(png_data, schema_data)
    inp, output = out / "generator_input", out / "candidate"
    inp.mkdir(parents=True)
    output.mkdir()
    (inp / "reference.png").write_bytes(png_data)
    (inp / "mechanism-ir.schema.json").write_bytes(schema_data)
    require((inp / "reference.png").read_bytes() == png_data, "PNG copy changed")
    ticket = secrets.token_hex(24)
    config = {"base": str(inp), "output": str(output), "ticket": ticket, "dry_run": dry_run,
              "upstream": UPSTREAM, "png_sha256": sha(png_data), "schema_sha256": sha(schema_data)}
    config_path = out / "broker-config.json"
    config_path.write_bytes(json_bytes(config))
    instructions = out / "generic-instructions.txt"
    instructions.write_text(INSTRUCTIONS, encoding="utf-8")
    code = Path(__file__).resolve()
    python = Path(python).resolve()
    args = confined_command(codex, [python, "-B", code, "--worker", config_path], inp,
        [inp, config_path, code, code.with_name("firewall.py"), python.parent], writable=[output], forbidden=forbidden, network=True)
    broker = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                              errors="replace", creationflags=subprocess.CREATE_NO_WINDOW)
    readiness = queue.Queue()
    threading.Thread(target=lambda: readiness.put(broker.stdout.readline()), daemon=True).start()
    try:
        ready = parse(readiness.get(timeout=20).encode())
        require(ready.get("ready"), "broker not ready")
        provider = {"name": "Paired PNG-only projection", "base_url": "http://127.0.0.1:" + str(ready["port"]) + "/" + ticket,
                    "wire_api": "responses", "requires_openai_auth": True, "supports_websockets": False,
                    "request_max_retries": 0, "stream_max_retries": 0, "stream_idle_timeout_ms": 900000}
        cli = [str(codex), "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral", "--skip-git-repo-check",
               "--json", "-C", str(inp), "-m", MODEL, "--image", str(inp / "reference.png")]
        overrides = {"model_provider": "paired_projection", "model_providers.paired_projection": provider,
                     "model_reasoning_effort": EFFORT, "approval_policy": "never", "project_doc_max_bytes": 0,
                     "developer_instructions": "", "web_search": "disabled", "mcp_servers": {},
                     "model_instructions_file": str(instructions), "log_dir": str(output / "cli-logs"),
                     "default_permissions": "paired-model-tools",
                     "permissions.paired-model-tools.filesystem": {":root": "deny", ":minimal": "read", str(inp): "read"},
                     "permissions.paired-model-tools.network.enabled": False}
        for k, v in overrides.items(): cli += ["-c", k + "=" + toml(v)]
        for feature in ("shell_tool", "unified_exec", "apps", "plugins", "memories", "hooks", "skill_search",
                        "browser_use", "computer_use", "image_generation", "multi_agent", "goals", "sleep_tool",
                        "workspace_dependencies", "view_image", "code_mode_host", "shell_snapshot"):
            cli += ["--disable", feature]
        # Actual model input is rebuilt by broker; even this instruction is not
        # trusted as the projection source. No history is resumed.
        cli += ["Reconstruct the attached diagram using the supplied Mechanism IR schema."]
        (out / "custodian-command.json").write_bytes(json_bytes(cli))
        result = subprocess.run(cli, input="", capture_output=True, text=True, encoding="utf-8", errors="replace",
                                timeout=850, creationflags=subprocess.CREATE_NO_WINDOW)
        (output / "custodian-events.jsonl").write_text(result.stdout, encoding="utf-8")
        (output / "custodian-stderr.txt").write_text(result.stderr, encoding="utf-8")
        return {"custodian_returncode": result.returncode, "receipt": str(output / "generator-receipt.json"),
                "broker_command": args, "dry_run": dry_run}
    finally:
        broker.terminate()
        _, stderr = broker.communicate(timeout=10)
        (output / "broker-stderr.txt").write_text(stderr, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--png", type=Path)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--forbid", type=Path, action="append", default=[])
    parser.add_argument("--real-model", action="store_true", help="One explicitly authorized inference; default is local dry run")
    args = parser.parse_args()
    if args.worker:
        serve(args.worker)
    else:
        require(all((args.codex, args.png, args.schema, args.out)), "codex/png/schema/out are required")
        result = launch(args.codex, args.python, args.png, args.schema, args.out, args.forbid, not args.real_model)
        (args.out / "launch-receipt.json").write_bytes(json_bytes(result))
        print(json.dumps(result))


if __name__ == "__main__":
    main()
