"""Evaluator-only, scoped chemistry/depiction comparison for Mechanism IR v0.2.

This module does no target-file I/O, matching by native IDs, proximity inference,
rendering or model inference. The caller owns target custody and must supply:

* candidate_ir: the unmodified mechanism-ir/0.2 candidate;
* target: {version: 'paired-depiction-target/0.1', qualifications: {...},
  chemical_states: [...], depiction_states: [...], transitions: [...]};
* correspondence: {status, evidence_refs, atoms: {target_ref: candidate_map},
  states: {target_ref: candidate_id}, transitions: {target_ref: candidate_id}}.

Qualifications are separate for chemical, depiction, displayed_lp,
condition_only and flow_semantic. Each has status qualified/partial/unknown/
rejected and evidence_refs. These are caller assertions, not authenticated
reviewer identities. A missing qualification never becomes a successful match.

Target chemical states contain state_ref, atoms (atom_ref plus observed element,
formal_charge, implicit_h, isotope, radical_electrons, chemical_lone_pairs),
bonds (atom_refs, order), atom_inventory_complete and bond_inventory_complete.
None means unknown. Target depiction states contain state_ref, species
(atom_refs, role, optional label), lone_pairs (nullable atom_ref, displayed_pairs,
optional slots), captions (role, text, optional atom_refs), and independent
species_inventory_complete/lone_pair_inventory_complete/caption_inventory_complete.
Target transitions contain transition_ref, from_state_ref, to_state_ref,
electron_flows (electron_count, source, sink), flow_inventory_complete. Endpoint
atom_ref/atom_refs are target semantic references; no geometry is accepted as
semantic ownership. A bond source also needs its sigma/pi electrons annotation.

Inventory completeness is local to a state or transition and to the declared
annotation layer. Incomplete native drawings are not complete chemical targets.
Result 'match' means equality in the stated annotation scope, never chemistry,
native rendering, editability, human acceptance or gold qualification.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import math
from typing import Any, Literal, TypedDict

Status = Literal["match", "mismatch", "partial", "unknown", "reported"]


class LayerResult(TypedDict):
    status: Status
    observations: list[dict[str, Any]]
    scope: str


LAYERS = ("chemical", "depiction", "omitted_by_design", "condition_only",
          "displayed_lp", "flow_semantic", "geometry")
QUALIFIED_LAYERS = ("chemical", "depiction", "condition_only", "displayed_lp", "flow_semantic")
HIDDEN_ROLES = {"counterion_hidden", "spectator_hidden", "implicit", "omitted_by_convention"}
CAPTION_ROLES = {"condition_caption", "reagent_caption", "catalyst_caption"}
SPECIES_ROLES = HIDDEN_ROLES | CAPTION_ROLES | {"explicitly_drawn", "abbreviated"}
TEXT_ROLES = {"condition", "reagent", "catalyst", "solvent", "temperature", "time",
              "workup", "annotation", "state_label", "molecule_label"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _finite_json(value: Any) -> None:
    if isinstance(value, float):
        _require(math.isfinite(value), "Non-finite annotation or measurement")
    elif isinstance(value, dict):
        for item in value.values():
            _finite_json(item)
    elif isinstance(value, list):
        for item in value:
            _finite_json(item)


def _ref(value: Any) -> str:
    _require(isinstance(value, str) and bool(value.strip()), "A nonempty target semantic reference is required")
    return value


def _integer(value: Any, *, minimum: int | None = None) -> int:
    _require(type(value) is int and (minimum is None or value >= minimum), "Invalid integer annotation")
    return value


def _rows(value: Any, name: str) -> list[dict[str, Any]]:
    _require(isinstance(value, list) and all(isinstance(x, dict) for x in value), f"{name} must be an array of objects")
    return value


def _complete(row: dict, key: str) -> bool:
    value = row.get(key, False)
    _require(type(value) is bool, f"{key} must be boolean")
    return value


def _qualification(value: Any) -> dict:
    if value is None:
        return {"status": "unknown", "evidence_refs": []}
    _require(isinstance(value, dict), "Qualification must be an object")
    _require(value.get("status") in {"qualified", "partial", "unknown", "rejected"}, "Invalid qualification status")
    refs = value.get("evidence_refs", [])
    _require(isinstance(refs, list) and all(isinstance(x, str) and x.strip() for x in refs), "Invalid qualification evidence references")
    if value["status"] in {"qualified", "partial"}:
        _require(bool(refs), "Usable qualification requires evidence references")
    return deepcopy(value)


def _event(results: dict, layer: str, status: str, reason: str, **context: Any) -> None:
    results[layer]["observations"].append({"status": status, "reason": reason, **context})


def _equal(results: dict, layer: str, expected: Any, actual: Any, reason: str, **context: Any) -> None:
    _event(results, layer, "match" if expected == actual else "mismatch", reason,
           target=expected, candidate=actual, **context)


def _finish(results: dict) -> None:
    for row in results.values():
        statuses = {x["status"] for x in row["observations"]}
        row["status"] = ("mismatch" if "mismatch" in statuses else
                         "partial" if "unknown" in statuses and ("match" in statuses or "reported" in statuses) else
                         "match" if "match" in statuses else
                         "reported" if statuses == {"reported"} else "unknown")


def _target_atoms(row: dict, atom_map: dict) -> list[int] | None:
    refs = row.get("atom_refs")
    _require(isinstance(refs, list) and bool(refs), "atom_refs must be a nonempty array")
    refs = [_ref(x) for x in refs]
    _require(len(refs) == len(set(refs)), "Duplicate target atom reference")
    return [atom_map[x] for x in refs] if all(x in atom_map for x in refs) else None


def _endpoint(endpoint: Any, atom_map: dict, source: bool) -> tuple | None:
    if endpoint is None:
        return None
    _require(isinstance(endpoint, dict), "Endpoint must be an object or null")
    kind = endpoint.get("type")
    _require(kind in {"lone_pair", "bond", "forming_bond", "atom", "radical"}, "Unknown endpoint kind")
    if kind in {"bond", "forming_bond"}:
        atoms = _target_atoms(endpoint, atom_map)
        if atoms is None:
            return None
        _require(len(atoms) == 2, "Bond endpoint requires two atoms")
        electrons = endpoint.get("electrons") if source else None
        if source and electrons is None:
            return None
        if source:
            _require(electrons in {"sigma", "pi"}, "Invalid source-bond electron annotation")
        return kind, tuple(sorted(atoms)), electrons
    atom = endpoint.get("atom_ref")
    if atom is None:
        return None
    atom = _ref(atom)
    return (kind, atom_map[atom]) if atom in atom_map else None


def _candidate_endpoint(endpoint: dict, source: bool) -> tuple:
    kind = endpoint["type"]
    if kind in {"bond", "forming_bond"}:
        return kind, tuple(sorted(endpoint["atoms"])), endpoint.get("electrons") if source else None
    # Chemical LP identity is the donor atom; chemically equivalent pairs do not
    # acquire distinct identities merely from their display slot number.
    return kind, endpoint["atom"]


def compare_semantics(candidate_ir: dict, target: dict | None = None, *,
                      correspondence: dict | None = None,
                      geometry_report: dict | None = None,
                      expected_native_hashes: dict | None = None) -> dict:
    """Compare qualified annotation subsets; always leave acceptance gates unknown.

    A geometry_report may be an existing paired-evaluation/1.0 result. Its partial
    deltas are retained as measurements, not reinterpreted as thresholded failures
    or native-visual PASS. Optional expected_native_hashes must contain both
    target_sha256 and candidate_sha256 from the actual native artifact custody
    record, never from an IR hash. This function does not authenticate those
    artifacts or prove their relationship to candidate_ir. No implicit
    target/candidate reference matching occurs.
    """
    from contracts.ir_v02 import IRContractError, validate_mechanism

    _finite_json(candidate_ir)
    _finite_json(target)
    _finite_json(correspondence)
    _finite_json(geometry_report)
    _require(expected_native_hashes is None or geometry_report is not None, "Expected native hashes require a geometry report")
    results: dict[str, LayerResult] = {
        name: {"status": "unknown", "observations": [], "scope": "qualified annotation subset only"}
        for name in LAYERS
    }
    try:
        validation = validate_mechanism(candidate_ir)
        ir_validation = {"status": "valid", "report": validation,
                         "independent_chemical_qualification": "unknown"}
    except (IRContractError, ValueError) as exc:
        ir_validation = {"status": "invalid", "reason": str(exc),
                         "independent_chemical_qualification": "unknown"}
        for layer in LAYERS:
            _event(results, layer, "unknown", "Candidate IR validation failed")
        return _result(results, ir_validation, {}, None)

    target = target if target is not None else {"version": "paired-depiction-target/0.1", "qualifications": {}}
    _require(isinstance(target, dict), "Target annotation must be an object")
    _require(target.get("version") == "paired-depiction-target/0.1", "Unsupported target annotation version")
    qualifiers = target.get("qualifications", {})
    _require(isinstance(qualifiers, dict), "qualifications must be an object")
    qualifications = {name: _qualification(qualifiers.get(name)) for name in QUALIFIED_LAYERS}
    corr = correspondence or {"status": "unknown", "evidence_refs": []}
    corr_qualification = _qualification(corr)
    usable_correspondence = corr_qualification["status"] == "qualified"
    atoms = {x["map"]: x for x in candidate_ir["atom_catalog"]}
    states = {x["id"]: x for x in candidate_ir["states"]}
    transitions = {x["id"]: x for x in candidate_ir["transitions"]}
    depictions = {x["state_ref"]: x for x in candidate_ir["depiction_states"]}
    maps = {}
    for name, available in (("atoms", atoms), ("states", states), ("transitions", transitions)):
        mapping = corr.get(name, {})
        _require(isinstance(mapping, dict), f"{name} correspondence must be an object")
        for key, value in mapping.items():
            _ref(key)
            if name == "atoms":
                _integer(value, minimum=1)
            else:
                _ref(value)
            _require(value in available, f"Unknown candidate {name} reference")
        _require(len(mapping.values()) == len(set(mapping.values())), f"Non-injective {name} correspondence")
        maps[name] = mapping if usable_correspondence else {}
    atom_map, state_map, transition_map = (maps[x] for x in ("atoms", "states", "transitions"))

    for state_ref, depiction in depictions.items():
        for species in depiction["species"]:
            role = species["role"]
            if role in HIDDEN_ROLES | CAPTION_ROLES:
                layer = "omitted_by_design" if role in HIDDEN_ROLES else "condition_only"
                _event(results, layer, "reported", "Candidate depiction declaration; not observed native output",
                       side="candidate", state=state_ref, species=species["species_ref"], role=role)

    def allowed(layer: str) -> bool:
        if not usable_correspondence:
            _event(results, layer, "unknown", "No qualified semantic correspondence")
            return False
        qualification = qualifications[layer]
        if qualification["status"] not in {"qualified", "partial"}:
            _event(results, layer, "unknown", "Target annotation is not qualified for this layer")
            return False
        if qualification["status"] == "partial":
            _event(results, layer, "unknown", "Target qualification covers only a partial scope")
        return True

    if allowed("chemical"):
        chemical_states = _rows(target.get("chemical_states", []), "chemical_states")
        if not chemical_states:
            _event(results, "chemical", "unknown", "No qualified chemical state annotations")
        seen_states = set()
        for observed in chemical_states:
            target_state = _ref(observed["state_ref"])
            _require(target_state not in seen_states, "Duplicate chemical state annotation")
            seen_states.add(target_state)
            state_id = state_map.get(target_state)
            if state_id is None:
                _event(results, "chemical", "unknown", "Unmapped chemical state", state=target_state)
                continue
            state = states[state_id]
            charge = {x["atom"]: x["value"] for x in state["formal_charges"]}
            lp = {x["atom"]: x["count"] for x in state["lone_pairs"]}
            overrides = {x["atom"]: x for x in state.get("atom_properties", [])}
            observed_atoms = _rows(observed.get("atoms", []), "chemical atoms")
            seen_atoms, mapped_atoms = set(), set()
            for row in observed_atoms:
                ref = _ref(row["atom_ref"])
                _require(ref not in seen_atoms, "Duplicate chemical atom annotation")
                seen_atoms.add(ref)
                atom = atom_map.get(ref)
                if atom is None:
                    _event(results, "chemical", "unknown", "Unmapped chemical atom", atom=ref)
                    continue
                mapped_atoms.add(atom)
                actual = {"element": atoms[atom]["element"],
                          "formal_charge": charge.get(atom, 0),
                          "chemical_lone_pairs": lp.get(atom, 0),
                          "implicit_h": overrides.get(atom, {}).get("implicit_h", atoms[atom].get("implicit_h", 0)),
                          "isotope": overrides.get(atom, {}).get("isotope", atoms[atom].get("isotope", 0)),
                          "radical_electrons": overrides.get(atom, {}).get("radical_electrons", atoms[atom].get("radical_electrons", 0))}
                known = 0
                for field, value in actual.items():
                    if field not in row or row[field] is None:
                        continue
                    expected = row[field]
                    if field == "element":
                        _require(isinstance(expected, str) and bool(expected), "Invalid element annotation")
                    else:
                        _integer(expected, minimum=None if field == "formal_charge" else 0)
                    _equal(results, "chemical", expected, value, "Chemical atom property", state=state_id, atom=atom, field=field)
                    known += 1
                if known < len(actual):
                    _event(results, "chemical", "unknown", "Chemical atom properties are only partially annotated", state=state_id, atom=atom)
            candidate_bonds = {tuple(sorted(x["atoms"])): x["order"] for x in state["bonds"]}
            seen_bonds = set()
            for bond in _rows(observed.get("bonds", []), "chemical bonds"):
                pair = _target_atoms(bond, atom_map)
                if pair is None:
                    _event(results, "chemical", "unknown", "Unmapped chemical bond", state=state_id)
                    continue
                _require(len(pair) == 2, "Chemical bond requires two atoms")
                key = tuple(sorted(pair))
                _require(key not in seen_bonds, "Duplicate chemical bond annotation")
                seen_bonds.add(key)
                order = bond.get("order")
                if order is None:
                    _event(results, "chemical", "unknown", "Chemical bond order is unknown", state=state_id, atoms=pair)
                else:
                    _require(type(order) in (int, float) and order in {0, 1, 1.5, 2, 3}, "Invalid chemical bond order")
                    _equal(results, "chemical", order, candidate_bonds.get(key, 0), "Chemical bond order", state=state_id, atoms=pair)
            all_mapped = len(mapped_atoms) == len(observed_atoms)
            if _complete(observed, "atom_inventory_complete") and all_mapped:
                _equal(results, "chemical", sorted(mapped_atoms), sorted(atoms), "Complete chemical atom inventory", state=state_id)
            else:
                _event(results, "chemical", "unknown", "Unshown species are not assumed chemically absent", state=state_id)
            if _complete(observed, "bond_inventory_complete") and all_mapped:
                extra = sorted(k for k in candidate_bonds if set(k) <= mapped_atoms and k not in seen_bonds)
                _equal(results, "chemical", [], extra, "Additional bonds within annotated atom scope", state=state_id)
            else:
                _event(results, "chemical", "unknown", "Chemical bond inventory is incomplete", state=state_id)

    depiction_allowed = allowed("depiction")
    lp_allowed = allowed("displayed_lp")
    caption_allowed = allowed("condition_only")
    observed_depictions = _rows(target.get("depiction_states", []), "depiction_states")
    seen_states = set()
    for observed in observed_depictions:
        target_state = _ref(observed["state_ref"])
        _require(target_state not in seen_states, "Duplicate depiction state annotation")
        seen_states.add(target_state)
        state_id = state_map.get(target_state)
        if state_id is None:
            for layer, enabled in (("depiction", depiction_allowed), ("displayed_lp", lp_allowed), ("condition_only", caption_allowed)):
                if enabled:
                    _event(results, layer, "unknown", "Unmapped depiction state", state=target_state)
            continue
        depiction, state = depictions[state_id], states[state_id]
        species_atoms = {x["id"]: tuple(sorted(x["atoms"])) for x in state["chemical_species"]}
        drawn = {species_atoms[x["species_ref"]]: x for x in depiction["species"]}
        if depiction_allowed:
            seen_species = set()
            for row in _rows(observed.get("species", []), "depicted species"):
                _require(row.get("role") in SPECIES_ROLES, "Invalid target depiction role")
                mapped = _target_atoms(row, atom_map)
                if mapped is None:
                    _event(results, "depiction", "unknown", "Unmapped depicted species", state=state_id)
                    continue
                key = tuple(sorted(mapped))
                _require(key not in seen_species, "Duplicate depicted species annotation")
                seen_species.add(key)
                actual = drawn.get(key)
                if actual is None:
                    _event(results, "depiction", "unknown", "No qualified same-species partition in candidate", state=state_id, atoms=list(key))
                    continue
                _equal(results, "depiction", row["role"], actual["role"], "Species depiction role", state=state_id, atoms=list(key))
                if "label" in row and row["label"] is not None:
                    _require(isinstance(row["label"], str), "Invalid abbreviation label")
                    _equal(results, "depiction", row["label"], actual.get("label"), "Species abbreviation/caption label", state=state_id, atoms=list(key))
                if row["role"] in HIDDEN_ROLES | CAPTION_ROLES:
                    layer = "omitted_by_design" if row["role"] in HIDDEN_ROLES else "condition_only"
                    _event(results, layer, "reported", "Target depiction declaration; does not remove chemical inventory",
                           side="target", state=state_id, atoms=list(key), role=row["role"])
            if not _complete(observed, "species_inventory_complete"):
                _event(results, "depiction", "unknown", "Target depicted-species inventory is incomplete", state=state_id)
            elif len(seen_species) == len(observed.get("species", [])):
                # Omitted target species are compared only when depiction scope is
                # explicitly complete; this remains a display-layer finding.
                _equal(results, "depiction", [], [list(k) for k in sorted(set(drawn) - seen_species)
                       if drawn[k]["role"] not in HIDDEN_ROLES], "Additional candidate depicted species", state=state_id)
        if lp_allowed:
            visible = {x["atom_ref"]: x for x in depiction["lone_pairs"]}
            seen_lp, unresolved_lp = set(), False
            for row in _rows(observed.get("lone_pairs", []), "displayed lone pairs"):
                ref = row.get("atom_ref")
                if ref is not None:
                    _ref(ref)
                if ref is None or ref not in atom_map:
                    unresolved_lp = True
                    _event(results, "displayed_lp", "unknown", "Target LP ownership is unknown; proximity is not ownership", state=state_id)
                    continue
                atom = atom_map[_ref(ref)]
                _require(atom not in seen_lp, "Duplicate displayed LP atom annotation")
                seen_lp.add(atom)
                count = row.get("displayed_pairs")
                if count is None:
                    _event(results, "displayed_lp", "unknown", "Target displayed LP count is unknown", state=state_id, atom=atom)
                    continue
                _integer(count, minimum=0)
                _equal(results, "displayed_lp", count, visible.get(atom, {}).get("displayed_pairs", 0), "Displayed LP count only; not chemical LP count", state=state_id, atom=atom)
                if row.get("slots") is not None:
                    slots = _rows(row["slots"], "LP slots")
                    indices = [_integer(x.get("pair_index"), minimum=0) for x in slots]
                    _require(len(indices) == len(set(indices)), "Duplicate LP slot index")
                    _require(len(indices) == count, "LP slot annotations must cover the declared displayed pairs")
                    if any(not isinstance(x.get("orientation"), str) or not x["orientation"].strip() for x in slots):
                        _event(results, "displayed_lp", "unknown", "Target LP orientation is not annotated", state=state_id, atom=atom)
                    else:
                        entry = visible.get(atom, {"displayed_pairs": 0})
                        actual_slots = entry.get("slots", [{"pair_index": i, "orientation": "auto"} for i in range(entry["displayed_pairs"])])
                        canonical = lambda items: sorted((x["pair_index"], x["orientation"]) for x in items)
                        _equal(results, "displayed_lp", canonical(slots), canonical(actual_slots), "Declared LP display slots only; no measured native direction", state=state_id, atom=atom)
            if _complete(observed, "lone_pair_inventory_complete") and not unresolved_lp:
                extra = sorted(atom for atom, row in visible.items() if atom not in seen_lp and row["displayed_pairs"] > 0)
                _equal(results, "displayed_lp", [], extra, "Additional explicitly displayed LP owners", state=state_id)
            else:
                _event(results, "displayed_lp", "unknown", "Displayed LP inventory is incomplete or ownership unresolved", state=state_id)
        if caption_allowed:
            expected = []
            unresolved = False
            for caption in _rows(observed.get("captions", []), "captions"):
                _require(caption.get("role") in TEXT_ROLES and isinstance(caption.get("text"), str), "Caption needs typed role and text")
                binding = None
                if "atom_refs" in caption:
                    mapped = _target_atoms(caption, atom_map)
                    if mapped is None:
                        unresolved = True
                        _event(results, "condition_only", "unknown", "Unmapped caption chemical binding", state=state_id)
                        continue
                    binding = tuple(sorted(mapped))
                expected.append((caption["role"], " ".join(caption["text"].split()), binding))
            actual = []
            for caption in depiction["captions"]:
                linked = [a for ref in caption.get("species_refs", []) for a in species_atoms[ref]]
                actual.append((caption["role"], " ".join(caption["text"].split()), tuple(sorted(linked)) if linked else None))
            # An unbound target caption can qualify role/text without asserting an
            # unknown chemical owner. Bound target captions retain that check.
            remaining = list(actual)
            missing = []
            for item in sorted(expected, key=lambda row: row[2] is None):
                matches = [i for i, other in enumerate(remaining) if item[:2] == other[:2] and (item[2] is None or item[2] == other[2])]
                if matches:
                    remaining.pop(matches[0])
                else:
                    missing.append(item)
            _equal(results, "condition_only", [], missing, "Missing or differently typed condition/caption declarations", state=state_id)
            if _complete(observed, "caption_inventory_complete") and not unresolved:
                _equal(results, "condition_only", [], remaining, "Additional condition/caption declarations", state=state_id)
            else:
                _event(results, "condition_only", "unknown", "Caption inventory is incomplete", state=state_id)
    if not observed_depictions:
        for layer, enabled in (("depiction", depiction_allowed), ("displayed_lp", lp_allowed), ("condition_only", caption_allowed)):
            if enabled:
                _event(results, layer, "unknown", "No target depiction annotations")

    if allowed("flow_semantic"):
        observed_transitions = _rows(target.get("transitions", []), "transitions")
        seen_transitions = set()
        for observed in observed_transitions:
            ref = _ref(observed["transition_ref"])
            _require(ref not in seen_transitions, "Duplicate transition annotation")
            seen_transitions.add(ref)
            tid = transition_map.get(ref)
            if tid is None:
                _event(results, "flow_semantic", "unknown", "Unmapped transition", transition=ref)
                continue
            transition = transitions[tid]
            for role, key in (("from", "from_state_ref"), ("to", "to_state_ref")):
                state_ref = observed.get(key)
                if state_ref is not None:
                    _ref(state_ref)
                if state_ref is None or state_ref not in state_map:
                    _event(results, "flow_semantic", "unknown", "Unmapped flow transition state", transition=tid, role=role)
                else:
                    _equal(results, "flow_semantic", state_map[state_ref], transition[role], "Flow transition state", transition=tid, role=role)
            known, unresolved = [], False
            for flow in _rows(observed.get("electron_flows", []), "electron flows"):
                source = _endpoint(flow.get("source"), atom_map, True)
                sink = _endpoint(flow.get("sink"), atom_map, False)
                count = flow.get("electron_count")
                if source is None or sink is None or count is None:
                    unresolved = True
                    _event(results, "flow_semantic", "unknown", "Unqualified source/sink/electron count; native port is not inferred", transition=tid)
                    continue
                _integer(count, minimum=1)
                _require(count in (1, 2), "Invalid electron count annotation")
                known.append((count, source, sink))
            actual = Counter((x["electron_count"], _candidate_endpoint(x["source"], True),
                              _candidate_endpoint(x["sink"], False)) for x in transition["electron_flows"])
            wanted = Counter(known)
            missing = list((wanted - actual).elements())
            _equal(results, "flow_semantic", [], missing, "Missing or different electron-flow intent", transition=tid)
            if _complete(observed, "flow_inventory_complete") and not unresolved:
                _equal(results, "flow_semantic", [], list((actual - wanted).elements()), "Additional electron-flow intent", transition=tid)
            else:
                _event(results, "flow_semantic", "unknown", "Electron-flow inventory is incomplete", transition=tid)
        if not observed_transitions:
            _event(results, "flow_semantic", "unknown", "No qualified target flow semantics")

    if geometry_report is not None:
        from contracts.paired.validate_paired import validate as validate_paired
        from jsonschema import ValidationError
        _require(isinstance(geometry_report, dict), "Geometry report must be an object")
        try:
            validate_paired("evaluator", geometry_report)
        except (ValidationError, ValueError) as exc:
            raise ValueError(f"Invalid upstream geometry evidence: {exc}") from exc
        binding = {key: geometry_report[key] for key in ("target_sha256", "candidate_sha256")}
        if expected_native_hashes is not None:
            _require(isinstance(expected_native_hashes, dict) and set(expected_native_hashes) == set(binding),
                     "Expected native hashes must name both target and candidate artifacts")
            _require(binding == expected_native_hashes, "Native geometry artifact hash mismatch")
        geometry = geometry_report["geometry"]
        deltas = geometry_report["correction"]["deltas"]
        measured_count = sum(x["value"] is not None for x in deltas)
        if measured_count:
            _event(results, "geometry", "reported", "Schema-checked upstream partial geometry measurements; no thresholded mismatch decision",
                   upstream_status=geometry.get("status", "unknown"), delta_count=measured_count, **binding,
                   expected_native_hashes_checked=expected_native_hashes is not None,
                   trust_limit="Not authenticated or bound to IR by this function")
        _event(results, "geometry", "unknown", "Geometry mismatch needs qualified correspondence and independent per-metric policy",
               **binding, trust_limit="Not authenticated or bound to IR by this function")
    else:
        _event(results, "geometry", "unknown", "No candidate/target native geometry report supplied")
    _finish(results)
    return _result(results, ir_validation, qualifications, corr_qualification)


def _result(results: dict, ir_validation: dict, qualifications: dict, correspondence: dict | None) -> dict:
    return {"version": "paired-depiction-evaluation/0.1", "comparisons": results,
            "candidate_ir_validation": ir_validation,
            "target_qualifications": qualifications, "correspondence_qualification": correspondence,
            "gates": {"chemical_correctness": "unknown", "native_editability": "unknown",
                      "native_visual_quality": "unknown", "human_acceptance": "unknown"},
            "actual_gold": False, "identity_authenticated": False,
            "limits": ["Target qualification and correspondence assertions require independent custodian verification.",
                       "IR intent is not proof of the generated native depiction or measured ports.",
                       "No full chemical plausibility, stereochemical equivalence or flow-effect proof is provided.",
                       "Missing target species, LP ownership and arrow ports are never filled from the candidate.",
                       "Partial geometry is not a native visual PASS; no calibrated native pixel oracle is run."]}
