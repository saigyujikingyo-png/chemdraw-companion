"""Bind local geometry to a completed native executor receipt and exact bytes.

The trusted boundary is the locally executed probe and its journal. This is not
a cryptographic attestation against an attacker who can rewrite that executor.
"""
from pathlib import Path
import hashlib,json,math,re
import xml.etree.ElementTree as ET
from runtime.chemical_ir import canonical_hash
from runtime.adapters.cdxml_atom_identity import verify_atom_readback


def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_style(path,style):
    root=ET.parse(path).getroot()
    for native,key in [('LabelSize','font_pt'),('CaptionSize','font_pt'),('BondLength','bond_length_pt'),('LineWidth','stroke_pt')]:
        value=float(root.get(native,'nan'))
        if not math.isfinite(value) or abs(value-style[key])>1e-4:raise ValueError('Native style mismatch: '+native)
    fonts={f.get('id'):f.get('name') for f in root.findall('fonttable/font')}
    if fonts.get(root.get('LabelFont'))!=style['font_family'] or fonts.get(root.get('CaptionFont'))!=style['font_family']:raise ValueError('Native font mismatch')
    for run in root.iter('s'):
        value=float(run.get('size','nan'))
        if not math.isfinite(value) or abs(value-style['font_pt'])>1e-4 or fonts.get(run.get('font'))!=style['font_family']:raise ValueError('Native text run style mismatch')


def verify_geometry_receipt(mechanism,style,manifest,input_folder,output_folder,*,depiction_plan=None,semantic_qualification=None):
    input_folder=Path(input_folder);output_folder=Path(output_folder)
    receipt_path=output_folder/'native-geometry-receipt.json'
    if not receipt_path.is_file():raise ValueError('Missing completed native geometry execution receipt')
    read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
    receipt=read(receipt_path);seed=read(input_folder/'seed-provenance.json')
    if manifest!=read(input_folder/'geometry-manifest.json'):raise ValueError('Caller manifest differs from executed seed manifest')
    semantic_freeze=None
    if semantic_qualification is not None:
        from runtime.native_source_binding import load_qualification,verify_source_freeze,verify_process_binding,verify_observer_binding
        semantic_freeze=load_qualification(semantic_qualification)
        frozen=verify_source_freeze(semantic_freeze)
        if receipt.get('source_freeze_sha256')!=frozen['sha256'] or receipt.get('source_bytes_rechecked') is not True:raise ValueError('Native semantic execution/source binding mismatch')
    expected_version='native-geometry-receipt/0.2' if semantic_freeze is not None else 'native-geometry-receipt/0.1'
    if receipt.get('version')!=expected_version or receipt.get('status')!='complete' or receipt.get('operation')!='ChemDraw.Objects.Clean(true)':raise ValueError('Uncompleted, unqualified or wrong native operation')
    if receipt.get('seed_provenance_sha256')!=file_hash(input_folder/'seed-provenance.json'):raise ValueError('Seed receipt hash mismatch')
    if seed.get('mechanism_sha256')!=canonical_hash(mechanism) or seed.get('style_sha256')!=canonical_hash(style):raise ValueError('IR/style provenance mismatch')
    if depiction_plan:
        for key in ('ir_sha256','chemical_inventory_sha256','depiction_plan_sha256'):
            if seed.get(key)!=depiction_plan[key]:raise ValueError('Depiction provenance mismatch: '+key)
        if seed.get('lowered_depiction_file_sha256')!=file_hash(input_folder/'lowered-depiction.json') or read(input_folder/'lowered-depiction.json')!=depiction_plan:raise ValueError('Lowered depiction file mismatch')
        expected={s['state_ref']:sorted(a['atom_ref'] for a in s['visible_atoms']) for s in depiction_plan['states']}
        if len(manifest)!=len(expected) or {e['state']:e.get('visible_atom_refs') for e in manifest}!=expected:raise ValueError('Visible occurrence manifest mismatch')
    if receipt.get('manifest_sha256')!=file_hash(input_folder/'geometry-manifest.json'):raise ValueError('Geometry manifest hash mismatch')
    environment=receipt.get('environment',{})
    for key in ('application_build','interop_version','executable_sha256','interop_sha256','executor_sha256','bridge_sha256'):
        if not environment.get(key):raise ValueError('Incomplete native build provenance: '+key)
    if environment.get('application_build')!='26.0.0.6141' or environment.get('interop_version')!='22.0.0.0':raise ValueError('Native build outside the qualified receipt scope')
    for key in ('executable_sha256','interop_sha256','executor_sha256','bridge_sha256'):
        if not re.fullmatch('[a-f0-9]{64}',environment[key]):raise ValueError('Invalid native build hash')
    if environment['executable_sha256']!='f5383228898b6e6be08abded9f6db0909d0841a2f6a5bbef50ba00f44af8a084' or environment['interop_sha256']!='ecaed777a648df79927c79c3d7a33e1a813c6b027c4111396b7139fdda81959a':
        raise ValueError('Native binary hashes outside qualified build')
    if semantic_freeze is None and (environment.get('hwnd_bound_pid')!=environment.get('owned_pid') or not environment.get('owned_pid')):raise ValueError('Native process identity receipt mismatch')
    artifacts={a['file']:a for a in receipt.get('artifacts',[])};seeds={a['file']:a for a in seed['inputs']}
    if len(seeds)!=len(seed['inputs']) or set(seeds)!={x['file'] for x in manifest}:raise ValueError('Seed coverage mismatch')
    if len(artifacts)!=len(receipt.get('artifacts',[])) or set(artifacts)!={x['file'] for x in manifest}:raise ValueError('Native receipt coverage mismatch')
    atom_readbacks={}
    for entry in manifest:
        name=entry['file']
        if Path(name).name!=name or not name.endswith('.cdxml'):raise ValueError('Invalid receipt artifact name')
        native=artifacts[name]
        if semantic_freeze is not None:
            for phase in ('cleanup_process','reopen_process'):verify_process_binding(native[phase],receipt['run_id'])
            if (native.get('different_process_reopen') is not True or native.get('distinct_document_identity') is not True
                    or native['cleanup_process']['pid']==native['reopen_process']['pid'] or native.get('reopen_warnings')!=0
                    or native.get('cleanup_file')!='clean/'+name or native.get('cleanup_sha256')!=file_hash(output_folder/'clean'/name)):
                raise ValueError('Native semantic fresh-process reopen binding mismatch')
            cleanup_sidecar_path=output_folder/'clean'/(Path(name).stem+'.atoms.json')
            if native['cleanup_atom_readback'].get('file')!=cleanup_sidecar_path.name or native['cleanup_atom_readback'].get('sha256')!=file_hash(cleanup_sidecar_path):raise ValueError('Native cleanup sidecar hash mismatch')
            cleanup_value=read(cleanup_sidecar_path)
            verify_observer_binding(cleanup_value,frozen)
            verify_atom_readback(output_folder/'clean'/name,cleanup_value)
            if cleanup_value['environment']!=environment or cleanup_value['process']!=native['cleanup_process'] or cleanup_value['job_id']!=receipt['run_id'] or cleanup_value.get('phase')!='cleanup' or cleanup_value.get('chemical_warnings')!=0:raise ValueError('Native cleanup observation/process mismatch')
        if native.get('cleanup_completed') is not True or native.get('warnings')!=0:raise ValueError('Native cleanup failed or has warnings')
        if native.get('input_sha256')!=file_hash(input_folder/name) or seeds[name]['sha256']!=native['input_sha256']:raise ValueError('Native input hash mismatch')
        if native.get('output_sha256')!=file_hash(output_folder/name):raise ValueError('Native output hash mismatch')
        if native.get('before_sha256')!=file_hash(output_folder/(Path(name).stem+'-before.cdxml')):raise ValueError('Pre-clean native snapshot hash mismatch')
        if depiction_plan and native.get('atom_readback'):
            observation=native['atom_readback'];observation_name=observation.get('file','')
            if Path(observation_name).name!=observation_name or observation_name!=Path(name).stem+'.atoms.json':raise ValueError('Invalid native atom observation filename')
            if observation.get('sha256')!=file_hash(output_folder/observation_name):raise ValueError('Native atom observation hash mismatch')
            value=read(output_folder/observation_name)
            if value.get('source_cdxml_sha256')!=native['output_sha256']:raise ValueError('Native atom observation/source mismatch')
            if semantic_freeze is not None:
                verify_observer_binding(value,frozen)
                if value['environment']!=environment or value['process']!=native['reopen_process'] or value['job_id']!=receipt['run_id'] or value.get('phase')!='fresh_process_reopen' or value.get('chemical_warnings')!=0:
                    raise ValueError('Native semantic observation/process mismatch')
            if value.get('version') in ('native-atom-readback/0.4','native-atom-readback/0.5'):
                verify_atom_readback(output_folder/name,value)
                atom_readbacks[name]=value
        elif semantic_freeze is not None:raise ValueError('New semantic scope requires all atom readbacks')
        check_style(input_folder/name,style);check_style(output_folder/name,style)
    result={'receipt_sha256':file_hash(receipt_path),'source':'ChemDraw native Clean(true), bound to completed local execution receipt','environment':environment}
    if depiction_plan:result['atom_readbacks']=atom_readbacks
    if semantic_freeze is not None:result['semantic_source_freeze']=semantic_freeze
    return result
