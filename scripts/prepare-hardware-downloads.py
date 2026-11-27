#!/usr/bin/env python3
"""Pin the matched local PCB review bundle for the website and a new release."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist/lcd-module-2.8'
manifest = json.loads((OUT / 'review-downloads.json').read_text())
board = ROOT / 'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
assert manifest['boardSha256'] == hashlib.sha256(board.read_bytes()).hexdigest(), 'Run hardware:package first'
manifest['release'] = 'pill-assembly-0.0.13-ili9341-r1'
manifest['publicationStatus'] = 'prepared_review_release'
for asset in manifest['assets']:
    assert hashlib.sha256((OUT / asset['name']).read_bytes()).hexdigest() == asset['sha256'], asset['name']
    asset.pop('path', None)
    asset['url'] = ('https://github.com/lightningspore/shieldsigner-dev/releases/download/'
                    + manifest['release'] + '/' + asset['name'])
(ROOT / 'assets/modular-downloads.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Pinned six matched PCB review downloads:', manifest['release'])
