"""Evaluator-side CDXML inventory. Never import this module in a generator process."""
from __future__ import annotations
import argparse, hashlib, json, math, re
from pathlib import Path
import xml.etree.ElementTree as ET

VERSION = "paired-native-inventory/1.0"
GEOMETRY = {"p", "xyz", "BoundingBox", "CurvePoints", "Head3D", "Tail3D", "Center3D", "MajorAxisEnd3D", "MinorAxisEnd3D"}
PRIMITIVES = {"n", "b", "fragment", "curve", "arrow", "graphic", "t", "scheme", "step", "bracketedgroup", "geometry", "constraint"}

def numbers(value):
    values = [float(v) for v in value.split()]
    if not all(math.isfinite(v) for v in values):
        raise ValueError("non-finite geometry")
    return values

def extract(path):
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) > 32 * 1024 * 1024:
        raise ValueError("bounded extractor: file exceeds 32 MiB")
    # ChemDraw DOCTYPE is normal; entity definitions are not required by this prototype.
    if b"<!ENTITY" in raw.upper():
        raise ValueError("entity declarations are forbidden")
    root = ET.fromstring(raw)
    if root.tag.split("}")[-1] != "CDXML":
        raise ValueError("expected CDXML root; CDX requires native conversion")
    objects, warnings, ids = [], [], set()
    native_nodes = {n.get("id"):n for n in root.iter() if n.get("id")}
    def walk(node, parents, page):
        tag = node.tag.split("}")[-1]
        page = node.get("id", page) if tag == "page" else page
        ident = node.get("id")
        if ident:
            if ident in ids:
                raise ValueError("duplicate native object id: " + ident)
            ids.add(ident)
        if tag in PRIMITIVES:
            geometry = {}
            for key in GEOMETRY.intersection(node.attrib):
                try:
                    geometry[key] = numbers(node.attrib[key])
                except ValueError:
                    warnings.append({"object_id": ident, "attribute": key, "reason": "unparsed geometry"})
            has_head = any(node.get(k) not in (None, "", "None", "0") for k in ("ArrowheadHead", "ArrowheadTail", "ArrowType"))
            try:
                # Vendor Curve_Type SDK: bits 8/16/32/64 indicate full/half heads.
                has_head = has_head or tag == "curve" and bool(int(node.get("CurveType", "0")) & 120)
                angle = float(node.get("AngularSize", "0"))
                if not math.isfinite(angle): raise ValueError("non-finite angle")
                angular = abs(angle) > 1e-12
            except ValueError:
                angular = False
                warnings.append({"object_id":ident,"attribute":"CurveType/AngularSize","reason":"unparsed arrow classification"})
            successor = node.get("SupersededBy")
            valid_successor = successor in native_nodes and successor != ident and native_nodes[successor].tag.split("}")[-1] == "arrow" and not native_nodes[successor].get("SupersededBy")
            if successor and not valid_successor:
                warnings.append({"object_id":ident,"attribute":"SupersededBy","reason":"unresolved or unsupported supersession; retained candidate"})
            is_curved_arrow = has_head and (tag == "curve" or tag == "arrow" and angular or tag == "graphic" and node.get("GraphicType") == "Arc") and not valid_successor
            objects.append({"id": ident, "tag": tag, "parents": list(parents), "page": page,
                "attributes": dict(node.attrib), "geometry": geometry,
                "text": "".join(node.itertext()) if tag == "t" else None,
                "curved_arrow_candidate": is_curved_arrow,
                "semantic_source": None, "semantic_sink": None})
        for child in node:
            walk(child, parents + ([ident] if ident else []), page)
    walk(root, [], None)
    count = lambda pred: sum(bool(pred(o)) for o in objects)
    atom_charge = count(lambda o: o["tag"] == "n" and o["attributes"].get("Charge", "0") != "0")
    lp = count(lambda o: o["attributes"].get("SymbolType") == "LonePair")
    profile = {"atom_count": count(lambda o: o["tag"] == "n"), "bond_count": count(lambda o: o["tag"] == "b"),
        "fragment_count": count(lambda o: o["tag"] == "fragment"), "curve_count": count(lambda o: o["tag"] == "curve"),
        "curved_arrow_candidate_count": count(lambda o: o["curved_arrow_candidate"]),
        "confirmed_electron_flow_count": None, "lone_pair_object_count": lp,
        "charged_atom_count": atom_charge, "charge_symbol_count": count(lambda o: o["attributes"].get("SymbolType") in ("Plus", "Minus", "CirclePlus", "CircleMinus", "CircledPlus", "CircledMinus")),
        "radical_object_count": count(lambda o: o["attributes"].get("SymbolType") in ("Electron", "RadicalAnion", "RadicalCation") or o["attributes"].get("Radical", "0") not in ("0", "None")),
        "caption_object_count": count(lambda o: o["tag"] == "t"), "explicit_scheme_step_count": count(lambda o: o["tag"] == "step"),
        "state_count": None, "step_count": None, "condition_text_present": None,
        "simultaneous_flow_count": None, "common_scaffold_count": None, "dense_anchor_risk": None, "multirow": None, "snake_layout": None}
    return {"version": VERSION, "source_sha256": hashlib.sha256(raw).hexdigest(), "source_bytes": len(raw),
        "root_attributes": dict(root.attrib), "objects": objects, "complexity_profile": profile,
        "warnings": warnings, "native_execution_verified": False,
        "limits": ["XML inventory is not native editability", "curve arrowheads are candidates, not verified electron flows", "text includes atom labels; condition roles need verification", "visible arrowhead tips require native render measurement", "no inferred state or electron-flow binding is ground truth"]}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("output")
    a = ap.parse_args(); result = extract(a.input)
    Path(a.output).write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
