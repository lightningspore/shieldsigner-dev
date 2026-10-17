"""Deploy an allowlisted immutable release to the existing website VM."""
import json
import os
import subprocess
from pathlib import Path
root = Path(__file__).resolve().parents[1]
release = json.loads((root/'artifacts/release.json').read_text())
host = os.environ['SHIELDSIGNER_DEPLOY_HOST']
identifier = release['release']
# identifier is generated SHA-256 hex, not user-provided shell text.
if len(identifier)!=16 or any(c not in '0123456789abcdef' for c in identifier): raise ValueError('Invalid release hash')
# /tmp is a small tmpfs on the website host; use disk-backed account cache.
upload=f'.cache/shieldsigner-deploy/{identifier}.tar.gz'
subprocess.run(['ssh',host,'mkdir -p .cache/shieldsigner-deploy'],check=True)
subprocess.run(['scp',release['archive'],f'{host}:{upload}'],check=True)
command = f'''sudo -n mkdir -p /opt/shieldsigner/releases/{identifier} &&
sudo -n tar --warning=no-timestamp -xzf {upload} -C /opt/shieldsigner/releases/{identifier} &&
cd /opt/shieldsigner/releases/{identifier} &&
sudo -n env SHIELDSIGNER_RELEASE={identifier} docker compose -f compose.production.yml build web &&
sudo -n env SHIELDSIGNER_RELEASE={identifier} docker compose -f compose.production.yml up -d web shieldsigner-caddy &&
curl --retry 5 --retry-delay 2 --retry-all-errors -fsS -H 'Host: shieldsigner.dev' http://127.0.0.1:8082/healthz &&
sudo -n ln -sfn /opt/shieldsigner/releases/{identifier} /opt/shieldsigner/current &&
cd &&
rm -- {upload}'''
subprocess.run(['ssh',host,command],check=True)
print(f'Origin healthy; current release {identifier}. Tunnel connector is managed separately.')
