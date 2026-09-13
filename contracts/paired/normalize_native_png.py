"""Deterministic display normalization, not a new native render or layout repair.

Keeps dimensions and all native pixels, alpha-composited on fixed white only.
The original native PNG and its hash remain the visual provenance root.
"""
import argparse, hashlib, json
from pathlib import Path
from PIL import Image

def normalize(source, output):
    source,output=Path(source),Path(output)
    if output.exists(): raise ValueError("preserve prior artifact")
    with Image.open(source) as original:
        if original.format != "PNG": raise ValueError("native PNG required")
        rgba=original.convert("RGBA")
        result=Image.alpha_composite(Image.new("RGBA",rgba.size,(255,255,255,255)),rgba).convert("RGB")
        output.parent.mkdir(parents=True,exist_ok=True)
        result.save(output,format="PNG")
    return {"version":"native-png-display-normalization/1.0","operation":"fixed-white alpha composite; no crop, resize, drawing, geometry or text changes", "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(), "output_sha256":hashlib.sha256(output.read_bytes()).hexdigest(), "source_mode":rgba.mode, "output_mode":"RGB", "size":list(result.size), "source_native_render_required":True, "output_is_direct_native_export":False,"original_preserved":True, "human_acceptance":"unmeasured"}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument("source");ap.add_argument("output");ap.add_argument("receipt");a=ap.parse_args()
    r=normalize(a.source,a.output);Path(a.receipt).write_text(json.dumps(r,indent=2)+"\n");print(json.dumps(r))
