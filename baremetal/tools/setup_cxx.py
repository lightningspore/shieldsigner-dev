# SPDX-License-Identifier: MIT
"""Prepare a pinned complete C++/newlib toolchain in ignored local tools."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request
root=Path(__file__).resolve().parents[1]
cfg=json.loads((root/'cxx-toolchain.json').read_text())
cache=root/'.tools';archive=cache/cfg['archive'];prefix=cache/cfg['directory']
cache.mkdir(exist_ok=True)
if not archive.exists():
    part=archive.with_suffix(archive.suffix+'.part')
    with urllib.request.urlopen(cfg['url'],timeout=30) as response,part.open('wb') as out:
        shutil.copyfileobj(response,out)
    if hashlib.file_digest(part.open('rb'),'sha256').hexdigest()!=cfg['sha256']:
        raise SystemExit('Official C++ archive checksum mismatch; not extracted')
    part.rename(archive)
if hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()!=cfg['sha256']:
    raise SystemExit('Cached C++ archive changed; not extracted')
if not (prefix/'bin/arm-none-eabi-g++').exists():
    with tarfile.open(archive) as source:
        source.extractall(cache,filter='data')
compiler=prefix/'bin/arm-none-eabi-g++'
version=subprocess.check_output([str(compiler),'--version'],text=True).splitlines()[0]
standard=Path(subprocess.check_output([str(compiler),'-print-file-name=libstdc++.a'],text=True).strip())
assert standard.is_file(),'C++ runtime missing from complete toolchain'
print(json.dumps({'compiler':str(compiler),'version':version,'runtime':str(standard),'sha256':cfg['sha256']},indent=2))
