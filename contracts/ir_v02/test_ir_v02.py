"""Synthetic contract tests only: no native/target/benchmark files are read."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contracts.ir_v02 import (IRContractError, ELEMENT_SYMBOLS, ATOMIC_NUMBERS,
    canonical_sha256, migrate_v01, validate_mechanism, compile_electron_flows,
    lower_depiction, validate_depiction_capabilities)


def proton_transfer_v01():
    # Hydroxide + HF -> water + fluoride; H2 is explicitly atom-mapped.
    return {"ir_version": "mechanism-ir/0.1", "atom_catalog": [
        {"map": 1, "element": "O", "implicit_h": 1},
        {"map": 2, "element": "H", "implicit_h": 0},
        {"map": 3, "element": "F", "implicit_h": 0}],
        "states": [
            {"id": "initial", "label": "Initial", "formal_charges": [{"atom": 1, "value": -1}], "lone_pairs": [{"atom": 1, "count": 3}, {"atom": 3, "count": 3}], "bonds": [{"atoms": [2, 3], "order": 1}]},
            {"id": "final", "label": "Final", "formal_charges": [{"atom": 3, "value": -1}], "lone_pairs": [{"atom": 1, "count": 2}, {"atom": 3, "count": 4}], "bonds": [{"atoms": [1, 2], "order": 1}]}],
        "transitions": [{"id": "transfer", "from": "initial", "to": "final", "label": "Proton transfer", "kind": "elementary_step", "electron_flows": [
            {"id": "donation", "electron_count": 2, "source": {"type": "lone_pair", "atom": 1, "pair_index": 0}, "target": {"type": "atom", "atom": 2}},
            {"id": "cleavage", "electron_count": 2, "source": {"type": "bond", "atoms": [2, 3], "electrons": "sigma"}, "target": {"type": "atom", "atom": 3}}],
            "bond_changes": [{"atoms": [2, 3], "from_order": 1, "to_order": 0}, {"atoms": [1, 2], "from_order": 0, "to_order": 1}],
            "charge_changes": [{"atom": 1, "from": -1, "to": 0}, {"atom": 3, "from": 0, "to": -1}]}],
        "stereo_constraints": [], "entry_state": "initial"}


def nonendpoint_v01():
    # Ethene pi electrons attack H3, which is not a source-bond endpoint.
    return {"ir_version": "mechanism-ir/0.1", "atom_catalog": [
        {"map": 1, "element": "C", "implicit_h": 2}, {"map": 2, "element": "C", "implicit_h": 2},
        {"map": 3, "element": "H", "implicit_h": 0}, {"map": 4, "element": "F", "implicit_h": 0}],
        "states": [
            {"id": "a", "label": "Alkene", "formal_charges": [], "lone_pairs": [{"atom": 4, "count": 3}], "bonds": [{"atoms": [1, 2], "order": 2}, {"atoms": [3, 4], "order": 1}]},
            {"id": "b", "label": "Cation", "formal_charges": [{"atom": 2, "value": 1}, {"atom": 4, "value": -1}], "lone_pairs": [{"atom": 4, "count": 4}], "bonds": [{"atoms": [1, 2], "order": 1}, {"atoms": [1, 3], "order": 1}]}],
        "transitions": [{"id": "addition", "from": "a", "to": "b", "label": "Electrophilic addition", "kind": "elementary_step", "electron_flows": [
            {"id": "pi-donation", "electron_count": 2, "source": {"type": "bond", "atoms": [1, 2], "electrons": "pi"}, "target": {"type": "atom", "atom": 3}},
            {"id": "cleavage", "electron_count": 2, "source": {"type": "bond", "atoms": [3, 4], "electrons": "sigma"}, "target": {"type": "atom", "atom": 4}}],
            "bond_changes": [{"atoms": [1, 2], "from_order": 2, "to_order": 1}, {"atoms": [3, 4], "from_order": 1, "to_order": 0}, {"atoms": [1, 3], "from_order": 0, "to_order": 1}],
            "charge_changes": [{"atom": 2, "from": 0, "to": 1}, {"atom": 4, "from": 0, "to": -1}]}],
        "stereo_constraints": [], "entry_state": "a"}


def v02():
    return migrate_v01(proton_transfer_v01(), policy="preserve_v01_display")


def single_atom(element="He"):
    return {"ir_version": "mechanism-ir/0.2", "atom_catalog": [{"map": 8, "element": element, "implicit_h": 0}],
        "states": [{"id": "one", "label": "Species", "formal_charges": [], "lone_pairs": [], "bonds": [], "chemical_species": [{"id": "component", "atoms": [8]}]}],
        "transitions": [], "stereo_constraints": [], "entry_state": "one",
        "depiction_states": [{"state_ref": "one", "species": [{"species_ref": "component", "role": "explicitly_drawn"}], "lone_pairs": [], "captions": []}]}


class ContractTests(unittest.TestCase):
    def assertCode(self, code, call):
        with self.assertRaises(IRContractError) as context:
            call()
        self.assertEqual(code, context.exception.code)
        self.assertTrue(context.exception.path)
        return context.exception

    def test_schema_valid(self):
        import jsonschema
        schema = json.loads(Path(__file__).with_name("mechanism-ir.schema.json").read_text())
        jsonschema.Draft202012Validator.check_schema(schema)

    def test_118_element_identity_and_number_order(self):
        self.assertEqual(118, len(set(ELEMENT_SYMBOLS)))
        for symbol, number in [("H",1),("Br",35),("K",19),("Sm",62),("Lu",71),("Au",79),("Og",118)]:
            self.assertEqual(number, ATOMIC_NUMBERS[symbol])
        for element in ELEMENT_SYMBOLS:
            doc = single_atom(element)
            if element in {"H","C","N","O","F"}:
                # An isolated neutral atom's radical electrons are explicit.
                doc["atom_catalog"][0]["radical_electrons"] = {"H":1,"C":4,"N":5,"O":6,"F":7}[element]
            self.assertEqual("pass", validate_mechanism(doc)["checked_invariants"]["status"])

    def test_invalid_element_rejected(self):
        self.assertCode("SCHEMA_INVALID", lambda: validate_mechanism(single_atom("Xx")))

    def test_migration_is_deterministic_and_does_not_mutate(self):
        original = proton_transfer_v01()
        frozen = deepcopy(original)
        one = migrate_v01(original, policy="preserve_v01_display")
        two = migrate_v01(original, policy="preserve_v01_display")
        self.assertEqual(original, frozen)
        self.assertEqual(one, two)
        self.assertEqual(canonical_sha256(original), one["migration"]["source_sha256"])
        self.assertEqual(original["atom_catalog"], one["atom_catalog"])
        for old, new in zip(original["states"], one["states"]):
            self.assertEqual(old, {k:v for k,v in new.items() if k != "chemical_species"})
        for old, new in zip(original["transitions"], one["transitions"]):
            back = deepcopy(new)
            for flow in back["electron_flows"]:
                flow["target"] = flow.pop("sink")
            self.assertEqual(old, back)

    def test_strict_migration_requires_depiction(self):
        self.assertCode("MIGRATION_DEPICTION_REQUIRED", lambda: migrate_v01(proton_transfer_v01()))

    def test_strict_migration_accepts_explicit_depiction(self):
        explicit = v02()["depiction_states"]
        result = migrate_v01(proton_transfer_v01(), depiction_states=explicit)
        self.assertEqual(explicit, result["depiction_states"])
        self.assertEqual("strict", result["migration"]["policy"])

    def test_preserve_policy_rejects_replacement_intent(self):
        self.assertCode("MIGRATION_POLICY_CONFLICT", lambda: migrate_v01(proton_transfer_v01(), policy="preserve_v01_display", depiction_states=[]))

    def test_unknown_migration_policy(self):
        self.assertCode("UNKNOWN_MIGRATION_POLICY", lambda: migrate_v01(proton_transfer_v01(), policy="guess"))

    def test_explicit_version_dispatch(self):
        self.assertCode("SCHEMA_INVALID", lambda: validate_mechanism(proton_transfer_v01()))
        self.assertCode("SCHEMA_INVALID", lambda: migrate_v01(v02()))

    def test_pure_legacy_preserves_all_species_lps_labels(self):
        doc = v02()
        plan = lower_depiction(doc)
        for old, state in zip(doc["states"], plan["states"]):
            self.assertEqual(3, len(state["visible_atoms"]))
            self.assertEqual(sum(x["count"] for x in old["lone_pairs"]), len(state["lone_pair_slots"]))
            self.assertEqual(old["label"], state["captions"][0]["text"])
        self.assertEqual("annotation", plan["states"][0]["captions"][1]["role"])
        self.assertEqual("Proton transfer", plan["states"][0]["captions"][1]["text"])

    def test_nonendpoint_pi_flow_compiles(self):
        doc = migrate_v01(nonendpoint_v01(), policy="preserve_v01_display")
        flow = compile_electron_flows(doc)["transitions"][0]["electron_flows"][0]
        self.assertNotIn(flow["sink"]["atom"], flow["source"]["atoms"])
        self.assertEqual([[1,3]], flow["related_bond_increases"])
        self.assertEqual("intent_lowered", lower_depiction(doc)["status"])

    def test_forming_bond_sink(self):
        doc = v02()
        doc["transitions"][0]["electron_flows"][0]["sink"] = {"type":"forming_bond","atoms":[1,2]}
        self.assertEqual("forming_bond", compile_electron_flows(doc)["transitions"][0]["electron_flows"][0]["sink"]["type"])

    def test_forming_bond_requires_absent_prestate(self):
        doc = migrate_v01(nonendpoint_v01(), policy="preserve_v01_display")
        doc["transitions"][0]["electron_flows"][0]["sink"] = {"type":"forming_bond","atoms":[1,2]}
        self.assertCode("FLOW_GRAPH_MISMATCH", lambda: validate_mechanism(doc))

    def test_declared_graph_change_cannot_override_actual(self):
        doc = v02()
        doc["transitions"][0]["bond_changes"][0]["to_order"] = 2
        self.assertCode("GRAPH_DELTA_MISMATCH", lambda: validate_mechanism(doc))

    def test_declared_charge_change_cannot_override_actual(self):
        doc = v02()
        doc["transitions"][0]["charge_changes"] = []
        self.assertCode("GRAPH_DELTA_MISMATCH", lambda: validate_mechanism(doc))

    def test_matching_optional_effect(self):
        doc = v02()
        doc["transitions"][0]["electron_flows"][0]["effect"] = {"bond_changes":[doc["transitions"][0]["bond_changes"][1]],"charge_changes":[doc["transitions"][0]["charge_changes"][0]]}
        validate_mechanism(doc)

    def test_effect_cannot_override_graph(self):
        doc = v02()
        doc["transitions"][0]["electron_flows"][0]["effect"] = {"bond_changes":[{"atoms":[1,2],"from_order":0,"to_order":2}],"charge_changes":[]}
        self.assertCode("FLOW_EFFECT_MISMATCH", lambda: validate_mechanism(doc))

    def test_missing_flow_does_not_cover_graph(self):
        doc = v02()
        doc["transitions"][0]["electron_flows"].pop()
        self.assertCode("UNCOVERED_GRAPH_CHANGE", lambda: validate_mechanism(doc))

    def test_missing_chemical_donor_rejected(self):
        doc = v02()
        doc["transitions"][0]["electron_flows"][0]["source"]["pair_index"] = 3
        self.assertCode("INVALID_LONE_PAIR_SOURCE", lambda: validate_mechanism(doc))

    def test_lone_pair_cannot_be_spent_twice(self):
        doc = v02()
        duplicate = deepcopy(doc["transitions"][0]["electron_flows"][0]); duplicate["id"] = "duplicate"
        doc["transitions"][0]["electron_flows"].append(duplicate)
        self.assertCode("REUSED_ELECTRON_SOURCE", lambda: validate_mechanism(doc))

    def test_unrelated_sink_rejected(self):
        doc = v02()
        doc["transitions"][0]["electron_flows"][0]["sink"]["atom"] = 1
        # This port is chemically ambiguous, but still touches the donated bond;
        # selecting the donor itself must not receive an electron gain.
        self.assertCode("FLOW_GRAPH_MISMATCH", lambda: validate_mechanism(doc))

    def test_nonfinite_json_rejected(self):
        doc = v02(); doc["nan"] = float("nan")
        self.assertCode("INVALID_JSON_VALUE", lambda: validate_mechanism(doc))

    def test_duplicate_catalog_atom_rejected(self):
        doc = v02(); doc["atom_catalog"].append(deepcopy(doc["atom_catalog"][0]))
        self.assertCode("DUPLICATE_ID", lambda: validate_mechanism(doc))

    def test_dangling_bond_rejected(self):
        doc = v02(); doc["states"][0]["bonds"][0]["atoms"] = [2,99]
        self.assertCode("UNKNOWN_ATOM", lambda: validate_mechanism(doc))

    def test_duplicate_reverse_bond_rejected(self):
        doc = v02(); doc["states"][0]["bonds"].append({"atoms":[3,2],"order":1})
        self.assertCode("DUPLICATE_BOND", lambda: validate_mechanism(doc))

    def test_species_cannot_omit_ions(self):
        doc = v02(); doc["states"][0]["chemical_species"].pop(0)
        self.assertCode("SPECIES_PARTITION_INVALID", lambda: validate_mechanism(doc))

    def test_species_must_equal_connectivity(self):
        doc = v02(); doc["states"][0]["chemical_species"] = [{"id":"merged","atoms":[1,2,3]}]
        self.assertCode("SPECIES_CONNECTIVITY_MISMATCH", lambda: validate_mechanism(doc))

    def test_hidden_species_remains_in_chemical_inventory(self):
        doc = v02()
        doc["depiction_states"][1]["species"][1]["role"] = "counterion_hidden"
        doc["depiction_states"][1]["lone_pairs"] = [x for x in doc["depiction_states"][1]["lone_pairs"] if x["atom_ref"] != 3]
        plan = lower_depiction(doc)
        self.assertEqual(3, len(plan["chemical_inventory"]["atom_catalog"]))
        self.assertEqual([1,2], [x["atom_ref"] for x in plan["states"][1]["visible_atoms"]])
        self.assertEqual("counterion_hidden", plan["states"][1]["hidden_species"][0]["reason"])

    def test_caption_can_bind_multiple_disconnected_species(self):
        doc = v02(); dep = doc["depiction_states"][0]
        refs = [x["species_ref"] for x in dep["species"]]
        for spec in dep["species"]: spec["role"] = "condition_caption"
        dep["lone_pairs"] = []
        dep["captions"] = [{"id":"conditions","role":"condition","text":"Base and acid","species_refs":refs}]
        validate_mechanism(doc)
        plan = lower_depiction(doc)
        self.assertEqual(0, len(plan["states"][0]["visible_atoms"]))
        self.assertEqual("unresolved_depiction", plan["status"])
        self.assertTrue(all(d["code"] == "DEPICTION_PORT_UNRESOLVED" for d in plan["diagnostics"]))

    def test_caption_species_requires_matching_caption_role(self):
        doc = v02(); doc["depiction_states"][0]["species"][0]["role"] = "reagent_caption"
        self.assertCode("SPECIES_CAPTION_REQUIRED", lambda: validate_mechanism(doc))

    def test_selective_lps_and_virtual_donor(self):
        doc = v02(); doc["depiction_states"][0]["lone_pairs"] = [{"atom_ref":1,"displayed_pairs":1,"slots":[{"pair_index":2,"orientation":"outward"}]}]
        plan = lower_depiction(doc)
        self.assertEqual(1, len(plan["states"][0]["lone_pair_slots"]))
        self.assertEqual(3, plan["states"][0]["visible_atoms"][0]["chemical_lone_pairs"])
        self.assertEqual("virtual_lone_pair", plan["electron_flows"][0]["source"]["kind"])
        self.assertFalse(plan["electron_flows"][0]["source"]["draw_lone_pair"])

    def test_displayed_lps_cannot_exceed_chemical(self):
        doc = v02(); doc["depiction_states"][0]["lone_pairs"][0]["displayed_pairs"] = 4
        self.assertCode("DISPLAYED_LP_EXCEEDS_CHEMICAL", lambda: validate_mechanism(doc))

    def test_duplicate_lp_slots_rejected(self):
        doc = v02(); doc["depiction_states"][0]["lone_pairs"][0]["slots"][1]["pair_index"] = 0
        self.assertCode("INVALID_LP_SLOTS", lambda: validate_mechanism(doc))

    def test_abbreviation_without_anchor_is_unresolved_for_flow(self):
        doc = v02(); spec = doc["depiction_states"][0]["species"][0]
        spec.update({"role":"abbreviated","label":"Base"})
        doc["depiction_states"][0]["lone_pairs"] = []
        self.assertEqual("unresolved_depiction", lower_depiction(doc)["status"])

    def test_abbreviation_anchor_preserves_virtual_lp_port(self):
        doc = v02(); spec = doc["depiction_states"][0]["species"][0]
        spec.update({"role":"abbreviated","label":"Base","attachment_atom_ref":1})
        doc["depiction_states"][0]["lone_pairs"] = []
        plan = lower_depiction(doc)
        self.assertEqual("intent_lowered", plan["status"])
        self.assertEqual("abbreviation_attachment", plan["electron_flows"][0]["source"]["atom_ports"][0]["kind"])

    def test_abbreviation_cannot_guess_different_species_anchor(self):
        doc = v02(); spec = doc["depiction_states"][0]["species"][0]
        spec.update({"role":"abbreviated","label":"Base","attachment_atom_ref":3})
        self.assertCode("INVALID_ABBREVIATION_ATTACHMENT", lambda: validate_mechanism(doc))

    def test_isotope_identity_catalog_only(self):
        doc = v02(); doc["atom_catalog"][1]["isotope"] = 2
        self.assertEqual(2, lower_depiction(doc)["states"][0]["visible_atoms"][1]["isotope"])
        doc["states"][1]["atom_properties"] = [{"atom":2,"isotope":3}]
        self.assertCode("SCHEMA_INVALID", lambda: validate_mechanism(doc))

    def test_isotope_mass_cannot_be_less_than_atomic_number(self):
        doc = single_atom("K"); doc["atom_catalog"][0]["isotope"] = 1
        self.assertCode("ISOTOPE_IDENTITY_INVALID", lambda: validate_mechanism(doc))

    def test_state_radical_override_is_separate_from_catalog(self):
        doc = single_atom("C")
        doc["states"][0]["atom_properties"] = [{"atom":8,"radical_electrons":4}]
        self.assertEqual(4, lower_depiction(doc)["states"][0]["visible_atoms"][0]["radical_electrons"])
        self.assertNotIn("radical_electrons", doc["atom_catalog"][0])

    def test_unknown_valence_is_not_invalid_chemistry_or_full_pass(self):
        for element in ("P","S","Br","K","Na","Fe","Cu","Xe"):
            report = validate_mechanism(single_atom(element))
            self.assertEqual("partial", report["valence_coverage"]["status"])
            self.assertEqual("not_established", report["chemical_validity"]["status"])

    def test_known_electron_inventory_mismatch_rejected(self):
        doc = v02(); doc["states"][0]["lone_pairs"][0]["count"] = 2
        self.assertCode("ELECTRON_INVENTORY_MISMATCH", lambda: validate_mechanism(doc))

    def test_depiction_cannot_inject_absolute_coordinates(self):
        doc = v02(); doc["depiction_states"][0]["species"][0]["x"] = 3
        self.assertCode("SCHEMA_INVALID", lambda: validate_mechanism(doc))

    def test_lowering_hash_bound_and_deterministic(self):
        doc = v02(); one = lower_depiction(doc)
        self.assertEqual(one, lower_depiction(doc))
        self.assertEqual(canonical_sha256(doc), one["ir_sha256"])
        self.assertEqual(doc["states"], one["chemical_inventory"]["states"])
        self.assertNotIn("x", one["states"][0]["visible_atoms"][0])

    def test_empty_capabilities_fail_closed(self):
        result = validate_depiction_capabilities(v02(), {})
        self.assertEqual("unsupported_or_unknown", result["status"])
        self.assertTrue(result["diagnostics"])

    def test_explicit_capabilities_cover_intent_but_not_native_claim(self):
        result = validate_depiction_capabilities(v02(), {"elements":["O","H","F"],"roles":["explicitly_drawn"],"flow_electron_counts":[2],"orientations":["auto"],"typed_captions":True})
        self.assertEqual("declared_capabilities_cover_intent", result["status"])
        self.assertEqual("not_performed", result["native_execution"])

    def test_virtual_lp_capability_is_explicit(self):
        doc = v02(); doc["depiction_states"][0]["lone_pairs"] = []
        result = validate_depiction_capabilities(doc, {"virtual_lone_pair_ports":False})
        self.assertTrue(any(x.get("capability") == "virtual_lone_pair_ports" and x["code"] == "DEPICTION_CAPABILITY_UNSUPPORTED" for x in result["diagnostics"]))

    def test_capability_declaration_rejects_tricky_truthy_values(self):
        self.assertCode("INVALID_CAPABILITY_DECLARATION", lambda: validate_depiction_capabilities(v02(), {"isotopes":"false"}))
        self.assertCode("INVALID_CAPABILITY_DECLARATION", lambda: validate_depiction_capabilities(v02(), {"elements":"*"}))

    def test_bond_electrons_cannot_be_spent_twice(self):
        doc = v02()
        duplicate = deepcopy(doc["transitions"][0]["electron_flows"][1]); duplicate["id"] = "duplicate-bond"
        doc["transitions"][0]["electron_flows"].append(duplicate)
        self.assertCode("REUSED_ELECTRON_SOURCE", lambda: validate_mechanism(doc))

    def test_independent_proton_transfers_cannot_crosswire_bond_sinks(self):
        old = proton_transfer_v01()
        # Two independent, balanced proton transfers in one teaching step.
        extra = deepcopy(old)
        for atom in extra["atom_catalog"]: atom["map"] += 10
        old["atom_catalog"].extend(extra["atom_catalog"])
        for state, extra_state in zip(old["states"], extra["states"]):
            for key in ("formal_charges","lone_pairs"):
                for item in extra_state[key]: item["atom"] += 10
                state[key].extend(extra_state[key])
            for bond in extra_state["bonds"]: bond["atoms"] = [a+10 for a in bond["atoms"]]
            state["bonds"].extend(extra_state["bonds"])
        tr, et = old["transitions"][0], extra["transitions"][0]
        for flow in et["electron_flows"]:
            flow["id"] += "-second"
            for port in (flow["source"],flow["target"]):
                if "atom" in port: port["atom"] += 10
                if "atoms" in port: port["atoms"] = [a+10 for a in port["atoms"]]
        tr["electron_flows"].extend(et["electron_flows"])
        for change in et["bond_changes"]: change["atoms"] = [a+10 for a in change["atoms"]]
        for change in et["charge_changes"]: change["atom"] += 10
        tr["bond_changes"].extend(et["bond_changes"]); tr["charge_changes"].extend(et["charge_changes"])
        doc = migrate_v01(old,policy="preserve_v01_display")
        tr = doc["transitions"][0]
        tr["electron_flows"][0]["sink"] = {"type":"forming_bond","atoms":[11,12]}
        tr["electron_flows"][2]["sink"] = {"type":"forming_bond","atoms":[1,2]}
        self.assertCode("FLOW_GRAPH_MISMATCH",lambda:validate_mechanism(doc))

    def test_display_only_change_preserves_chemical_hash(self):
        doc = v02(); before = lower_depiction(doc)
        doc["depiction_states"][0]["lone_pairs"] = []
        after = lower_depiction(doc)
        self.assertEqual(before["chemical_inventory_sha256"],after["chemical_inventory_sha256"])
        self.assertNotEqual(before["depiction_plan_sha256"],after["depiction_plan_sha256"])
        self.assertNotEqual(before["ir_sha256"],after["ir_sha256"])
        self.assertEqual(canonical_sha256(after["chemical_inventory"]),after["chemical_inventory_sha256"])
        self.assertEqual(canonical_sha256({k:after[k] for k in ("plan_version","states","electron_flows","diagnostics")}),after["depiction_plan_sha256"])

    def test_chemical_change_alters_chemical_hash(self):
        before = lower_depiction(v02())
        doc = v02(); doc["atom_catalog"][2]["element"] = "Cl"
        after = lower_depiction(doc)
        self.assertNotEqual(before["chemical_inventory_sha256"],after["chemical_inventory_sha256"])

    def test_nonlocal_bond_to_atom_pool_gain_is_uncovered(self):
        # Two independent HF heterolyses, intentionally crosswired destinations.
        doc = {"ir_version":"mechanism-ir/0.2","atom_catalog":[
            {"map":1,"element":"H","implicit_h":0},{"map":2,"element":"F","implicit_h":0},
            {"map":3,"element":"H","implicit_h":0},{"map":4,"element":"F","implicit_h":0}],
            "states":[
                {"id":"a","label":"Before","formal_charges":[],"lone_pairs":[{"atom":2,"count":3},{"atom":4,"count":3}],"bonds":[{"atoms":[1,2],"order":1},{"atoms":[3,4],"order":1}],"chemical_species":[{"id":"hf1","atoms":[1,2]},{"id":"hf2","atoms":[3,4]}]},
                {"id":"b","label":"After","formal_charges":[{"atom":1,"value":1},{"atom":2,"value":-1},{"atom":3,"value":1},{"atom":4,"value":-1}],"lone_pairs":[{"atom":2,"count":4},{"atom":4,"count":4}],"bonds":[],"chemical_species":[{"id":str(a),"atoms":[a]} for a in range(1,5)]}],
            "transitions":[{"id":"t","from":"a","to":"b","label":"Formal control","kind":"elementary_teaching_step","electron_flows":[
                {"id":"f1","electron_count":2,"source":{"type":"bond","atoms":[1,2],"electrons":"sigma"},"sink":{"type":"atom","atom":4}},
                {"id":"f2","electron_count":2,"source":{"type":"bond","atoms":[3,4],"electrons":"sigma"},"sink":{"type":"atom","atom":2}}],
                "bond_changes":[{"atoms":[1,2],"from_order":1,"to_order":0},{"atoms":[3,4],"from_order":1,"to_order":0}],
                "charge_changes":[{"atom":a,"from":0,"to":1 if a%2 else -1} for a in range(1,5)]}],
            "entry_state":"a","stereo_constraints":[]}
        doc["depiction_states"] = [{"state_ref":st["id"],"species":[{"species_ref":sp["id"],"role":"explicitly_drawn"} for sp in st["chemical_species"]],"lone_pairs":[],"captions":[]} for st in doc["states"]]
        result = validate_mechanism(doc)
        self.assertEqual("partial",result["electron_flow_coverage"]["status"])
        self.assertEqual(2,len(result["electron_flow_coverage"]["diagnostics"]))
        self.assertEqual("unresolved_depiction",lower_depiction(doc)["status"])

    def test_triple_pi_pool_can_supply_two_distinct_pairs(self):
        # Formal inventory test, not a proposed stable reaction.
        doc = {"ir_version":"mechanism-ir/0.2","atom_catalog":[{"map":a,"element":"N","implicit_h":0} for a in (1,2)],
            "states":[{"id":sid,"label":sid,"formal_charges":[],"lone_pairs":[{"atom":a,"count":lp} for a in (1,2)],"bonds":[{"atoms":[1,2],"order":order}],"chemical_species":[{"id":"nitrogen-pair","atoms":[1,2]}]} for sid,lp,order in (("a",1,3),("b",2,1))],
            "transitions":[{"id":"t","from":"a","to":"b","label":"Formal electron inventory","kind":"elementary_teaching_step","electron_flows":[{"id":str(a),"electron_count":2,"source":{"type":"bond","atoms":[1,2],"electrons":"pi"},"sink":{"type":"atom","atom":a}} for a in (1,2)],"bond_changes":[{"atoms":[1,2],"from_order":3,"to_order":1}],"charge_changes":[]}],
            "entry_state":"a","stereo_constraints":[],"depiction_states":[{"state_ref":sid,"species":[{"species_ref":"nitrogen-pair","role":"explicitly_drawn"}],"lone_pairs":[],"captions":[]} for sid in ("a","b")]}
        self.assertEqual("checked_relationships_only",validate_mechanism(doc)["electron_flow_coverage"]["status"])
        extra = deepcopy(doc["transitions"][0]["electron_flows"][0]); extra["id"] = "third-pair"
        doc["transitions"][0]["electron_flows"].append(extra)
        self.assertCode("REUSED_ELECTRON_SOURCE",lambda:validate_mechanism(doc))

    def test_one_electron_radical_profile_stays_partial(self):
        # H radicals combine. Syntax/graph inventory are valid; full 1e compiler
        # and native fishhook depiction are explicitly outside this prototype.
        doc = {"ir_version":"mechanism-ir/0.2","atom_catalog":[{"map":a,"element":"H","implicit_h":0} for a in (1,2)],
            "states":[
                {"id":"a","label":"Radicals","formal_charges":[],"lone_pairs":[],"bonds":[],"atom_properties":[{"atom":a,"radical_electrons":1} for a in (1,2)],"chemical_species":[{"id":str(a),"atoms":[a]} for a in (1,2)]},
                {"id":"b","label":"Dihydrogen","formal_charges":[],"lone_pairs":[],"bonds":[{"atoms":[1,2],"order":1}],"chemical_species":[{"id":"h2","atoms":[1,2]}]}],
            "transitions":[{"id":"t","from":"a","to":"b","label":"Radical coupling","kind":"elementary_step","electron_flows":[{"id":str(a),"electron_count":1,"source":{"type":"radical","atom":a},"sink":{"type":"forming_bond","atoms":[1,2]}} for a in (1,2)],"bond_changes":[{"atoms":[1,2],"from_order":0,"to_order":1}],"charge_changes":[]}],
            "entry_state":"a","stereo_constraints":[]}
        doc["depiction_states"] = [{"state_ref":st["id"],"species":[{"species_ref":sp["id"],"role":"explicitly_drawn"} for sp in st["chemical_species"]],"lone_pairs":[],"captions":[]} for st in doc["states"]]
        self.assertEqual("partial",validate_mechanism(doc)["electron_flow_coverage"]["status"])
        plan = lower_depiction(doc)
        self.assertTrue(all(f["electron_count"]==1 for f in plan["electron_flows"]))
        self.assertEqual("unresolved_depiction",plan["status"])
        doc["transitions"][0]["electron_flows"][0]["electron_count"] = 2
        self.assertCode("INVALID_RADICAL_SOURCE",lambda:validate_mechanism(doc))

    def test_cli_preserves_typed_migration_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            inp, out = Path(directory)/"input.json", Path(directory)/"receipt.json"
            inp.write_text(json.dumps(proton_transfer_v01()), encoding="utf-8")
            result = subprocess.run([sys.executable,"-m","contracts.ir_v02","migrate",str(inp),"--output",str(out)], capture_output=True,text=True)
            self.assertEqual(1, result.returncode)
            self.assertEqual("MIGRATION_DEPICTION_REQUIRED", json.loads(out.read_text())["error"]["code"])
            self.assertNotIn("Traceback", result.stderr)

    def test_cli_refuses_overwrite_and_retains_input(self):
        with tempfile.TemporaryDirectory() as directory:
            inp = Path(directory)/"input.json"; inp.write_text(json.dumps(proton_transfer_v01()),encoding="utf-8")
            before = inp.read_bytes()
            result = subprocess.run([sys.executable,"-m","contracts.ir_v02","migrate",str(inp),"--output",str(inp)],capture_output=True,text=True)
            self.assertEqual("OUTPUT_EXISTS",json.loads(result.stdout)["error"]["code"])
            self.assertEqual(before, inp.read_bytes())

    def test_cli_bad_arguments_are_typed(self):
        result = subprocess.run([sys.executable,"-m","contracts.ir_v02","nonsense"],capture_output=True,text=True)
        self.assertEqual(1,result.returncode)
        self.assertEqual("CLI_ARGUMENT_ERROR",json.loads(result.stdout)["error"]["code"])


if __name__ == "__main__":
    unittest.main()
