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
# Refresh the order bundle from the same checked BOM/CPL/Gerbers plus current notes.
with ZipFile(OUT / 'shieldsigner-modular-order.zip', 'w', ZIP_DEFLATED) as archive:
    archive.write(OUT/'shieldsigner-modular-gerbers.zip','shieldsigner-modular-gerbers.zip')
    for source in sorted((VARIANT/'manufacturing').rglob('*')):
        if source.is_file():archive.write(source,source.relative_to(VARIANT/'manufacturing'))
    archive.write(VARIANT/'jlc-placement-corrections.json', 'placement-review/cpl-corrections.json')
    guide = (VARIANT/'manufacturing/placement-review/README.md').read_text()
    archive.writestr('READ-FIRST-PLACEMENT.md', guide.replace('(smartcard-contact-audit.json)', '(placement-review/smartcard-contact-audit.json)'))
    archive.write(VARIANT/'testpoints.json','testpoints.json')
    archive.write(ROOT/'docs/BRINGUP.md','BRINGUP.md')
    archive.write(VARIANT/'assembly-extras.csv','customer-parts.csv')
    archive.write(OUT/'drill-report.txt','drill-report.txt')
allowed = {'.kicad_pcb', '.kicad_sch', '.kicad_pro', '.kicad_mod', '.kicad_sym', '.step', '.svg', '.png', '.json', '.csv', '.md', '.txt'}
with ZipFile(OUT / 'shieldsigner-modular-kicad.zip', 'w', ZIP_DEFLATED) as archive:
    archive.writestr('README.txt', 'ShieldSigner eight-pin pill, 0.0.7-dev\nOpen variants/lcd-module-2.8/kicad/SeedSigner-Plus-smartcard-pico.kicad_pro in KiCad 10.\nLocal footprints, symbols and STEP models are included.\nRead docs/LCD-MODULE-VARIANT.md and docs/MODULAR-ASSEMBLY.md.\nAutomated mise workflows require a checkout of https://github.com/lightningspore/shieldsigner-dev\nPrototype quotation/review design; physical fit and powered bring-up remain unqualified.\n')
    for source in sorted(VARIANT.rglob('*')):
        if source.is_file() and (source.suffix in allowed or source.name in {'fp-lib-table', 'sym-lib-table'}):
            archive.write(source, source.relative_to(ROOT))
    for source in [ROOT / 'LICENSE', ROOT / 'docs/LCD-MODULE-VARIANT.md', ROOT / 'docs/MODULAR-ASSEMBLY.md', ROOT / 'docs/BRINGUP.md', *sorted((ROOT / 'reference/pdfs').glob('*.pdf'))]:
        archive.write(source, source.relative_to(ROOT))
tag = 'pill-assembly-0.0.7-r2'
names = ['shieldsigner-modular-order.zip', 'shieldsigner-modular-gerbers.zip', 'shieldsigner-modular-kicad.zip', 'shieldsigner-modular-assembly.step', 'shieldsigner-modular-assembly.glb', 'shieldsigner-modular-schematic.pdf']
manifest = {'release': tag, 'boardSha256': board_sha, 'assets': []}
for name in names:
    source = OUT / name
    manifest['assets'].append({'name': name, 'url': f'https://github.com/lightningspore/shieldsigner-dev/releases/download/{tag}/{name}', 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
(ROOT / 'assets/modular-downloads.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Packaged portable native project and pinned six modular prerelease assets.')
