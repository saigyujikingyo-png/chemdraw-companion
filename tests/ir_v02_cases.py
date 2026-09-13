"""Independent synthetic integration inputs; never production templates."""
from copy import deepcopy
from contracts.ir_v02 import migrate_v01
from contracts.ir_v02.test_ir_v02 import proton_transfer_v01, nonendpoint_v01

STYLE = {'flow': 'serpentine', 'first_row_direction': 'left_to_right',
         'max_columns': 2, 'minimum_row_turns': 0, 'canvas_width_mm': 180,
         'canvas_height_mm': 120, 'outer_margin_mm': 5, 'row_gap_bond_lengths': 1.5,
         'font_family': 'Arial', 'font_pt': 8, 'bond_length_pt': 14.4,
         'stroke_pt': .6, 'minimum_native_dpi': 600}


def request(mechanism):
    return {'contract_version': 'composer-request/0.2',
            'mechanism': deepcopy(mechanism), 'layout_policy': deepcopy(STYLE)}


def selected_pairs():
    mechanism = migrate_v01(proton_transfer_v01(), policy='preserve_v01_display')
    mechanism['depiction_states'][0]['lone_pairs'] = [
        {'atom_ref': 1, 'displayed_pairs': 1, 'slots': [{'pair_index': 2, 'orientation': 'auto'}]}]
    mechanism['depiction_states'][1]['lone_pairs'] = [
        {'atom_ref': 3, 'displayed_pairs': 1, 'slots': [{'pair_index': 3, 'orientation': 'auto'}]}]
    return request(mechanism)


def nonendpoint():
    return request(migrate_v01(nonendpoint_v01(), policy='preserve_v01_display'))


def static_selected_pair():
    return request({'ir_version': 'mechanism-ir/0.2', 'entry_state': 'water',
        'atom_catalog': [{'map': 1, 'element': 'O', 'implicit_h': 2}],
        'states': [{'id': 'water', 'label': 'Water', 'bonds': [], 'formal_charges': [],
                    'lone_pairs': [{'atom': 1, 'count': 2}],
                    'chemical_species': [{'id': 'water_species', 'atoms': [1]}]}],
        'transitions': [], 'stereo_constraints': [],
        'depiction_states': [{'state_ref': 'water', 'species': [
            {'species_ref': 'water_species', 'role': 'explicitly_drawn'}],
            'lone_pairs': [{'atom_ref': 1, 'displayed_pairs': 1, 'slots': [
                {'pair_index': 1, 'orientation': 'auto'}]}],
            'captions': [{'id': 'name', 'role': 'state_label', 'text': 'Water'}]}]})


def ammonium_salt(role='counterion_hidden'):
    mechanism = {'ir_version': 'mechanism-ir/0.2', 'entry_state': 'salt',
        'atom_catalog': [{'map': 10, 'element': 'N', 'implicit_h': 4},
                         {'map': 20, 'element': 'Cl', 'implicit_h': 0}],
        'states': [{'id': 'salt', 'label': 'Ammonium salt', 'bonds': [],
                    'formal_charges': [{'atom': 10, 'value': 1}, {'atom': 20, 'value': -1}],
                    'lone_pairs': [{'atom': 20, 'count': 4}],
                    'chemical_species': [{'id': 'cation', 'atoms': [10]}, {'id': 'anion', 'atoms': [20]}]}],
        'transitions': [], 'stereo_constraints': [],
        'depiction_states': [{'state_ref': 'salt', 'species': [
            {'species_ref': 'cation', 'role': 'explicitly_drawn'},
            {'species_ref': 'anion', 'role': role}], 'lone_pairs': [],
            'captions': [{'id': 'name', 'role': 'state_label', 'text': 'Ammonium salt'}]}]}
    if role == 'condition_caption':
        mechanism['depiction_states'][0]['captions'].append(
            {'id': 'condition', 'role': 'condition', 'text': 'Chloride present', 'species_refs': ['anion']})
    return request(mechanism)
