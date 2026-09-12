"""Bind local geometry to a completed native executor receipt and exact bytes.

The trusted boundary is the locally executed probe and its journal. This is not
a cryptographic attestation against an attacker who can rewrite that executor.
"""
from pathlib import Path
import hashlib,json,math,re
import xml.etree.ElementTree as ET
from runtime.chemical_ir import canonical_hash


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


def verify_geometry_receipt(mechanism,style,manifest,input_folder,output_folder):
    input_folder=Path(input_folder);output_folder=Path(output_folder)
    receipt_path=output_folder/'native-geometry-receipt.json'
    if not receipt_path.is_file():raise ValueError('Missing completed native geometry execution receipt')
    read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
    receipt=read(receipt_path);seed=read(input_folder/'seed-provenance.json')
    if manifest!=read(input_folder/'geometry-manifest.json'):raise ValueError('Caller manifest differs from executed seed manifest')
    if receipt.get('version')!='native-geometry-receipt/0.1' or receipt.get('status')!='complete' or receipt.get('operation')!='ChemDraw.Objects.Clean(true)':raise ValueError('Uncompleted or wrong native operation')
    if receipt.get('seed_provenance_sha256')!=file_hash(input_folder/'seed-provenance.json'):raise ValueError('Seed receipt hash mismatch')
    if seed.get('mechanism_sha256')!=canonical_hash(mechanism) or seed.get('style_sha256')!=canonical_hash(style):raise ValueError('IR/style provenance mismatch')
    if receipt.get('manifest_sha256')!=file_hash(input_folder/'geometry-manifest.json'):raise ValueError('Geometry manifest hash mismatch')
    environment=receipt.get('environment',{})
    for key in ('application_build','interop_version','executable_sha256','interop_sha256','executor_sha256','bridge_sha256'):
        if not environment.get(key):raise ValueError('Incomplete native build provenance: '+key)
    if environment.get('application_build')!='26.0.0.6141' or environment.get('interop_version')!='22.0.0.0':raise ValueError('Native build outside the qualified receipt scope')
    for key in ('executable_sha256','interop_sha256','executor_sha256','bridge_sha256'):
        if not re.fullmatch('[a-f0-9]{64}',environment[key]):raise ValueError('Invalid native build hash')
    if environment['executable_sha256']!='f5383228898b6e6be08abded9f6db0909d0841a2f6a5bbef50ba00f44af8a084' or environment['interop_sha256']!='ecaed777a648df79927c79c3d7a33e1a813c6b027c4111396b7139fdda81959a':
        raise ValueError('Native binary hashes outside qualified build')
    if environment.get('hwnd_bound_pid')!=environment.get('owned_pid') or not environment.get('owned_pid'):raise ValueError('Native process identity receipt mismatch')
    artifacts={a['file']:a for a in receipt.get('artifacts',[])};seeds={a['file']:a for a in seed['inputs']}
    if len(seeds)!=len(seed['inputs']) or set(seeds)!={x['file'] for x in manifest}:raise ValueError('Seed coverage mismatch')
    if len(artifacts)!=len(receipt.get('artifacts',[])) or set(artifacts)!={x['file'] for x in manifest}:raise ValueError('Native receipt coverage mismatch')
    for entry in manifest:
        name=entry['file']
        if Path(name).name!=name or not name.endswith('.cdxml'):raise ValueError('Invalid receipt artifact name')
        native=artifacts[name]
        if native.get('cleanup_completed') is not True or native.get('warnings')!=0:raise ValueError('Native cleanup failed or has warnings')
        if native.get('input_sha256')!=file_hash(input_folder/name) or seeds[name]['sha256']!=native['input_sha256']:raise ValueError('Native input hash mismatch')
        if native.get('output_sha256')!=file_hash(output_folder/name):raise ValueError('Native output hash mismatch')
        if native.get('before_sha256')!=file_hash(output_folder/(Path(name).stem+'-before.cdxml')):raise ValueError('Pre-clean native snapshot hash mismatch')
        check_style(input_folder/name,style);check_style(output_folder/name,style)
    return {'receipt_sha256':file_hash(receipt_path),'source':'ChemDraw native Clean(true), bound to completed local execution receipt','environment':environment}
