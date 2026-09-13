"""Draft corpus validation. No network, native execution, gold approval or training.
Syntax and integrity checks are separate from a bounded closed-shell H/C/N/O/Br
electron-accounting check. Unsupported chemistry fails closed for that check.
"""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import sys
from jsonschema import Draft202012Validator

HERE = Path(__file__).parent
ENTITY_ARRAYS = ("atoms", "states", "species", "molecules", "atom_occurrences",
                 "bonds", "charges", "radicals", "lone_pairs", "reaction_steps",
                 "reaction_arrows", "condition_texts", "electron_flows", "layout_constraints")
LAYERS = ("page_and_reading_order", "molecular_graph", "participant_roles",
          "reaction_arrows", "conditions", "electronic_marks", "electron_flow", "visual_geometry")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(rows, key="id"):
    keys = [r[key] for r in rows]
    require(len(keys) == len(set(keys)), "duplicate identity: " + key)
    return {r[key]: r for r in rows}


def acyclic_references(rows, field, message):
    """Reject missing/self/cyclic parent links; a shared ancestor is valid."""
    visiting = set(); finished = set()
    def visit(identity):
        require(identity in rows, message + ": missing reference")
        require(identity not in visiting, message + ": cycle")
        if identity in finished: return
        visiting.add(identity)
        for parent in rows[identity][field]: visit(parent)
        visiting.remove(identity); finished.add(identity)
    for identity in rows: visit(identity)


def syntax(kind, value):
    import math
    def finite(x):
        if isinstance(x, float): require(math.isfinite(x), "nonfinite JSON number")
        elif isinstance(x, dict):
            for y in x.values(): finite(y)
        elif isinstance(x, list):
            for y in x: finite(y)
    finite(value)
    schema = json.loads((HERE / (kind + ".schema.json")).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value),
                    key=lambda e: str(list(e.path)))
    require(not errors, "schema: " + "; ".join(e.message for e in errors[:3]))


def mechanism(value):
    syntax("mechanism-ir", value)
    tables = {name: unique(value[name]) for name in ENTITY_ARRAYS}
    all_ids = [r["id"] for name in ENTITY_ARRAYS for r in value[name]]
    require(len(all_ids) == len(set(all_ids)), "entity IDs must be globally unique")
    atoms, states, occ, bonds = (tables[n] for n in ("atoms", "states", "atom_occurrences", "bonds"))
    require(value["entry_state"] in states, "unknown entry state")
    for item in occ.values():
        require(item["atom_ref"] in atoms and item["state_ref"] in states, "unknown atom occurrence reference")
        m = tables["molecules"].get(item["molecule_ref"])
        require(m and m["state_ref"] == item["state_ref"] and item["id"] in m["atom_refs"], "occurrence/molecule mismatch")
    for state in states.values():
        members = [o for o in occ.values() if o["state_ref"] == state["id"]]
        require(len({o["atom_ref"] for o in members}) == len(members), "duplicate atom in state")
        if value["scope"]["atom_inventory"] == "closed":
            require({o["atom_ref"] for o in members} == set(atoms), "closed state atom inventory differs")
        require(set(state["species_refs"]) == {s["id"] for s in tables["species"].values() if s["state_ref"] == state["id"]}, "state/species coverage")
    molecule_owner = collections.Counter()
    for species in tables["species"].values():
        require(species["state_ref"] in states, "unknown species state")
        for mid in species["molecule_refs"]:
            m = tables["molecules"].get(mid)
            require(m and m["state_ref"] == species["state_ref"], "species/molecule mismatch")
            molecule_owner[mid] += 1
    require(set(molecule_owner) == set(tables["molecules"]) and all(n == 1 for n in molecule_owner.values()), "molecule ownership")
    bond_owner = collections.Counter()
    for m in tables["molecules"].values():
        require(m["state_ref"] in states, "unknown molecule state")
        for oid in m["atom_refs"]:
            require(oid in occ and occ[oid]["state_ref"] == m["state_ref"] and occ[oid]["molecule_ref"] == m["id"], "molecule atom membership")
        adjacency = {oid: set() for oid in m["atom_refs"]}
        for bid in m["bond_refs"]:
            b = bonds.get(bid)
            require(b and b["state_ref"] == m["state_ref"] and set(b["atom_refs"]) <= set(m["atom_refs"]), "molecule bond membership")
            a, c = b["atom_refs"]; adjacency[a].add(c); adjacency[c].add(a); bond_owner[bid] += 1
        visited = set(); todo = [m["atom_refs"][0]]
        while todo:
            current = todo.pop()
            if current not in visited:
                visited.add(current); todo.extend(adjacency[current] - visited)
        require(visited == set(m["atom_refs"]), "molecule must be a connected component")
    require(set(bond_owner) == set(bonds) and all(n == 1 for n in bond_owner.values()), "bond ownership")
    pairs = [(b["state_ref"], tuple(sorted(b["atom_refs"]))) for b in bonds.values()]
    require(len(pairs) == len(set(pairs)), "duplicate bond pair")
    charge = {}; lp = collections.Counter(); radical = collections.Counter(); slots = collections.defaultdict(list)
    for name in ("charges", "radicals", "lone_pairs"):
        for row in tables[name].values():
            require(row["atom_ref"] in occ, "electronic mark has unknown occurrence")
            oid = row["atom_ref"]
            if name == "charges":
                require(oid not in charge, "duplicate formal charge"); charge[oid] = row["value"]
            if name == "radicals": radical[oid] += row["unpaired_electrons"]
            if name == "lone_pairs": lp[oid] += 1; slots[oid].append(row["slot"])
    for values in slots.values():
        require(sorted(values) == list(range(len(values))), "duplicate or noncontiguous lone-pair slots")
    steps = tables["reaction_steps"]
    for step in steps.values():
        require(step["from_state"] in states and step["to_state"] in states and step["from_state"] != step["to_state"], "invalid step endpoints")
        require(set(step["electron_flow_refs"]) == {f["id"] for f in tables["electron_flows"].values() if f["step_ref"] == step["id"]}, "step flow coverage")
        require(set(step["condition_refs"]) == {t["id"] for t in tables["condition_texts"].values() if t["step_ref"] == step["id"]}, "step condition coverage")
    for arrow in tables["reaction_arrows"].values():
        s = steps.get(arrow["step_ref"])
        require(s and arrow["from_state"] == s["from_state"] and arrow["to_state"] == s["to_state"], "reaction arrow endpoints")
    for text in tables["condition_texts"].values():
        require(text["step_ref"] in steps, "condition has unknown step")
    def resolve_port(port, state):
        require(port["state_ref"] == state, "electron port must refer to pre-transition state")
        typ = port["type"]
        if typ == "atom":
            ids = [port["atom_ref"]]
        elif typ == "prospective_bond":
            ids = port["atom_refs"]
        elif typ == "bond":
            b = bonds.get(port["bond_ref"]); require(b and b["state_ref"] == state, "unknown source/target bond")
            ids = b["atom_refs"]
        else:
            key = "lone_pairs" if typ == "lone_pair" else "radicals"
            field = "lone_pair_ref" if typ == "lone_pair" else "radical_ref"
            mark = tables[key].get(port[field]); require(mark is not None, "unknown electronic port")
            ids = [mark["atom_ref"]]
        require(all(i in occ and occ[i]["state_ref"] == state for i in ids), "port occurrence scope")
        return tuple(occ[i]["atom_ref"] for i in ids)
    for flow in tables["electron_flows"].values():
        s = steps.get(flow["step_ref"]); require(s is not None, "unknown flow step")
        require(flow["simultaneous_group"] == s["id"], "elementary flows must share the step group")
        resolve_port(flow["source"], s["from_state"]); resolve_port(flow["sink"], s["from_state"])
    for constraint in tables["layout_constraints"].values():
        require(set(constraint["subjects"]) <= set(all_ids), "unknown layout-constraint entity")
        if constraint["kind"] in ("anti", "syn"):
            require(len(constraint["subjects"]) == 4 and all(i in occ for i in constraint["subjects"]), "stereo relation requires four atom occurrences")
            require(len({occ[i]["state_ref"] for i in constraint["subjects"]}) == 1, "stereo relation spans states")
            require(constraint["strength"] == "hard", "chemical stereo cannot be soft")
            a, b, x, y = constraint["subjects"]
            orders = {frozenset(q["atom_refs"]): q["order"] for q in bonds.values()}
            require(orders.get(frozenset((a, b))) == 2 and frozenset((a, x)) in orders and frozenset((b, y)) in orders, "stereo central bond or substituent roles invalid")
    unsupported = []
    supported_elements = {"H": 1, "C": 4, "N": 5, "O": 6, "Br": 7}
    if any(a["element"] not in supported_elements for a in atoms.values()): unsupported.append("element outside bounded profile")
    if value["radicals"] or any(f["electron_count"] != 2 for f in value["electron_flows"]): unsupported.append("radical or single-electron semantics")
    if value["scope"]["atom_inventory"] != "closed": unsupported.append("open inventory")
    if any(s["kind"] not in ("elementary", "teaching_elementary") for s in steps.values()): unsupported.append("non-elementary step")
    if any(f["source"]["type"] not in ("lone_pair", "bond") or f["sink"]["type"] not in ("atom", "bond", "prospective_bond") for f in value["electron_flows"]): unsupported.append("unsupported port chemistry")
    if any(s["stoichiometry"] != 1 for s in value["species"]): unsupported.append("non-unit drawn inventory")
    if unsupported:
        return {"representable": "pass", "semantic_valid": "unsupported", "limitations": unsupported}
    state_graph = {}; state_lp = {}; charges = []
    for sid in states:
        members = {o["atom_ref"]: o for o in occ.values() if o["state_ref"] == sid}
        graph = {tuple(sorted(occ[i]["atom_ref"] for i in b["atom_refs"])): b["order"] for b in bonds.values() if b["state_ref"] == sid}
        state_graph[sid] = graph
        state_lp[sid] = {aid: lp[o["id"]] for aid, o in members.items()}
        charges.append(sum(charge.get(o["id"], 0) for o in members.values()))
        for aid, o in members.items():
            valence = sum(order for edge, order in graph.items() if aid in edge) + o["implicit_h"]
            e = supported_elements[atoms[aid]["element"]]
            require(abs(e - 2 * lp[o["id"]] - valence - charge.get(o["id"], 0)) < 1e-8, "electron/valence accounting: " + o["id"])
    require(len(set(charges)) == 1, "total charge not conserved")
    for aid in atoms:
        require(len({o["implicit_h"] for o in occ.values() if o["atom_ref"] == aid}) == 1, "moving H must have explicit mapped atoms")
    for step in steps.values():
        graph = collections.Counter(state_graph[step["from_state"]])
        pairs_count = collections.Counter(state_lp[step["from_state"]])
        used_lp = set(); bond_use = collections.Counter()
        for fid in step["electron_flow_refs"]:
            f = tables["electron_flows"][fid]; source = f["source"]; sink = f["sink"]
            a = resolve_port(source, step["from_state"]); b = resolve_port(sink, step["from_state"])
            if source["type"] == "lone_pair":
                require(source["lone_pair_ref"] not in used_lp, "same lone pair spent twice"); used_lp.add(source["lone_pair_ref"]); pairs_count[a[0]] -= 1
                edge = tuple(sorted((a[0], b[0]))) if sink["type"] == "atom" else tuple(sorted(b))
                require(len(set(edge)) == 2 and a[0] in edge, "invalid lone-pair bond donation"); graph[edge] += 1
            else:
                edge = tuple(sorted(a)); order = state_graph[step["from_state"]][edge]
                bond_use[(edge, source["electron_kind"])] += 1
                capacity = 1 if source["electron_kind"] == "sigma" else order - 1
                require(bond_use[(edge, source["electron_kind"])] <= capacity, "donor bond electron capacity")
                graph[edge] -= 1
                if sink["type"] == "atom":
                    require(b[0] in edge, "unsupported nonlocal bond-to-atom flow"); pairs_count[b[0]] += 1
                else: graph[tuple(sorted(b))] += 1
        require(all(v >= 0 for v in graph.values()) and all(v >= 0 for v in pairs_count.values()), "negative electron inventory")
        require({k: v for k, v in graph.items() if v} == state_graph[step["to_state"]], "flows do not explain bond changes")
        require(dict(pairs_count) == state_lp[step["to_state"]], "flows do not explain lone-pair changes")
    return {"representable": "pass", "semantic_valid": "bounded_pass", "states": len(states), "steps": len(steps), "flows": len(value["electron_flows"]), "runtime_projection": "unverified", "native_verified": "unverified", "scientific_review": value["scope"]["scientific_status"]}


def annotation(value):
    syntax("annotation", value)
    require(sorted(r["name"] for r in value["layers"]) == sorted(LAYERS), "all eight annotation layers exactly once")
    acyclic_references({r["name"]:r for r in value["layers"]}, "depends_on", "annotation layer dependency")
    actors = unique(value["actors"]); reviews = unique(value["reviews"]); unique(value["observations"])
    for review in reviews.values():
        require(review["actor_ref"] in actors and actors[review["actor_ref"]]["kind"] == "human", "accepted reviews must be actual human records")
        require(review["target_revision"] == value["revision_id"], "stale annotation review")
    for observation in value["observations"]:
        require(observation["actor_ref"] in actors, "unknown annotation actor")
        require(set(observation["review_refs"]) <= set(reviews), "unknown observation review")
        if observation["alignment_status"] == "verified":
            require(any(reviews[i]["status"] == "accepted" for i in observation["review_refs"]), "verified alignment needs recorded human review")
        n = len(observation["geometry"]["points"]); kind = observation["geometry"]["kind"]
        require((kind == "none" and n == 0) or (kind == "point" and n == 1) or (kind == "box" and n == 2) or (kind == "bezier" and n == 4) or (kind == "polyline" and n >= 2) or (kind == "polygon" and n >= 3), "incomplete geometry points")
    return {"representable": "pass", "gold_approval": "not_conferred"}


def manifest(value):
    syntax("corpus-manifest", value)
    samples = unique(value["samples"])
    groups = collections.defaultdict(set)
    for sample in samples.values():
        assets = unique(sample["assets"]); rights = unique(sample["rights"]); groups[sample["leakage_group_id"]].add("evaluation" if sample["split"] in ("fixed_regression","evaluation_reserved") else sample["split"])
        if sample["exposure_status"] == "unseen":
            require(not any(e["known_to"] in ("development", "tuning") for e in sample["exposure_log"]), "exposure history contradicts unseen label")
        require(sample["source"]["kind"] != "schema_probe" or sample["tier"] != "gold", "schema proof cannot become gold")
        require(sample["mechanism_asset_ref"] in assets, "missing IR artifact")
        require(assets[sample["mechanism_asset_ref"]]["kind"] == "ir" and assets[sample["mechanism_asset_ref"]]["mime"] == "application/json", "mechanism asset kind/MIME mismatch")
        generation = set(sample["generation_asset_refs"]); oracle = set(sample["oracle_asset_refs"])
        require(generation <= set(assets) and oracle <= set(assets) and not generation & oracle, "generation/oracle asset boundary")
        if sample["task_mode"] == "anti_selection":
            require(generation and oracle and all(assets[i]["kind"] == "substrate_input" for i in generation), "anti selection cannot receive complete answer IR")
        if sample["annotation_asset_ref"] is not None:
            require(sample["annotation_asset_ref"] in assets, "missing annotation artifact")
            require(assets[sample["annotation_asset_ref"]]["kind"] == "annotation" and assets[sample["annotation_asset_ref"]]["mime"] == "application/json", "annotation asset kind/MIME mismatch")
        frames = {}
        for asset in assets.values():
            require(asset["rights_ref"] in rights, "unknown asset rights")
            for frame in asset["frames"]:
                require(frame["id"] not in frames, "duplicate frame ID"); frames[frame["id"]] = frame
            require(set(asset["derived_from"]) <= set(assets), "missing parent asset")
        acyclic_references(assets, "derived_from", "asset lineage")
        for frame in frames.values():
            require(frame["parent_frame_ref"] is None or frame["parent_frame_ref"] in frames, "unknown parent frame")
            require((frame["parent_frame_ref"] is None) == (frame["to_parent_affine"] is None), "frame transform relation missing")
            if frame["to_parent_affine"] is not None:
                import math
                a,b,c,d,e,f = frame["to_parent_affine"]
                require(all(math.isfinite(x) for x in (a,b,c,d,e,f)) and abs(a*d-b*c)>1e-12, "invalid affine transform")
            seen = set(); cursor = frame
            while cursor["parent_frame_ref"] is not None:
                require(cursor["id"] not in seen, "cyclic frame chain")
                seen.add(cursor["id"]); cursor = frames[cursor["parent_frame_ref"]]
        require((not sample["derived_from"]) == (sample["lineage_relation"] == "root"), "lineage relation/parent mismatch")
        for parent in sample["derived_from"]:
            require(parent in samples and samples[parent]["leakage_group_id"] == sample["leakage_group_id"], "lineage split or missing parent")
            if sample["lineage_relation"] == "same_semantics" and samples[parent]["exposure_status"] != "unseen":
                require(sample["exposure_status"] != "unseen", "same-semantics derivative cannot erase exposure")
        for use, permission in (("rule_tuning", "train"), ("training", "train"), ("public_distribution", "redistribute")):
            if sample["uses"][use]:
                require(all(rights[a["rights_ref"]]["status"] == "approved" and rights[a["rights_ref"]]["permissions"][permission] for a in assets.values()), "rights not cleared for " + use)
        if sample["uses"]["training"] or sample["uses"]["rule_tuning"]:
            require(sample["tier"] in ("silver", "gold") and sample["split"] == "development", "unreviewed or evaluation record cannot fit")
        reviews = unique(sample["reviews"])
        for review in reviews.values():
            require(review["revision_id"] == sample["revision_id"], "stale corpus review")
            require(review["target_sha256"] in {a["sha256"] for a in assets.values()}, "review target hash missing")
            require(set(review["evidence_refs"]) <= set(assets), "review evidence missing")
        if sample["tier"] == "gold":
            scope_kinds = {"semantic":{"ir"},"native_geometry":{"cdxml","receipt"},"visual":{"native_render","raster_source"},"correction":{"correction"}}
            for scope in sample["gold_scopes"]:
                acceptable_hashes = {a["sha256"] for a in assets.values() if a["kind"] in scope_kinds[scope]}
                require(any(r["scope"] == scope and r["target_sha256"] in acceptable_hashes and r["actor_kind"] == "human" and r["independent_of_author"] and r["decision"] == "accepted" for r in reviews.values()), "gold review targets wrong artifact kind")
                require(any(r["scope"] == scope and r["actor_kind"] == "human" and r["independent_of_author"] and r["decision"] == "accepted" for r in reviews.values()), "gold needs independent human scope review")
            require(all(rights[a["rights_ref"]]["status"] == "approved" for a in assets.values()), "gold rights pending")
            if "native_geometry" in sample["gold_scopes"]:
                require({"cdx", "cdxml", "native_render", "receipt"} <= {a["kind"] for a in assets.values()}, "native gold evidence incomplete")
        else:
            require(not sample["gold_scopes"], "non-gold record cannot claim gold scopes")
    for sample in samples.values():
        seen = set()
        def ancestors(s):
            require(s["id"] not in seen, "cyclic sample lineage")
            seen.add(s["id"])
            for pid in s["derived_from"]:
                yield samples[pid]
                yield from ancestors(samples[pid])
            seen.remove(s["id"])
        for parent in ancestors(sample):
            for use, permission in (("rule_tuning","train"),("training","train"),("public_distribution","redistribute")):
                if sample["uses"][use]:
                    rights = {r["id"]:r for r in parent["rights"]}
                    require(all(rights[a["rights_ref"]]["status"] == "approved" and rights[a["rights_ref"]]["permissions"][permission] for a in parent["assets"]), "ancestor rights not cleared")
    require(all(len(splits) == 1 for splits in groups.values()), "leakage group spans splits")
    return {"representable": "pass", "samples": len(samples), "gold_samples": sum(s["tier"] == "gold" for s in samples.values())}


def correction(value):
    syntax("correction-record", value)
    require(value["before_revision"] != value["after_revision"], "immutable revisions must differ")
    unique(value["operations"])
    if value["claims"]["geometry_only"]:
        require(value["semantic_equivalence"]["status"] == "pass", "geometry-only claim needs semantic equality")
        require(all(o["kind"] not in ("chemistry_change",) for o in value["operations"]), "geometry-only contains chemistry change")
    if value["claims"]["nonzero_edit"]:
        require(any(o["before"] != o["after"] and o["kind"] != "serialization_only" for o in value["operations"]), "no observed nonzero edit")
    if value["claims"]["human_accepted"]: require(bool(value["review_refs"]), "human acceptance needs review evidence")
    if value["record_kind"] != "design_fixture":
        require(all(c["status"] == "unique" for c in value["correspondences"]), "unresolved identity prevents correction diff")

    for side in ("before", "after"):
        known = {k:a["sha256"] for k,a in unique(value[side+"_artifacts"], "asset_ref").items()}
        for c in value["correspondences"]:
            require(all(known.get(l["asset_ref"]) == l["asset_sha256"] for l in c[side+"_locators"]), "correction locator not bound to artifact")
    for o in value["operations"]:
        if o["units"] in ("pt","px","mm","degree"): require(o["frame_ref"] is not None, "geometric diff has no frame")
    t = value["timing"]
    if t["measurement"] == "unmeasured": require(t["manual_active_seconds"] is None, "unmeasured manual time must be null")
    if value["actor"]["kind"] != "human": require(t["manual_active_seconds"] is None, "automated time cannot become human correction")
    if t["manual_active_seconds"] is not None and t["wall_seconds"] is not None: require(t["manual_active_seconds"] <= t["wall_seconds"], "manual time exceeds wall time")
    return {"representable": "pass", "native_execution": "not_performed", "gold_approval": "not_conferred"}


def split(value):
    syntax("split-manifest", value)
    unique(value["assignments"], "sample_id"); groups = collections.defaultdict(set)
    for row in value["assignments"]:
        groups[row["leakage_group_id"]].add("evaluation" if row["split"] in ("fixed_regression","evaluation_reserved") else row["split"])
        require(not (row["split"] == "evaluation_reserved" and row["exposure_status"] != "unseen"), "exposed sample in unseen evaluation")
    require(all(len(x) == 1 for x in groups.values()), "leakage group spans splits")
    if value["freeze"]["status"] == "not_started":
        require(not value["freeze"]["selected_holdout_ids"], "holdout selected before freeze")
        require(not value["freeze"]["selections"] and value["freeze"]["generation"] == 0, "selection/generation before freeze")
        require(all(value["freeze"][k] is None for k in ("base_pass_receipt_sha256","base_passed_at","frozen_at")), "unstarted freeze has base-pass claims")
        require(value["freeze"]["commit"] is None and value["freeze"]["bundle_sha256"] is None, "unstarted freeze has forged fields")
    else:
        require(bool(value["freeze"]["commit"]) and bool(value["freeze"]["bundle_sha256"]), "incomplete freeze receipt")
        from datetime import datetime
        f = value["freeze"]
        require(f["generation"] > 0 and f["base_pass_receipt_sha256"] and f["base_passed_at"] and f["frozen_at"], "missing base-pass/freeze lineage")
        stamp = lambda x: datetime.fromisoformat(x.replace("Z","+00:00"))
        require(stamp(f["base_passed_at"]) <= stamp(f["frozen_at"]), "freeze precedes base pass")
        selected = unique(f["selections"],"sample_id")
        require(set(selected) == set(f["selected_holdout_ids"]), "holdout selection inventory")
        assignments = {a["sample_id"]:a for a in value["assignments"]}
        for row in selected.values():
            require(row["sample_id"] in assignments and assignments[row["sample_id"]]["split"] == "evaluation_reserved", "selection outside reserved partition")
            require(row["independent_of_tuning"] and row["freeze_bundle_sha256"] == f["bundle_sha256"], "selection evaluator/freeze mismatch")
            require(stamp(row["selected_at"]) >= stamp(f["frozen_at"]), "holdout chosen before freeze")
            if row["disclosed_at"]: require(stamp(row["disclosed_at"]) >= stamp(row["selected_at"]), "disclosure precedes selection")
    return {"representable": "pass", "holdout_selection": value["freeze"]["status"]}


def bundle(directory):
    """Check actual local probe bytes and cross-file references; never fetch URLs."""
    directory = Path(directory).resolve()
    registry = json.loads((directory/"proof-manifest.json").read_text())
    partitions = json.loads((directory/"split-manifest.json").read_text())
    registry_result = manifest(registry); split(partitions)
    require(partitions["corpus_revision"] == registry["revision"], "split corpus revision mismatch")
    require(partitions["policy_version"] == registry["policy_version"], "split policy version mismatch")
    assignments = {a["sample_id"]:a for a in partitions["assignments"]}
    require(set(assignments) == {s["id"] for s in registry["samples"]}, "split sample inventory")
    results = []; local_assets = 0; external_assets = 0
    for sample in registry["samples"]:
        a = assignments[sample["id"]]
        require(all(a[k] == sample[k] for k in ("leakage_group_id","split","exposure_status")), "split/registry disagreement")
        assets = {a["id"]:a for a in sample["assets"]}
        documents = {}
        for asset in assets.values():
            if asset["uri"].startswith("https://"):
                external_assets += 1; continue
            path = (directory/asset["uri"]).resolve()
            require(path.is_relative_to(directory), "asset path escapes bundle")
            data = path.read_bytes()
            require(len(data) == asset["bytes"] and hashlib.sha256(data).hexdigest() == asset["sha256"], "local asset hash/bytes mismatch")
            local_assets += 1
            if asset["mime"] == "application/json": documents[asset["id"]] = json.loads(data)
        ir = documents[sample["mechanism_asset_ref"]]
        require(ir["id"] == sample["id"], "IR/sample identity mismatch")
        result = mechanism(ir); result["sample_id"] = sample["id"]; results.append(result)
        if sample["annotation_asset_ref"]:
            value = documents[sample["annotation_asset_ref"]]; annotation(value)
            require(value["sample_id"] == sample["id"] and value["revision_id"] == sample["revision_id"], "annotation sample/revision mismatch")
            require(value["mechanism_sha256"] == assets[sample["mechanism_asset_ref"]]["sha256"], "annotation IR hash mismatch")
            entities = {r["id"] for name in ENTITY_ARRAYS for r in ir[name]}
            for observation in value["observations"]:
                require(set(observation["entity_refs"]) <= entities, "annotation unknown semantic entity")
                require(set(observation["evidence_asset_refs"]) <= set(assets), "observation evidence asset missing")
                for assessment in observation["assessments"]:
                    require(set(assessment["entity_refs"]) <= entities and set(assessment["evidence_asset_refs"]) <= set(assets), "visual assessment reference mismatch")
                artifact = assets.get(observation["asset_ref"])
                require(artifact and artifact["sha256"] == observation["asset_sha256"], "annotation artifact binding")
                require(observation["frame_ref"] in {f["id"] for f in artifact["frames"]}, "annotation frame not in referenced artifact")
    return {"status":"pass","mechanisms":results,"local_assets_hash_checked":local_assets,"external_asset_bindings_only":external_assets,"gold_samples":registry_result["gold_samples"],"fresh_native_execution":False}


CHECKERS = {"mechanism-ir": mechanism, "annotation": annotation, "corpus-manifest": manifest, "correction-record": correction, "split-manifest": split}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=CHECKERS)
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        result = CHECKERS[args.kind](json.loads(args.file.read_text(encoding="utf-8")))
        print(json.dumps(result))
        return 0 if result.get("semantic_valid") != "unsupported" else 2
    except (ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
