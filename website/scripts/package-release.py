"""Build an allowlisted, content-addressed release without credentials/private data."""
import hashlib
import json
import tarfile
from pathlib import Path
root = Path(__file__).resolve().parents[1]
paths = []
for name in ['siteconfig', 'knowledge', 'templates', 'static', 'content', 'public']:
    paths += [p for p in (root/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
paths += [root/name for name in ['manage.py', 'version.json', 'pyproject.toml', 'uv.lock', 'Dockerfile', '.dockerignore', 'Caddyfile', 'compose.production.yml']]
digest = hashlib.sha256()
for path in sorted(paths):
    digest.update(str(path.relative_to(root)).encode()+b'\0'+path.read_bytes())
release = digest.hexdigest()[:16]
output = root/'artifacts'; output.mkdir(exist_ok=True)
archive = output/f'shieldsigner-{release}.tar.gz'
with tarfile.open(archive, 'w:gz') as tar:
    for path in sorted(paths): tar.add(path, arcname=str(path.relative_to(root)))
(output/'release.json').write_text(json.dumps({'release': release, 'archive': str(archive), 'files': len(paths)},indent=2)+'\n')
print(release)
