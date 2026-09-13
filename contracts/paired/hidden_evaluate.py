"""Conservative hidden-side comparison; uncertain correspondence never becomes a zero delta."""
from __future__ import annotations
import argparse, collections, json, math
from pathlib import Path
from target_extract import extract

DELTA_KINDS = ["fragment_translation", "fragment_rotation", "atom_displacement", "lp_displacement", "lp_angular", "charge_displacement", "caption_displacement", "arrow_source_anchor", "arrow_target_anchor", "control_point", "curve_shape", "step_spacing"]

def graphs(inv, issues=None):
    if issues is None: issues = []
    objs = {o["id"]: o for o in inv["objects"] if o["id"]}
    result = []
    for f in inv["objects"]:
        if f["tag"] != "fragment" or not f["id"]:
            continue
        atoms = [o for o in inv["objects"] if o["tag"] == "n" and next((p for p in reversed(o["parents"]) if objs.get(p, {}).get("tag") == "fragment"), None) == f["id"]]
        if not atoms or any(o["attributes"].get("NodeType", "Element") != "Element" for o in atoms):
            continue
        nodes = {o["id"]: (o["attributes"].get("Element", "6"), o["attributes"].get("Charge", "0"), o["attributes"].get("Isotope", ""), o["attributes"].get("Radical", "0"), o["attributes"].get("AS", "")) for o in atoms if o["id"]}
        edges = {}
        for o in inv["objects"]:
            a = o["attributes"]
            belongs = f["id"] in o["parents"] or a.get("B") in nodes or a.get("E") in nodes
            if o["tag"] == "b" and belongs:
                key = frozenset((a.get("B"), a.get("E")))
                if a.get("B") not in nodes or a.get("E") not in nodes or len(key) != 2 or key in edges:
                    issues.append({"fragment":f["id"],"bond":o["id"],"reason":"unresolved, cross-fragment, self or duplicate bond"})
                    nodes = {}; break
                # Endpoint-sensitive wedge stereochemistry is not automatically mapped.
                if a.get("Display", "Solid") not in ("Solid", "Dash", "Bold"):
                    issues.append({"fragment":f["id"],"bond":o["id"],"reason":"unsupported bond stereo display"})
                    nodes = {}; break
                edges[key] = (a.get("Order", "1"), a.get("BS", ""))
        if nodes:
            result.append({"id": f["id"], "nodes": nodes, "edges": edges})
    return result

def unique_isomorphism(a, b, budget=20000):
    if len(a["nodes"]) != len(b["nodes"]) or len(a["edges"]) != len(b["edges"]): return None, "different"
    degree = lambda g,n: sum(n in e for e in g["edges"])
    choices = {n: [m for m in b["nodes"] if a["nodes"][n] == b["nodes"][m] and degree(a,n) == degree(b,m)] for n in a["nodes"]}
    order = sorted(choices, key=lambda n: len(choices[n])); solutions = []; visited = 0; exhausted = False
    def search(mapping, used):
        nonlocal visited, exhausted
        visited += 1
        if visited > budget: exhausted = True; return
        if len(solutions) > 1: return
        if len(mapping) == len(order): solutions.append(dict(mapping)); return
        n = order[len(mapping)]
        for m in choices[n]:
            if m in used: continue
            if all(a["edges"].get(frozenset((n, x))) == b["edges"].get(frozenset((m, y))) for x,y in mapping.items()):
                mapping[n] = m; search(mapping, used | {m}); del mapping[n]
    search({}, set())
    if exhausted: return None, "budget_exceeded"
    if len(solutions) == 1: return solutions[0], "unique"
    return None, "ambiguous" if solutions else "different"

def rigid_fit(candidate, target):
    n = len(candidate); c = [sum(p[k] for p in candidate)/n for k in (0,1)]; t = [sum(p[k] for p in target)/n for k in (0,1)]
    dot = sum((p[0]-c[0])*(q[0]-t[0])+(p[1]-c[1])*(q[1]-t[1]) for p,q in zip(candidate,target))
    cross = sum((p[0]-c[0])*(q[1]-t[1])-(p[1]-c[1])*(q[0]-t[0]) for p,q in zip(candidate,target))
    angle = math.atan2(cross,dot) if n > 1 and abs(dot)+abs(cross)>1e-12 else None
    co,si = math.cos(angle or 0),math.sin(angle or 0)
    translation = [t[0]-co*c[0]+si*c[1], t[1]-si*c[0]-co*c[1]]
    aligned = [[co*p[0]-si*p[1]+translation[0], si*p[0]+co*p[1]+translation[1]] for p in candidate]
    return {"rotation_radians": angle, "translation": translation, "centroid_displacement": [t[k]-c[k] for k in (0,1)], "aligned_rmsd": math.sqrt(sum(sum((p[k]-q[k])**2 for k in (0,1)) for p,q in zip(aligned,target))/n)}

def compare(target, candidate):
    issues = []; tg,cg = graphs(target,issues),graphs(candidate,issues); possible = []
    for a in tg:
        for b in cg:
            mapping, status = unique_isomorphism(a,b)
            if status == "unique": possible.append((a,b,mapping))
            elif status in ("ambiguous", "budget_exceeded"): issues.append({"target":a["id"],"candidate":b["id"],"reason":status})
    tc = collections.Counter(a["id"] for a,b,m in possible); cc = collections.Counter(b["id"] for a,b,m in possible)
    pairs = [(a,b,m) for a,b,m in possible if tc[a["id"]] == cc[b["id"]] == 1]
    ti = {o["id"]:o for o in target["objects"] if o["id"]}; ci = {o["id"]:o for o in candidate["objects"] if o["id"]}
    deltas = []; correspondence = []
    for a,b,mapping in pairs:
        correspondence.append({"target_fragment":a["id"],"candidate_fragment":b["id"],"atom_map":mapping,"method":"unique_exact_graph_isomorphism", "semantic_scope":"explicit atom element/charge/isotope/radical/AS and bond order/BS only"})
        points = [(ti[x]["geometry"].get("p"),ci[y]["geometry"].get("p"),x,y) for x,y in mapping.items()]
        if not all(p and q and len(p)==len(q)==2 for p,q,x,y in points):
            issues.append({"target":a["id"],"candidate":b["id"],"reason":"missing atom positions"}); continue
        fit = rigid_fit([q for p,q,x,y in points],[p for p,q,x,y in points])
        correspondence[-1]["rigid_fit"] = fit
        deltas.append({"kind":"fragment_translation","target_id":a["id"],"candidate_id":b["id"],"value":fit["centroid_displacement"],"unit":"CDXML points", "frame":"candidate_centroid_to_target_centroid"})
        deltas.append({"kind":"fragment_rotation","target_id":a["id"],"candidate_id":b["id"],"value":fit["rotation_radians"],"unit":"radians", "frame":"candidate_to_target_global_rigid"})
        for p,q,x,y in points:
            deltas.append({"kind":"atom_displacement","target_id":x,"candidate_id":y,"value":[p[k]-q[k] for k in (0,1)],"unit":"CDXML points", "frame":"unaligned_native_global"})
    covered = {d["kind"] for d in deltas if d["value"] is not None}
    def counts(inv): return dict(collections.Counter(o["tag"] for o in inv["objects"]))
    return {"version":"paired-evaluation/1.0", "target_sha256":target["source_sha256"],"candidate_sha256":candidate["source_sha256"],
        "gates": {"chemical_correctness":"unmeasured", "native_editability":"unmeasured", "visual_quality":"unmeasured", "human_acceptance":"unmeasured"},
        "semantic": {"status":"partial", "matched_fragment_count":len(pairs), "target_supported_fragment_count":len(tg), "candidate_supported_fragment_count":len(cg), "unmeasured":["roles/state sequence", "conditions", "electron-flow source/sink", "lone-pair semantics", "bond changes", "full stereochemistry"]},
        "objects": {"status":"inventory_only", "target_counts":counts(target),"candidate_counts":counts(candidate),"native_reopen_evidence":None},
        "geometry": {"status":"partial" if deltas else "unmeasured","correspondence":correspondence,"ambiguities":issues,"unmatched_or_unsupported_target_fragments":sum(o["tag"]=="fragment" for o in target["objects"])-len(pairs)},
        "native_visual": {"status":"unmeasured", "oracle_result":None,"reason":"requires hash-bound native renders, independently measured ports/ink and calibrated Quality Oracle v1 packet"},
        "correction": {"version":"paired-correction-deltas/1.0","tier":"silver", "actual_gold":False,"direction":"candidate_to_target", "target_sha256":target["source_sha256"],"candidate_sha256":candidate["source_sha256"], "deltas":deltas, "unmeasured_kinds":[k for k in DELTA_KINDS if k not in covered],"human_active_seconds":None},
        "limits":["unique graph matching can still be wrong across mechanism states; reviewer must qualify state correspondence", "no arrow identity inferred from native ID or array order", "same counts do not establish chemical correctness", "target quality and rights require independent review"]}

if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("target"); ap.add_argument("candidate"); ap.add_argument("output"); a=ap.parse_args()
    Path(a.output).write_text(json.dumps(compare(extract(a.target),extract(a.candidate)),indent=2)+"\n",encoding="utf-8")
