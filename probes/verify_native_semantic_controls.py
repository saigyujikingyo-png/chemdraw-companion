"""Compare real scoped native observations to the independent frozen chemistry.

Only the reviewed synthetic control directory is accepted. This program does
not read a private candidate and never changes or reruns a native document.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from contracts.ir_v02 import ATOMIC_NUMBERS
from runtime.native_observation import verify_frozen_sources
from runtime.native_semantics import observe_document,compare_document,PROFILE
from runtime.native_source_binding import verify_source_freeze,verify_process_binding,read_json,digest
from runtime.adapters.cdxml_atom_identity import read_explicit_geometry


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--source-freeze',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():raise FileExistsError(args.out)
    inputs=ROOT/'verification/2026-09-13-p0b-semantic-readback/inputs'
    frozen=verify_source_freeze(args.source_freeze)
    verify_frozen_sources(ROOT,read_json(args.source_freeze)['inputs'])
    matrix=read_json(inputs/'control-matrix.json')
    receipt=read_json(args.native/'native-geometry-receipt.json')
    if (receipt.get('version')!='native-geometry-receipt/0.2' or receipt.get('status')!='complete'
            or receipt.get('source_freeze_sha256')!=frozen['sha256'] or receipt.get('source_bytes_rechecked') is not True
            or receipt.get('manifest_sha256')!=digest(inputs/'geometry-manifest.json')
            or receipt.get('seed_provenance_sha256')!=digest(inputs/'seed-provenance.json')):
        raise ValueError('Native execution receipt is incomplete or not bound to this freeze')
    by_file={a['file']:a for a in receipt['artifacts']}
    if len(by_file)!=len(receipt['artifacts']) or set(by_file)!={c['file'] for c in matrix['controls']}:
        raise ValueError('Native control coverage differs from the frozen matrix')
    args.out.mkdir(parents=True,exist_ok=False)
    all_records=[];counts=Counter();branch_counts=Counter();processes=set();qualified=True
    for control in matrix['controls']:
        name=control['file'];artifact=by_file[name]
        for phase in ('cleanup_process','reopen_process'):
            verify_process_binding(artifact[phase],receipt['run_id'])
            processes.add((artifact[phase]['pid'],artifact[phase]['os_start_utc']))
        if (artifact['cleanup_process']['pid']==artifact['reopen_process']['pid']
                or artifact.get('different_process_reopen') is not True or artifact.get('distinct_document_identity') is not True
                or artifact['input_sha256']!=control['seed_sha256'] or digest(inputs/name)!=control['seed_sha256']
                or artifact['before_sha256']!=digest(args.native/(Path(name).stem+'-before.cdxml'))
                or artifact['output_sha256']!=digest(args.native/name)
                or artifact.get('cleanup_file')!='clean/'+name or artifact['cleanup_sha256']!=digest(args.native/'clean'/name)):
            raise ValueError('Native input, artifact or distinct-process binding failed: '+name)
        expected={a['atom_map']:{**deepcopy(a),'atomic_number':ATOMIC_NUMBERS[a['element']],
                  'implicit_h':a['non_node_attached_h'],
                  'explicit_h_neighbor_nodes':[dict(atom_map=n['atom_map'],isotope=n['isotope'],order=n['bond_order'])
                                               for n in a['explicit_h_neighbor_nodes']]} for a in control['expected_atoms']}
        phases={}
        for phase,folder,sidecar_field,binding_field in [('cleanup',args.native/'clean','cleanup_atom_readback','cleanup_process'),
                         ('reopen',args.native,'atom_readback','reopen_process')]:
            path=folder/name;sidecar_path=path.with_suffix('.atoms.json')
            if (artifact[sidecar_field]['file']!=sidecar_path.name or artifact[sidecar_field]['sha256']!=digest(sidecar_path)):
                raise ValueError('Native sidecar hash mismatch')
            sidecar=read_json(sidecar_path)
            if sidecar['process']!=artifact[binding_field] or sidecar['environment']!=receipt['environment'] or sidecar['job_id']!=receipt['run_id']:
                raise ValueError('Native sidecar process/build mismatch')
            if sidecar.get('phase')!=('cleanup' if phase=='cleanup' else 'fresh_process_reopen') or sidecar['chemical_warnings']!=artifact['warnings' if phase=='cleanup' else 'reopen_warnings']:
                raise ValueError('Native sidecar phase/warning mismatch')
            observed=observe_document(path,sidecar,source_freeze=args.source_freeze)
            comparison=compare_document(observed,expected,control['expected_bonds'])
            adapter={}
            try:
                measured=read_explicit_geometry(path,expected,control['expected_bonds'],atom_readback=sidecar,semantic_source_freeze=args.source_freeze)
                adapter=dict(status='match',atom_count=len(measured['atoms']),bond_count=len(measured['bonds']))
            except ValueError as exc:
                adapter=dict(status='refused',diagnostic=exc.as_dict() if hasattr(exc,'as_dict') else dict(message=str(exc)))
            mutation_check=True
            for m in observed['atoms']:
                before=deepcopy(observed);changed=deepcopy(expected)
                value=expected[m].get('implicit_h')
                changed[m]['non_node_attached_h']=99 if value is None else value+1
                compare_document(observed,changed,control['expected_bonds'])
                mutation_check &= before==observed
            for atom in observed['atoms'].values():
                h=atom['non_node_attached_h'];field=atom['serialized_label_h']
                branch_counts[(phase,'present' if field['present'] else 'missing',h['source_class'],h['source_field'],h['scope'],h['value'],h['reason'])]+=1
            phases[phase]=dict(observations=observed,comparison=comparison,production_adapter=adapter,
                expected_mutation_preserves_observations=mutation_check,warnings=sidecar['chemical_warnings'])
        # Native IDs may differ; compare identity and quantities by stable chemical map.
        def semantic_signature(value):
            return {m:dict(identity={k:v['value'] for k,v in a['identity'].items()},h=a['non_node_attached_h']['value'],
                explicit_h=[{k:v for k,v in x.items() if k!='native_id'} for x in a['explicit_h_neighbor_nodes']['value']])
                    for m,a in value['observations']['atoms'].items()}
        consistent=semantic_signature(phases['cleanup'])==semantic_signature(phases['reopen'])
        positive=control['purpose']=='qualification_candidate' or control['control'] in ('ammonium','chloride')
        if positive:
            passed=all(p['comparison']['status']=='match' and p['production_adapter']['status']=='match' and p['warnings']==0 and p['expected_mutation_preserves_observations'] for p in phases.values()) and consistent
            result='qualification_match' if passed else 'qualification_not_established'
            qualified &= passed
        elif control['purpose']=='unsupported_negative':
            passed=all(p['comparison']['status']=='unverified' and p['production_adapter']['status']=='refused' and
                       all(a['non_node_attached_h']['value'] is None for a in p['observations']['atoms'].values()) for p in phases.values())
            result='expected_scope_refusal' if passed else 'unexpected_negative_outcome';qualified &= passed
        else:
            # Conflict normalization and methane observations can never become positives.
            result='diagnostic_observation_only'
        counts[result]+=1
        record=dict(control=control['control'],file=name,purpose=control['purpose'],result=result,
            exact_preregistration_sha256=control['seed_sha256'],source_conflict=control['source_conflict'],
            cross_process_semantic_consistency=consistent,independent_expected_source='preregistered literal chemistry',
            native_consistency_is_independent_chemical_truth=False,phases=phases)
        all_records.append(record)
        (args.out/(Path(name).stem+'.semantic.json')).write_bytes((json.dumps(record,indent=2)+'\n').encode())
    if len(processes)!=2*len(all_records):
        raise ValueError('Every native phase must have its own fresh process identity')
    branches=[dict(phase=k[0],serialized_h_presence=k[1],resolved_source_class=k[2],resolved_source_field=k[3],scope=k[4],h=k[5],reason=k[6],atoms=v)
              for k,v in branch_counts.items()]
    report=dict(version='native-semantic-control-receipt/1.0',profile=PROFILE,source_freeze_sha256=frozen['sha256'],
        native_receipt_sha256=digest(args.native/'native-geometry-receipt.json'),matrix_sha256=digest(inputs/'control-matrix.json'),
        control_count=len(all_records),atom_count=sum(len(c['expected_atoms']) for c in matrix['controls']),
        distinct_native_process_count=len(processes),counts=dict(counts),branches=branches,
        controls=[{k:v for k,v in c.items() if k!='phases'} for c in all_records],
        qualification_status='qualified_declared_scope' if qualified else 'partial_not_qualified',
        all_expected_mutations_preserved_observations=all(p['expected_mutation_preserves_observations'] for c in all_records for p in c['phases'].values()),
        source_bytes_rechecked=bool(verify_source_freeze(args.source_freeze)),
        limitations=['All seeds explicitly contained NumHydrogens; branch coverage is measured only after native cleanup/reopen.',
          'Conflict input and methane remain diagnostic-only regardless of native normalization.',
          'Cyclopentanone is a new qualification of exposed chemistry, not retroactive acceptance of an old negative.',
          'Query, abnormal, cyclic-unsaturation and multiple-cycle guard fixtures are unit controls, not additional native executions.',
          'No private candidate, visual acceptance, chemical-mechanism approval or Gold promotion.'])
    (args.out/'control-receipt.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:report[k] for k in ('qualification_status','control_count','atom_count','distinct_native_process_count','counts')}))


if __name__=='__main__':main()
