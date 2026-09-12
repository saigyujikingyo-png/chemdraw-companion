"""Negative receipt controls using a separately completed native micro-run."""
import argparse,copy,hashlib,json,shutil,sys
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.chemical_ir import validate_request
from runtime.native_provenance import verify_geometry_receipt


def run(request,seed,native,out):
    out.mkdir(parents=True,exist_ok=False);read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));mechanism,style=validate_request(read(request));manifest=read(seed/'geometry-manifest.json')
    positive=verify_geometry_receipt(mechanism,style,manifest,seed,native);records=[]
    cases=['raw_seed','changed_output_bytes','wrong_input_hash','wrong_build_hash','wrong_style','wrong_text_run_with_matching_hash','wrong_state_manifest']
    for case in cases:
        folder=out/case;shutil.copytree(native,folder);test_style=copy.deepcopy(style);test_manifest=copy.deepcopy(manifest);target=folder
        receipt=read(folder/'native-geometry-receipt.json')
        if case=='raw_seed':target=seed
        elif case=='changed_output_bytes':
            path=folder/manifest[0]['file'];path.write_bytes(path.read_bytes()+b'\n')
        elif case=='wrong_input_hash':receipt['artifacts'][0]['input_sha256']='0'*64
        elif case=='wrong_build_hash':receipt['environment']['executable_sha256']='0'*64
        elif case=='wrong_style':test_style['font_pt']+=1
        elif case=='wrong_text_run_with_matching_hash':
            path=folder/manifest[0]['file'];root=ET.parse(path).getroot();run=root.find('.//s')
            if run is None:raise ValueError('Control requires an actual native text run')
            run.set('size',str(style['font_pt']+2));ET.ElementTree(root).write(path,encoding='utf-8')
            next(a for a in receipt['artifacts'] if a['file']==manifest[0]['file'])['output_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        elif case=='wrong_state_manifest':test_manifest[0]['state']='not-the-executed-state'
        (folder/'native-geometry-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
        try:verify_geometry_receipt(mechanism,test_style,test_manifest,seed,target);verdict='false_pass';error=None
        except (ValueError,FileNotFoundError,KeyError) as exc:verdict='rejected';error=str(exc)
        records.append({'case':case,'verdict':verdict,'error':error})
    report={'positive_native_receipt':positive,'controls':records,'scope':'Local receipt trust and hash binding; not adversarial executor attestation.'};(out/'provenance-controls.json').write_text(json.dumps(report,indent=2),encoding='utf-8');return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--seed',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=run(a.request,a.seed,a.native,a.out);print(json.dumps(r));raise SystemExit(0 if all(c['verdict']=='rejected' for c in r['controls']) else 1)
