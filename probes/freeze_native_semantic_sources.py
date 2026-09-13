"""Freeze raw committed source and preregistered inputs before native execution."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runtime.native_source_binding import REQUIRED
from runtime.native_semantics import PROFILE


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--powershell',type=Path,required=True)
    parser.add_argument('--prior-native-attempts',type=int,default=0)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    if args.prior_native_attempts<0:raise ValueError('Prior native attempt count must be nonnegative')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    names=set(REQUIRED)
    names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'runtime').rglob('*.py'))
    names.update('contracts/ir_v02/'+p for p in ('__init__.py','core.py','elements.py','mechanism-ir.schema.json'))
    names.update(('contracts/mechanism-ir.schema.json','contracts/composer-request.schema.json',
                  'requirements-probes-win-py312.lock','probes/run_with_deadline.py',
                  'probes/freeze_native_semantic_sources.py','probes/verify_native_semantic_controls.py',
                  'probes/run_ir_v02_regression.py','probes/make_native_semantic_controls.py',
                  'tests/test_native_observation.py','tests/test_native_semantics.py'))
    base='verification/2026-09-13-p0b-semantic-readback'
    inputs=sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/base/'inputs').iterdir() if p.is_file())
    inputs.append(base+'/preregistration-manifest.json')
    def row(name):
        raw=(ROOT/name).read_bytes()
        committed=subprocess.check_output(['git','show',head+':'+name],cwd=ROOT)
        if raw!=committed:raise ValueError('Raw working file differs from committed blob: '+name)
        return dict(file=name,bytes=len(raw),sha256=sha(raw),matches_git_blob=True)
    sources=[row(n) for n in sorted(names)]
    packages=[]
    for name in ('jsonschema','attrs','jsonschema-specifications','referencing','rpds-py','typing_extensions'):
        distribution=importlib.metadata.distribution(name)
        record=next(p for p in distribution.files if p.name=='RECORD')
        packages.append(dict(name=name,version=distribution.version,installed_record_sha256=sha(distribution.locate_file(record).read_bytes())))
    binaries=[dict(role=role,name=path.name,bytes=path.stat().st_size,sha256=sha(path.read_bytes()))
              for role,path in [('python',Path(sys.executable)),('powershell',args.powershell)]]
    freeze=dict(version='native-semantic-source-freeze/1.0',created_utc=datetime.now(timezone.utc).isoformat(),
        source_commit=head,profile=PROFILE,profile_sha256=next(r['sha256'] for r in sources if r['file']=='runtime/native_semantic_profile.json'),
        sources=sources,inputs=[row(n) for n in inputs],dependencies=dict(new_dependencies=False,python_version=platform.python_version(),
            packages=packages,executor_binaries=binaries,vendor_binaries='exact hashes in the frozen profile; not redistributed'),
        native_worker_attempts_before_freeze=args.prior_native_attempts,qualification='prospective; not native-qualified by source freeze',
        production_source_policy='All runtime Python, required IR implementation/schemas, profile, native worker/common/bridge/observer, entrypoints and exact diagnostic scripts are listed. Test modules are additional source evidence.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes((json.dumps(freeze,indent=2)+'\n').encode())
    print(json.dumps(dict(file=str(args.output),sha256=sha(args.output.read_bytes()),source_commit=head,sources=len(sources),inputs=len(inputs))))


if __name__=='__main__':main()
