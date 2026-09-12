"""Validate the bounded M2 teaching contract; does not execute ChemDraw or assess layout."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def validate_semantics(fixture: dict) -> None:
    """Raise ValueError on invalid M2 graphs, flows or logical layout constraints."""
    def require(ok, reason):
        if not ok:
            raise ValueError(reason)

    def edge(atoms):
        require(len(atoms) == 2 and atoms[0] != atoms[1], "invalid bond endpoints")
        return tuple(sorted(atoms))

    atoms = {a["map"]: a for a in fixture["atom_catalog"]}
    require(len(atoms) == len(fixture["atom_catalog"]), "duplicate atom map")
    expected_atoms = {1: "C", 2: "N", 3: "O", 4: "C", 20: "O", 21: "O"}
    expected_atoms.update({i: "C" for i in range(10, 16)})
    expected_atoms.update({i: "H" for i in range(30, 36)})
    require({i: a["element"] for i, a in atoms.items()} == expected_atoms, "M2 atom catalog mismatch")
    require(all(a["implicit_h"] == (3 if i == 4 else 1 if 11 <= i <= 15 else 0)
                for i, a in atoms.items()), "M2 implicit H mismatch")
    states = {s["id"]: s for s in fixture["states"]}
    require(list(states) == [f"s{i}" for i in range(7)] and len(fixture["states"]) == 7,
            "seven ordered distinct states required")
    graphs, charges, pairs = {}, {}, {}
    for name, state in states.items():
        graph = {edge(b["atoms"]): b["order"] for b in state["bonds"]}
        q = {x["atom"]: x["value"] for x in state["formal_charges"]}
        lp = {x["atom"]: x["count"] for x in state["lone_pairs"]}
        require(len(graph) == len(state["bonds"]), f"{name}: duplicate bond")
        require(len(q) == len(state["formal_charges"]) and set(q) <= atoms.keys(), f"{name}: charges")
        require(len(lp) == len(state["lone_pairs"]) and set(lp) == {2, 3, 20, 21}, f"{name}: lone pairs")
        valence = {i: a["implicit_h"] for i, a in atoms.items()}
        for (a, b), order in graph.items():
            require(a in atoms and b in atoms, f"{name}: unmapped bond")
            valence[a] += order
            valence[b] += order
        for i, atom in atoms.items():
            el = atom["element"]
            v, formal, count = valence[i], q.get(i, 0), lp.get(i, 0)
            if el in ("C", "H"):
                require(v == (4 if el == "C" else 1) and formal == 0, f"{name}: C/H valence")
            else:
                require(v + count == 4, f"{name}: octet")
                require(formal == {"N": 5, "O": 6}[el] - v - 2 * count, f"{name}: charge/LP")
        require(sum(q.values()) == 1, f"{name}: total charge")
        graphs[name], charges[name], pairs[name] = graph, q, lp

    require(fixture["stereo_constraints"] == [{
        "type": "anti_across_double_bond", "states": ["s0", "s1"],
        "central_bond": [1, 2], "substituent_atoms": [10, 3]}], "missing/wrong anti constraint")
    require(all(graphs[n].get((1, 2)) == 2 and graphs[n].get((1, 10)) == 1
                and graphs[n].get((2, 3)) == 1 for n in ("s0", "s1")), "anti graph mismatch")
    require(graphs["s2"].get((2, 10)) == 1 and (1, 10) not in graphs["s2"]
            and all(graphs[n].get((1, 4)) == 1 for n in states), "wrong migrating group")
    require(graphs["s6"].get((1, 21)) == 2 and graphs["s6"].get((2, 35)) == 1
            and graphs["s6"].get((3, 30)) == 1 and graphs["s6"].get((3, 31)) == 1,
            "final product/provenance mismatch")
    require(len(fixture["transitions"]) == 6, "six transitions required")
    all_flow_ids = set()
    for idx, transition in enumerate(fixture["transitions"]):
        before, after = f"s{idx}", f"s{idx+1}"
        require(transition["id"] == f"t{idx+1}" and transition["from"] == before
                and transition["to"] == after, "transition continuity")
        g, h = graphs[before], graphs[after]
        q, z = charges[before], charges[after]
        delta, dq = Counter(), Counter()
        used_lp, used_bond = set(), set()
        require(len(transition["electron_flows"]) == [2, 3, 2, 2, 2, 4][idx], "flow count")
        for flow in transition["electron_flows"]:
            require(flow["id"] not in all_flow_ids and flow["electron_count"] == 2, "flow identity/count")
            all_flow_ids.add(flow["id"])
            source, target = flow["source"], flow["target"]
            if source["type"] == "lone_pair":
                a, slot = source["atom"], source["pair_index"]
                require(a in atoms and 0 <= slot < pairs[before].get(a, 0), "unavailable donor pair")
                require((a, slot) not in used_lp, "reused donor pair")
                used_lp.add((a, slot))
                if target["type"] == "atom":
                    b = target["atom"]
                else:
                    e = edge(target["atoms"])
                    require(a in e, "LP donor must lie on target bond")
                    b = e[0] if e[1] == a else e[1]
                require(b in atoms and b != a, "invalid target")
                delta[edge([a, b])] += 1
                dq[a] += 1
                dq[b] -= 1
            else:
                e = edge(source["atoms"])
                kind = source["electrons"]
                require(e in g and ((kind == "sigma" and g[e] == 1)
                                    or (kind == "pi" and g[e] >= 2)), "invalid bond donor")
                require((e, kind) not in used_bond, "reused bond donor")
                used_bond.add((e, kind))
                delta[e] -= 1
                if target["type"] == "atom":
                    b = target["atom"]
                    require(b in e, "ambiguous bond migration: identify new target bond")
                    a = e[0] if e[1] == b else e[1]
                else:
                    t = edge(target["atoms"])
                    shared = set(e) & set(t)
                    require(len(shared) == 1 and set(t) <= atoms.keys(), "invalid migration bond")
                    a = next(iter(set(e) - shared))
                    b = next(iter(set(t) - shared))
                    delta[t] += 1
                dq[a] += 1
                dq[b] -= 1
        clean = lambda d: {k: v for k, v in d.items() if v}
        graph_diff = {e: h.get(e, 0) - g.get(e, 0) for e in g.keys() | h.keys()}
        charge_diff = {a: z.get(a, 0) - q.get(a, 0) for a in atoms}
        require(clean(delta) == clean(graph_diff), "electron flow does not explain bond changes")
        require(clean(dq) == clean(charge_diff), "electron flow does not explain charges")
        declared = {edge(x["atoms"]): (x["from_order"], x["to_order"])
                    for x in transition["bond_changes"]}
        expected = {e: (g.get(e, 0), h.get(e, 0)) for e, d in graph_diff.items() if d}
        require(declared == expected and len(declared) == len(transition["bond_changes"]),
                "declared graph diff mismatch")
        declared_q = {x["atom"]: (x["from"], x["to"]) for x in transition["charge_changes"]}
        expected_q = {a: (q.get(a, 0), z.get(a, 0)) for a, d in charge_diff.items() if d}
        require(declared_q == expected_q and len(declared_q) == len(transition["charge_changes"]),
                "declared charge diff mismatch")

    layout = fixture["layout_request"]
    require(layout["rows_left_to_right"] == [["s0", "s1", "s2"], ["s5", "s4", "s3"], ["s6"]]
            and layout["traversal"] == list(states), "wrong snake topology")
    require(len(all_flow_ids) == 15, "fifteen curves required")


if __name__ == "__main__":
    import argparse
    from jsonschema import Draft202012Validator
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    schema = json.loads(Path(__file__).with_name("mechanism-test-case.schema.json").read_text())
    data = json.loads(args.fixture.read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(data)
    validate_semantics(data)
    print("PASS: bounded M2 contract, graph/flow accounting and logical snake topology.")
    print("NOT TESTED: ChemDraw, coordinates, native stereochemistry, editability or visual quality.")
