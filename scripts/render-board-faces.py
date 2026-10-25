#!/usr/bin/env python3
"""Render unobstructed, orthographic PCB faces without changing native hardware."""
import hashlib
import runpy
import subprocess
import struct
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANT = ROOT / 'variants/lcd-module-2.8'
board = VARIANT / 'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
original = board.read_bytes()
sx = runpy.run_path(str(ROOT / 'scripts/kicad-sexpr.py'))
text = original.decode()
# Hide 3D bodies only in a disposable rendering copy. Copper, silk and mask stay native.
spans = [(a, b) for a, b, raw in sx['expressions'](text) if raw.startswith('(model ')]
for a, b in sorted(spans, reverse=True):
    text = text[:a] + text[b:]
cli = runpy.run_path(str(ROOT / 'scripts/kicad.py'))['cli']()
(ROOT / '.tools').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='board-faces-', dir=ROOT / '.tools') as tmp:
    preview = Path(tmp) / 'carrier.kicad_pcb'
    preview.write_text(text)
    for side in ['top', 'bottom']:
        subprocess.run([str(cli), 'pcb', 'render', '--side', side,
                        '--width', '2824', '--height', '1424', '--zoom', '1.8',
                        '--background', 'transparent', '--quality', 'high',
                        '--output', str(VARIANT / f'board-{side}.png'), str(preview)], check=True)
# KiCad 10 macOS subtracts its 24 px render-window frame from requested dimensions.
for side in ['top','bottom']:
    assert struct.unpack('>II', (VARIANT / f'board-{side}.png').read_bytes()[16:24]) == (2800,1400)
assert board.read_bytes() == original
print('Rendered both PCB faces; native board unchanged:', hashlib.sha256(original).hexdigest())
