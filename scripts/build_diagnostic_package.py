"""Build an allowlisted diagnostic artifact from an exact clean source commit."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
RUNTIME_URL='https://www.python.org/ftp/python/3.13.15/python-3.13.15-embed-amd64.zip'
RUNTIME_SHA='d1f04d990aee1253d8569e8e5104e30fa9f5fa830899f14843448872d936a2cf'
PLUGIN='chemdraw-companion'
FILES=['.codex-plugin/plugin.json','.mcp.json','server.py','companion_status.py','package_integrity.py',
       'install.py','Install.cmd','connect_codex.py','Connect Codex.cmd','README.md']
EXTRA={'LICENSE':'LICENSE','THIRD_PARTY_NOTICES.md':'THIRD_PARTY_NOTICES.md',
       'LIFECYCLE_RECORD.md':'LIFECYCLE_RECORD.md',
       'contracts/output/diagnostic-status.schema.json':'schemas/diagnostic-status.schema.json',
       'contracts/output/diagnostic-jsonrpc-error.schema.json':'schemas/diagnostic-jsonrpc-error.schema.json'}


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(root,path,data):
    target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)


def json_bytes(value):
    return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()


def build(runtime_zip,output):
    sys.dont_write_bytecode=True
    if git('status','--porcelain','--untracked-files=all').strip():
        raise ValueError('Build requires an exact clean source commit; commit the reviewed allowlisted files first')
    commit=git('rev-parse','HEAD').decode().strip()
    if not re.fullmatch('[a-f0-9]{40}',commit):raise ValueError('Invalid source revision')
    runtime_data=runtime_zip.read_bytes()
    if sha(runtime_data)!=RUNTIME_SHA:raise ValueError('Official runtime SHA-256 mismatch')
    if output.exists():raise ValueError('Use a new output directory; existing artifacts are preserved')
    package=output/PLUGIN;package.mkdir(parents=True)
    sources=[]
    for source,destination in [(f'packaging/{PLUGIN}/{name}',name) for name in FILES]+list(EXTRA.items()):
        data=git('show',f'{commit}:{source}')
        put(package,destination,data)
        sources.append({'path':source,'package_path':destination,'bytes':len(data),'sha256':sha(data)})
    plugin=json.loads((package/'.codex-plugin/plugin.json').read_text())
    version=plugin['version']
    with zipfile.ZipFile(runtime_zip) as archive:
        names=set()
        for item in archive.infolist():
            part=PurePosixPath(item.filename)
            if (part.is_absolute() or '..' in part.parts or '\\' in item.filename or item.filename in names
                    or ((item.external_attr>>16)&0o170000)==0o120000):
                raise ValueError('Unsafe or duplicate upstream runtime member')
            names.add(item.filename)
            if not item.is_dir():put(package,'runtime/'+item.filename,archive.read(item))
    if not (package/'runtime/LICENSE.txt').is_file():raise ValueError('Upstream runtime licence missing')
    info={'product':PLUGIN,'version':version,'source_commit':commit,'build_kind':'diagnostic-preview',
          'native_execution_enabled':False,'source_files':sources,
          'runtime':{'name':'CPython','version':'3.13.15','platform':'windows-x64','url':RUNTIME_URL,'archive_sha256':RUNTIME_SHA}}
    put(package,'build-info.json',json_bytes(info))
    rows=[]
    for path in sorted(package.rglob('*')):
        if path.is_file():
            data=path.read_bytes();rows.append({'path':path.relative_to(package).as_posix(),'bytes':len(data),'sha256':sha(data)})
    manifest={'manifest_version':'chemdraw-package/0.1','product':PLUGIN,'version':version,'source_commit':commit,'files':rows}
    put(package,'package-manifest.json',json_bytes(manifest))
    spec=importlib.util.spec_from_file_location('package_integrity',package/'package_integrity.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    verification=module.verify_package(package)
    if not verification['ok']:raise ValueError('Built package verification failed: '+repr(verification))
    artifact=output/f'{PLUGIN}-{version}-windows-x64.zip'
    with zipfile.ZipFile(artifact,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in sorted(package.rglob('*')):
            if path.is_file():
                item=zipfile.ZipInfo(PLUGIN+'/'+path.relative_to(package).as_posix(),(2026,9,19,0,0,0))
                item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16
                archive.writestr(item,path.read_bytes())
    result={'source_commit':commit,'version':version,'package_files':len(rows),
            'artifact':str(artifact),'bytes':artifact.stat().st_size,'sha256':sha(artifact.read_bytes()),
            'manifest_sha256':sha((package/'package-manifest.json').read_bytes()),'runtime_archive_sha256':RUNTIME_SHA}
    put(output,'build-receipt.json',json_bytes(result))
    put(output,'SHA256SUMS.txt',(result['sha256']+'  '+artifact.name+'\n').encode())
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-zip',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(build(args.runtime_zip.resolve(),args.output.resolve()),indent=2))
