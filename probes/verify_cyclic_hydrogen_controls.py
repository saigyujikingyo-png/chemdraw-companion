"""Verify the named synthetic cyclic-H controls against actual native sidecars."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runtime.adapters.cdxml_atom_identity import verify_atom_readback, read_explicit_geometry, qualified_carbon_neighborhood

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=Path,required=True)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists(): parser.error('Output exists; preserve prior evidence.')
    receipt=read(args.native/'native-geometry-receipt.json')
    manifest=read(args.seed/'geometry-manifest.json');expected=read(args.seed/'control-expected.json')
    assert receipt['status']=='complete' and receipt['operation']=='ChemDraw.Objects.Clean(true)'
    assert receipt['manifest_sha256']==sha(args.seed/'geometry-manifest.json')
    assert receipt['seed_provenance_sha256']==sha(args.seed/'seed-provenance.json')
    environment=receipt['environment']
    assert environment['executor_sha256']==sha(ROOT/'probes/native-ir-fragments.ps1')
    assert environment['bridge_sha256']==sha(ROOT/'probes/NativeChemDraw.cs')
    assert environment['owned_pid']==environment['hwnd_bound_pid'] and environment['owned_pid']>0
    assert environment['application_build']=='26.0.0.6141' and environment['interop_version']=='22.0.0.0'
    assert environment['executable_sha256']=='f5383228898b6e6be08abded9f6db0909d0841a2f6a5bbef50ba00f44af8a084'
    assert environment['interop_sha256']=='ecaed777a648df79927c79c3d7a33e1a813c6b027c4111396b7139fdda81959a'
    controls=[]
    for entry in manifest:
        name=entry['file'];meta=expected[name]
        native=next(a for a in receipt['artifacts'] if a['file']==name)
        assert native['warnings']==0 and native['cleanup_completed'] is True
        assert native['input_sha256']==sha(args.seed/name) and native['output_sha256']==sha(args.native/name)
        sidecar_file=args.native/native['atom_readback']['file']
        assert native['atom_readback']['sha256']==sha(sidecar_file)
        sidecar=read(sidecar_file);observations=verify_atom_readback(args.native/name,sidecar)
        root=ET.parse(args.native/name).getroot()
        nodes={int(n.get('AtomNumber')):n for n in root.iter('n')}
        ids={n.get('id'):m for m,n in nodes.items()}
        adjacency={m:{} for m in nodes}
        for b in root.iter('b'):
            a,c=ids[b.get('B')],ids[b.get('E')]
            adjacency[a][c]=adjacency[c][a]=float(b.get('Order','1'))
        eligible={m:qualified_carbon_neighborhood(m,nodes,adjacency,observations) for m in meta['ring_atom_maps']}
        assert all(v is meta['cyclic_profile_expected'] for v in eligible.values()),meta['control']
        values=[]
        if meta['cyclic_profile_expected']:
            source=ET.parse(args.seed/name).getroot()
            source_ids={n.get('id'):int(n.get('AtomNumber')) for n in source.iter('n')}
            expected_atoms={int(n.get('AtomNumber')):dict(element='C',atomic_number=6,implicit_h=int(n.get('NumHydrogens'))) for n in source.iter('n')}
            expected_bonds=[dict(atoms=[source_ids[b.get('B')],source_ids[b.get('E')]],order=float(b.get('Order','1'))) for b in source.iter('b')]
            result=read_explicit_geometry(args.native/name,expected_atoms,expected_bonds,atom_readback=sidecar)
            for m in meta['ring_atom_maps']:
                atom=result['atoms'][m]
                assert 'FormulaHTML' in atom['implicit_h_source']
                values.append(dict(atom_map=m,observed_h=atom['implicit_h'],source=atom['implicit_h_source']))
        selections=[]
        for m in meta['ring_atom_maps']:
            row=observations[int(nodes[m].get('id'))]
            selections.append({k:row[k] for k in ('native_id','atom_map','atomic_number','formal_charge','isotope','radical_native_value',
                                                'selected_count','selected_atom_count','selected_bond_count','selected_formula_html') if k in row})
        controls.append(dict(control=meta['control'],file=name,ring_size=meta['ring_size'],
                             expected_cyclic_profile=meta['cyclic_profile_expected'],ring_atoms=len(eligible),
                             profile_decision='qualified' if meta['cyclic_profile_expected'] else 'refused',
                             warnings=0,native_input_sha256=native['input_sha256'],native_cdxml_sha256=native['output_sha256'],
                             sidecar_sha256=sha(sidecar_file),after_selection_sha256=sidecar['selection_after_cdxml']['sha256'],
                             exact_graph_and_identity_verified=True,unchanged_native_smiles=True,
                             ring_selections=selections,hydrogen_observations=values))
    record=dict(version='cyclic-hydrogen-native-controls/0.1',status='pass',
                producer_receipt_sha256=sha(args.native/'native-geometry-receipt.json'),
                native_build=environment['application_build'],interop_version=environment['interop_version'],
                controls=controls,positive_controls=sum(c['expected_cyclic_profile'] for c in controls),
                negative_controls=sum(not c['expected_cyclic_profile'] for c in controls),
                qualified_ring_atom_observations=sum(len(c['hydrogen_observations']) for c in controls),
                refused_ring_atom_profiles=sum(c['ring_atoms'] for c in controls if not c['expected_cyclic_profile']),
                independent_disk_reopen=False,quality_acceptance='not_implied',gold=0)
    args.out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:record[k] for k in ('status','positive_controls','negative_controls','qualified_ring_atom_observations','refused_ring_atom_profiles')}))


if __name__=='__main__':main()
