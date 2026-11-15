# SPDX-License-Identifier: MIT
"""Snapshot the app's original UR2 and exact requirements-pinned urtypes sources.

Run with uv --with the immutable urtypes archive URL below. No protocol algorithms
are substituted. Original notices/licenses and input/output hashes are retained.
"""
import hashlib,importlib.metadata,json,shutil,subprocess
from pathlib import Path
import urtypes
root=Path(__file__).resolve().parents[1];repo=root.parent
source=repo/'dist/firmware/sources/lvgl/application'
lock=json.loads((repo/'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==lock['commit']
url='https://github.com/selfcustody/urtypes/archive/7fb280eab3b3563dfc57d2733b0bf5cbc0a96a6a.zip'
dist=importlib.metadata.distribution('urtypes');direct=json.loads(dist.read_text('direct_url.json'))
assert direct['url']==url,'Use the original app requirements-pinned urtypes archive'
receipt={'application':lock,'urtypesSource':url,'files':{},'changes':[]}
original=source/'src/seedsigner/helpers/ur2';target=root/'app/seedsigner_port/ur2';target.mkdir(exist_ok=True)
for src in sorted(original.glob('*.py')):
    rel=str(src.relative_to(source));raw=src.read_bytes()
    assert raw==subprocess.check_output(['git','show',lock['commit']+':'+rel],cwd=source)
    source_hash=hashlib.sha256(raw).hexdigest()
    if src.name=='fountain_decoder.py':
        # Baremetal time has no wall clock (time.time). The original timing value
        # only feeds a commented-out debug print, so drop it; algorithm unchanged.
        old=b'        start = time.time()\n';assert raw.count(old)==1
        raw=raw.replace(old,b'        # Baremetal: unused debug timing removed; no time.time wall clock.\n')
        receipt['changes'].append({'file':rel,'change':'Remove unused debug time.time() call in process_queue_item; baremetal time module has no wall clock'})
    out=target/src.name;out.write_bytes(raw)
    receipt['files'][str(out.relative_to(root/'app'))]={'source':rel,'sourceSha256':source_hash,'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest()}
shutil.copyfile(original/'LICENSE',root/'app/LICENSE.UR2')
original=Path(urtypes.__file__).parent;target=root/'app/urtypes';target.mkdir(exist_ok=True)
for src in sorted(original.rglob('*.py')):
    rel=src.relative_to(original);raw=src.read_bytes();out=target/rel;out.parent.mkdir(exist_ok=True)
    out.write_bytes(raw)
    receipt['files'][str(out.relative_to(root/'app'))]={'source':'urtypes/'+str(rel),'sourceSha256':hashlib.sha256(raw).hexdigest(),'outputSha256':hashlib.sha256(raw).hexdigest()}
licenses=list(original.parent.glob('urtypes-*.dist-info/licenses/LICENSE.md'));assert len(licenses)==1
shutil.copyfile(licenses[0],root/'app/LICENSE.urtypes')
(root/'app/ur-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Prepared',len(receipt['files']),'original UR source files')
