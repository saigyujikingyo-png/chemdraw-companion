"""Check the narrow ethanol evidence. This is not a general chemistry validator."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
from xml.etree import ElementTree as ET


def graph_snapshot(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) > 2 * 1024 * 1024 or b'<!ENTITY' in data.upper():
        raise ValueError('Oversized or entity-bearing XML is outside the smoke scope')
    root = ET.fromstring(data)
    if root.tag != 'CDXML':
        raise ValueError('Expected native CDXML')
    unsupported = {'arrow', 'curve', 'graphic', 'embeddedobject', 'picture', 'scheme', 'step'}
    if any(node.tag in unsupported for node in root.iter()):
        raise ValueError('Drawable/reaction objects need a separate qualified comparator')
    raw_atoms = []
    for atom in root.iter('n'):
        raw_atoms.append((atom.attrib['id'], (
            int(atom.get('Element', '6')), int(atom.get('Charge', '0')),
            atom.get('Isotope', ''), atom.get('NumHydrogens', ''),
            tuple(float(value) for value in atom.attrib['p'].split()),
            atom.get('AS', ''), tuple(''.join(text.itertext()) for text in atom.iter('s')),
        )))
    if len({item[0] for item in raw_atoms}) != len(raw_atoms):
        raise ValueError('Duplicate native atom IDs')
    atoms = sorted(raw_atoms, key=lambda item: item[1])
    index = {item[0]: position for position, item in enumerate(atoms)}
    bonds = []
    for bond in root.iter('b'):
        if bond.get('B') not in index or bond.get('E') not in index:
            raise ValueError('Dangling native bond endpoint')
        # Preserve endpoint orientation: it matters to wedges and dashed wedges.
        bonds.append((index[bond.attrib['B']], index[bond.attrib['E']], bond.get('Order', '1'), bond.get('Display', 'Solid')))
    # Free text is included, not silently lost in a graph-only match.
    all_text = tuple(sorted(''.join(text.itertext()) for text in root.iter('s')))
    return {'atoms': [item[1] for item in atoms], 'bonds': sorted(bonds), 'text': all_text}


def verify(directory: Path) -> dict:
    before = graph_snapshot(directory / 'before-clean.cdxml')
    after = graph_snapshot(directory / 'ethanol.cdxml')
    reopened = graph_snapshot(directory / 'reopened.cdxml')
    elements = Counter(atom[0] for atom in after['atoms'])
    charge = sum(atom[1] for atom in after['atoms'])
    degree = Counter(index for bond in after['bonds'] for index in bond[:2])
    degree_by_element = sorted((atom[0], degree[i]) for i, atom in enumerate(after['atoms']))
    png = (directory / 'ethanol.png').read_bytes()
    if png[:8] != b'\x89PNG\r\n\x1a\n' or png[12:16] != b'IHDR' or len(png) < 33:
        raise ValueError('Invalid PNG header')
    dimensions = struct.unpack('>II', png[16:24])
    if min(dimensions) <= 0:
        raise ValueError('Empty image dimensions')
    cdx = (directory / 'ethanol.cdx').read_bytes()
    if not cdx.startswith(b'VjCD0100'):
        raise ValueError('Native CDX magic not present')
    checks = {
        'ethanol_elements_and_charge': elements == Counter({6: 2, 8: 1}) and charge == 0,
        'ethanol_connectivity': degree_by_element == [(6, 1), (6, 2), (8, 1)] and all(bond[2:] == ('1', 'Solid') for bond in after['bonds']),
        'reopened_atoms_bonds_text_equal': after == reopened,
        'native_cleanup_changed_coordinates': [atom[4] for atom in before['atoms']] != [atom[4] for atom in after['atoms']],
    }
    return {
        'scope': 'ethanol_only_not_S1_or_full_quality_gate',
        'checks': checks,
        'automated_smoke_pass': all(checks.values()),
        'png_dimensions': dimensions,
        'cdx_sha256': hashlib.sha256(cdx).hexdigest(),
        'license': 'unverified', 'owner_acceptance': 'pending',
        'product_gate': 'blocked',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    result = verify(args.directory)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['automated_smoke_pass'] else 1)
