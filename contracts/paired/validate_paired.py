"""Fail-closed metadata and byte-binding checks. Does not authenticate native or human claims."""
import argparse, hashlib, json, math, re
from datetime import datetime
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

BASE = Path(__file__).resolve().parent

def validate(kind, record, asset_root=None):
    def finite(value):
        if isinstance(value,float) and not math.isfinite(value): raise ValueError("non-finite measurement")
        if isinstance(value,dict):
            for key,item in value.items():
                if key in ("timestamp","retrieved_at"):
                    if not isinstance(item,str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",item): raise ValueError("timezone-aware timestamp required")
                    if datetime.fromisoformat(item.replace("Z","+00:00")).tzinfo is None: raise ValueError("timestamp timezone missing")
                finite(item)
        elif isinstance(value,list):
            for item in value: finite(item)
    finite(record)
    schema=json.loads((BASE/(kind+".schema.json")).read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(record)
    if kind == "registry":
        if record["frozen_or_descendant"] or any("beckmann" in x.lower() or bool(re.search(r"(?:^|[^a-z0-9])m2(?:$|[^a-z0-9])",x.lower())) or "holdout" in x.lower() for x in [record["sample_id"],record["mechanism_family"],*record["lineage"]]):
            if record["split"] != "excluded": raise ValueError("frozen lineage is excluded from research")
        if record["redistributable"] != record["source"]["redistributable"]: raise ValueError("rights disagreement")
        if record["native_render_available"] and not any(a["role"] == "native_reference_png" for a in record["assets"]): raise ValueError("native render availability requires an asset")
    assets = record.get("assets", [])
    if kind in ("registry","source-manifest"):
        originals = [a for a in assets if a["role"] == "original_target"]
        if len(originals) != 1 or originals[0]["sha256"] != record["source"]["original_sha256"]: raise ValueError("source hash must bind exactly one original target asset")
        container=record["source"]["container"]
        if container:
            if not container["member"] and not container["stream"]: raise ValueError("container requires archive member or direct OLE stream")
            if not any(a["role"] == "source_container" and a["sha256"] == container["sha256"] for a in assets): raise ValueError("source container hash lacks bound asset")
    if kind == "registry":
        roles = {a["role"] for a in assets}
        if record["structured_target_available"] and not any(a["media_type"] in ("chemical/x-cdx","chemical/x-cdxml","text/xml") for a in assets): raise ValueError("structured target claim lacks asset")
        if record["research_status"] == "native_paired" and not {"native_reference_png","native_cdxml","native_cdx","native_receipt"}.issubset(roles): raise ValueError("native-paired state requires render, both formats and receipt")
    if kind == "hidden-split":
        roles = {a["role"] for a in record["generator_input"]}
        allowed = {"reference_png", "runtime_ir_schema"} if record["task"] == "A_png_reconstruction" else {"input_mechanism_ir", "request_text", "runtime_ir_schema"}
        if not roles.issubset(allowed) or not roles: raise ValueError("generator exposure outside task allowlist")
        if record["task"] == "A_png_reconstruction" and sum(a["role"] == "reference_png" for a in record["generator_input"]) != 1: raise ValueError("Task A requires exactly one PNG")
        if record["task"] == "B_blind_composition" and not roles.intersection({"input_mechanism_ir","request_text"}): raise ValueError("Task B lacks semantic input")
        if record["target_geometry_exposed"]: raise ValueError("target geometry exposed")
        hidden = {a["sha256"] for a in record["hidden_target"] if a["role"] != "native_reference_png"}
        if any(a["sha256"] in hidden for a in record["generator_input"]): raise ValueError("hidden bytes exposed")
        run = record["run"]
        if run:
            if not asset_root: raise ValueError("run validation requires actual byte verification")
            hidden_roles={a["role"] for a in record["hidden_target"]}
            if not hidden_roles.intersection({"target_cdx","target_cdxml"}) or not {"target_readback","target_inventory","target_geometry"}.issubset(hidden_roles): raise ValueError("run lacks complete hidden target packet")
            if run["status"] == "completed" and (not isinstance(run["actual_model"],str) or not run["actual_model"].strip()): raise ValueError("completed inference lacks actual model identity")
            if run["status"] == "completed" and not any(a["role"] == "candidate_ir" for a in record["candidate"]): raise ValueError("completed inference lacks candidate IR")
            evidence=record["evaluation"]
            if not any(a["role"] == "model_request_packet" and a["sha256"] == run["exposed_payload_sha256"] for a in evidence): raise ValueError("run payload hash lacks bound packet")
            if not any(a["role"] == "isolation_receipt" and a["sha256"] == run["isolation_receipt_sha256"] for a in evidence): raise ValueError("run isolation hash lacks bound receipt")
            if not record["sealed_before_generation"] or run["target_access_test"] != "pass": raise ValueError("run requires sealed split and actual denial test")
            if run["task"] != record["task"] or run["exposed_assets"] != record["generator_input"]: raise ValueError("run exposure mismatch")
        assets = [a for group in ("generator_input","hidden_target","candidate","evaluation") for a in record[group]]
    if kind == "evaluator":
        if record["correction"]["target_sha256"] != record["target_sha256"] or record["correction"]["candidate_sha256"] != record["candidate_sha256"]: raise ValueError("correction hash binding mismatch")
    correction=record.get("correction") if kind=="evaluator" else record if kind=="correction-delta" else None
    if correction:
        for d in correction["deltas"]:
            angular=d["kind"] in ("fragment_rotation","lp_angular")
            point_kinds={"fragment_translation","atom_displacement","lp_displacement","charge_displacement","caption_displacement","arrow_source_anchor","arrow_target_anchor"}
            if angular:
                if d["unit"]!="radians" or d["value"] is not None and (isinstance(d["value"],bool) or not isinstance(d["value"],(int,float))): raise ValueError("angular delta needs radians")
            elif d["kind"] in point_kinds:
                if d["unit"]!="CDXML points" or not isinstance(d["value"],list) or len(d["value"])!=2 or any(isinstance(x,bool) or not isinstance(x,(int,float)) for x in d["value"]): raise ValueError("displacement requires finite two-vector in CDXML points")
            else: raise ValueError("delta kind reserved but not implemented in prototype")
            if d["frame"] not in ("candidate_to_target_global_rigid","candidate_centroid_to_target_centroid","unaligned_native_global"): raise ValueError("unknown coordinate frame")
    if asset_root:
        root=Path(asset_root).resolve()
        for asset in assets:
            path=(root/asset["relative_locator"]).resolve()
            if not path.is_relative_to(root): raise ValueError("asset escapes corpus root")
            raw=path.read_bytes()
            if len(raw)!=asset["bytes"] or hashlib.sha256(raw).hexdigest()!=asset["sha256"]: raise ValueError("asset bytes/hash mismatch: "+asset["role"])
            if asset["role"] in ("reference_png","native_reference_png"):
                from PIL import Image
                with Image.open(path) as image:
                    if image.format != "PNG": raise ValueError("reference is not PNG")
                    image.verify()
    return {"schema_valid":True,"assets_checked":len(assets) if asset_root else 0,"native_claim_authenticated":False,"human_claim_authenticated":False}

if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("kind"); ap.add_argument("record"); ap.add_argument("--asset-root"); a=ap.parse_args()
    print(json.dumps(validate(a.kind,json.loads(Path(a.record).read_text(encoding="utf-8")),a.asset_root),indent=2))
