"""Pure, deterministic IR checks and lowering; no file or native target access.

The chemical report is deliberately bounded. Ports plus graph differences are
not a proof of a proposed reaction, orbital feasibility, or stereochemical truth.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from .elements import ATOMIC_NUMBERS

SCHEMA_PATH = Path(__file__).with_name("mechanism-ir.schema.json")
LEGACY_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "mechanism-ir.schema.json"
CAPTION_SPECIES_ROLES = {"condition_caption": "condition", "reagent_caption": "reagent", "catalyst_caption": "catalyst"}
# Only electron inventory bookkeeping, not an octet/stability model.
CHECKED_VALENCE_ELECTRONS = {"H": 1, "C": 4, "N": 5, "O": 6, "F": 7}


class IRContractError(ValueError):
    def __init__(self, code, path, message, details=None):
        super().__init__(message)
        self.code, self.path, self.message = code, path, message
        self.details = {} if details is None else details

    def to_dict(self):
        return {"code": self.code, "path": self.path, "message": self.message, "details": self.details}


def _fail(code, path, message, details=None):
    raise IRContractError(code, path, message, details)


def canonical_sha256(value):
    try:
        data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        _fail("INVALID_JSON_VALUE", "$", "Input must be finite JSON data", {"reason": str(exc)})
    return hashlib.sha256(data).hexdigest()


def _schema(ir, path=SCHEMA_PATH):
    canonical_sha256(ir)
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        _fail("VALIDATOR_DEPENDENCY_UNAVAILABLE", "$", "jsonschema is required; no syntax validation was performed")
    schema = json.loads(path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(ir), key=lambda e: str(list(e.absolute_path)))
    if errors:
        error = errors[0]
        location = "$" + "".join(f"[{x}]" if isinstance(x, int) else f".{x}" for x in error.absolute_path)
        _fail("SCHEMA_INVALID", location, error.message, {"error_count": len(errors)})


def _unique(items, key, path):
    out = {}
    for i, item in enumerate(items):
        value = item[key]
        if value in out:
            _fail("DUPLICATE_ID", f"{path}[{i}].{key}", "Identity must be unique", {"value": value})
        out[value] = item
    return out


def _pair(atoms):
    return tuple(sorted(atoms))


def _atom_refs(refs, atoms, path):
    unknown = sorted(set(refs) - set(atoms))
    if unknown:
        _fail("UNKNOWN_ATOM", path, "Atom reference is absent from the catalog", {"atoms": unknown})


def _bonds(state, atoms, path):
    out = {}
    for i, bond in enumerate(state["bonds"]):
        _atom_refs(bond["atoms"], atoms, f"{path}.bonds[{i}]")
        key = _pair(bond["atoms"])
        if key in out:
            _fail("DUPLICATE_BOND", f"{path}.bonds[{i}]", "An unordered atom pair has one bond")
        out[key] = bond["order"]
    return out


def _components(atoms, bonds):
    adjacent = {a: set() for a in atoms}
    for a, b in bonds:
        adjacent[a].add(b)
        adjacent[b].add(a)
    pending = set(atoms)
    components = []
    while pending:
        start = min(pending)
        stack, seen = [start], set()
        while stack:
            atom = stack.pop()
            if atom not in seen:
                seen.add(atom)
                stack.extend(adjacent[atom] - seen)
        pending -= seen
        components.append(tuple(sorted(seen)))
    return components


def _species(atoms, bonds):
    return [{"id": "sp-" + canonical_sha256(list(c))[:20], "atoms": list(c)} for c in _components(atoms, bonds)]


def _state_data(ir):
    atoms = _unique(ir["atom_catalog"], "map", "$.atom_catalog")
    states = _unique(ir["states"], "id", "$.states")
    if ir["entry_state"] not in states:
        _fail("UNKNOWN_ENTRY_STATE", "$.entry_state", "Entry state does not exist")
    for atom in atoms.values():
        if atom.get("isotope", ATOMIC_NUMBERS[atom["element"]]) < ATOMIC_NUMBERS[atom["element"]]:
            _fail("ISOTOPE_IDENTITY_INVALID", "$.atom_catalog", "Mass number cannot be less than atomic number", {"atom": atom["map"]})
    data, uncovered, checked = {}, [], 0
    for index, state in enumerate(ir["states"]):
        path = f"$.states[{index}]"
        bonds = _bonds(state, atoms, path)
        charges = _unique(state["formal_charges"], "atom", path + ".formal_charges")
        lps = _unique(state["lone_pairs"], "atom", path + ".lone_pairs")
        overrides = _unique(state.get("atom_properties", []), "atom", path + ".atom_properties")
        _atom_refs(list(charges) + list(lps) + list(overrides), atoms, path)
        charges = {a: charges.get(a, {}).get("value", 0) for a in atoms}
        lps = {a: lps.get(a, {}).get("count", 0) for a in atoms}
        props = {a: {"implicit_h": overrides.get(a, {}).get("implicit_h", item["implicit_h"]),
                     "radical_electrons": overrides.get(a, {}).get("radical_electrons", item.get("radical_electrons", 0)),
                     **({"isotope": item["isotope"]} if "isotope" in item else {})} for a, item in atoms.items()}
        species = _unique(state["chemical_species"], "id", path + ".chemical_species")
        members = [a for sp in species.values() for a in sp["atoms"]]
        _atom_refs(members, atoms, path + ".chemical_species")
        if Counter(members) != Counter(atoms.keys()):
            _fail("SPECIES_PARTITION_INVALID", path + ".chemical_species", "Chemical species must partition the complete atom catalog exactly once")
        actual = sorted(_components(atoms, bonds))
        supplied = sorted(tuple(sorted(sp["atoms"])) for sp in species.values())
        if supplied != actual:
            _fail("SPECIES_CONNECTIVITY_MISMATCH", path + ".chemical_species", "Species must equal graph connected components")
        bond_sums = Counter()
        for (a, b), order in bonds.items():
            bond_sums[a] += order
            bond_sums[b] += order
        for a, item in atoms.items():
            element = item["element"]
            if element not in CHECKED_VALENCE_ELECTRONS:
                uncovered.append({"state_ref": state["id"], "atom_ref": a, "element": element, "reason": "valence_profile_not_implemented"})
                continue
            expected = CHECKED_VALENCE_ELECTRONS[element] - bond_sums[a] - props[a]["implicit_h"] - 2 * lps[a] - props[a]["radical_electrons"]
            if expected != charges[a]:
                _fail("ELECTRON_INVENTORY_MISMATCH", path, "Declared charge disagrees with covered-element electron bookkeeping", {"atom": a, "element": element, "expected_charge": expected, "declared_charge": charges[a]})
            checked += 1
        data[state["id"]] = {"state": state, "bonds": bonds, "charges": charges, "lps": lps, "props": props, "species": species}
    return atoms, states, data, checked, uncovered


def _actual_deltas(before, after):
    bonds = [{"atoms": list(pair), "from_order": before["bonds"].get(pair, 0), "to_order": after["bonds"].get(pair, 0)}
             for pair in sorted(set(before["bonds"]) | set(after["bonds"]))
             if before["bonds"].get(pair, 0) != after["bonds"].get(pair, 0)]
    charges = [{"atom": a, "from": before["charges"][a], "to": after["charges"][a]}
               for a in sorted(before["charges"]) if before["charges"][a] != after["charges"][a]]
    return bonds, charges


def _change_maps(bonds, charges, atoms, path):
    bm, cm = {}, {}
    for change in bonds:
        _atom_refs(change["atoms"], atoms, path)
        key = _pair(change["atoms"])
        if key in bm or change["from_order"] == change["to_order"]:
            _fail("INVALID_BOND_CHANGE", path, "Bond changes must be unique nonzero changes")
        bm[key] = (change["from_order"], change["to_order"])
    for change in charges:
        _atom_refs([change["atom"]], atoms, path)
        if change["atom"] in cm or change["from"] == change["to"]:
            _fail("INVALID_CHARGE_CHANGE", path, "Charge changes must be unique nonzero changes")
        cm[change["atom"]] = (change["from"], change["to"])
    return bm, cm


def _flows(ir, atoms, states, data):
    transitions = _unique(ir["transitions"], "id", "$.transitions")
    compiled, diagnostics = [], []
    for index, tr in enumerate(ir["transitions"]):
        path = f"$.transitions[{index}]"
        if tr["from"] not in states or tr["to"] not in states or tr["from"] == tr["to"]:
            _fail("INVALID_TRANSITION_STATE", path, "Transitions must join two distinct existing states")
        before, after = data[tr["from"]], data[tr["to"]]
        if sum(before["charges"].values()) != sum(after["charges"].values()):
            _fail("CHARGE_NOT_CONSERVED", path, "Closed mapped inventory must conserve total formal charge")
        if sum(p["implicit_h"] for p in before["props"].values()) != sum(p["implicit_h"] for p in after["props"].values()):
            _fail("HYDROGEN_NOT_CONSERVED", path, "State implicit-H overrides must conserve total H in the closed inventory")
        actual_bc, actual_cc = _actual_deltas(before, after)
        actual_bm, actual_cm = _change_maps(actual_bc, actual_cc, atoms, path)
        declared_bm, declared_cm = _change_maps(tr["bond_changes"], tr["charge_changes"], atoms, path)
        if (actual_bm, actual_cm) != (declared_bm, declared_cm):
            _fail("GRAPH_DELTA_MISMATCH", path, "Declared bond/charge changes must exactly equal actual state differences", {"actual_bond_changes": actual_bc, "actual_charge_changes": actual_cc})
        _unique(tr["electron_flows"], "id", path + ".electron_flows")
        negative = {p for p, (a, b) in actual_bm.items() if b < a}
        positive = {p for p, (a, b) in actual_bm.items() if b > a}
        covered_negative, covered_positive = set(), set()
        flow_records, used_lp, used_radical = [], Counter(), Counter()
        used_bond, used_bond_pool = Counter(), Counter()
        for fi, flow in enumerate(tr["electron_flows"]):
            fp = f"{path}.electron_flows[{fi}]"
            source, sink = flow["source"], flow["sink"]
            source_atoms = source.get("atoms", [source.get("atom")])
            sink_atoms = sink.get("atoms", [sink.get("atom")])
            _atom_refs(source_atoms + sink_atoms, atoms, fp)
            withdrawals, deposits = set(), set()
            if source["type"] == "lone_pair":
                if flow["electron_count"] != 2 or source["pair_index"] >= before["lps"][source["atom"]]:
                    _fail("INVALID_LONE_PAIR_SOURCE", fp, "A two-electron source must reference an available pre-state chemical lone pair")
                key = (source["atom"], source["pair_index"])
                used_lp[key] += 1
                if used_lp[key] > 1:
                    _fail("REUSED_ELECTRON_SOURCE", fp, "A simultaneous transition cannot spend the same chemical lone pair twice")
            elif source["type"] == "bond":
                pair = _pair(source["atoms"])
                order = before["bonds"].get(pair, 0)
                if order == 0 or (source["electrons"] == "pi" and order < 1.5):
                    _fail("INVALID_BOND_SOURCE", fp, "Source bond/electron type is not available in the pre-state")
                if pair not in negative:
                    _fail("FLOW_GRAPH_MISMATCH", fp, "A bond source must correspond to a decrease of that bond in the actual graph")
                used_bond[pair] += flow["electron_count"]
                pool = (pair, source["electrons"])
                used_bond_pool[pool] += flow["electron_count"]
                decrease = before["bonds"][pair] - after["bonds"].get(pair, 0)
                if order == 1.5 or decrease % 1:
                    # Aromatic fractional orders do not define a localized
                    # electron-pair budget; never call that fully checked.
                    diagnostics.append({"code": "AROMATIC_ELECTRON_BUDGET_UNSUPPORTED", "transition_ref": tr["id"], "flow_ref": flow["id"]})
                else:
                    pool_budget = 2 if source["electrons"] == "sigma" else 2 * (order - 1)
                    if used_bond[pair] > 2 * decrease or used_bond_pool[pool] > pool_budget:
                        _fail("REUSED_ELECTRON_SOURCE", fp, "Bond-source spending exceeds its actual graph decrease or available sigma/pi electron pool", {"atoms": list(pair), "spent_electrons": used_bond[pair], "graph_decrease_budget": 2 * decrease, "pool_budget": pool_budget})
                if used_bond[pair] > 2 * order:
                    _fail("REUSED_ELECTRON_SOURCE", fp, "Bond-source spending exceeds total pre-state bond electrons")
                withdrawals.add(pair)
                if order == 1.5:
                    diagnostics.append({"code": "AROMATIC_FLOW_PROFILE_UNSUPPORTED", "transition_ref": tr["id"], "flow_ref": flow["id"]})
            elif source["type"] == "radical":
                atom = source["atom"]
                used_radical[atom] += 1
                if flow["electron_count"] != 1 or used_radical[atom] > before["props"][atom]["radical_electrons"]:
                    _fail("INVALID_RADICAL_SOURCE", fp, "A one-electron source must have available pre-state radical inventory")
            else:
                diagnostics.append({"code": "ATOM_SOURCE_PROFILE_UNSUPPORTED", "transition_ref": tr["id"], "flow_ref": flow["id"]})
            if flow["electron_count"] == 1:
                diagnostics.append({"code": "ONE_ELECTRON_ACCOUNTING_UNSUPPORTED", "transition_ref": tr["id"], "flow_ref": flow["id"]})
            if sink["type"] in {"bond", "forming_bond"}:
                pair = _pair(sink["atoms"])
                if pair not in positive:
                    _fail("FLOW_GRAPH_MISMATCH", fp, "A bond sink must increase that bond in the actual graph")
                if sink["type"] == "forming_bond" and before["bonds"].get(pair, 0) != 0:
                    _fail("FORMING_BOND_ALREADY_EXISTS", fp, "forming_bond denotes a pair absent from the pre-state")
                if not set(pair).intersection(source_atoms):
                    _fail("FLOW_GRAPH_MISMATCH", fp, "A bond sink must share a chemical atom with its donor; unrelated electron-transfer profiles are unsupported")
                deposits.add(pair)
            else:
                atom = sink["atom"]
                if source["type"] in {"lone_pair", "atom", "radical"} and source["atom"] == atom:
                    _fail("FLOW_GRAPH_MISMATCH", fp, "A local atomic electron source cannot donate back to the same atom")
                # A target atom can receive into a new/strengthened bond or a
                # nonbonding pool after bond cleavage. Never require it to be
                # an endpoint of the source bond.
                deposits = {pair for pair in positive if atom in pair and (set(pair) & set(source_atoms))}
                pool_gain = (2 * (after["lps"][atom] - before["lps"][atom]) + after["props"][atom]["radical_electrons"] - before["props"][atom]["radical_electrons"]) > 0
                charge_gain = after["charges"][atom] < before["charges"][atom]
                if not deposits and atom not in source_atoms and (pool_gain or charge_gain):
                    diagnostics.append({"code": "NONLOCAL_ELECTRON_TRANSFER_PROFILE_UNSUPPORTED", "transition_ref": tr["id"], "flow_ref": flow["id"], "reason": "A remote pool gain is not a checked local bond-cleavage destination"})
                if not deposits and not pool_gain and not charge_gain:
                    _fail("FLOW_GRAPH_MISMATCH", fp, "Atom sink has no related increasing bond or electron-pool/charge gain")
            if source["type"] in {"lone_pair", "radical"}:
                atom = source["atom"]
                loss = (2 * (before["lps"][atom] - after["lps"][atom]) + before["props"][atom]["radical_electrons"] - after["props"][atom]["radical_electrons"]) > 0
                if not loss and before["charges"][atom] >= after["charges"][atom] and not any(atom in pair for pair in positive):
                    _fail("FLOW_GRAPH_MISMATCH", fp, "Electron donor has no pool/charge loss or related increasing bond")
            if "effect" in flow:
                eb, ec = _change_maps(flow["effect"]["bond_changes"], flow["effect"]["charge_changes"], atoms, fp + ".effect")
                if any(actual_bm.get(p) != v for p, v in eb.items()) or any(actual_cm.get(a) != v for a, v in ec.items()):
                    _fail("FLOW_EFFECT_MISMATCH", fp + ".effect", "Flow effect must be a subset of actual state differences")
                if any(not (set(pair) & set(source_atoms + sink_atoms)) for pair in eb) or any(a not in source_atoms + sink_atoms for a in ec):
                    _fail("FLOW_EFFECT_UNRELATED", fp + ".effect", "Flow effect must touch its declared ports")
            covered_negative |= withdrawals
            covered_positive |= deposits
            flow_records.append({"id": flow["id"], "electron_count": flow["electron_count"], "source": deepcopy(source), "sink": deepcopy(sink), "related_bond_decreases": [list(x) for x in sorted(withdrawals)], "related_bond_increases": [list(x) for x in sorted(deposits)], "effect": deepcopy(flow.get("effect"))})
        if covered_negative != negative or covered_positive != positive:
            _fail("UNCOVERED_GRAPH_CHANGE", path, "Every bond decrease/increase must be related to an electron-flow source/sink", {"uncovered_decreases": [list(p) for p in sorted(negative - covered_negative)], "uncovered_increases": [list(p) for p in sorted(positive - covered_positive)]})
        compiled.append({"id": tr["id"], "from": tr["from"], "to": tr["to"], "electron_flows": flow_records, "bond_changes": actual_bc, "charge_changes": actual_cc})
    return transitions, compiled, diagnostics


def _depiction(ir, atoms, states, data, transitions):
    depictions = _unique(ir["depiction_states"], "state_ref", "$.depiction_states")
    if set(depictions) != set(states):
        _fail("DEPICTION_STATE_COVERAGE", "$.depiction_states", "Exactly one depiction record is required for every chemical state")
    for i, depiction in enumerate(ir["depiction_states"]):
        path = f"$.depiction_states[{i}]"
        state = data[depiction["state_ref"]]
        species = _unique(depiction["species"], "species_ref", path + ".species")
        if set(species) != set(state["species"]):
            _fail("DEPICTION_SPECIES_COVERAGE", path, "Every chemical species requires one explicit depiction role")
        caps = _unique(depiction["captions"], "id", path + ".captions")
        for cap in caps.values():
            if set(cap.get("species_refs", [])) - set(species):
                _fail("UNKNOWN_CAPTION_SPECIES", path, "Caption species refs must belong to this state")
            if "transition_ref" in cap:
                tr = transitions.get(cap["transition_ref"])
                if tr is None or tr["from"] != depiction["state_ref"]:
                    _fail("INVALID_CAPTION_TRANSITION", path, "Transition caption must be anchored to its source state")
        for ref, spec in species.items():
            if spec["role"] == "abbreviated" and "label" not in spec:
                _fail("ABBREVIATION_LABEL_REQUIRED", path, "Abbreviated species need an explicit label")
            if "attachment_atom_ref" in spec and (spec["role"] != "abbreviated" or spec["attachment_atom_ref"] not in state["species"][ref]["atoms"]):
                _fail("INVALID_ABBREVIATION_ATTACHMENT", path, "An abbreviation attachment atom must belong to that species")
            if spec["role"] in CAPTION_SPECIES_ROLES and not any(cap["role"] == CAPTION_SPECIES_ROLES[spec["role"]] and ref in cap.get("species_refs", []) for cap in caps.values()):
                _fail("SPECIES_CAPTION_REQUIRED", path, "Caption-only species require a corresponding typed caption")
        lp_entries = _unique(depiction["lone_pairs"], "atom_ref", path + ".lone_pairs")
        _atom_refs(lp_entries, atoms, path + ".lone_pairs")
        for atom, entry in lp_entries.items():
            count = entry["displayed_pairs"]
            if count > state["lps"][atom]:
                _fail("DISPLAYED_LP_EXCEEDS_CHEMICAL", path, "Displayed pairs cannot exceed chemical pair inventory")
            slots = _lp_slots(entry)
            if len(slots) != count or len({x["pair_index"] for x in slots}) != count or any(x["pair_index"] >= state["lps"][atom] for x in slots):
                _fail("INVALID_LP_SLOTS", path, "Slots must identify exactly the displayed number of distinct available chemical pairs")
            owner = next(ref for ref, sp in state["species"].items() if atom in sp["atoms"])
            role = species[owner]
            visible_owner = role["role"] == "explicitly_drawn" or (role["role"] == "abbreviated" and role.get("attachment_atom_ref") == atom)
            if count and not visible_owner:
                _fail("LP_OWNER_NOT_DEPICTED", path, "Displayed lone pairs require an explicitly visible atom or an explicit abbreviation attachment")
    return depictions


def _lp_slots(entry):
    return deepcopy(entry.get("slots", [{"pair_index": i, "orientation": "auto"} for i in range(entry["displayed_pairs"])]))


def _stereo(ir, atoms, states, data):
    for i, constraint in enumerate(ir["stereo_constraints"]):
        path = f"$.stereo_constraints[{i}]"
        a, b = constraint["central_bond"]
        sa, sb = constraint["substituent_atoms"]
        _atom_refs([a, b, sa, sb], atoms, path)
        if len({a, b, sa, sb}) != 4:
            _fail("INVALID_STEREO_REFERENCE", path, "Central atoms and substituent atoms must be distinct")
        for sid in constraint["states"]:
            if sid not in states:
                _fail("UNKNOWN_STEREO_STATE", path, "Stereo constraint references an unknown state")
            bonds = data[sid]["bonds"]
            if bonds.get(_pair([a, b])) != 2 or not bonds.get(_pair([a, sa])) or not bonds.get(_pair([b, sb])):
                _fail("STEREO_GRAPH_MISMATCH", path, "Ordered substituents must attach to the corresponding ends of a double bond")


def _checked(ir):
    _schema(ir)
    atoms, states, data, count, uncovered = _state_data(ir)
    transitions, compiled, diagnostics = _flows(ir, atoms, states, data)
    depiction = _depiction(ir, atoms, states, data, transitions)
    _stereo(ir, atoms, states, data)
    return atoms, states, data, transitions, compiled, diagnostics, depiction, count, uncovered


def validate_mechanism(ir):
    atoms, states, data, transitions, compiled, diagnostics, depiction, count, uncovered = _checked(ir)
    return {"ir_version": "mechanism-ir/0.2", "ir_sha256": canonical_sha256(ir),
            "checked_invariants": {"status": "pass", "atom_count": len(atoms), "state_count": len(states), "transition_count": len(transitions)},
            "chemical_validity": {"status": "not_established", "checked_status": "no_contradiction_in_checked_invariants", "limitations": ["No reaction feasibility, complete valence/stability, orbital or stereochemical proof", "Electron-flow coverage checks graph relationships, not a complete electron-accounting derivation"]},
            "valence_coverage": {"status": "partial" if uncovered else "covered_inventory_only", "checked_atom_states": count, "uncovered": uncovered, "profile": "H-C-N-O-F electron bookkeeping; no octet rule"},
            "electron_flow_coverage": {"status": "partial" if diagnostics else "checked_relationships_only", "diagnostics": diagnostics},
            "depiction": {"status": "intent_valid", "native_capability": "not_checked", "visual_quality": "not_measured"}}


def compile_electron_flows(ir):
    checked = _checked(ir)
    return {"compiled_version": "electron-flow/0.2", "ir_sha256": canonical_sha256(ir), "transitions": checked[4], "diagnostics": checked[5], "chemical_validity": "not_established", "coordinates": "not_generated"}


def migrate_v01(ir, *, policy="strict", depiction_states=None):
    if policy not in {"strict", "preserve_v01_display"}:
        _fail("UNKNOWN_MIGRATION_POLICY", "$.policy", "Migration policy must be explicitly supported")
    _schema(ir, LEGACY_SCHEMA_PATH)
    if policy == "strict" and depiction_states is None:
        _fail("MIGRATION_DEPICTION_REQUIRED", "$.depiction_states", "migration requires explicit depiction semantics")
    if policy == "preserve_v01_display" and depiction_states is not None:
        _fail("MIGRATION_POLICY_CONFLICT", "$.depiction_states", "Legacy preservation cannot also receive replacement depiction semantics")
    result = deepcopy(ir)
    result["ir_version"] = "mechanism-ir/0.2"
    atoms = _unique(result["atom_catalog"], "map", "$.atom_catalog")
    for index, state in enumerate(result["states"]):
        state["chemical_species"] = _species(atoms, _bonds(state, atoms, f"$.states[{index}]"))
    for tr in result["transitions"]:
        for flow in tr["electron_flows"]:
            flow["sink"] = flow.pop("target")
    if policy == "strict":
        result["depiction_states"] = deepcopy(depiction_states)
    else:
        result["depiction_states"] = []
        for state in result["states"]:
            caps = [{"id": "state-label", "role": "state_label", "text": state["label"]}]
            for tr in result["transitions"]:
                if tr["from"] == state["id"]:
                    caps.append({"id": "transition-label-" + canonical_sha256(tr["id"])[:20], "role": "annotation", "text": tr["label"], "transition_ref": tr["id"]})
            result["depiction_states"].append({"state_ref": state["id"], "species": [{"species_ref": sp["id"], "role": "explicitly_drawn"} for sp in state["chemical_species"]], "lone_pairs": [{"atom_ref": lp["atom"], "displayed_pairs": lp["count"], "slots": [{"pair_index": i, "orientation": "auto"} for i in range(lp["count"])]} for lp in state["lone_pairs"]], "captions": caps})
    result["migration"] = {"source_version": "mechanism-ir/0.1", "policy": policy, "source_sha256": canonical_sha256(ir)}
    validate_mechanism(result)
    return result


def _occurrence(kind, state, identity):
    return kind + "-" + canonical_sha256([state, identity])[:24]


def lower_depiction(ir):
    atoms, states, data, transitions, compiled, flow_diagnostics, depictions, _, _ = _checked(ir)
    plans, lookup, diagnostics = [], {}, list(flow_diagnostics)
    for sid, state in states.items():
        sd, dep = data[sid], depictions[sid]
        visible_atoms, visible_bonds, abbreviations, hidden, lp_slots = [], [], [], [], []
        atom_ports, selected_pairs = {}, {}
        for spec in dep["species"]:
            ref, role = spec["species_ref"], spec["role"]
            chemical_atoms = sd["species"][ref]["atoms"]
            if role == "explicitly_drawn":
                for atom in chemical_atoms:
                    occurrence = _occurrence("atom", sid, atom)
                    atom_ports[atom] = {"kind": "atom", "occurrence_ref": occurrence, "atom_ref": atom}
                    visible_atoms.append({"occurrence_ref": occurrence, "atom_ref": atom, "species_ref": ref, "element": atoms[atom]["element"], "formal_charge": sd["charges"][atom], "chemical_lone_pairs": sd["lps"][atom], **sd["props"][atom]})
            elif role == "abbreviated":
                occurrence = _occurrence("abbreviation", sid, ref)
                entry = {"occurrence_ref": occurrence, "species_ref": ref, "label": spec["label"], "chemical_atom_refs": list(chemical_atoms)}
                if "attachment_atom_ref" in spec:
                    atom = spec["attachment_atom_ref"]
                    entry["attachment_atom_ref"] = atom
                    atom_ports[atom] = {"kind": "abbreviation_attachment", "occurrence_ref": occurrence, "atom_ref": atom}
                abbreviations.append(entry)
            else:
                hidden.append({"species_ref": ref, "chemical_atom_refs": list(chemical_atoms), "reason": role})
        for pair, order in sorted(sd["bonds"].items()):
            if all(a in atom_ports and atom_ports[a]["kind"] == "atom" for a in pair):
                visible_bonds.append({"occurrence_ref": _occurrence("bond", sid, list(pair)), "atoms": list(pair), "order": order, "atom_occurrence_refs": [atom_ports[a]["occurrence_ref"] for a in pair]})
        for entry in dep["lone_pairs"]:
            atom = entry["atom_ref"]
            selected_pairs[atom] = {x["pair_index"] for x in _lp_slots(entry)}
            for slot in _lp_slots(entry):
                lp_slots.append({"occurrence_ref": _occurrence("lone-pair", sid, [atom, slot["pair_index"]]), "atom_ref": atom, "owner_occurrence_ref": atom_ports[atom]["occurrence_ref"], **slot})
        captions = [{"occurrence_ref": _occurrence("caption", sid, cap["id"]), "state_ref": sid, **deepcopy(cap)} for cap in dep["captions"]]
        plan = {"state_ref": sid, "visible_atoms": visible_atoms, "visible_bonds": visible_bonds, "abbreviations": abbreviations, "lone_pair_slots": lp_slots, "captions": captions, "hidden_species": hidden}
        plans.append(plan)
        lookup[sid] = (atom_ports, selected_pairs)
    lowered_flows = []
    for tr in compiled:
        atom_ports, selected_pairs = lookup[tr["from"]]
        for flow in tr["electron_flows"]:
            ports = {}
            for name in ("source", "sink"):
                chemical = flow[name]
                refs = chemical.get("atoms", [chemical.get("atom")])
                missing = [a for a in refs if a not in atom_ports]
                if missing:
                    diagnostic = {"code": "DEPICTION_PORT_UNRESOLVED", "transition_ref": tr["id"], "flow_ref": flow["id"], "port": name, "atom_refs": missing, "reason": "hidden species or unanchored abbreviation has no visible chemical atom port"}
                    diagnostics.append(diagnostic)
                    ports[name] = {"status": "unresolved", "chemical_port": deepcopy(chemical), "diagnostic": diagnostic["code"]}
                    continue
                port = {"status": "resolved_intent", "chemical_port": deepcopy(chemical), "atom_ports": [deepcopy(atom_ports[a]) for a in refs]}
                if chemical["type"] == "lone_pair":
                    atom, index = chemical["atom"], chemical["pair_index"]
                    if index in selected_pairs.get(atom, set()):
                        port.update({"kind": "displayed_lone_pair", "occurrence_ref": _occurrence("lone-pair", tr["from"], [atom, index])})
                    else:
                        port.update({"kind": "virtual_lone_pair", "strategy": "atom_associated", "draw_lone_pair": False})
                elif chemical["type"] in {"bond", "forming_bond"}:
                    port["kind"] = chemical["type"]
                    if any(atom_ports[a]["kind"] != "atom" for a in refs):
                        diagnostic = {"code": "ABBREVIATED_BOND_PORT_UNSUPPORTED", "transition_ref": tr["id"], "flow_ref": flow["id"], "port": name}
                        diagnostics.append(diagnostic)
                        port["status"] = "unresolved"
                        port["diagnostic"] = diagnostic["code"]
                    elif chemical["type"] == "bond":
                        # A sink bond may be newly formed, so it has no pre-state
                        # ink. Keep it an explicit prospective bond port.
                        pair = _pair(chemical["atoms"])
                        if pair in data[tr["from"]]["bonds"]:
                            port["occurrence_ref"] = _occurrence("bond", tr["from"], list(pair))
                        else:
                            port["kind"] = "forming_bond"
                else:
                    port["kind"] = chemical["type"]
                ports[name] = port
            lowered_flows.append({"transition_ref": tr["id"], "flow_ref": flow["id"], "state_ref": tr["from"], "electron_count": flow["electron_count"], **ports})
    inventory = {"atom_catalog": deepcopy(ir["atom_catalog"]), "states": deepcopy(ir["states"]), "transitions": deepcopy(ir["transitions"]), "stereo_constraints": deepcopy(ir["stereo_constraints"]), "entry_state": ir["entry_state"]}
    depiction_payload = {"plan_version": "lowered-depiction/0.2", "states": plans, "electron_flows": lowered_flows, "diagnostics": diagnostics}
    return {**depiction_payload, "ir_sha256": canonical_sha256(ir), "chemical_inventory": inventory,
            "chemical_inventory_sha256": canonical_sha256(inventory), "depiction_plan_sha256": canonical_sha256(depiction_payload),
            "status": "unresolved_depiction" if diagnostics else "intent_lowered", "native_capability": "not_checked", "geometry": "not_generated"}


def validate_depiction_capabilities(ir, capabilities):
    if not isinstance(capabilities, dict):
        _fail("INVALID_CAPABILITY_DECLARATION", "$.capabilities", "Capabilities must be an explicit mapping")
    allowed = {"elements", "isotopes", "radicals", "roles", "flow_electron_counts", "virtual_lone_pair_ports", "orientations", "typed_captions"}
    if set(capabilities) - allowed:
        _fail("INVALID_CAPABILITY_DECLARATION", "$.capabilities", "Unknown capability keys", {"keys": sorted(set(capabilities) - allowed)})
    for key in ("elements", "roles", "flow_electron_counts", "orientations"):
        if key in capabilities and (not isinstance(capabilities[key], list) or any(isinstance(x, (list, dict, bool)) for x in capabilities[key])):
            _fail("INVALID_CAPABILITY_DECLARATION", "$.capabilities." + key, "Capability values must be explicit lists")
    for key in ("isotopes", "radicals", "virtual_lone_pair_ports", "typed_captions"):
        if key in capabilities and not isinstance(capabilities[key], bool):
            _fail("INVALID_CAPABILITY_DECLARATION", "$.capabilities." + key, "Capability value must be boolean")
    plan = lower_depiction(ir)
    requirements = defaultdict(set)
    for state in plan["states"]:
        for atom in state["visible_atoms"]:
            requirements["elements"].add(atom["element"])
            if "isotope" in atom:
                requirements["isotopes"].add(True)
            if atom["radical_electrons"]:
                requirements["radicals"].add(True)
        for lp in state["lone_pair_slots"]:
            requirements["orientations"].add(lp["orientation"])
        if state["captions"]:
            requirements["typed_captions"].add(True)
    for dep in ir["depiction_states"]:
        requirements["roles"].update(x["role"] for x in dep["species"])
    for flow in plan["electron_flows"]:
        requirements["flow_electron_counts"].add(flow["electron_count"])
        if flow["source"].get("kind") == "virtual_lone_pair":
            requirements["virtual_lone_pair_ports"].add(True)
    issues = list(plan["diagnostics"])
    for key, values in sorted(requirements.items()):
        for value in sorted(values, key=str):
            if key not in capabilities:
                issues.append({"code": "DEPICTION_CAPABILITY_UNKNOWN", "capability": key, "required": value})
            elif isinstance(capabilities[key], list) and value not in capabilities[key] or isinstance(capabilities[key], bool) and not capabilities[key]:
                issues.append({"code": "DEPICTION_CAPABILITY_UNSUPPORTED", "capability": key, "required": value})
    return {"ir_sha256": canonical_sha256(ir), "status": "unsupported_or_unknown" if issues else "declared_capabilities_cover_intent", "diagnostics": issues, "native_execution": "not_performed", "chemical_validity": "not_established"}
