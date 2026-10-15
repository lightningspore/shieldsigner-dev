#!/usr/bin/env python3
"""Build explicit dimensional envelopes from HTM-TFT028A16-SPI drawing p5.

Run with mise run variant:lcd:display-model, then regenerate review/package
outputs. These are review envelopes, not vendor CAD.
"""
from pathlib import Path
import hashlib
import json
import cadquery as cq
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'variants/lcd-module-2.8/kicad/3dmodels/vendor'

def box(x, y, z, dx, dy, dz):
    return cq.Workplane('XY').box(dx, dy, dz, centered=False).translate((x, y, z))

pcb = box(0, -53.3, 0, 88, 53.3, 1.6)
for x in [2.75, 85.25]:
    for y in [-2.75, -50.55]:
        hole = cq.Workplane('XY').circle(1.5).extrude(1.6).translate((x, y, 0))
        pcb = pcb.cut(hole)
# The module's 2.54-mm connection is J1, opposite the separate 2-mm J2.
for n in range(8):
    hole = cq.Workplane('XY').circle(.5).extrude(1.6).translate((2.5, -17.76-n*2.54, 0))
    pcb = pcb.cut(hole)
assembly = cq.Assembly(name='HTM-TFT028A16-SPI-dimensional-model')
assembly.add(pcb, name='PCB-envelope', color=cq.Color(.05, .30, .17))
assembly.add(box(6.1, -52.15, 1.6, 70.2, 51, 3.8), name='frame-envelope', color=cq.Color(.72, .74, .75))
assembly.add(box(14.2, -49.25, 5.4, 59.6, 45.2, .2), name='glass-envelope', color=cq.Color(.025, .03, .035))
assembly.add(box(15.2, -48.25, 5.6, 57.6, 43.2, .1), name='active-area', color=cq.Color(.10, .13, .15))
assembly.add(box(80, -36.65, -5.2, 8, 20, 5.2), name='rear-J2-keepout-envelope', color=cq.Color(.85, .84, .77))
assembly.save(str(OUT / 'HOTHMI-HTM-TFT028A16-SPI-envelope.step'))
spacer = cq.Workplane('XY').circle(2.5).circle(1.25).extrude(12)
cq.exporters.export(spacer, str(OUT / 'M2.5x12-standoff-envelope.step'))
provenance_path = OUT.parent / 'provenance.json'
provenance = json.loads(provenance_path.read_text())
for name in ['HOTHMI-HTM-TFT028A16-SPI-envelope.step', 'M2.5x12-standoff-envelope.step']:
    path = OUT / name
    record = provenance['models']['vendor/' + name]
    record['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    record['bytes'] = path.stat().st_size
provenance_path.write_text(json.dumps(provenance, indent=2) + '\n')
print('Generated drawing-based module and threadless 12 mm support envelopes.')
