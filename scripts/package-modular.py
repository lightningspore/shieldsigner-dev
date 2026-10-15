#!/usr/bin/env python3
"""Package reviewed modular outputs and pin their public prerelease checksums."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
VARIANT = ROOT / 'variants/lcd-module-2.8'
OUT = ROOT / 'dist/lcd-module-2.8'
board_sha = hashlib.sha256((VARIANT / 'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb').read_bytes()).hexdigest()
readiness = json.loads((VARIANT / 'manufacturing/readiness.json').read_text())
assert readiness['boardSha256'] == board_sha, 'Run variant:lcd:fab first'
allowed = {'.kicad_pcb', '.kicad_sch', '.kicad_pro', '.kicad_mod', '.kicad_sym', '.step', '.svg', '.png', '.json', '.csv', '.md', '.txt'}
with ZipFile(OUT / 'shieldsigner-modular-kicad.zip', 'w', ZIP_DEFLATED) as archive:
    for source in sorted(VARIANT.rglob('*')):
        if source.is_file() and (source.suffix in allowed or source.name in {'fp-lib-table', 'sym-lib-table'}):
            archive.write(source, source.relative_to(ROOT))
    for source in [ROOT / 'LICENSE', ROOT / 'docs/LCD-MODULE-VARIANT.md', ROOT / 'docs/MODULAR-ASSEMBLY.md', *sorted((ROOT / 'reference/pdfs').glob('*.pdf'))]:
        archive.write(source, source.relative_to(ROOT))
tag = 'modular-preview-0.0.3-dev'
names = ['shieldsigner-modular-order.zip', 'shieldsigner-modular-gerbers.zip', 'shieldsigner-modular-kicad.zip', 'shieldsigner-modular-assembly.step', 'shieldsigner-modular-assembly.glb']
manifest = {'release': tag, 'boardSha256': board_sha, 'assets': []}
for name in names:
    source = OUT / name
    manifest['assets'].append({'name': name, 'url': f'https://github.com/lightningspore/shieldsigner-dev/releases/download/{tag}/{name}', 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
(ROOT / 'assets/modular-downloads.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Packaged portable native project and pinned five modular prerelease assets.')
