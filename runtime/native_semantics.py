"""Scoped native observations; expected chemistry is only a later comparison.

The v1 candidate covers simple neutral C/N/O acyclic graphs, saturated C5/C6
monocycles and a saturated C4O five-cycle, terminal H/D, NH4+ and Cl-. It is
not an aromaticity or valence engine. A source freeze and independent native
qualification are required at the production entry; calling this pure reader
on a synthetic fixture does not establish native qualification.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from contracts.ir_v02 import ATOMIC_NUMBERS
from runtime.native_observation import (quantity, observe_atom_label,
    observe_serialized_label_h, compare_quantity)

PROFILE = 'native-semantic-readback/1.0'
SYMBOLS = {number: symbol for symbol, number in ATOMIC_NUMBERS.items()}


def exact_int(raw):
    if isinstance(raw, bool) or re.fullmatch(r'-?[0-9]+', str(raw)) is None:
        raise ValueError('Invalid native integer')
    return int(raw)


def simple_label(node):
    """Parse a single atom label, never page text or compound abbreviations.

    A label can be written in either orientation (CH3 / H3C). Text run styles
    remain in the raw subtree; this bounded grammar accepts plain counts and
    one +/- charge, not arbitrary rich-text formula interpretation.
    """
    labels = node.findall('t')
    if not labels:
        return {'status': 'absent', 'raw': None}
    if len(labels) != 1 or not list(labels[0]) or any(c.tag != 's' or list(c) for c in labels[0]):
        return {'status': 'unsupported', 'reason': 'compound_or_nested_label'}
    text = ''.join(c.text or '' for c in labels[0])
    normalized = text.replace('\u2212', '-')
    forward = re.fullmatch(r'(C|N|O|Cl|D|H)(?:H([1-9][0-9]*)?)?([+-])?', normalized)
    reverse = re.fullmatch(r'H([1-9][0-9]*)?(C|N|O)([+-])?', normalized)
    if forward:
        symbol, count, sign = forward.groups()
        suffix = normalized[len(symbol):].rstrip('+-')
        hydrogens = int(count or 1) if suffix.startswith('H') else 0
    elif reverse:
        count, symbol, sign = reverse.groups()
        hydrogens = int(count or 1)
    else:
        return {'status': 'unsupported', 'raw': text, 'reason': 'label_grammar_unqualified'}
    if symbol in ('H', 'D') and hydrogens:
        return {'status': 'unsupported', 'raw': text, 'reason': 'compound_hydrogen_label'}
    return dict(status='parsed', raw=text, atomic_number=1 if symbol == 'D' else ATOMIC_NUMBERS[symbol],
                isotope=2 if symbol == 'D' else 0, charge={'+': 1, '-': -1, None: 0}[sign],
                non_node_attached_h=hydrogens)


def native_graph(root):
    by_map, by_id, adjacency, bonds = {}, {}, {}, []
    for node in root.iter('n'):
        atom_map, native_id = exact_int(node.get('AtomNumber')), exact_int(node.get('id'))
        if atom_map in by_map or native_id in by_id:
            raise ValueError('NATIVE_ATOM_MAPPING_CHANGED')
        by_map[atom_map], by_id[native_id], adjacency[atom_map] = node, atom_map, {}
    bond_ids = set()
    for bond in root.iter('b'):
        bond_id = exact_int(bond.get('id'))
        a, b = (by_id[exact_int(bond.get(end))] for end in ('B', 'E'))
        order = float(bond.get('Order', '1'))
        if bond_id in bond_ids or a == b or b in adjacency[a] or order not in (1, 1.5, 2, 3):
            raise ValueError('NATIVE_BOND_MAPPING_CHANGED')
        bond_ids.add(bond_id)
        adjacency[a][b] = adjacency[b][a] = order
        bonds.append(dict(native_id=bond_id, atoms=sorted((a, b)), order=order))
    return by_map, adjacency, bonds


def component_scope(atom_map, by_map, adjacency, rows):
    component, pending = set(), [atom_map]
    while pending:
        current = pending.pop()
        if current not in component:
            component.add(current)
            pending.extend(adjacency[current])
    try:
        for current in component:
            node = by_map[current]
            raw = rows[exact_int(node.get('id'))]
            z, charge, isotope = (exact_int(node.get(k, d)) for k, d in
                                  (('Element', '6'), ('Charge', '0'), ('Isotope', '0')))
            if (node.get('NodeType') not in (None, 'Element') or node.get('Radical') not in (None, '0', 'None')
                    or any(k.startswith('Restrict') or k in ('GenericNickname', 'Nickname', 'ElementList',
                           'AbnormalValence', 'ImplicitHydrogens') for k in node.attrib)
                    or exact_int(raw['radical_native_value']) != 0 or exact_int(raw['node_type_native_value']) != 1
                    or raw['abnormal_valence_allowed'] is not False):
                return None, 'query_radical_abnormal_or_non_element'
            if z == 1:
                if (isotope not in (0, 2) or charge or len(adjacency[current]) != 1
                        or next(iter(adjacency[current].values())) != 1):
                    return None, 'nonterminal_or_unqualified_hydrogen_node'
            elif z in (6, 7, 8):
                if isotope or (charge and not (len(component) == 1 and z == 7 and charge == 1)):
                    return None, 'charge_or_isotope_outside_scope'
            elif not (z == 17 and charge == -1 and isotope == 0 and len(component) == 1):
                return None, 'element_hydrogen_capability_unqualified'
            if any(order not in (1, 2, 3) for order in adjacency[current].values()):
                return None, 'aromatic_or_query_bond'
        if len(component) == 1:
            n = by_map[atom_map]
            if (exact_int(n.get('Element', '6')), exact_int(n.get('Charge', '0'))) in ((7, 1), (17, -1)):
                return 'isolated_ammonium_or_chloride', None
            return None, 'isolated_atom_attached_h_unqualified'
        edges = sum(len(adjacency[a]) for a in component) // 2
        if edges == len(component) - 1:
            return 'acyclic_normal_cno_hd', None
        if edges != len(component):
            return None, 'multiple_cycle_scope_unqualified'
        core = set(component)
        degree = {a: len(adjacency[a]) for a in core}
        leaves = [a for a in core if degree[a] < 2]
        while leaves:
            a = leaves.pop()
            if a not in core:
                continue
            core.remove(a)
            for b in adjacency[a]:
                if b in core:
                    degree[b] -= 1
                    if degree[b] < 2:
                        leaves.append(b)
        if any(degree[a] != 2 or any(order != 1 for b, order in adjacency[a].items() if b in core) for a in core):
            return None, 'cyclic_unsaturation_unqualified'
        elements = sorted(exact_int(by_map[a].get('Element', '6')) for a in core)
        if elements in ([6]*5, [6]*6):
            return 'saturated_c5_c6_monocycle', None
        if elements == [6, 6, 6, 6, 8]:
            return 'saturated_c4o_five_cycle', None
        return None, 'cycle_size_or_heteroatom_scope_unqualified'
    except (KeyError, ValueError, TypeError):
        return None, 'incomplete_native_domain_evidence'


def selected_carbon_h(node, row, incident_order):
    """Interpret the actual selected formula; do not compute H from valence."""
    try:
        if (exact_int(node.get('Element', '6')) != 6 or exact_int(node.get('Charge', '0'))
                or exact_int(node.get('Isotope', '0')) or row['implicit_h_allowed'] is not True
                or exact_int(row['selected_count']) != 1 or exact_int(row['selected_atom_count']) != 1
                or exact_int(row['selected_bond_count']) != 0
                or [exact_int(x) for x in row['selected_atom_ids']] != [exact_int(node.get('id'))]
                or float(row['used_valences']) != incident_order):
            return None, 'selection_or_valence_binding_unqualified'
        formula = row['selected_formula_html']
        match = re.fullmatch(r'C(?:(H)(?:<sub>([1-9][0-9]*)</sub>)?)?(?:<sup>([1-9][0-9]*)?&bull;</sup>)?', formula)
        if not match:
            return None, 'selected_formula_grammar_unqualified'
        hydrogens = int(match[2] or 1) if match[1] else 0
        cut_bonds = int(match[3] or 1) if '<sup>' in formula else 0
        if hydrogens > 4 or cut_bonds != incident_order:
            return None, 'selected_formula_cut_bond_mismatch'
        return hydrogens, None
    except (KeyError, TypeError, ValueError):
        return None, 'selection_missing_or_ambiguous'


def observe_atom(node, by_map, adjacency, rows, artifact_hash, *, warnings):
    atom_map, native_id = exact_int(node.get('AtomNumber')), exact_int(node.get('id'))
    binding = dict(artifact_sha256=artifact_hash, native_id=native_id, atom_map=atom_map, profile=PROFILE)
    def q(name, value, source, field, *, raw=None, present=True, reason=None, scope='atom-local serialized identity'):
        return quantity(name, value, source, field=field, raw=raw, present=present, reason=reason, scope=scope, **binding)
    label = simple_label(node)
    identity, conflicts = {}, []
    for name, attr, default in [('atomic_number', 'Element', '6'), ('charge', 'Charge', '0'), ('isotope', 'Isotope', '0')]:
        value = exact_int(node.get(attr, default))
        if name == 'atomic_number' and value not in SYMBOLS:
            raise ValueError('ELEMENT_IDENTITY_INVALID')
        identity[name] = q(name, value, 'explicit_native_field' if attr in node.attrib else 'qualified_format_decode',
                           'n@'+attr, raw=node.get(attr), present=attr in node.attrib)
        if label['status'] == 'parsed' and label[name] != value:
            conflicts.append('label_'+name+'_conflict')
    radical = node.get('Radical')
    radical_value = {None: 0, 'None': 0, '0': 0, 'Doublet': 1, 'Singlet': 2, 'Triplet': 2}.get(radical)
    identity['radical_electrons'] = q('radical_electrons', radical_value,
        'unknown' if radical_value is None else 'explicit_native_field' if radical is not None else 'qualified_format_decode',
        'n@Radical', raw=radical, present=radical is not None,
        reason='radical_encoding_unqualified' if radical_value is None else None)
    explicit_h = []
    for other, order in adjacency[atom_map].items():
        neighbor = by_map[other]
        if exact_int(neighbor.get('Element', '6')) == 1:
            explicit_h.append(dict(atom_map=other, native_id=exact_int(neighbor.get('id')),
                                   isotope=exact_int(neighbor.get('Isotope', '0')), order=order))
    explicit_h.sort(key=lambda x: x['atom_map'])
    raw_h = observe_serialized_label_h(node, artifact_hash)
    label_h = q('label_non_node_h', label.get('non_node_attached_h'),
                'qualified_format_decode' if label['status'] == 'parsed' else 'unknown', 'n/t/s simple label',
                raw=label, present=label['status'] != 'absent', reason=None if label['status'] == 'parsed' else label['status'])
    scope, scope_reason = component_scope(atom_map, by_map, adjacency, rows)
    row = rows.get(native_id, {})
    api_h, api_reason = selected_carbon_h(node, row, sum(adjacency[atom_map].values()))
    api = q('selected_formula_non_node_h', api_h, 'native_api_observation' if api_h is not None else 'unknown',
            'Document.Selection.Objects.FormulaHTML', raw=deepcopy(row), present='selected_formula_html' in row,
            reason=api_reason, scope='one neutral carbon; exact selection and incident cut-bond binding')
    values = [x for x in (raw_h['value'], label_h['value'], api_h) if x is not None]
    if len(set(values)) > 1:
        conflicts.append('attached_h_sources_conflict')
    reason = (','.join(conflicts) if conflicts else 'native_chemical_warnings' if warnings != 0 else scope_reason
              or ('malformed_label_h' if raw_h['present'] and raw_h['value'] is None else None)
              or ('unqualified_atom_label' if label['status'] == 'unsupported' else None))
    # Independent H/D nodes stay separate; no neighbor count is added to any H field.
    if reason:
        resolved = q('non_node_attached_h', None, 'unknown', 'scoped evidence resolution', raw=values,
                     reason=reason, scope=scope)
    elif raw_h['value'] is not None:
        resolved = q('non_node_attached_h', raw_h['value'], 'qualified_format_decode', 'n@NumHydrogens',
                     raw=raw_h['raw'], scope=scope)
    elif label_h['value'] is not None:
        resolved = q('non_node_attached_h', label_h['value'], 'qualified_format_decode', 'n/t/s simple label',
                     raw=label, scope=scope)
    elif api_h is not None:
        resolved = q('non_node_attached_h', api_h, 'native_api_observation', 'Document.Selection.Objects.FormulaHTML',
                     raw=row['selected_formula_html'], scope=scope)
    else:
        resolved = q('non_node_attached_h', None, 'unknown', 'scoped evidence resolution',
                     reason='missing_qualified_attached_h_observation', scope=scope)
    return dict(native_id=native_id, atom_map=atom_map, identity=identity,
                serialized_label_h=raw_h, atom_label=observe_atom_label(node, artifact_hash),
                label_non_node_h=label_h, explicit_h_neighbor_nodes=q('explicit_h_neighbor_nodes', explicit_h,
                    'qualified_format_decode', 'native n/b graph', raw=explicit_h, scope='independent H/D nodes, counted once'),
                selected_formula_non_node_h=api, non_node_attached_h=resolved, conflicts=conflicts)


def observe_document(path, atom_readback, *, source_freeze):
    """Actual production reader. It takes no expected atoms, H or graph."""
    from runtime.adapters.cdxml_atom_identity import verify_atom_readback
    from runtime.native_source_binding import verify_source_freeze, verify_observer_binding
    path = Path(path)
    if atom_readback.get('version') != 'native-atom-readback/0.5':
        raise ValueError('NATIVE_SEMANTIC_OBSERVER_UNQUALIFIED: v1 requires the frozen 0.5 observer')
    verify_observer_binding(atom_readback, verify_source_freeze(source_freeze))
    rows = verify_atom_readback(path, atom_readback)
    root = ET.parse(path).getroot()
    by_map, adjacency, bonds = native_graph(root)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    atoms = {m: observe_atom(n, by_map, adjacency, rows, digest,
                            warnings=atom_readback.get('chemical_warnings')) for m, n in by_map.items()}
    return dict(version=PROFILE, artifact_sha256=digest, atoms=atoms, bonds=bonds,
                evidence_class='observations under versioned scope; qualification requires separate native controls')


def compare_document(observed, expected_atoms, expected_bonds):
    """Separate immutable comparison; unknown never receives the expected value."""
    expected = {int(k): v for k, v in expected_atoms.items()}
    atoms = {}
    for m in sorted(set(expected) & set(observed['atoms'])):
        row, wanted = observed['atoms'][m], expected[m]
        atoms[m] = {key: compare_quantity(value, wanted.get(key, 0)) for key, value in row['identity'].items()}
        atoms[m]['non_node_attached_h'] = compare_quantity(row['non_node_attached_h'],
                                             wanted.get('non_node_attached_h', wanted.get('implicit_h')))
        if 'explicit_h_neighbor_nodes' in wanted:
            # Native IDs are phase-specific custody, not expected chemical IDs.
            h = deepcopy(row['explicit_h_neighbor_nodes'])
            h['value'] = [{k: v for k, v in n.items() if k != 'native_id'} for n in h['value']]
            atoms[m]['explicit_h_neighbor_nodes'] = compare_quantity(h, wanted['explicit_h_neighbor_nodes'])
    actual_bonds = sorted((tuple(b['atoms']), b['order']) for b in observed['bonds'])
    wanted_bonds = sorted((tuple(sorted(b['atoms'])), b['order']) for b in expected_bonds)
    statuses = [item['status'] for row in atoms.values() for item in row.values()]
    inventory_equal = set(expected) == set(observed['atoms'])
    graph_equal = actual_bonds == wanted_bonds
    return dict(status='mismatch' if not inventory_equal or not graph_equal or 'mismatch' in statuses else
                'unverified' if 'unverified' in statuses else 'match', inventory_equal=inventory_equal,
                graph_equal=graph_equal, atoms=atoms)
