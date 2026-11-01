"""Precompile guarded import edits outside the wallet process; no logic rewrite."""
import hashlib,importlib.util,json,marshal,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(data):return hashlib.sha256(data).hexdigest()
def policy_sha(root=None):
    root=Path(root or HERE);data=(root/'dependency_policy.py').read_bytes()
    stream=root/'stream_imports.py'
    if stream.is_file():data+=stream.read_bytes()
    return sha(data)
def load(name,source,filename=None):
    candidates=[HERE/'import-cache']
    if sys.pycache_prefix:candidates.insert(0,Path(sys.pycache_prefix)/'lvgl-imports')
    for root in candidates:
        index=root/'index.json'
        if not index.is_file():continue
        record=json.loads(index.read_text())
        if record['magic']!=importlib.util.MAGIC_NUMBER.hex() or record['policySha256']!=policy_sha():continue
        entry=record['modules'].get(name)
        if entry is None or entry['sourceSha256']!=sha(source):continue
        if Path(entry['file']).name!=entry['file']:raise ValueError('Unsafe import-cache path')
        data=(root/entry['file']).read_bytes()
        if sha(data)!=entry['codeSha256']:raise ValueError('Import-cache artifact changed')
        code=marshal.loads(data)
        if filename is not None and code.co_filename!=filename:continue
        return code
    return None

def prepare(app_root,guards_path,output,filename_root=None,stream_source=None):
    from dependency_policy import specifications,transform
    app_root=Path(app_root).resolve();output=Path(output);output.mkdir(parents=True,exist_ok=True)
    guards=json.loads(Path(guards_path).read_text());modules={}
    for name,(relative,kind) in specifications().items():
        source=(app_root/'seedsigner'/relative).read_bytes()
        if sha(source)!=guards[relative]:raise ValueError('Unreviewed import-cache source: '+relative)
        filename=str(Path(filename_root or app_root)/'seedsigner'/relative)
        if kind not in ('seed_views','pil','controller','screen','settings','storage','tools'):filename+=' [LVGL dependency policy]'
        data=marshal.dumps(compile(transform(source,kind),filename,'exec'))
        file=name+'.marshal';(output/file).write_bytes(data)
        modules[name]=dict(file=file,sourceSha256=sha(source),codeSha256=sha(data))
    from stream_imports import deferred,NAME
    stream=Path(stream_source or '/usr/lib/shieldsigner-camera/python/shieldsigner_video_stream.py')
    source=stream.read_bytes();filename='/usr/lib/shieldsigner-camera/python/shieldsigner_video_stream.py'
    data=marshal.dumps(compile(deferred(source),filename,'exec'));file=NAME+'.marshal'
    (output/file).write_bytes(data)
    modules[NAME]=dict(file=file,sourceSha256=sha(source),codeSha256=sha(data))
    record=dict(magic=importlib.util.MAGIC_NUMBER.hex(),policySha256=policy_sha(),modules=modules)
    (output/'index.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    return dict(prepared=True,modules=len(modules),bytes=sum(p.stat().st_size for p in output.iterdir() if p.is_file()))
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('app_root');parser.add_argument('guards');parser.add_argument('output');parser.add_argument('--filename-root');parser.add_argument('--stream-source');args=parser.parse_args()
    print(json.dumps(prepare(args.app_root,args.guards,args.output,args.filename_root,args.stream_source)))
