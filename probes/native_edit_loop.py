"""Bounded local, JSON-in/JSON-out caption editing. No network or MCP server.

Each public invocation submits ONE action to a retained STA COM owner. Internal
commands below are deterministic readers/checkers, never native mutators.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
DEFAULT_STATE = HERE.parent / ".local" / "agent-edit-loop"
METADATA = {"CDXML": {"CreationDate", "ModificationDate", "Name", "BoundingBox", "WindowSize"},
            "page": {"BoundingBox"}}
BASE_KEYS = {"action", "session_id", "document_id", "revision", "request_id"}
ACTION_KEYS = {
    "open-copy": {"source", "expected_sha256", "role"},
    "inspect": {"end_session", "keep_open"},
    "relative-position": {"caption_id", "caption_token", "arrow_id", "arrow_token", "intent"},
    "save": {"stem"},
    "reopen": {"artifact_id"},
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_value(node, target=None, metadata=None):
    """All elements, attributes, order and text runs, except explicit metadata.

    The complete original XML is always retained. Only target t p/BoundingBox
    may be omitted for a movement comparison; no other object tolerance.
    """
    attrs = dict(node.attrib)
    for name in sorted(METADATA.get(node.tag, set())):
        if name in attrs:
            if metadata is not None:
                metadata.append({"tag": node.tag, "id": node.get("id"),
                                 "attribute": name, "value": attrs[name]})
            del attrs[name]
    if target is not None and node.tag == "t" and node.get("id") == str(target):
        attrs.pop("p", None)
        attrs.pop("BoundingBox", None)
    text = node.text or ""
    if node.tag != "s" and not text.strip():
        text = ""
    return {"tag": node.tag, "attributes": attrs, "text": text,
            "children": [tree_value(n, target, metadata) for n in node]}


def diff(left, right, path=""):
    if type(left) is not type(right):
        return [{"path": path, "before": left, "after": right}]
    if isinstance(left, dict):
        result = []
        for key in sorted(left.keys() | right.keys()):
            if key not in left or key not in right:
                result.append({"path": path + "/" + key, "before": left.get(key), "after": right.get(key)})
            else:
                result.extend(diff(left[key], right[key], path + "/" + key))
        return result
    if isinstance(left, list):
        if len(left) != len(right):
            return [{"path": path, "before": left, "after": right}]
        return [d for i, (a, b) in enumerate(zip(left, right)) for d in diff(a, b, f"{path}/{i}")]
    return [] if left == right else [{"path": path, "before": left, "after": right}]


def xml_root(path):
    # ElementTree does not resolve external DTDs/entities. Preserve all elements.
    return ET.fromstring(Path(path).read_text(encoding="utf-8-sig"))


def snapshot(base):
    base = Path(base)
    raw = read(str(base) + ".native.json")
    root = xml_root(str(base) + ".cdxml")
    parents = {child: parent for parent in root.iter() for child in parent}
    by_id = {}
    for node in root.iter():
        if node.get("id"):
            if node.get("id") in by_id:
                raise ValueError("Duplicate XML identity; refusing ambiguous snapshot")
            by_id[node.get("id")] = node
    def atom_owned(node):
        while node in parents:
            node = parents[node]
            if node.tag == "n":
                return True
        return False
    def page_owner(node):
        while node in parents:
            node = parents[node]
            if node.tag == "page":
                return node.get("id")
        return None
    metadata = []
    tree = tree_value(root, metadata=metadata)
    captions, excluded = [], []
    for cap in raw["captions"]:
        node = by_id.get(str(cap["id"]))
        if node is None or node.tag != "t":
            raise ValueError("Native text not found in complete CDXML")
        if atom_owned(node):
            excluded.append({"id": cap["id"], "reason": "atom-owned text, not a caption"})
            continue
        item = dict(cap)
        item["native_text_api_raw"] = item["text"]
        item["text"] = "".join(n.text or "" for n in node.iter("s"))
        item["size_api_raw"] = item.pop("size")
        item["styles_api_raw"] = item.pop("styles")
        item["owner"] = parents[node].tag
        item["page_id"] = page_owner(node)
        item["xml_attributes"] = dict(node.attrib)
        item["text_runs"] = [dict(n.attrib, text=n.text or "") for n in node.iter("s")]
        captions.append(item)
    # Coverage checks make this a document snapshot, not a selected-object scene.
    for kind, tag in (("atom_ids", "n"), ("bond_ids", "b")):
        if set(map(str, raw[kind])) != {n.get("id") for n in root.iter(tag)}:
            raise ValueError("Native/XML document coverage mismatch: " + kind)
    for arrow in raw["arrows"]:
        node = by_id.get(str(arrow["id"]))
        if node is None:
            raise ValueError("Native arrow absent from full XML")
        ids = [str(arrow["id"])]
        if node.tag == "graphic" and node.get("GraphicType") == "Line":
            modern = by_id.get(node.get("SupersededBy"))
            if modern is None or modern.tag != "arrow":
                raise ValueError("Legacy arrow lacks an explicit SupersededBy arrow")
            ids.append(modern.get("id"))
        elif node.tag != "arrow":
            raise ValueError("Native arrow has an unsupported XML owner")
        arrow["xml_ids"] = ids
        arrow["page_ids"] = sorted({page_owner(by_id[i]) or "unknown" for i in ids})
    content = {k: v for k, v in raw.items() if k not in {"binding", "document_full_name", "session_id", "document_id", "revision"}}
    fingerprint = digest({"xml": tree, "native": content})
    context = {"session_id": raw["session_id"], "document_id": raw["document_id"],
               "revision": raw["revision"], "fingerprint": fingerprint}
    for item in captions + raw["arrows"]:
        item["token"] = digest({**context, "id": item["id"], "kind": "t" if item in captions else "arrow"})
    result = {**context, "bond_length": raw["bond_length"], "binding": raw["binding"],
              "captions": captions, "arrows": raw["arrows"], "excluded_text": excluded,
              "counts": raw["counts"], "hydrogen_status": "unknown; not inferred or qualified by this edit loop",
              "pages": [{"id": p.get("id"), "bounds": [float(v) for v in p.get("BoundingBox", "").split()],
                         "width_pages": p.get("WidthPages"), "height_pages": p.get("HeightPages")}
                        for p in root.iter("page")],
              "xml": str(base) + ".cdxml", "xml_sha256": file_hash(str(base) + ".cdxml"),
              "raw_native": str(base) + ".native.json", "metadata": metadata}
    write(str(base) + ".snapshot.json", result)
    return result


def native_comparable(snap, target=None):
    value = read(snap["raw_native"])
    for name in ("binding", "document_full_name", "session_id", "document_id", "revision"):
        value.pop(name, None)
    if target is not None:
        for cap in value["captions"]:
            if str(cap["id"]) == str(target):
                cap.pop("anchor", None)
                cap.pop("bounds", None)
    return value


def derived_associations(before, comparison_copy, target, arrow_ids):
    """Mask only an authorised derived target association in a comparison copy.

    Never write these XML attributes to a native document/file. Exact source XML
    remains intact. All other step attributes and object associations still diff.
    """
    if target is None or not arrow_ids:
        return []
    target = str(target)
    aliases = set(map(str, arrow_ids))
    def selected(root):
        return [n for n in root.iter("step")
                if n.get("ReactionStepArrows", "").split()
                and set(n.get("ReactionStepArrows").split()) <= aliases]
    old, new = selected(before), selected(comparison_copy)
    if len(old) != 1 or len(new) != 1:
        return []
    a, b = old[0], new[0]
    if not a.get("id") or a.get("id") != b.get("id") or a.get("ReactionStepArrows") != b.get("ReactionStepArrows"):
        return []
    changes = []
    for key in ("ReactionStepObjectsAboveArrow", "ReactionStepObjectsBelowArrow"):
        left, right = a.get(key), b.get(key)
        if left == right:
            continue
        l_ids, r_ids = (left or "").split(), (right or "").split()
        if (l_ids.count(target) not in (0, 1) or r_ids.count(target) not in (0, 1)
                or l_ids.count(target) == r_ids.count(target)
                or [i for i in l_ids if i != target] != [i for i in r_ids if i != target]):
            continue
        changes.append({"step_id": a.get("id"), "reaction_step_arrows": a.get("ReactionStepArrows"),
                        "selected_arrow_aliases": sorted(aliases), "target_caption_id": target,
                        "attribute": key, "before": left, "after": right,
                        "classification": "native-derived target association; not no-edit normalization"})
        if left is None:
            b.attrib.pop(key, None)
        else:
            b.set(key, left)
    return changes


def initial_stereo_markers(before, comparison_copy):
    """Only initial-export absent->N atom AS / bond BS additions; never edits XML files."""
    old = {(n.tag, n.get('id')): n for n in before.iter() if n.get('id')}
    changes = []
    for node in comparison_copy.iter():
        key = {'n': 'AS', 'b': 'BS'}.get(node.tag)
        prior = old.get((node.tag, node.get('id')))
        if key and prior is not None and key not in prior.attrib and node.get(key) == 'N':
            changes.append({'tag': node.tag, 'id': node.get('id'), 'attribute': key,
                            'before': None, 'after': 'N', 'stage': 'initial native export only'})
            del node.attrib[key]
    return changes


def compare(before, after, target=None, arrow_ids=None, initial=False):
    a, b = read(before), read(after)
    old_root, comparison_copy = xml_root(a["xml"]), xml_root(b["xml"])
    association = derived_associations(old_root, comparison_copy, target, arrow_ids)
    initial_changes = initial_stereo_markers(old_root, comparison_copy) if initial else []
    xml_diffs = diff(tree_value(old_root, target), tree_value(comparison_copy, target))
    native_diffs = diff(native_comparable(a, target), native_comparable(b, target))
    metadata_diff = diff(a["metadata"], b["metadata"])
    return {"ok": not (xml_diffs or native_diffs or (initial and metadata_diff)), "xml_differences": xml_diffs,
            "native_differences": native_diffs, "metadata_differences": metadata_diff,
            "derived_association": association,
            "initial_native_normalization": initial_changes,
            "allowed_target_position_id": target, "other_object_tolerance": 0}


def intersects(a, b, pad):
    return a[0] < b[2] + pad and a[2] > b[0] - pad and a[1] < b[3] + pad and a[3] > b[1] - pad


def plan(req, snap):
    candidates = {"captions": snap["captions"], "arrows": snap["arrows"]}
    def refuse(reason):
        return {"ok": False, "reason": reason, "candidates": candidates, "native_write": False}
    caps = [c for c in snap["captions"] if c["id"] == req.get("caption_id")]
    arrows = [a for a in snap["arrows"] if a["id"] == req.get("arrow_id")]
    if len(caps) != 1 or len(arrows) != 1:
        return refuse("Select one live non-atom caption and one arrow from inspect; ambiguous/absent IDs refuse")
    cap, arrow = caps[0], arrows[0]
    if cap["token"] != req.get("caption_token") or arrow["token"] != req.get("arrow_token"):
        return refuse("Stale or incorrect object token")
    if abs(cap["angle"]) > 1e-9:
        return refuse("Rotated caption avoidance is not qualified")
    if cap["owner"] != "page":
        return refuse("This version supports direct page captions only; fragment/group captions refuse")
    pages = snap["pages"]
    if len(pages) != 1 or pages[0]["width_pages"] != "1" or pages[0]["height_pages"] != "1":
        return refuse("This version requires one known physical page")
    page = pages[0]
    bounds = page["bounds"]
    if (len(bounds) != 4 or not all(math.isfinite(v) for v in bounds)
            or bounds[2] <= bounds[0] or bounds[3] <= bounds[1]
            or cap["page_id"] != page["id"] or arrow["page_ids"] != [page["id"]]):
        return refuse("Unknown page bounds or caption/arrow page mismatch")
    bond = snap["bond_length"]
    if not isinstance(bond, (int, float)) or not math.isfinite(bond) or bond <= 0:
        return refuse("Missing actual native BondLength")
    box, anchor = cap["bounds"], cap["anchor"]
    if len(box) != 4 or not all(math.isfinite(x) for x in box + anchor):
        return refuse("Invalid live native caption bounds")
    root = xml_root(snap["xml"])
    selected_ids = {str(cap["id"]), *arrow["xml_ids"]}
    obstacles, missing = [], []
    drawable = {"fragment", "group", "n", "b", "t", "arrow", "graphic", "curve", "spectrum", "embeddedobject", "table"}
    def collect(node):
        if node.get("id") in selected_ids:
            return
        if node.tag in drawable:
            # Target-containing groups cannot safely serve as obstacle boxes.
            contains_target = any(n.get("id") == str(cap["id"]) for n in node.iter())
            if not contains_target:
                data = node.get("BoundingBox")
                if data:
                    bb = [float(v) for v in data.split()]
                    if len(bb) == 4 and all(math.isfinite(v) for v in bb):
                        bb = [min(bb[0],bb[2]), min(bb[1],bb[3]), max(bb[0],bb[2]), max(bb[1],bb[3])]
                        obstacles.append({"id": node.get("id"), "tag": node.tag, "bounds": bb})
                        return
                missing.append({"id": node.get("id"), "tag": node.tag})
                return
        for child in node:
            collect(child)
    collect(root)
    if missing:
        return refuse("Drawable obstacle lacks a usable native BoundingBox: " + str(missing))
    def moved(dx, dy):
        return [box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy]
    padding = bond * .10
    intent = req.get("intent")
    if intent == "above-arrow":
        dx = (arrow["start"][0] + arrow["end"][0] - box[0] - box[2]) / 2
        base_dy = min(arrow["start"][1], arrow["end"][1]) - bond * .25 - box[3]
        solutions = [(dx, base_dy - i * bond * .25) for i in range(17)]
    elif intent == "up-half-bond":
        solutions = [(0., -.5 * bond)]
    else:
        return refuse("Only above-arrow and up-half-bond are supported")
    for dx, dy in solutions:
        bb = moved(dx, dy)
        if bb[0] < bounds[0] or bb[1] < bounds[1] or bb[2] > bounds[2] or bb[3] > bounds[3]:
            continue
        if not any(intersects(bb, o["bounds"], padding) for o in obstacles):
            return {"ok": True, "caption_id": cap["id"], "intent": intent,
                    "selected_arrow_ids": arrow["xml_ids"],
                    "computed_anchor": [anchor[0] + dx, anchor[1] + dy], "delta": [dx, dy],
                    "before_anchor": anchor, "before_bounds": box, "expected_bounds": bb,
                    "native_bond_length": bond, "obstacle_padding": padding, "obstacles": obstacles,
                    "page_id": page["id"], "page_bounds": bounds,
                    "rule": "Native bounds/arrow endpoints; fixed 0.25 BondLength gap, bounded upward avoidance"}
    return refuse("No collision-free solution within the bounded search; font and structures untouched")


def verify_move(before, after, plan_file):
    motion = read(plan_file)
    result = compare(before, after, motion["caption_id"], motion["selected_arrow_ids"])
    post = next(c for c in read(after)["captions"] if c["id"] == motion["caption_id"])
    residuals = [a - b for a, b in zip(post["anchor"] + post["bounds"],
                                     motion["computed_anchor"] + motion["expected_bounds"])]
    result["target_native_coordinate_residuals"] = residuals
    result["target_absolute_tolerance"] = 1e-6
    result["ok"] = result["ok"] and all(abs(v) <= 1e-6 for v in residuals)
    return result


def preview(native_png):
    # Deterministic alpha compositing only; preserve exact native PNG alongside.
    from PIL import Image
    src = Path(native_png)
    with Image.open(src) as im:
        rgba = im.convert("RGBA")
        white = Image.new("RGBA", rgba.size, "white")
        white.alpha_composite(rgba)
        out = src.with_name(src.stem + ".white.png")
        white.convert("RGB").save(out)
    return {"native_png": str(src), "native_png_sha256": file_hash(src),
            "preview_png": str(out), "preview_sha256": file_hash(out),
            "preview_derivation": "native PNG alpha-composited onto white; no geometry edits"}


def submit(req, state, pwsh=None, timeout=50):
    action = req.get("action")
    if action not in ACTION_KEYS or set(req) - BASE_KEYS - ACTION_KEYS[action]:
        return {"ok": False, "reason": "Unknown action/fields; final coordinates are not accepted", "native_write": False}
    request_id = req.setdefault("request_id", str(uuid.uuid4()))
    uuid.UUID(request_id)
    if action == "open-copy":
        source = Path(req["source"]).resolve(strict=True)
        if source.suffix.lower() not in {".cdxml", ".cdx"} or not source.is_file():
            raise ValueError("One ordinary CDXML/CDX source file is required")
        if file_hash(source) != req.get("expected_sha256", "").lower():
            raise ValueError("Source hash required and must match before creating a copy")
        if req.get("role") not in {"workflow-control", "script-safety-control", "no-edit-control", "development-copy"}:
            raise ValueError("Declare the source role")
        sid = str(uuid.uuid4())
        folder = state / sid
        folder.mkdir(parents=True, exist_ok=False)
        for name in ("inbox", "replies", "evidence", "saved"):
            (folder / name).mkdir()
        copied = folder / ("source" + source.suffix.lower())
        shutil.copyfile(source, copied)
        if file_hash(copied) != req["expected_sha256"].lower():
            raise ValueError("Copy hash changed")
        req["source"] = str(source)
        req["session_id"] = sid
        write(folder / "init.json", {"request": req, "copy": str(copied), "source": str(source),
                                    "source_sha256": file_hash(source), "max_idle_seconds": 1200})
        worker = pwsh or shutil.which("pwsh")
        if not worker:
            raise ValueError("PowerShell 7 path required with --powershell")
        with (folder / "worker.log").open("wb") as log:
            proc = subprocess.Popen([worker, "-NoProfile", "-STA", "-File", str(HERE / "native-edit-loop.ps1"),
                                     "-SessionDirectory", str(folder), "-PythonExe", sys.executable],
                                    stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        write(folder / "worker.json", {"pid": proc.pid, "started_unix": time.time()})
    else:
        sid = str(uuid.UUID(req["session_id"]))
        folder = state / sid
        if not folder.is_dir():
            return {"ok": False, "reason": "Unknown session", "native_write": False}
        if (folder / "closed.json").exists():
            return {"ok": False, "reason": "Session closed; start a new copy explicitly", "closed": read(folder / "closed.json")}
        if (folder / "UNCERTAIN.json").exists() and action != "inspect":
            return {"ok": False, "reason": "Previous deadline expired; mutation locked. Inspect evidence; never replay", "native_write": False}
    reply = folder / "replies" / (request_id + ".json")
    request_file = folder / "inbox" / (request_id + ".json")
    claim = folder / "client.lock"
    try:
        claim.mkdir()
    except FileExistsError:
        return {"ok": False, "reason": "Another action is pending; no concurrent submission", "native_write": False}
    try:
        if request_file.exists():
            if read(request_file) != req:
                return {"ok": False, "reason": "Request ID reused with different content", "native_write": False}
        elif action != "open-copy":
            tmp = request_file.with_suffix(".tmp")
            write(tmp, req)
            tmp.rename(request_file)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if reply.exists():
                result = read(reply)
                result["session_directory"] = str(folder)
                return result
            time.sleep(.15)
        uncertain = {"ok": False, "status": "deadline-uncertain", "session_id": sid,
                     "request_id": request_id, "reply_path": str(reply),
                     "reason": "Do not retry writes. The retained worker may still return a late receipt."}
        write(folder / "UNCERTAIN.json", uncertain)
        return uncertain
    finally:
        claim.rmdir()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    if len(sys.argv) > 1 and sys.argv[1] == "--internal":
        operation, *args = sys.argv[2:]
        if operation == "snapshot":
            result = snapshot(args[0])
        elif operation == "plan":
            result = plan(read(args[0]), read(args[1]))
        elif operation == "compare":
            result = compare(*args[:2], target=int(args[2]) if len(args) == 4 else None)
        elif operation == "verify-move":
            result = verify_move(*args[:3])
        elif operation == "compare-movement-export":
            motion = read(args[2])
            result = compare(args[0], args[1], motion["caption_id"], motion["selected_arrow_ids"])
        elif operation == "compare-initial-export":
            result = compare(*args[:2], initial=True)
        elif operation == "preview":
            result = preview(args[0])
        else:
            raise ValueError("Unknown internal reader")
        write(args[-1], result)
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", help="UTF-8 JSON request file; otherwise read stdin")
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--powershell", help="PowerShell 7 executable, needed only for open-copy")
    parser.add_argument("--timeout", type=int, choices=range(5, 61), default=50)
    args = parser.parse_args()
    try:
        req = read(args.request) if args.request else json.load(sys.stdin)
        result = submit(req, args.state_dir.resolve(), args.powershell, args.timeout)
    except Exception as exc:
        result = {"ok": False, "reason": str(exc), "native_write": False, "layer": "client"}
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result.get("ok") else 2)


if __name__ == "__main__":
    main()
