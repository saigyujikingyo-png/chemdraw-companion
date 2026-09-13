"""Explicit CDXML atom observations, without a guessed valence model.

The COM NumImplicitHydrogens property is not used: a native control returned
zero for atoms whose saved CDXML explicitly retained NumHydrogens=2 and =3.
Element identity is supplied by the IR contract's periodic table, not a native
capability whitelist. Unsupported native encodings remain separate errors.

CDXML field definitions (original SDK specification, preserved by IUPAC):
https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Atom_NumHydrogens.htm
https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Node_Type.htm
"""
from __future__ import annotations
import math
import xml.etree.ElementTree as ET


class NativeDepictionError(ValueError):
    def __init__(self, code, path, message, details=None):
        self.code, self.path, self.details = code, path, details or {}
        super().__init__(message)

    def as_dict(self):
        return dict(code=self.code, path=self.path, message=str(self), details=self.details)


def integer(value, path):
    try:
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


def read_node_identity(node, expected, *, path='native_atom'):
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
        raise NativeDepictionError('NATIVE_HYDROGEN_UNVERIFIED', path,
                                   'Native CDXML did not explicitly preserve the hydrogen count.',
                                   {'native_id': node.get('id'), 'field': 'NumHydrogens'})
    observed = {
        'atomic_number': integer(node.get('Element', '6'), path + '.Element'),
        'charge': integer(node.get('Charge', '0'), path + '.Charge'),
        'implicit_h': integer(node.get('NumHydrogens'), path + '.NumHydrogens'),
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
    return {**observed, 'implicit_h_source': 'native CDXML NumHydrogens'}


def read_explicit_geometry(path, expected_atoms, expected_bonds):
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
    atoms, bonds = {}, []
    for atom_map, node in by_map.items():
        identity = read_node_identity(node, expected_atoms[atom_map], path=f'atom[{atom_map}]')
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
