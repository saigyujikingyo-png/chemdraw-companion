"""Direct developer entry for the generic chemical IR / Composer boundary."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.chemical_ir import validate_request,validate_semantics,canonical_hash
from runtime.adapters.chemdraw_cdxml import seed_documents,read_geometry,materialize

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['seed','compose']);p.add_argument('--request',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--seed',type=Path);p.add_argument('--native',type=Path);p.add_argument('--head-metrics',type=Path);a=p.parse_args()
    payload=json.loads(a.request.read_text(encoding='utf-8'));mechanism,style=validate_request(payload)
    if a.mode=='seed':
        seed_documents(mechanism,style,a.out)
        (a.out/'semantic-receipt.json').write_text(json.dumps({'request_sha256':canonical_hash(payload),'validation':validate_semantics(mechanism),'automatic_anti_selection':'unverified; input supplies complete semantic IR'},indent=2),encoding='utf-8')
    else:
        from runtime.mechanism_composer import compose
        manifest=json.loads((a.seed/'geometry-manifest.json').read_text(encoding='utf-8'));geometry=read_geometry(mechanism,manifest,a.native,input_folder=a.seed,style=style)
        head_metrics=json.loads(a.head_metrics.read_text(encoding='utf-8')) if a.head_metrics else None
        scene=compose(mechanism,style,geometry,head_metrics);materialize(scene,a.out)
        (a.out/'native-geometry.json').write_text(json.dumps(geometry,indent=2),encoding='utf-8')
    print(json.dumps({'mode':a.mode,'output':str(a.out),'semantic_validation':'pass','native_quality':'not_implied'}))
