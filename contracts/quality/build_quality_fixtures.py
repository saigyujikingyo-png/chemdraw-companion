"""Deterministic pixel controls, not ChemDraw runs or chemically complete drawings.

Uses only the existing public proton-transfer design IR. Each case is an isolated
visual metric control, not a complete native mechanism. No M2/holdout input is
accepted. Expected outcomes in the index are test intentions, not review records.
"""
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
IR_FILE = HERE.parents[1] / "examples" / "corpus" / "proton-transfer.ir.json"
STYLE = {"font_family": "Arial", "font_pt": 8.0, "bond_pt": 14.4,
         "stroke_pt": 0.6, "head_size": 650, "head_width": 163,
         "head_center_size": 569, "head_type": "Solid", "head": "Full",
         "tail": "None", "curve_type": "8"}
NATIVE_BUILD = "synthetic-fixture/not-a-native-execution"
SIZE = (320, 200)
METRICS = ("visible_tip_target", "visible_tail_source", "lone_pair_orientation",
           "ink_clearance", "curve_bend_severity", "head_glyph_overlap",
           "step_spacing", "common_scaffold")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def png_bytes(im):
    buffer = io.BytesIO()
    im.save(buffer, format="PNG", optimize=False, compress_level=9)
    return buffer.getvalue()


def layer(draw):
    im = Image.new("RGBA", SIZE, (255, 255, 255, 0))
    draw(ImageDraw.Draw(im))
    return im


def dots(points):
    return layer(lambda d: [d.ellipse((x-2, y-2, x+2, y+2), fill="black") for x, y in points])


def plus(x, y):
    return layer(lambda d: (d.line((x-4, y, x+4, y), fill="black", width=2),
                            d.line((x, y-4, x, y+4), fill="black", width=2)))


def arrow(path=None, tip=(160, 70)):
    path = path or [(40, 70), (90, 70), (tip[0]-20, tip[1])]
    head = layer(lambda d: d.polygon([tip, (tip[0]-20, tip[1]-6),
                                     (tip[0]-20, tip[1]+6)], fill="black"))
    shaft = layer(lambda d: d.line(path, fill="black", width=3))
    return {"arrow": Image.alpha_composite(shaft, head), "head": head}


def object_row(oid, kind, semantic_ref, state="before"):
    return {"id": oid, "kind": kind, "state_ref": state, "semantic_refs": [semantic_ref]}


def flow_objects():
    return [object_row("arrow", "arrow", "make_OH"),
            object_row("head", "arrowhead", "make_OH")]


def locked_measurement(measurement):
    m = copy.deepcopy(measurement)
    for key in {"visible_tip_target": ("arrow_object", "head_object"),
                "visible_tail_source": ("arrow_object", "head_object"),
                "lone_pair_orientation": ("lp_object",),
                "curve_bend_severity": ("arrow_object", "head_object", "centerline")}.get(m["metric"], ()):
        m.pop(key)
    return m


def controls():
    """Explicit synthetic geometry; never a mechanism Composer or native adapter."""
    rows = []

    def add(name, metric, expected, images, objects, fields, pp=4):
        rows.append({"name": name, "metric": metric, "expected": expected,
                     "images": images, "objects": objects, "pixels_per_pt": pp,
                     "measurement": {"id": "measurement", "metric": metric, **fields}})

    tip_fields = {"flow_ref": "make_OH", "arrow_object": "arrow", "head_object": "head",
                  "target": {"entity_ref": "before:a4", "point": [160, 70]}}
    add("tip-positive", METRICS[0], "pass", arrow(), flow_objects(), tip_fields)
    add("tip-displaced", METRICS[0], "fail", arrow(tip=(192, 70)), flow_objects(), tip_fields)
    for suffix, transformed, point, pp in (
        ("rotated", {k: im.transpose(Image.Transpose.ROTATE_270) for k, im in arrow().items()}, [129, 160], 4),
        ("scaled", {k: im.resize((640, 400), Image.Resampling.NEAREST) for k, im in arrow().items()}, [320, 140], 8)):
        fields = copy.deepcopy(tip_fields)
        fields["target"]["point"] = point
        add("tip-" + suffix, METRICS[0], "unmeasured" if suffix == "scaled" else "pass", transformed, flow_objects(), fields, pp)
    tail_fields = {"flow_ref": "make_OH", "arrow_object": "arrow", "head_object": "head",
                   "source": {"entity_ref": "before:lp1:0", "point": [40, 70]}}
    add("tail-positive", METRICS[1], "pass", arrow(), flow_objects(), tail_fields)
    add("tail-wrong-source", METRICS[1], "fail", arrow([(68, 70), (100, 70), (140, 70)]), flow_objects(), tail_fields)
    lp_fields = {"lp_ref": "before:lp1:0", "lp_object": "lp", "atom_point": [80, 78],
                 "local_axis": [1, 0], "expected_radial_deg": 315, "expected_dot_deg": 0,
                 "allowed_quadrants": [4]}
    lp_objects = [object_row("lp", "lone_pair", "before:lp1:0")]
    for name, points, expected in (("lp-positive", [(100, 48), (120, 48)], "pass"),
                                   ("lp-wrong-quadrant", [(40, 108), (60, 108)], "fail"),
                                   ("lp-wrong-dot-axis", [(110, 38), (110, 58)], "fail")):
        add(name, METRICS[2], expected, {"lp": dots(points)}, lp_objects, lp_fields)
    charged = flow_objects() + [object_row("charge", "charge", "before:q2")]
    for name, x, expected in (("ink-positive", 200, "pass"), ("ink-near-charge", 165, "fail")):
        add(name, METRICS[3], expected, {**arrow(), "charge": plus(x, 70)}, charged,
            {"objects": ["head", "charge"]})
    for name, path, expected in (("bend-positive", [(40, 70), (90, 70), (140, 70)], "pass"),
                                 ("bend-excessive", [(40, 150), (40, 30), (140, 30), (140, 70)], "fail")):
        add(name, METRICS[4], expected, arrow(path), flow_objects(),
            {"flow_ref": "make_OH", "arrow_object": "arrow", "head_object": "head", "centerline": path})
    for name, x, expected in (("overlap-positive", 185, "pass"), ("overlap-charge", 155, "fail")):
        add(name, METRICS[5], expected, {**arrow(), "charge": plus(x, 70)}, charged,
            {"head_object": "head", "glyph_object": "charge"})
    # Text shapes are deliberately untyped captions, bound only to the state.
    # In particular, "Br" is not a Br atom and does not change the chemical IR.
    for name, text, position, tested_object in (
        ("ink-shaft-through-caption", "heat", (80, 63), "arrow"),
        ("ink-head-near-br-caption", "Br", (162, 63), "head")):
        caption = layer(lambda d: d.text(position, text, fill="black"))
        add(name, METRICS[3], "fail", {**arrow(), "caption": caption},
            flow_objects() + [object_row("caption", "caption", "before")],
            {"objects": [tested_object, "caption"]})
        rows[-1]["note"] = ("Partial synthetic pixel control. Text is an untyped caption with state-only binding; "
                            "Br lettering is not a chemical atom or a complete chemical diagram.")
    step_objects = [object_row("before-group", "label", "before:a1"),
                    object_row("after-group", "label", "after:a1", "after")]
    for name, x, expected in (("spacing-positive", 120, "pass"), ("spacing-too-close", 75, "fail")):
        images = {"before-group": layer(lambda d: d.rectangle((30, 130, 65, 150), fill="black")),
                  "after-group": layer(lambda d: d.rectangle((x, 130, x+35, 150), fill="black"))}
        add(name, METRICS[6], expected, images, step_objects,
            {"from_state": "before", "to_state": "after", "axis": [1, 0],
             "from_objects": ["before-group"], "to_objects": ["after-group"]})
    before = [(30, 120), (60, 120), (30, 150)]
    for name, after, expected in (("scaffold-positive", [(190, 120), (220, 120), (190, 150)], "pass"),
                                  ("scaffold-mirrored", [(220, 120), (190, 120), (220, 150)], "fail"),
                                  ("scaffold-scaled", [(190, 120), (244, 120), (190, 174)], "fail")):
        images, objects, pairs = {}, [], []
        for aid, p, q in zip(("a2", "a5", "a6"), before, after):
            for state, point in (("before", p), ("after", q)):
                oid = state + "-" + aid
                images[oid] = dots([point])
                objects.append(object_row(oid, "label", state + ":" + aid, state))
            pairs.append({"before_ref": "before:"+aid, "after_ref": "after:"+aid,
                          "before": p, "after": q})
        add(name, METRICS[7], expected, images, objects, {"atom_pairs": pairs, "expected_rotation_deg": 0})
    return rows


def build(out):
    out = Path(out).resolve()
    if out.exists():
        raise ValueError("refusing to overwrite existing output directory")
    # Read fixed, authorized source before creating output. No configurable IR input.
    ir_bytes = IR_FILE.read_bytes()
    policy_bytes = (HERE / "policy-v1.json").read_bytes()
    out.mkdir(parents=True)
    (out / "assets").mkdir()

    def asset(data, kind, suffix):
        sha = digest(data)
        relative = "assets/" + sha + suffix
        target = out / relative
        if not target.exists():
            target.write_bytes(data)
        elif target.read_bytes() != data:
            raise ValueError("content-addressed asset collision")
        return {"id": kind + ":" + sha, "path": relative, "bytes": len(data), "sha256": sha, "kind": kind}

    ir_asset = asset(ir_bytes, "mechanism_ir", ".json")
    calibration = {"version": "quality-calibration/1.0", "id": "synthetic-calibration",
                   "native_build": NATIVE_BUILD, "style": STYLE, "measurement_status": "measured",
                   "measurement_source": "synthetic", "limits": {"head_extension_pt": 4.0, "uncertainty_pt": 0.1}}
    calibration_asset = asset(json_bytes(calibration), "calibration", ".json")
    index = {"version": "synthetic-quality-controls/1.0", "evidence_mode": "synthetic",
             "actual_gold_collected": False, "native_execution": False,
             "scope": "Eight metric families across separate partial synthetic cases, not one complete native diagram.",
             "chemical_ir_sha256": digest(ir_bytes), "cases": []}
    for case in controls():
        measurement = copy.deepcopy(case["measurement"])
        objects = copy.deepcopy(case["objects"])
        reference = {"version": "quality-reference/1.0", "ir_sha256": digest(ir_bytes), "source": "synthetic",
                     "coordinate_units": "px", "pixels_per_pt": case["pixels_per_pt"],
                     "object_bindings": copy.deepcopy(objects), "measurements": [locked_measurement(measurement)]}
        reference_data = json_bytes(reference)
        reference_name = case["name"] + ".reference.json"
        (out / reference_name).write_bytes(reference_data)
        render = Image.new("RGBA", next(iter(case["images"].values())).size, "white")
        assets = [copy.deepcopy(ir_asset), copy.deepcopy(calibration_asset)]
        for obj in objects:
            im = case["images"][obj["id"]]
            render = Image.alpha_composite(render, im)
            item = asset(png_bytes(im), "object_layer", ".png")
            obj["asset_ref"] = item["id"]
            if not any(a["id"] == item["id"] for a in assets):
                assets.append(item)
        render_asset = asset(png_bytes(render), "synthetic_render", ".png")
        assets.append(render_asset)
        value = {"version": "quality-observation/1.0", "sample_id": case["name"], "evidence_mode": "synthetic",
                 "render_asset_ref": render_asset["id"], "ir_asset_ref": ir_asset["id"],
                 "calibration_asset_ref": calibration_asset["id"], "native_build": NATIVE_BUILD,
                 "style": STYLE, "policy_sha256": digest(policy_bytes), "reference_sha256": digest(reference_data),
                 "pixels_per_pt": case["pixels_per_pt"], "assets": assets, "objects": objects,
                 "measurements": [measurement], "evidence": {"native_receipt_asset_ref": None,
                     "annotation_review_asset_ref": None, "inventory_complete": False,
                     "object_layers": "independent_renders", "human_acceptance": "pending"}}
        case_name = case["name"] + ".case.json"
        (out / case_name).write_bytes(json_bytes(value))
        index["cases"].append({"name": case["name"], "case": case_name, "reference": reference_name,
                               "target_metric": case["metric"], "expected_metric_status": case["expected"],
                               **({"note": case["note"]} if "note" in case else {})})
    (out / "index.json").write_bytes(json_bytes(index))
    files = [{"path": path.relative_to(out).as_posix(), "bytes": path.stat().st_size,
              "sha256": digest(path.read_bytes())} for path in sorted(out.rglob("*")) if path.is_file()]
    (out / "manifest.json").write_bytes(json_bytes({"version": "synthetic-quality-assets/1.0", "files": files,
        "manifest_scope": "All delivered files except this self-referential manifest; no native or human evidence."}))
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    index = build(args.out)
    print(json.dumps({"output": str(args.out.resolve()), "cases": len(index["cases"]),
                      "evidence_mode": "synthetic", "actual_gold_collected": False}))


if __name__ == "__main__":
    main()
