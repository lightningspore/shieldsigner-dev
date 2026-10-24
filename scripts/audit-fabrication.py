#!/usr/bin/env python3
"""Screen native geometry against dated published JLC limits, not factory DFM."""
import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'variants/lcd-module-2.8'
PCB = V / 'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
sx = runpy.run_path(str(ROOT / 'scripts/kicad-sexpr.py'))
one, children = sx['one'], sx['children']
tree = sx['parse'](PCB.read_text())
rules = json.loads(PCB.with_suffix('.kicad_pro').read_text())['board']['design_settings']['rules']
native = json.loads((V / 'check-results.json').read_text())
assert native['boardSha256'] == hashlib.sha256(PCB.read_bytes()).hexdigest(), 'Stale native checks'
track_min = min(float(one(t, 'width')[1]) for t in children(tree, 'segment'))
vias = [{'diameterMm': float(one(v, 'size')[1]), 'drillMm': float(one(v, 'drill')[1])}
        for v in children(tree, 'via')]
slots, silk = [], []
for f in children(tree, 'footprint'):
    ref = next(p[2] for p in children(f, 'property') if p[1] == 'Reference')
    for pad in children(f, 'pad'):
        drill = one(pad, 'drill')
        if drill and drill[1] == 'oval':
            w, length = sorted(map(float, drill[2:4]))
            slots.append({'reference': ref, 'pad': pad[1], 'type': pad[2],
                          'widthMm': w, 'lengthMm': length, 'aspectRatio': length / w})
    for text in children(f, 'property') + children(f, 'fp_text'):
        if one(text, 'layer')[1:] not in [['F.SilkS'], ['B.SilkS']] or one(text, 'hide') or 'hide' in text:
            continue
        font = one(one(text, 'effects'), 'font')
        size, thickness = one(font, 'size'), one(font, 'thickness')
        if (size and min(map(float, size[1:])) < .8) or (thickness and float(thickness[1]) < .15):
            silk.append({'reference': ref, 'text': text[2],
                         'sizeMm': list(map(float, size[1:])) if size else None,
                         'strokeMm': float(thickness[1]) if thickness else None})
assert track_min >= .1
assert rules['min_clearance'] >= .1 and rules['min_copper_edge_clearance'] >= .2
assert all(v['drillMm'] >= .15 and (v['diameterMm'] - v['drillMm']) / 2 >= .13 for v in vias)
assert all(s['type'] == 'thru_hole' and s['widthMm'] >= .5 and s['aspectRatio'] >= 2 for s in slots)
assert not any(v['active'] or v['excluded'] or v['unconnected'] or v['parity'] for v in native['checks'].values())
report = {
    'boardSha256': native['boardSha256'], 'capabilityProfileCheckedDate': '2026-10-22',
    'status': 'Selected nominal fabrication features screen within published limits; factory DFM and assembly preparation remain open.',
    'profile': {'material': 'FR4', 'copperLayers': 2, 'copperThicknessMm': .035,
                'boardThicknessMm': 1.6, 'outline': '160x70mm capsule, as checked by mechanical gate'},
    'measurements': {'minimumRoutedTrackWidthMm': track_min,
                     'configuredMinimumClearanceMm': rules['min_clearance'],
                     'configuredCopperToEdgeClearanceMm': rules['min_copper_edge_clearance'],
                     'viaCount': len(vias), 'minimumViaDrillMm': min(v['drillMm'] for v in vias),
                     'minimumActualViaAnnularRingMm': min((v['diameterMm'] - v['drillMm']) / 2 for v in vias),
                     'platedSlots': slots},
    'scopeLimits': [
        'Trace width and via/slot dimensions are extracted directly. Copper spacing and edge clearance rely on the recorded native DRC and project rules, not an independent Gerber geometry engine.',
        'No actual PCB, stencil or factory tooling has been inspected.',
        'Only named features are screened; this is not a comprehensive factory DFM approval.',
        'The PCB project allows a 0.05mm minimum via annulus, but actual vias are 0.15mm; this screen checks actual geometry rather than accepting that permissive setting.'
    ],
    'assemblyPreparation': {
        'railFiducialToolingPlanApproved': False,
        'nativeFiducialFootprints': [next(p[2] for p in children(f, 'property') if p[1] == 'Reference')
                                    for f in children(tree, 'footprint') if 'fiducial' in f[1].lower()],
        'action': 'Have assembler propose/approve rails, optical fiducials, tooling and depanelization for this capsule. Keep attachments away from USB/card access and display supports; do not assume a bare-board Gerber is an assembly panel.'},
    'silkLegibilityReview': {'advisoryThresholds': {'textHeightMm': .8, 'strokeMm': .15},
                             'smallerVisibleFootprintText': silk,
                             'action': 'Review these reference markings in the fabrication preview; these are legibility advisories, not established electrical faults. Board-level artwork/graphics are outside this text scan.'},
    'sources': [
        {'url': 'https://jlcpcb.com/capabilities/pcb-capabilities/',
         'limitsUsed': '2-layer 1oz track/space 0.10/0.10mm; routed edge copper 0.2mm; plated slot width 0.5mm, length at least twice width. Profile includes conservative 0.13mm annular-ring screen.'},
        {'url': 'https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order',
         'scope': 'Standard assembly requires rail/fiducial preparation; supplier must approve the actual implementation.'},
        {'url': 'https://jlcpcb.com/help/article/pcb-dimensions',
         'scope': 'An irregular outline requires manual manufacturability review.'}
    ]
}
output = V / 'manufacturing/fabrication-capability-audit.json'
output.write_text(json.dumps(report, indent=2) + '\n')
print(f'Nominal screen passed: {track_min}mm tracks, {len(vias)} vias, {len(slots)} plated slots; assembly tooling remains unapproved.')
print('Silk legibility advisories:', ', '.join(p['reference'] for p in silk))
