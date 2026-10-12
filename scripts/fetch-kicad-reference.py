#!/usr/bin/env python3
"""Fetch a complete native KiCad working copy at the pinned upstream revision."""
import hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
COMMIT='efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f'
PREFIX='electronics/SeedSigner-Plus-smartcard-luckfoxpicozero/'
request=urllib.request.Request(f'https://api.github.com/repos/3rdIteration/seedsigner/git/trees/{COMMIT}?recursive=1',headers={'User-Agent':'ShieldSigner-local-build'})
with urllib.request.urlopen(request) as response: tree=json.load(response)
if tree.get('truncated'): raise RuntimeError('Incomplete upstream tree')
manifest=[]
for entry in tree['tree']:
 path=entry['path']
 if entry['type']!='blob' or not path.startswith(PREFIX):continue
 relative=path[len(PREFIX):]
 if relative.startswith('jlcpcb/') or relative=='example-phohotos.jpg':continue
 target=ROOT/'kicad'/relative
 if target.exists():raise RuntimeError(f'Refusing to overwrite existing working file: {target}')
 target.parent.mkdir(parents=True,exist_ok=True)
 with urllib.request.urlopen(f'https://raw.githubusercontent.com/3rdIteration/seedsigner/{COMMIT}/{path}') as response:data=response.read()
 target.write_bytes(data)
 manifest.append({'path':relative,'upstreamGitBlob':entry['sha'],'sha256':hashlib.sha256(data).hexdigest()})
(ROOT/'kicad/provenance.json').write_text(json.dumps({'repository':'https://github.com/3rdIteration/seedsigner','commit':COMMIT,'files':manifest},indent=2)+'\n')
print(f'Fetched {len(manifest)} native project/library files.')
