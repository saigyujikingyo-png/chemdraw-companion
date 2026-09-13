"""Explicit CDXML atom observations, without a guessed valence model.

The COM NumImplicitHydrogens property is not used: native controls returned zero
for both labeled and unlabeled atoms. Missing serialized H may use a separately
bound selected-object FormulaHTML only in a qualified neutral-carbon profile.
It is never calculated from an element/valence table or expected IR.
Element identity is supplied by the IR contract's periodic table, not a native
capability whitelist. Unsupported native encodings remain separate errors.

CDXML field definitions (original SDK specification, preserved by IUPAC):
https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_NumHydrogens.htm
https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Node_Type.htm
"""
from __future__ import annotations
import math
import hashlib
import re
import xml.etree.ElementTree as ET


class NativeDepictionError(ValueError):
    def __init__(self, code, path, message, details=None):
        self.code, self.path, self.details = code, path, details or {}
        super().__init__(message)

    def as_dict(self):
        return dict(code=self.code, path=self.path, message=str(self), details=self.details)


def integer(value, path):
    try:
        if isinstance(value, bool):
            raise ValueError
        number = float(value)
        if not math.isfinite(number) or not number.is_integer():
            raise ValueError
        return int(number)
    except (TypeError, ValueError, OverflowError) as exc:
        raise NativeDepictionError('NATIVE_ATOM_FIELD_INVALID', path,
                                   'Expected an exact finite integer.') from exc


def node_attributes(atom, atomic_number):
    """Encode supplied atom identity; never infer H from element or charge."""
    if not isinstance(atomic_number, int) or not 1 <= atomic_number <= 118:
        raise NativeDepictionError('ELEMENT_IDENTITY_INVALID', 'atomic_number',
                                   'Expected a periodic-table atomic number.')
    if atom.get('radical_electrons', 0):
        raise NativeDepictionError('NATIVE_RADICAL_UNSUPPORTED', 'radical_electrons',
                                   'Native radical depiction has not been qualified.')
    values = {'Element': str(atomic_number), 'NumHydrogens': str(atom['implicit_h'])}
    if atom.get('charge', 0):
        values['Charge'] = str(atom['charge'])
    if atom.get('isotope'):
        values['Isotope'] = str(atom['isotope'])
    return values


def native_carbon_hydrogens(node, observation, bond_valence, path, neighborhood_qualified=False):
    """Native formula fallback limited to normal, bonded, neutral carbon.

    UnusedValences is NOT a universal H count (chloride is a counterexample).
    The caller supplies a hash-bound observation from the qualified native
    executor; all conditions refer to actual native data, not expected IR.
    """
    failure = NativeDepictionError('NATIVE_HYDROGEN_UNVERIFIED', path,
        'Missing serialized H has no qualified atom-associated native observation.',
        {'native_id': node.get('id'), 'profile': 'native-carbon-selection-formula-h/0.2'})
    if observation is None or bond_valence is None or not neighborhood_qualified:
        raise failure
    try:
        exact = lambda value: integer(value, path)
        if (exact(node.get('Element', '6')) != 6 or exact(node.get('Charge', '0')) != 0
                or exact(observation['atomic_number']) != 6 or exact(observation['formal_charge']) != 0
                or exact(observation['radical_native_value']) != 0 or exact(observation['node_type_native_value']) != 1
                or observation['implicit_h_allowed'] is not True or observation['abnormal_valence_allowed'] is not False
                or exact(observation['native_id']) != exact(node.get('id'))
                or exact(observation['atom_map']) != exact(node.get('AtomNumber'))
                or exact(observation['isotope']) != 0 or exact(node.get('Isotope', '0')) != 0
                or bond_valence <= 0 or exact(observation['used_valences']) != bond_valence
                or exact(observation['selected_count']) != 1
                or exact(observation['selected_atom_count']) != 1
                or exact(observation['selected_bond_count']) != 0
                or len(observation['selected_atom_ids']) != 1
                or exact(observation['selected_atom_ids'][0]) != exact(node.get('id'))):
            raise failure
        # FormulaHTML reports H explicitly and marks bonds outside the selection
        # with a superscript bullet suffix. That suffix is not an atom radical.
        formula = re.fullmatch(r'C(?:(H)(?:<sub>([1-9][0-9]*)</sub>)?)?(?:<sup>([1-9][0-9]*)?&bull;</sup>)?', observation['selected_formula_html'])
        if formula is None:
            raise failure
        hydrogens = (int(formula[2]) if formula[2] else 1) if formula[1] else 0
        cut_bond_units = int(formula[3] or '1') if '<sup>' in observation['selected_formula_html'] else 0
        if not 0 <= hydrogens <= 3 or cut_bond_units != bond_valence:
            raise failure
    except (KeyError, TypeError, ValueError) as exc:
        if exc is failure:
            raise
        raise failure from exc
    return hydrogens


def read_node_identity(node, expected, *, path='native_atom', native_observation=None, native_bond_valence=None, native_neighborhood_qualified=False):
    """Cross-check actual serialized fields before attaching expected metadata.

    CDXML's omitted Element denotes carbon. Omitted NumHydrogens is deliberately
    not interpreted as zero or inferred from a closed-shell valence table.
    """
    if node.get('NodeType') not in (None, 'Element'):
        raise NativeDepictionError('NATIVE_NODE_TYPE_UNSUPPORTED', path,
                                   'Only explicit element atom occurrences are supported.')
    if node.get('Radical') not in (None, 'None', '0'):
        raise NativeDepictionError('NATIVE_RADICAL_UNSUPPORTED', path,
                                   'Unexpected or unqualified native radical encoding.')
    if node.get('NumHydrogens') is None:
        hydrogens = native_carbon_hydrogens(node, native_observation, native_bond_valence, path, native_neighborhood_qualified)
        h_source = 'Document.Selection.Objects.FormulaHTML; native-carbon-selection-formula-h/0.2'
    else:
        hydrogens = integer(node.get('NumHydrogens'), path + '.NumHydrogens')
        h_source = 'native CDXML NumHydrogens'
    observed = {
        'atomic_number': integer(node.get('Element', '6'), path + '.Element'),
        'charge': integer(node.get('Charge', '0'), path + '.Charge'),
        'implicit_h': hydrogens,
        'isotope': integer(node.get('Isotope', '0'), path + '.Isotope'),
        'radical_electrons': 0,
    }
    for key, actual in observed.items():
        wanted = expected.get(key, 0)
        if actual != wanted:
            raise NativeDepictionError('NATIVE_ATOM_IDENTITY_CHANGED', path + '.' + key,
                                       'Native atom identity differs from the declared occurrence.',
                                       {'expected': wanted, 'observed': actual,
                                        'native_id': node.get('id')})
    return {**observed, 'implicit_h_source': h_source}


def graph_attributes(root):
    result = {}
    for tag in ('n', 'b'):
        rows = list(root.iter(tag))
        values = {row.get('id'): dict(row.attrib) for row in rows}
        if None in values or len(values) != len(rows):
            raise ValueError('Native graph has missing or duplicate object IDs.')
        result[tag] = values
    return result


def verify_atom_readback(path, atom_readback):
    """Check sidecar content against both actual native snapshots, never IR H."""
    failure = NativeDepictionError('NATIVE_ATOM_OBSERVATION_UNVERIFIED', str(path),
                                  'Native atom observation lacks exact file, graph and identity bindings.')
    try:
        source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if (atom_readback.get('version') != 'native-atom-readback/0.4'
                or atom_readback.get('source_cdxml_sha256') != source_hash):
            raise failure
        before = atom_readback.get('chemical_export_before_sha256', '')
        if (atom_readback.get('selection_chemical_export_unchanged') is not True
                or atom_readback.get('chemical_export_mime') != 'chemical/x-smiles'
                or not re.fullmatch('[a-f0-9]{64}', before)
                or atom_readback.get('chemical_export_after_sha256') != before
                or atom_readback.get('selection_graph_unchanged') is not True):
            raise failure
        after = atom_readback['selection_after_cdxml']
        if after['file'] != path.stem + '-selection-after.cdxml':
            raise failure
        after_path = path.parent / after['file']
        if after['sha256'] != hashlib.sha256(after_path.read_bytes()).hexdigest():
            raise failure
        root = ET.parse(path).getroot()
        if graph_attributes(root) != graph_attributes(ET.parse(after_path).getroot()):
            raise failure
        observations = {}
        for row in atom_readback['atoms']:
            key = integer(row['native_id'], 'native_observation.native_id')
            if key in observations:
                raise failure
            observations[key] = row
        nodes = list(root.iter('n'))
        if set(observations) != {integer(n.get('id'), 'native_atom.id') for n in nodes}:
            raise failure
        for node in nodes:
            row = observations[integer(node.get('id'), 'native_atom.id')]
            for field, attribute, default in (('atom_map','AtomNumber',None), ('atomic_number','Element','6'),
                                              ('formal_charge','Charge','0'), ('isotope','Isotope','0')):
                if integer(row[field], field) != integer(node.get(attribute, default), attribute):
                    raise failure
        return observations
    except (KeyError, TypeError, ValueError, OSError, ET.ParseError) as exc:
        if exc is failure:
            raise
        raise failure from exc


def qualified_saturated_carbon_monocycle(atom_map, by_map, adjacency, observations):
    """Qualified cyclic profile, checked on the complete native component.

    One 3-8 member saturated carbon cycle, optionally bearing saturated carbon
    trees. No heteroatoms/explicit H, charge, isotope, radical or unsaturation.
    The graph only selects a capability profile; it never calculates H.
    """
    if observations is None:
        return False
    component, pending = set(), [atom_map]
    while pending:
        current = pending.pop()
        if current in component:
            continue
        component.add(current)
        pending.extend(adjacency[current])
    try:
        for current in component:
            node = by_map[current]
            observed = observations[integer(node.get('id'), 'native_atom.id')]
            if (integer(node.get('Element', '6'), 'Element') != 6
                    or integer(node.get('Charge', '0'), 'Charge') != 0
                    or integer(node.get('Isotope', '0'), 'Isotope') != 0
                    or node.get('NodeType') not in (None, 'Element')
                    or node.get('Radical') not in (None, 'None', '0')
                    or integer(observed['atomic_number'], 'atomic_number') != 6
                    or integer(observed['formal_charge'], 'formal_charge') != 0
                    or integer(observed['isotope'], 'isotope') != 0
                    or integer(observed['radical_native_value'], 'radical_native_value') != 0
                    or integer(observed['node_type_native_value'], 'node_type_native_value') != 1
                    or observed['implicit_h_allowed'] is not True
                    or observed['abnormal_valence_allowed'] is not False
                    or any(order != 1 for order in adjacency[current].values())):
                return False
    except (KeyError, TypeError, ValueError):
        return False
    # Remove terminal trees. A single simple cycle has a connected 2-core with
    # degree two everywhere; fused, spiro, bridged and joined cycles fail here.
    core = set(component)
    degree = {current: len(adjacency[current]) for current in core}
    leaves = [current for current in core if degree[current] < 2]
    while leaves:
        current = leaves.pop()
        if current not in core:
            continue
        core.remove(current)
        for other in adjacency[current]:
            if other in core:
                degree[other] -= 1
                if degree[other] < 2:
                    leaves.append(other)
    return atom_map in core and 3 <= len(core) <= 8 and all(degree[current] == 2 for current in core)


def qualified_carbon_neighborhood(atom_map, by_map, adjacency, observations=None):
    """Acyclic profile, or the independently qualified saturated monocycle."""
    neighbors = adjacency[atom_map]
    if not neighbors or any(order not in (1, 2, 3) for order in neighbors.values()):
        return False
    explicit_h = [other for other in neighbors if integer(by_map[other].get('Element', '6'), 'Element') == 1]
    if len(explicit_h) > 1:
        return False
    for other in explicit_h:
        node = by_map[other]
        if (neighbors[other] != 1 or adjacency[other] != {atom_map: 1}
                or node.get('NodeType') not in (None, 'Element')
                or node.get('Radical') not in (None, 'None', '0')
                or integer(node.get('Isotope', '0'), 'Isotope') not in (0, 2)
                or integer(node.get('Charge', '0'), 'Charge') != 0
                or integer(node.get('NumHydrogens'), 'NumHydrogens') != 0):
            return False
    seen = {atom_map}
    for neighbor in neighbors:
        if neighbor in seen:
            return qualified_saturated_carbon_monocycle(atom_map, by_map, adjacency, observations)
        pending = [neighbor]
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            pending.extend(other for other in adjacency[current] if other not in seen)
    return True


def read_explicit_geometry(path, expected_atoms, expected_bonds, *, atom_readback=None):
    """Read a depicted subset only; caller separately verifies IR and receipt."""
    root = ET.parse(path).getroot()
    nodes = list(root.iter('n'))
    by_map, native_ids = {}, {}
    for node in nodes:
        atom_map = integer(node.get('AtomNumber'), 'native_atom.AtomNumber')
        native_id = node.get('id')
        if atom_map in by_map or not native_id or native_id in native_ids:
            raise NativeDepictionError('NATIVE_ATOM_MAPPING_CHANGED', str(path),
                                       'Native atom occurrences do not have unique map and object identities.')
        by_map[atom_map], native_ids[native_id] = node, atom_map
    if set(by_map) != set(expected_atoms):
        raise NativeDepictionError('NATIVE_VISIBLE_INVENTORY_CHANGED', str(path),
                                   'Native atom coverage differs from the explicit depiction plan.',
                                   {'expected': sorted(expected_atoms), 'observed': sorted(by_map)})
    observations = verify_atom_readback(path, atom_readback) if atom_readback is not None else {}
    native_valences = {i: 0 for i in by_map}
    adjacency = {i: {} for i in by_map}
    for bond in root.iter('b'):
        for end in ('B', 'E'):
            if bond.get(end) not in native_ids:
                raise NativeDepictionError('NATIVE_BOND_MAPPING_CHANGED', str(path), 'Unknown native bond endpoint.')
            native_valences[native_ids[bond.get(end)]] += float(bond.get('Order', '1'))
        a, b = (native_ids[bond.get(end)] for end in ('B', 'E'))
        adjacency[a][b] = adjacency[b][a] = float(bond.get('Order', '1'))
    atoms, bonds = {}, []
    for atom_map, node in by_map.items():
        identity = read_node_identity(node, expected_atoms[atom_map], path=f'atom[{atom_map}]',
                                      native_observation=observations.get(integer(node.get('id'), 'native_atom.id')),
                                      native_bond_valence=native_valences[atom_map],
                                      native_neighborhood_qualified=(node.get('NumHydrogens') is None and
                                          qualified_carbon_neighborhood(atom_map, by_map, adjacency, observations)))
        position = tuple(map(float, node.get('p', '').split()))
        if len(position) != 2 or not all(math.isfinite(v) for v in position):
            raise NativeDepictionError('NATIVE_COORDINATE_INVALID', f'atom[{atom_map}]',
                                       'Native atom coordinates must be finite two-dimensional points.')
        text = node.find('t')
        label = None
        if text is not None:
            anchor = tuple(map(float, text.get('p', '').split()))
            bounds = tuple(map(float, text.get('BoundingBox', '').split()))
            if len(anchor) != 2 or len(bounds) != 4 or not all(math.isfinite(v) for v in (*anchor, *bounds)):
                raise NativeDepictionError('NATIVE_LABEL_GEOMETRY_UNVERIFIED', f'atom[{atom_map}]',
                                           'Native label lacks complete measured anchor/bounds.')
            label = {
                'offset': [anchor[k] - position[k] for k in range(2)],
                'bbox_offset': [bounds[k] - position[k % 2] for k in range(4)],
                'alignment': {key: text.get(key) for key in
                              ('LabelJustification', 'LabelAlignment', 'Justification') if text.get(key) is not None},
                'runs': [{'text': run.text or '', 'face': run.get('face', '0'),
                          'size': float(run.get('size', '8'))} for run in text.findall('s')],
            }
        atoms[atom_map] = {**identity, 'position': position, 'label': label,
                           'element': expected_atoms[atom_map]['element']}
    actual = {}
    for node in root.iter('b'):
        if node.get('B') not in native_ids or node.get('E') not in native_ids:
            raise NativeDepictionError('NATIVE_BOND_MAPPING_CHANGED', str(path),
                                       'Native bond refers to an unknown visible atom.')
        endpoints = (native_ids[node.get('B')], native_ids[node.get('E')])
        key, order = frozenset(endpoints), float(node.get('Order', '1'))
        if len(key) != 2 or key in actual or not math.isfinite(order):
            raise NativeDepictionError('NATIVE_BOND_MAPPING_CHANGED', str(path),
                                       'Duplicate or invalid native bond.')
        actual[key] = order
        bonds.append({'atoms': endpoints, 'order': order, 'display': node.get('Display', 'Solid')})
    expected = {frozenset(b['atoms']): b['order'] for b in expected_bonds}
    if actual != expected:
        raise NativeDepictionError('NATIVE_VISIBLE_BONDS_CHANGED', str(path),
                                   'Native bond graph differs from the seeded visible graph.')
    return {'atoms': atoms, 'bonds': bonds}
