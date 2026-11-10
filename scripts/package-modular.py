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
assert readiness['status'] in {'review_required', 'stock_review_required'}
for name, expected in readiness['files'].items():
    source = (OUT if name.endswith('.zip') else VARIANT / 'manufacturing') / name
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected, 'Stale manufacturing output: ' + name
proof = VARIANT / readiness['compatibilityProof']['file']
assert hashlib.sha256(proof.read_bytes()).hexdigest() == readiness['compatibilityProof']['sha256'], 'Stale service layout proof'
assert json.loads(proof.read_text())['boardSha256'] == board_sha
datasheet_manifest = json.loads((ROOT/'datasheets/manifest.json').read_text())
coverage = json.loads((ROOT/'datasheets/bom-coverage.json').read_text())
assert coverage['bomSha256'] == hashlib.sha256((VARIANT/'manufacturing/bom-jlcpcb.csv').read_bytes()).hexdigest(), 'Run datasheets:check for current BOM'
for record in datasheet_manifest['files']:
    assert hashlib.sha256((ROOT/'datasheets'/record['file']).read_bytes()).hexdigest() == record['sha256'], 'Stale/missing datasheet: '+record['file']
def add_datasheets(archive):
    for source in sorted((ROOT/'datasheets').iterdir()):
        if source.is_file() and source.suffix in {'.pdf','.md','.json'}:
            archive.write(source,source.relative_to(ROOT))
def add_electrical_sources(archive):
    for name in ['carrier-runtime-sources.json','gpio-cdev-sources.json','hothmi-init.json','io-config-efdd1cfd.json']:
        source=ROOT/'reference/research/firmware'/name
        archive.write(source,source.relative_to(ROOT))
# Refresh the order bundle from the same checked BOM/CPL/Gerbers plus current notes.
with ZipFile(OUT / 'shieldsigner-modular-order.zip', 'w', ZIP_DEFLATED) as archive:
    add_datasheets(archive)
    add_electrical_sources(archive)
    archive.write(OUT/'shieldsigner-modular-gerbers.zip','shieldsigner-modular-gerbers.zip')
    for source in sorted((VARIANT/'manufacturing').rglob('*')):
        if source.is_file():archive.write(source,source.relative_to(VARIANT/'manufacturing'))
    archive.write(VARIANT/'jlc-placement-corrections.json', 'placement-review/cpl-corrections.json')
    guide = (VARIANT/'manufacturing/placement-review/README.md').read_text()
    archive.writestr('READ-FIRST-PLACEMENT.md', guide.replace('(smartcard-contact-audit.json)', '(placement-review/smartcard-contact-audit.json)'))
    archive.write(VARIANT/'testpoints.json','testpoints.json')
    archive.write(VARIANT/'serviceability-audit.json','serviceability-audit.json')
    archive.write(VARIANT/'silkscreen-label-audit.json','silkscreen-label-audit.json')
    archive.write(VARIANT/'serviceability.json','serviceability.json')
    archive.write(ROOT/'docs/PCB-ORDER-READINESS.md','PCB-ORDER-READINESS.md')
    archive.write(ROOT/'docs/PCB-SOFTWARE-COMPATIBILITY.md','PCB-SOFTWARE-COMPATIBILITY.md')
    archive.write(ROOT/'docs/DISPLAY-BUTTON-REVIEW.md','DISPLAY-BUTTON-REVIEW.md')
    archive.write(ROOT/'docs/MODULE-PINOUT-AUDIT.md','MODULE-PINOUT-AUDIT.md')
    archive.write(VARIANT/'pinout-audit.json','pinout-audit.json')
    archive.write(VARIANT/'carrier-runtime-audit.json','carrier-runtime-audit.json')
    archive.write(VARIANT/'transport-test-receipt.json','transport-test-receipt.json')
    archive.write(VARIANT/'compiled-pinmux-audit.json','compiled-pinmux-audit.json')
    archive.write(VARIANT/'carrier-build-preparation.json','carrier-build-preparation.json')
    archive.write(VARIANT/'carrier-image-verification.json','carrier-image-verification.json')
    archive.write(ROOT/'reverse-engineering/rkaiq/image-sdk-kernel-abi-development-zram-carrier-validation.json','carrier-kernel-validation.json')
    archive.write(ROOT/'docs/BRINGUP.md','BRINGUP.md')
    archive.write(ROOT/'docs/BRINGUP-RESULTS.md','BRINGUP-RESULTS.md')
    archive.write(VARIANT/'assembly-extras.csv','customer-parts.csv')
    archive.write(OUT/'drill-report.txt','drill-report.txt')
allowed = {'.kicad_pcb', '.kicad_sch', '.kicad_pro', '.kicad_mod', '.kicad_sym', '.step', '.svg', '.png', '.json', '.csv', '.md', '.txt'}
with ZipFile(OUT / 'shieldsigner-modular-kicad.zip', 'w', ZIP_DEFLATED) as archive:
    add_datasheets(archive)
    add_electrical_sources(archive)
    archive.writestr('README.txt', 'ShieldSigner eight-pin pill, 0.0.11-dev\nOpen kicad/SeedSigner-Plus-smartcard-pico.kicad_pro in KiCad 10.\nLocal footprints, symbols and STEP models are included.\nRead docs/LCD-MODULE-VARIANT.md and docs/MODULAR-ASSEMBLY.md.\nAutomated mise workflows require a checkout of https://github.com/lightningspore/shieldsigner-dev\nPrototype quotation/review design; physical fit and powered bring-up remain unqualified.\n')
    for source in sorted((ROOT/'kicad').rglob('*')):
        if source.is_file() and (source.suffix in allowed or source.name in {'fp-lib-table','sym-lib-table'}):
            archive.write(source,source.relative_to(ROOT))
    for source in sorted(VARIANT.rglob('*')):
        if source.is_file() and (source.suffix in allowed or source.name in {'fp-lib-table', 'sym-lib-table'}):
            archive.write(source, source.relative_to(ROOT))
    for source in [ROOT / 'LICENSE', ROOT / 'docs/LCD-MODULE-VARIANT.md', ROOT / 'docs/MODULAR-ASSEMBLY.md', ROOT / 'docs/BRINGUP.md', ROOT / 'docs/BRINGUP-RESULTS.md', ROOT / 'docs/PCB-ORDER-READINESS.md', ROOT / 'docs/PCB-SOFTWARE-COMPATIBILITY.md', ROOT / 'docs/DISPLAY-BUTTON-REVIEW.md', ROOT / 'docs/MODULE-PINOUT-AUDIT.md', *sorted((ROOT / 'reference/pdfs').glob('*.pdf'))]:
        archive.write(source, source.relative_to(ROOT))
tag = 'pill-assembly-0.0.11-r1'
names = ['shieldsigner-modular-order.zip', 'shieldsigner-modular-gerbers.zip', 'shieldsigner-modular-kicad.zip', 'shieldsigner-modular-assembly.step', 'shieldsigner-modular-assembly.glb', 'shieldsigner-modular-schematic.pdf']
manifest = {'release': tag, 'boardRevision':'0.0.11-dev', 'status':readiness['status'], 'publicationStatus':'local_review_only_not_published', 'boardSha256': board_sha, 'assets': []}
for name in names:
    source = OUT / name
    manifest['assets'].append({'name': name, 'path': name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
(OUT / 'review-downloads.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Packaged portable native project and six local supplier-review assets.')
