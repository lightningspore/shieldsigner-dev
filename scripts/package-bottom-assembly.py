#!/usr/bin/env python3
"""Derive a matched bottom-only quotation kit without changing the native board."""
import csv
import hashlib
import json
import runpy
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'variants/lcd-module-2.8'
M = V / 'manufacturing'
OUT = ROOT / 'dist/lcd-module-2.8/bottom-only'
PCB = V / 'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((ROOT / 'assets/modular-downloads.json').read_text())
assert sha(PCB) == manifest['boardSha256'], 'Board no longer matches pinned fabrication release'
readiness = json.loads((M / 'readiness.json').read_text())
assert readiness['boardSha256'] == sha(PCB)
for name in ['bom-jlcpcb.csv', 'cpl-jlcpcb.csv', 'population.csv']:
    assert sha(M / name) == readiness['files'][name], f'Mismatched parent {name}'
load = lambda path: list(csv.DictReader(path.open()))
population = load(M / 'population.csv')
assembled = {p['ref'] for p in population if p['role'] == 'JLCPCB SMT assembly'}
bottom = {p['ref'] for p in population if p['ref'] in assembled and p['side'] == 'B.Cu'}
top = assembled - bottom
assert len(bottom) == 24 and len(top) == 11
sx = runpy.run_path(str(ROOT / 'scripts/kicad-sexpr.py'))
fps = {next(p[2] for p in sx['children'](f, 'property') if p[1] == 'Reference'): f
       for f in sx['children'](sx['parse'](PCB.read_text()), 'footprint')}
for p in population:
    assert sx['one'](fps[p['ref']], 'layer')[1] == p['side']
bom = load(M / 'bom-jlcpcb.csv')
assert {ref for row in bom for ref in row['Designator'].split(',')} == assembled
subset = []
for row in bom:
    refs = set(row['Designator'].split(',')) & bottom
    if refs:
        subset.append(dict(row, Designator=','.join(sorted(refs))))
cpl = load(M / 'cpl-jlcpcb.csv')
assert len(cpl) == len(assembled) and {r['Designator'] for r in cpl} == assembled
cpl = [r for r in cpl if r['Designator'] in bottom]
assert {r['Designator'] for r in cpl} == {ref for row in subset for ref in row['Designator'].split(',')} == bottom
assert all(r['Layer'] == 'Bottom' for r in cpl)
for row in cpl:
    at = sx['one'](fps[row['Designator']], 'at')
    assert abs(float(row['Mid X']) - (float(at[1]) - 50)) < 1e-5
    assert abs(float(row['Mid Y']) - (130 - float(at[2]))) < 1e-5
artifact = next(a for a in manifest['assets'] if a['name'] == 'shieldsigner-modular-gerbers.zip')
candidates = [ROOT / 'dist/lcd-module-2.8' / artifact['name'],
              ROOT / '.tools/website-downloads' / artifact['sha256'] / artifact['name']]
gerbers = next((p for p in candidates if p.exists() and sha(p) == artifact['sha256']), None)
assert gerbers, 'Fetch the release-pinned Gerber ZIP before packaging; do not mix regenerated files'
OUT.mkdir(parents=True, exist_ok=True)

def write_csv(name, rows):
    with (OUT / name).open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)

write_csv('bom-bottom-only.csv', subset)
write_csv('cpl-bottom-only.csv', cpl)
write_csv('customer-top-population.csv', [p for p in population if p['ref'] in top])
catalog = {p['code']: p for p in json.loads((M / 'catalog-feasibility-snapshot.json').read_text())['parts']}
stock = []
for row in subset:
    p = catalog[row['LCSC Part #']]
    qty = len(row['Designator'].split(','))
    stock.append({'code': p['code'], 'mpn': p['componentModelEn'], 'perBoard': qty,
                  'assemblyStock': p['canPresaleNumber'], 'checkedAt': p['checkedAt'],
                  'stockCoversOneBeforeAttrition': p['canPresaleNumber'] >= qty,
                  'minimumPurchaseRaw': p.get('preMinPurchaseNum'),
                  'leastPatchNumberRaw': p.get('leastPatchNumber'),
                  'lossNumberRaw': p.get('lossNumber')})
report = {
    'status': 'Unsubmitted quotation option; not assembler-approved or purchased',
    'release': manifest['release'], 'boardSha256': sha(PCB),
    'firstArticlePopulatedQuantityRequested': 1,
    'supplierMinimumAssembledQuantity': None,
    'assemblySide': 'Bottom', 'smtPlacements': len(bottom), 'catalogLines': len(subset),
    'customerTopPlacements': len(top), 'stockReserved': False,
    'scope': 'Same PCB and complete Gerber set; only assembly BOM/CPL population is reduced.',
    'stockSnapshot': stock,
    'supplierQuestions': [
        'Quote ONE populated first article; separately state bare-PCB minimum and minimum assembled quantity. Do not assume all fabricated boards should be populated.',
        'Confirm QFN center through-via process, stencil thickness/apertures, solder wicking/void inspection and rework. No filled/capped via process is specified by these files.',
        'Confirm USB4125-GF-A 1mm shell-stake solder fill on 1.6mm board and socket handling/heat limits.',
        'Review bottom rotations, SEC1210 pin 1 and socket entrance; customer parts on top must remain absent.',
        'Itemize board, setup, parts including minimums/attrition/loading, stencil, inspection, freight and taxes. Raw catalog minimum fields are not interpreted as final charges.',
        'Specify any panel rails/fiducials/tooling added and any proposed fabrication change before acceptance.'
    ],
    'remainingCustomerWork': [
        'Solder 8 switches, U701 and C701/C702 on top; source the exact parts or reviewed substitutes. Top 10uF DigiKey selection is currently out of stock; exact original CL21A106KAYNNNE is separately listed at LCSC C15850 (shipping/minimums apply).',
        'Install 30 carrier header joints; modules may require additional header soldering.',
        'Perform staged first-article acceptance before populating repeat boards.'
    ],
    'files': {p.name: sha(p) for p in sorted(OUT.glob('*.csv'))},
    'gerberSha256': artifact['sha256']
}
support = ['fabrication-capability-audit.json', 'first-article-process.json', 'via-removal-experiment.json']
for name in support:
    source = M / name
    record = json.loads(source.read_text())
    assert record.get('boardSha256', record.get('referenceBoardSha256')) == sha(PCB), f'Stale review record: {name}'
    shutil.copyfile(source, OUT / name)
    report['files'][name] = sha(source)
(OUT / 'quote-request.json').write_text(json.dumps(report, indent=2) + '\n')
with ZipFile(OUT / 'shieldsigner-bottom-only-quote.zip', 'w', ZIP_DEFLATED) as z:
    z.write(gerbers, gerbers.name)
    for name in ['bom-bottom-only.csv', 'cpl-bottom-only.csv', 'customer-top-population.csv', 'quote-request.json', *support]:
        z.write(OUT / name, name)
(M / 'bottom-only-option.json').write_text(json.dumps(report, indent=2) + '\n')
full = next(a for a in manifest['assets'] if a['name'] == 'shieldsigner-modular-order.zip')
full_candidates = [ROOT / 'dist/lcd-module-2.8' / full['name'],
                   ROOT / '.tools/website-downloads' / full['sha256'] / full['name']]
full_kit = next((p for p in full_candidates if p.exists() and sha(p) == full['sha256']), None)
if full_kit:
    rfq = ROOT / 'dist/lcd-module-2.8/shieldsigner-first-article-rfq.zip'
    with ZipFile(rfq, 'w', ZIP_DEFLATED) as z:
        z.write(M / 'first-article-rfq.txt', 'first-article-rfq.txt')
        z.write(full_kit, 'option-a-full/' + full_kit.name)
        z.write(OUT / 'shieldsigner-bottom-only-quote.zip', 'option-b-bottom/shieldsigner-bottom-only-quote.zip')
    print('Combined unsubmitted comparison RFQ:', rfq)
else:
    print('Combined RFQ not built: fetch the release-pinned full order kit first.')
print(f'Unsubmitted bottom-only quote kit: {len(bottom)} placements / {len(subset)} lines; {len(top)} customer top placements.')
print(OUT / 'shieldsigner-bottom-only-quote.zip')
