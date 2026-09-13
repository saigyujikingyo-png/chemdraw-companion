"""Raw native quantities, immutable comparison, and exact source bindings.

This module does not infer H, accept an expected IR in an observation function,
or qualify a chemical domain by itself. Interpretation profiles are separate.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import re

SOURCE_CLASSES = {'explicit_native_field', 'native_api_observation', 'qualified_format_decode', 'unknown'}


def quantity(name, value, source_class, *, field, artifact_sha256, native_id,
             atom_map, scope, profile=None, raw=None, present=True, reason=None):
    if source_class not in SOURCE_CLASSES:
        raise ValueError('Invalid native observation source class')
    if source_class == 'unknown' and value is not None:
        raise ValueError('Unknown cannot contain a resolved value')
    return dict(quantity=name, value=deepcopy(value), source_class=source_class,
                source_field=field, artifact_sha256=artifact_sha256,
                native_id=native_id, atom_map=atom_map, scope=scope,
                qualification_profile=profile, raw=deepcopy(raw), present=present, reason=reason)


def observe_serialized_label_h(node, artifact_sha256):
    """Capture NumHydrogens, including missing versus zero, without interpreting omission."""
    raw = node.get('NumHydrogens')
    valid = raw is not None and re.fullmatch(r'[0-9]+', raw) is not None and int(raw) <= 65535
    return quantity('serialized_label_h', int(raw) if valid else None,
                    'explicit_native_field' if valid else 'unknown',
                    field='n@NumHydrogens', artifact_sha256=artifact_sha256,
                    native_id=node.get('id'), atom_map=node.get('AtomNumber'),
                    scope='raw label-H field; not an additional H quantity to add to attached H',
                    raw=raw, present=raw is not None,
                    reason=None if valid else 'missing_field' if raw is None else 'malformed_field')


def element_tree_evidence(element):
    """Include nested labels and significant text; ignore XML formatting whitespace."""
    text = element.text
    tail = element.tail
    return dict(tag=element.tag, attributes=dict(element.attrib),
                text=text if element.tag == 's' or text and text.strip() else None,
                tail=tail if tail and tail.strip() else None,
                children=[element_tree_evidence(child) for child in element])


def observe_atom_label(node, artifact_sha256):
    labels = [element_tree_evidence(label) for label in node.findall('t')]
    return quantity('atom_label', labels if labels else None,
                    'explicit_native_field' if labels else 'unknown', field='n/t subtree',
                    artifact_sha256=artifact_sha256, native_id=node.get('id'),
                    atom_map=node.get('AtomNumber'), scope='nested atom label only; not ordinary page text',
                    raw=labels, present=bool(labels), reason=None if labels else 'missing_label')


def complete_atom_bond_evidence(root):
    result = {}
    for tag in ('n', 'b'):
        entries = list(root.iter(tag))
        by_id = {e.get('id'): element_tree_evidence(e) for e in entries}
        if None in by_id or len(by_id) != len(entries):
            raise ValueError('Missing or duplicate native object identity')
        result[tag] = by_id
    return result


def compare_quantity(observed, expected):
    """Comparison cannot fill, choose or change an observation."""
    value = observed['value']
    status = ('unverified' if observed['source_class'] == 'unknown' or value is None
              else 'match' if value == expected else 'mismatch')
    return dict(status=status, observed=deepcopy(value), expected=deepcopy(expected),
                quantity=observed['quantity'], source_class=observed['source_class'])


def verify_frozen_sources(root, source_rows, *, required_files=()):
    """Compare actual raw files with a supplied trusted freeze, not just SHA syntax.

    The caller supplies the qualified freeze. This does not authenticate a
    manifest against an attacker who can rewrite both code and manifests.
    """
    root = Path(root).resolve()
    verified = {}
    for row in source_rows:
        name = row['file']
        if not isinstance(name, str) or name in verified or Path(name).is_absolute():
            raise ValueError('Invalid or duplicate source path')
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('Source path escapes the frozen tree or is absent')
        expected = row['sha256']
        if not isinstance(expected, str) or re.fullmatch(r'[a-f0-9]{64}', expected) is None:
            raise ValueError('Invalid frozen source hash')
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError('NATIVE_SOURCE_MISMATCH: ' + name)
        verified[name] = actual
    if not set(required_files) <= set(verified):
        raise ValueError('Required qualification source is absent from the freeze')
    return verified
