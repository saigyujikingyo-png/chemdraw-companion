"""Synthetic-only controls: no native targets, benchmark answers or human gold."""
from copy import deepcopy
import json
import unittest

try:
    from .depiction_semantics import compare_semantics
except ImportError:
    from depiction_semantics import compare_semantics


def fixture():
    """Small sodium hydroxide / hydrogen chloride bookkeeping fixture."""
    ir = {
        "ir_version": "mechanism-ir/0.2",
        "atom_catalog": [
            {"map": 1, "element": "O", "implicit_h": 1},
            {"map": 2, "element": "H", "implicit_h": 0},
            {"map": 3, "element": "Cl", "implicit_h": 0},
            {"map": 4, "element": "Na", "implicit_h": 0},
        ],
        "entry_state": "s0", "stereo_constraints": [],
        "states": [
            {"id": "s0", "label": "Initial", "bonds": [{"atoms": [2, 3], "order": 1}],
             "formal_charges": [{"atom": 1, "value": -1}, {"atom": 4, "value": 1}],
             "lone_pairs": [{"atom": 1, "count": 3}, {"atom": 3, "count": 3}],
             "chemical_species": [{"id": "base", "atoms": [1]}, {"id": "acid", "atoms": [2, 3]}, {"id": "ion", "atoms": [4]}]},
            {"id": "s1", "label": "Final", "bonds": [{"atoms": [1, 2], "order": 1}],
             "formal_charges": [{"atom": 3, "value": -1}, {"atom": 4, "value": 1}],
             "lone_pairs": [{"atom": 1, "count": 2}, {"atom": 3, "count": 4}],
             "chemical_species": [{"id": "water", "atoms": [1, 2]}, {"id": "halide", "atoms": [3]}, {"id": "ion", "atoms": [4]}]},
        ],
        "transitions": [{"id": "t0", "from": "s0", "to": "s1", "label": "Transfer", "kind": "elementary_teaching_step",
            "electron_flows": [
                {"id": "f0", "electron_count": 2, "source": {"type": "lone_pair", "atom": 1, "pair_index": 0}, "sink": {"type": "atom", "atom": 2}},
                {"id": "f1", "electron_count": 2, "source": {"type": "bond", "atoms": [2, 3], "electrons": "sigma"}, "sink": {"type": "atom", "atom": 3}},
            ],
            "bond_changes": [{"atoms": [2, 3], "from_order": 1, "to_order": 0}, {"atoms": [1, 2], "from_order": 0, "to_order": 1}],
            "charge_changes": [{"atom": 1, "from": -1, "to": 0}, {"atom": 3, "from": 0, "to": -1}]}],
        "depiction_states": [
            {"state_ref": "s0", "species": [{"species_ref": "base", "role": "explicitly_drawn"}, {"species_ref": "acid", "role": "abbreviated", "label": "HCl"}, {"species_ref": "ion", "role": "counterion_hidden"}],
             "lone_pairs": [{"atom_ref": 1, "displayed_pairs": 1}],
             "captions": [{"id": "c0", "role": "condition", "text": "aqueous"}]},
            {"state_ref": "s1", "species": [{"species_ref": "water", "role": "explicitly_drawn"}, {"species_ref": "halide", "role": "omitted_by_convention"}, {"species_ref": "ion", "role": "counterion_hidden"}],
             "lone_pairs": [], "captions": []},
        ],
    }
    corr = {"status": "qualified", "evidence_refs": ["synthetic:explicit-test-correspondence"],
            "atoms": {"O": 1, "H": 2, "X": 3, "M": 4},
            "states": {"before": "s0", "after": "s1"}, "transitions": {"transfer": "t0"}}
    target = {"version": "paired-depiction-target/0.1",
              "qualifications": {name: {"status": "qualified", "evidence_refs": ["synthetic:annotation-not-human-evidence"]}
                                 for name in ("chemical", "depiction", "displayed_lp", "condition_only", "flow_semantic")},
              "chemical_states": [], "depiction_states": [], "transitions": []}
    reverse = {value: key for key, value in corr["atoms"].items()}
    for state, state_ref, depiction in zip(ir["states"], ("before", "after"), ir["depiction_states"]):
        charge = {x["atom"]: x["value"] for x in state["formal_charges"]}
        lp = {x["atom"]: x["count"] for x in state["lone_pairs"]}
        target["chemical_states"].append({"state_ref": state_ref,
            "atoms": [{"atom_ref": reverse[x["map"]], "element": x["element"], "formal_charge": charge.get(x["map"], 0),
                       "implicit_h": x["implicit_h"], "isotope": 0, "radical_electrons": 0, "chemical_lone_pairs": lp.get(x["map"], 0)} for x in ir["atom_catalog"]],
            "bonds": [{"atom_refs": [reverse[a] for a in b["atoms"]], "order": b["order"]} for b in state["bonds"]],
            "atom_inventory_complete": True, "bond_inventory_complete": True})
        species = {x["id"]: x["atoms"] for x in state["chemical_species"]}
        target["depiction_states"].append({"state_ref": state_ref,
            "species": [{"atom_refs": [reverse[a] for a in species[x["species_ref"]]], "role": x["role"], **({"label": x["label"]} if "label" in x else {})} for x in depiction["species"]],
            "lone_pairs": [{"atom_ref": reverse[x["atom_ref"]], "displayed_pairs": x["displayed_pairs"]} for x in depiction["lone_pairs"]],
            "captions": [{"role": x["role"], "text": x["text"]} for x in depiction["captions"]],
            "species_inventory_complete": True, "lone_pair_inventory_complete": True, "caption_inventory_complete": True})
    target["transitions"] = [{"transition_ref": "transfer", "from_state_ref": "before", "to_state_ref": "after", "flow_inventory_complete": True,
        "electron_flows": [
            {"electron_count": 2, "source": {"type": "lone_pair", "atom_ref": "O"}, "sink": {"type": "atom", "atom_ref": "H"}},
            {"electron_count": 2, "source": {"type": "bond", "atom_refs": ["H", "X"], "electrons": "sigma"}, "sink": {"type": "atom", "atom_ref": "X"}},
        ]}]
    return ir, target, corr


def nonendpoint_fixture():
    """Synthetic ethene + HF protonation; no corpus-derived coordinates or IDs."""
    ir, target, corr = fixture()
    ir["atom_catalog"] = [{"map": 1, "element": "C", "implicit_h": 2}, {"map": 2, "element": "C", "implicit_h": 2},
                          {"map": 3, "element": "H", "implicit_h": 0}, {"map": 4, "element": "F", "implicit_h": 0}]
    a, b = ir["states"]
    a.update(bonds=[{"atoms": [1, 2], "order": 2}, {"atoms": [3, 4], "order": 1}], formal_charges=[], lone_pairs=[{"atom": 4, "count": 3}],
             chemical_species=[{"id": "alkene", "atoms": [1, 2]}, {"id": "acid", "atoms": [3, 4]}])
    b.update(bonds=[{"atoms": [1, 2], "order": 1}, {"atoms": [1, 3], "order": 1}], formal_charges=[{"atom": 2, "value": 1}, {"atom": 4, "value": -1}], lone_pairs=[{"atom": 4, "count": 4}],
             chemical_species=[{"id": "cation", "atoms": [1, 2, 3]}, {"id": "halide", "atoms": [4]}])
    ir["depiction_states"] = [{"state_ref": state["id"], "species": [{"species_ref": item["id"], "role": "explicitly_drawn"} for item in state["chemical_species"]], "lone_pairs": [], "captions": []} for state in ir["states"]]
    ir["transitions"][0].update(electron_flows=[
        {"id": "f0", "electron_count": 2, "source": {"type": "bond", "atoms": [1, 2], "electrons": "pi"}, "sink": {"type": "atom", "atom": 3}},
        {"id": "f1", "electron_count": 2, "source": {"type": "bond", "atoms": [3, 4], "electrons": "sigma"}, "sink": {"type": "atom", "atom": 4}}],
        bond_changes=[{"atoms": [1, 2], "from_order": 2, "to_order": 1}, {"atoms": [1, 3], "from_order": 0, "to_order": 1}, {"atoms": [3, 4], "from_order": 1, "to_order": 0}],
        charge_changes=[{"atom": 2, "from": 0, "to": 1}, {"atom": 4, "from": 0, "to": -1}])
    corr["atoms"] = {"C1": 1, "C2": 2, "H": 3, "F": 4}
    target["qualifications"] = {"flow_semantic": target["qualifications"]["flow_semantic"]}
    target["chemical_states"] = []
    target["depiction_states"] = []
    target["transitions"][0]["electron_flows"] = [
        {"electron_count": 2, "source": {"type": "bond", "atom_refs": ["C1", "C2"], "electrons": "pi"}, "sink": {"type": "atom", "atom_ref": "H"}},
        {"electron_count": 2, "source": {"type": "bond", "atom_refs": ["H", "F"], "electrons": "sigma"}, "sink": {"type": "atom", "atom_ref": "F"}}]
    return ir, target, corr


def geometry_fixture():
    """Schema-valid synthetic report; hashes identify only hypothetical bytes."""
    return {"version": "paired-evaluation/1.0", "target_sha256": "a" * 64, "candidate_sha256": "b" * 64,
            "gates": {"chemical_correctness": "unmeasured", "native_editability": "unmeasured", "visual_quality": "unmeasured", "human_acceptance": "unmeasured"},
            "semantic": {"status": "partial"}, "objects": {"status": "inventory_only"}, "geometry": {"status": "partial"},
            "native_visual": {"status": "unmeasured"}, "limits": ["Synthetic control only"],
            "correction": {"version": "paired-correction-deltas/1.0", "tier": "silver", "actual_gold": False,
                "direction": "candidate_to_target", "target_sha256": "a" * 64, "candidate_sha256": "b" * 64,
                "deltas": [{"kind": "atom_displacement", "target_id": "target-atom", "candidate_id": "candidate-atom", "value": [0, 0], "unit": "CDXML points", "frame": "unaligned_native_global"}],
                "unmeasured_kinds": ["arrow_source_anchor"], "human_active_seconds": None}}


class DepictionSemanticTests(unittest.TestCase):
    def setUp(self):
        self.ir, self.target, self.corr = fixture()

    def compare(self, **kwargs):
        return compare_semantics(self.ir, self.target, correspondence=self.corr, **kwargs)

    def status(self, result, layer):
        return result["comparisons"][layer]["status"]

    def test_synthetic_scoped_matches_are_not_gold_or_acceptance(self):
        result = self.compare()
        self.assertEqual(result["candidate_ir_validation"]["status"], "valid")
        for layer in ("chemical", "depiction", "condition_only", "displayed_lp", "flow_semantic"):
            self.assertEqual(self.status(result, layer), "match", layer)
        self.assertEqual(set(result["gates"].values()), {"unknown"})
        self.assertFalse(result["actual_gold"])
        self.assertFalse(result["identity_authenticated"])
        json.dumps(result, allow_nan=False)

    def test_no_target_keeps_chemical_semantics_unknown(self):
        result = compare_semantics(self.ir)
        self.assertEqual(self.status(result, "chemical"), "unknown")
        self.assertEqual(self.status(result, "flow_semantic"), "unknown")
        self.assertEqual(result["candidate_ir_validation"]["independent_chemical_qualification"], "unknown")

    def test_raw_unqualified_target_does_not_self_qualify(self):
        self.target["qualifications"] = {}
        result = self.compare()
        for layer in ("chemical", "depiction", "displayed_lp", "flow_semantic"):
            self.assertEqual(self.status(result, layer), "unknown")

    def test_partial_chemical_inventory_does_not_reject_unshown_counterion(self):
        row = self.target["chemical_states"][0]
        row["atoms"] = row["atoms"][:-1]
        row["atom_inventory_complete"] = False
        result = self.compare()
        self.assertEqual(self.status(result, "chemical"), "partial")
        self.assertFalse(any(x["status"] == "mismatch" for x in result["comparisons"]["chemical"]["observations"]))

    def test_extra_displayed_lp_is_not_chemical_mismatch(self):
        self.ir["depiction_states"][0]["lone_pairs"][0]["displayed_pairs"] = 3
        result = self.compare()
        self.assertEqual(self.status(result, "chemical"), "match")
        self.assertEqual(self.status(result, "displayed_lp"), "mismatch")

    def test_unshown_chemical_lp_can_still_donate(self):
        self.ir["depiction_states"][0]["lone_pairs"] = []
        result = self.compare()
        self.assertEqual(self.status(result, "flow_semantic"), "match")
        self.assertEqual(self.status(result, "displayed_lp"), "mismatch")

    def test_unknown_native_lp_owner_never_inferred_from_candidate(self):
        self.target["depiction_states"][0]["lone_pairs"][0]["atom_ref"] = None
        result = self.compare()
        self.assertEqual(self.status(result, "displayed_lp"), "partial")
        self.assertFalse(any(x["status"] == "mismatch" for x in result["comparisons"]["displayed_lp"]["observations"]))
        self.assertEqual(self.status(result, "chemical"), "match")

    def test_hidden_target_species_only_changes_depiction(self):
        self.ir["depiction_states"][1]["species"][1]["role"] = "explicitly_drawn"
        result = self.compare()
        self.assertEqual(self.status(result, "depiction"), "mismatch")
        self.assertEqual(self.status(result, "chemical"), "match")
        self.assertTrue(any(x.get("side") == "target" for x in result["comparisons"]["omitted_by_design"]["observations"]))

    def test_condition_caption_preserves_chemical_species(self):
        self.ir["depiction_states"][0]["species"][1] = {"species_ref": "acid", "role": "reagent_caption", "label": "HCl"}
        self.ir["depiction_states"][0]["captions"].append({"id": "c1", "role": "reagent", "text": "HCl", "species_refs": ["acid"]})
        result = self.compare()
        self.assertEqual(self.status(result, "chemical"), "match")
        self.assertEqual(self.status(result, "depiction"), "mismatch")
        self.assertTrue(any(x.get("role") == "reagent_caption" for x in result["comparisons"]["condition_only"]["observations"]))

    def test_wrong_typed_caption_is_depiction_not_chemistry(self):
        self.target["depiction_states"][0]["captions"][0]["role"] = "solvent"
        result = self.compare()
        self.assertEqual(self.status(result, "condition_only"), "mismatch")
        self.assertEqual(self.status(result, "chemical"), "match")

    def test_true_formal_charge_difference_is_chemical(self):
        self.target["chemical_states"][0]["atoms"][3]["formal_charge"] = 0
        self.assertEqual(self.status(self.compare(), "chemical"), "mismatch")

    def test_chemical_lp_count_is_independent_from_display_count(self):
        self.target["chemical_states"][0]["atoms"][0]["chemical_lone_pairs"] = 2
        result = self.compare()
        self.assertEqual(self.status(result, "chemical"), "mismatch")
        self.assertEqual(self.status(result, "displayed_lp"), "match")

    def test_unknown_source_sink_stays_unknown_even_with_complete_inventory(self):
        self.target["transitions"][0]["electron_flows"][0]["source"] = None
        result = self.compare()
        self.assertEqual(self.status(result, "flow_semantic"), "partial")
        self.assertFalse(any(x["status"] == "mismatch" for x in result["comparisons"]["flow_semantic"]["observations"]))

    def test_incomplete_target_flows_do_not_invent_extra_flow_error(self):
        self.target["transitions"][0]["electron_flows"].pop()
        self.target["transitions"][0]["flow_inventory_complete"] = False
        self.assertEqual(self.status(self.compare(), "flow_semantic"), "partial")

    def test_complete_target_detects_additional_flows(self):
        self.target["transitions"][0]["electron_flows"].pop()
        self.assertEqual(self.status(self.compare(), "flow_semantic"), "mismatch")

    def test_wrong_flow_sink_is_semantic_mismatch(self):
        self.target["transitions"][0]["electron_flows"][0]["sink"]["atom_ref"] = "X"
        self.assertEqual(self.status(self.compare(), "flow_semantic"), "mismatch")

    def test_wrong_transition_state_is_flow_semantic_mismatch(self):
        self.target["transitions"][0]["from_state_ref"] = "after"
        self.assertEqual(self.status(self.compare(), "flow_semantic"), "mismatch")

    def test_missing_correspondence_does_not_match_equal_ids(self):
        result = compare_semantics(self.ir, self.target)
        self.assertEqual(self.status(result, "chemical"), "unknown")

    def test_noninjective_correspondence_rejected(self):
        self.corr["atoms"]["X"] = 2
        with self.assertRaisesRegex(ValueError, "Non-injective"):
            self.compare()

    def test_qualification_needs_evidence_refs(self):
        self.target["qualifications"]["chemical"]["evidence_refs"] = []
        with self.assertRaisesRegex(ValueError, "evidence"):
            self.compare()

    def test_partial_qualification_cannot_yield_complete_layer_match(self):
        self.target["qualifications"]["chemical"]["status"] = "partial"
        self.assertEqual(self.status(self.compare(), "chemical"), "partial")

    def test_empty_qualified_annotations_remain_unknown(self):
        self.target["chemical_states"] = []
        self.target["depiction_states"] = []
        self.target["transitions"] = []
        result = self.compare()
        for layer in ("chemical", "depiction", "displayed_lp", "flow_semantic"):
            self.assertEqual(self.status(result, layer), "unknown")

    def test_array_order_does_not_supply_identity(self):
        baseline = self.compare()
        self.ir["atom_catalog"].reverse()
        self.ir["states"].reverse()
        self.ir["depiction_states"].reverse()
        self.ir["transitions"][0]["electron_flows"].reverse()
        for state in self.target["chemical_states"]:
            state["atoms"].reverse()
            for bond in state["bonds"]:
                bond["atom_refs"].reverse()
        self.target["transitions"][0]["electron_flows"].reverse()
        result = self.compare()
        for layer in ("chemical", "depiction", "displayed_lp", "flow_semantic"):
            self.assertEqual(self.status(result, layer), self.status(baseline, layer))

    def test_alternative_halogen_and_counterion_do_not_change_rules(self):
        self.ir["atom_catalog"][2]["element"] = "I"
        self.ir["atom_catalog"][3]["element"] = "K"
        for state in self.target["chemical_states"]:
            state["atoms"][2]["element"] = "I"
            state["atoms"][3]["element"] = "K"
        result = self.compare()
        self.assertEqual(self.status(result, "chemical"), "match")
        self.assertEqual(self.status(result, "flow_semantic"), "match")

    def test_invalid_ir_is_not_a_target_mismatch(self):
        self.ir["ir_version"] = "wrong"
        result = self.compare()
        self.assertEqual(result["candidate_ir_validation"]["status"], "invalid")
        self.assertEqual(self.status(result, "chemical"), "unknown")

    def test_partial_geometry_never_promotes_native_visual(self):
        report = geometry_fixture()
        result = self.compare(geometry_report=report)
        self.assertEqual(self.status(result, "geometry"), "partial")
        self.assertEqual(result["gates"]["native_visual_quality"], "unknown")

    def test_malformed_geometry_cannot_be_reported_as_measurements(self):
        with self.assertRaisesRegex(ValueError, "Invalid upstream geometry"):
            self.compare(geometry_report={"correction": {"deltas": [{}]}})

    def test_upstream_pass_is_rejected_by_existing_evaluator_contract(self):
        report = geometry_fixture()
        report["gates"]["visual_quality"] = "PASS"
        with self.assertRaisesRegex(ValueError, "Invalid upstream geometry"):
            self.compare(geometry_report=report)

    def test_geometry_artifact_hashes_checked_and_retained(self):
        hashes = {"target_sha256": "a" * 64, "candidate_sha256": "b" * 64}
        result = self.compare(geometry_report=geometry_fixture(), expected_native_hashes=hashes)
        event = next(x for x in result["comparisons"]["geometry"]["observations"] if x["status"] == "reported")
        self.assertEqual(event["target_sha256"], hashes["target_sha256"])
        self.assertEqual(event["candidate_sha256"], hashes["candidate_sha256"])
        self.assertTrue(event["expected_native_hashes_checked"])
        self.assertIn("Not authenticated", event["trust_limit"])

    def test_wrong_expected_native_hash_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
            self.compare(geometry_report=geometry_fixture(), expected_native_hashes={"target_sha256": "a" * 64, "candidate_sha256": "c" * 64})

    def test_wrong_internal_correction_hash_is_rejected(self):
        report = geometry_fixture()
        report["correction"]["candidate_sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "hash binding mismatch"):
            self.compare(geometry_report=report)

    def test_absent_geometry_is_unknown_not_zero_error(self):
        self.assertEqual(self.status(self.compare(), "geometry"), "unknown")

    def test_nonfinite_geometry_rejected(self):
        with self.assertRaisesRegex(ValueError, "Non-finite"):
            self.compare(geometry_report={"correction": {"deltas": [{"value": float("nan")}]}})

    def test_boolean_lp_count_is_not_numeric_evidence(self):
        self.target["depiction_states"][0]["lone_pairs"][0]["displayed_pairs"] = True
        with self.assertRaisesRegex(ValueError, "integer"):
            self.compare()

    def test_duplicate_atom_annotation_rejected(self):
        self.target["chemical_states"][0]["atoms"].append(deepcopy(self.target["chemical_states"][0]["atoms"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate chemical atom"):
            self.compare()

    def test_explicit_auto_lp_slot_matches_documented_default(self):
        self.target["depiction_states"][0]["lone_pairs"][0]["slots"] = [{"pair_index": 0, "orientation": "auto"}]
        self.assertEqual(self.status(self.compare(), "displayed_lp"), "match")

    def test_lp_slot_array_order_is_not_geometry(self):
        self.ir["depiction_states"][0]["lone_pairs"][0] = {"atom_ref": 1, "displayed_pairs": 2,
            "slots": [{"pair_index": 1, "orientation": "auto"}, {"pair_index": 0, "orientation": "auto"}]}
        self.target["depiction_states"][0]["lone_pairs"][0] = {"atom_ref": "O", "displayed_pairs": 2,
            "slots": [{"pair_index": 0, "orientation": "auto"}, {"pair_index": 1, "orientation": "auto"}]}
        self.assertEqual(self.status(self.compare(), "displayed_lp"), "match")

    def test_caption_binding_uses_qualified_binding_before_unbound_text(self):
        self.ir["depiction_states"][0]["captions"] = [
            {"id": "c0", "role": "reagent", "text": "reagent", "species_refs": ["base"]},
            {"id": "c1", "role": "reagent", "text": "reagent", "species_refs": ["acid"]}]
        self.target["depiction_states"][0]["captions"] = [
            {"role": "reagent", "text": "reagent"},
            {"role": "reagent", "text": "reagent", "atom_refs": ["O"]}]
        self.assertEqual(self.status(self.compare(), "condition_only"), "match")

    def test_bond_to_nonendpoint_atom_is_compared_without_old_endpoint_rule(self):
        self.ir, self.target, self.corr = nonendpoint_fixture()
        result = self.compare()
        self.assertEqual(result["candidate_ir_validation"]["status"], "valid")
        self.assertEqual(self.status(result, "flow_semantic"), "match")
        self.assertEqual(self.status(result, "chemical"), "unknown")

    def test_bond_to_forming_bond_intent_is_supported(self):
        self.ir, self.target, self.corr = nonendpoint_fixture()
        self.ir["transitions"][0]["electron_flows"][0]["sink"] = {"type": "forming_bond", "atoms": [1, 3]}
        self.target["transitions"][0]["electron_flows"][0]["sink"] = {"type": "forming_bond", "atom_refs": ["H", "C1"]}
        self.assertEqual(self.status(self.compare(), "flow_semantic"), "match")

    def test_lp_to_bond_intent_is_distinct_and_supported(self):
        self.ir["transitions"][0]["electron_flows"][0]["sink"] = {"type": "bond", "atoms": [1, 2]}
        self.target["transitions"][0]["electron_flows"][0]["sink"] = {"type": "bond", "atom_refs": ["H", "O"]}
        self.assertEqual(self.status(self.compare(), "flow_semantic"), "match")

    def test_atom_and_state_relabeling_requires_only_explicit_correspondence(self):
        atom_names = {1: 91, 2: 18, 3: 72, 4: 33}
        state_names = {"s0": "renamed-before", "s1": "renamed-after"}
        def rename(value, key=None):
            if isinstance(value, dict):
                return {k: rename(v, k) for k, v in value.items()}
            if isinstance(value, list):
                return [atom_names[x] for x in value] if key == "atoms" else [rename(x) for x in value]
            if key in ("map", "atom", "atom_ref"):
                return atom_names[value]
            if key in ("id", "entry_state", "state_ref", "from", "to") and isinstance(value, str):
                return state_names.get(value, value)
            return value
        self.ir = rename(self.ir)
        self.corr["atoms"] = {k: atom_names[v] for k, v in self.corr["atoms"].items()}
        self.corr["states"] = {k: state_names[v] for k, v in self.corr["states"].items()}
        result = self.compare()
        for layer in ("chemical", "depiction", "displayed_lp", "flow_semantic"):
            self.assertEqual(self.status(result, layer), "match", layer)

    def test_inputs_remain_immutable(self):
        before = deepcopy((self.ir, self.target, self.corr))
        self.compare()
        self.assertEqual(before, (self.ir, self.target, self.corr))


if __name__ == "__main__":
    unittest.main()
