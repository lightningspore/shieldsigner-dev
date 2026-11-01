"""Native build-input snapshot shared by build and temporary hardware runner."""
import hashlib
from pathlib import Path

def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(65536),b''):digest.update(chunk)
    return digest.hexdigest()

def inputs(root):
    root=Path(root)
    files=[root/name for name in ('build.py','assets.py','build_manifest.py','sources.py','sources.lock.json','artifact_paths.py')]
    files+=sorted((root/'native').glob('*'))+sorted((root/'patches').glob('*.patch'))
    result={str(path.relative_to(root)):sha256(path) for path in files if path.is_file()}
    shared=root.parents[1]/'scripts/firmware_paths.py'
    result['repo:scripts/firmware_paths.py']=sha256(shared)
    return result
