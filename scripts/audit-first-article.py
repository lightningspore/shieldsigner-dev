#!/usr/bin/env python3
"""Measure native assembly geometry; report process questions, not qualification."""
import collections
import hashlib
import json
import math
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANT = ROOT / 'variants/lcd-module-2.8'
PCB = VARIANT / 'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
sx = runpy.run_path(str(ROOT / 'scripts/kicad-sexpr.py'))
one, children = sx['one'], sx['children']
tree = sx['parse'](PCB.read_text())
fps = {next(p[2] for p in children(f, 'property') if p[1] == 'Reference'): f
       for f in children(tree, 'footprint')}
qfn = fps['U601']
pads = children(qfn, 'pad')
ep = next(p for p in pads if p[1] == '25')
windows = [p for p in pads if p[1] == '' and 'B.Paste' in one(p, 'layers')]

def area(pad):
    w, h = map(float, one(pad, 'size')[1:3])
    ratio = one(pad, 'roundrect_rratio')
    radius = min(w, h) * float(ratio[1]) if ratio else 0
    return w * h - (4 - math.pi) * radius * radius

perimeter = [p for p in pads if p[1] not in ['', '25']]
ratios = {}
for thickness in [.1, .127, .15]:
    ratios[str(thickness)] = min(
        area(p) / (thickness * (
            2 * sum(map(float, one(p, 'size')[1:3]))
            - (8 - 2 * math.pi) * min(map(float, one(p, 'size')[1:3]))
            * float(one(p, 'roundrect_rratio')[1])))
        for p in perimeter)
at = one(qfn, 'at')
cx, cy = map(float, at[1:3])
# Package is square: circle candidates inside its central copper square suffice
# for this footprint, whose current native rotation is 180 degrees.
assert float(at[3]) % 90 == 0, 'Review via containment for rotated QFN'
w, h = map(float, one(ep, 'size')[1:3])
vias = []
for via in children(tree, 'via'):
    x, y = map(float, one(via, 'at')[1:3])
    r = float(one(via, 'size')[1]) / 2
    if abs(x - cx) + r <= w / 2 and abs(y - cy) + r <= h / 2:
        vias.append({'atMm': [x, y], 'diameterMm': r * 2,
                     'drillMm': float(one(via, 'drill')[1]),
                     'note': 'Native through-via; no filled/capped process established.'})
population = []
import csv
with (VARIANT / 'manufacturing/population.csv').open() as file:
    for row in csv.DictReader(file):
        if row['role'] == 'JLCPCB SMT assembly':
            assert one(fps[row['ref']], 'layer')[1] == row['side']
            population.append(row)
report = {
    'boardSha256': hashlib.sha256(PCB.read_bytes()).hexdigest(),
    'qualification': 'Geometry/process review only; no physical assembly or yield evidence.',
    'smtPiecesBySide': dict(collections.Counter(p['side'] for p in population)),
    'qfn': {
        'reference': 'U601', 'pitchMm': .65,
        'exposedCopperAreaMm2': area(ep),
        'pasteWindowCount': len(windows),
        'pasteAreaMm2': sum(map(area, windows)),
        'pasteCoveragePercent': 100 * sum(map(area, windows)) / area(ep),
        'minimumPerimeterApertureAreaToWallAreaByStencilThicknessMm': ratios,
        'centralVias': vias,
        'openQuestions': [
            'Choose stencil thickness and paste using measured print/reflow results.',
            'Review solder wicking/voiding at the central through-via; mask tenting is not filling/capping.',
            'Do not simply delete the via: via-removal-experiment.json records a native connectivity regression.',
            'Establish hidden-pad inspection and rework capability; a working UART alone does not inspect the pad.'
        ]
    },
    'firstArticleProcessCandidate': {
        'bottom': 'Reflow the 24 bottom-side parts once with the component side up, subject to every part/paste thermal limits.',
        'top': 'Then hand-solder the eight accessible switches, SOT-25 LDO and two capacitors with local heat; verify access on a dry fit.',
        'benefit': 'Avoids requiring a second full-board reflow and inverted heavy socket retention for a one-off build.',
        'notYetProven': 'Operator/equipment, socket heat limits, USB shell solder fill and actual print/reflow profile.'
    },
    'sources': [
        {'path': 'reference/pdfs/Microchip-AN2089-QFN-assembly.pdf',
         'url': 'https://ww1.microchip.com/downloads/en/Appnotes/00002089A.pdf',
         'scope': 'Generic package mounting/profile/moisture handling, not SEC1210-specific process approval.'},
        {'path': 'reference/pdfs/GCT-USB4125.pdf',
         'scope': 'Drawing page 1: selected -0190 shell stake 1.90 mm; current PCB 1.60 mm.'}
    ]
}
output = VARIANT / 'manufacturing/first-article-process.json'
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
