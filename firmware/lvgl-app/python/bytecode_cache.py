"""Prepare source-checked CPython bytecode outside the installed app tree."""
import hashlib,importlib.util,json,marshal,os,py_compile,sys,time,types
from pathlib import Path

def current(cache,source):
    try:
        data=Path(cache).read_bytes()
        return (data[:4]==importlib.util.MAGIC_NUMBER and int.from_bytes(data[4:8],'little')==3 and data[8:16]==importlib.util.source_hash(source) and isinstance(marshal.loads(data[16:]),types.CodeType))
    except (OSError,ValueError,EOFError,TypeError):return False

def prepare(roots):
    if not sys.pycache_prefix:raise ValueError('An isolated pycache_prefix is required')
    prefix=Path(sys.pycache_prefix)
    if prefix.resolve()!=prefix.absolute():raise ValueError('Cache prefix must not traverse symlinks')
    prefix.mkdir(parents=True,exist_ok=True)
    sources=sorted({path for root in roots for path in Path(root).rglob('*.py') if '__pycache__' not in path.parts})
    compiled=0;reused=0;size=0;started=time.monotonic()
    for source in sources:
        cache=Path(importlib.util.cache_from_source(str(source.absolute())))
        if not cache.is_relative_to(prefix):raise ValueError('Cache escaped prefix')
        raw=source.read_bytes()
        if current(cache,raw):reused+=1
        else:
            py_compile.compile(str(source),cfile=str(cache),doraise=True,invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH)
            if not current(cache,raw):raise ValueError('Source changed during compilation')
            compiled+=1
        size+=cache.stat().st_size
    return dict(prepared=True,prefix=str(prefix),checkedHash=True,sources=len(sources),compiled=compiled,reused=reused,bytes=size,seconds=round(time.monotonic()-started,3))

def stage_sources(mapping,output):
    """Compile unchanged source for fixed target paths, never import it."""
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    previous=sys.pycache_prefix;sys.pycache_prefix=str(output);entries=[];filenames=set()
    try:
        for item in mapping:
            source=Path(item['source']);filename=item['filename'];target=Path(filename)
            if not target.is_absolute() or '..' in target.parts or source.is_symlink():raise ValueError('Unsafe source-cache input')
            if filename in filenames:raise ValueError('Duplicate source-cache target')
            filenames.add(filename)
            raw=source.read_bytes();cache=Path(importlib.util.cache_from_source(filename))
            if not cache.is_relative_to(output):raise ValueError('Source cache escaped prefix')
            py_compile.compile(str(source),cfile=str(cache),dfile=filename,doraise=True,invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH)
            data=cache.read_bytes()
            if not current(cache,raw) or marshal.loads(data[16:]).co_filename!=filename:raise ValueError('Invalid staged source cache')
            entries.append(dict(filename=filename,file=str(cache.relative_to(output)),sourceSha256=hashlib.sha256(raw).hexdigest(),checkedSourceHash=data[8:16].hex(),sha256=hashlib.sha256(data).hexdigest()))
    finally:sys.pycache_prefix=previous
    record=dict(schema=1,magic=importlib.util.MAGIC_NUMBER.hex(),cacheTag=sys.implementation.cache_tag,entries=entries)
    (output/'index.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
    return dict(prepared=True,checkedHash=True,files=len(entries))

if __name__=='__main__':
    if sys.argv[1:2]==['--stage-map']:
        result=stage_sources(json.loads(Path(sys.argv[2]).read_text()),Path(sys.argv[3]))
    else:result=prepare(sys.argv[1:])
    print(json.dumps(result),flush=True)

