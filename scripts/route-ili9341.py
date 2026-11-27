#!/usr/bin/env python3
"""Route the connections left open by scripts/add-ili9341-pcb.py.

Explicit, reviewed geometry (mm, 0.2 mm tracks, 0.6/0.3 mm vias, 0.2 mm
clearance). J702 sits one 2.54 mm column right of J701, so tracks crossing the
J702 column use the 0.84 mm gaps between its pads ("channels", at the
mid-points 76.88, 81.96, 84.50, 92.12, 94.66, 97.20 ...).

- In1.Cu stays an unbroken GND plane. In2.Cu (GND pour) carries the four
  J702-to-J701 links: RST and DC loop left of J701 (nested), CS and LED run
  right of J702 and join their nets through vias.
- F.Cu/B.Cu restore the J701-to-Luckfox links that crossed the J702 column and
  carry the LCD_3V3, +5V and LCD_ALT_VCC (JP701/JP702) wiring.

Refuses to run twice; validate with DRC afterwards.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / '.tools/kicad-10/KiCad/KiCad.app/Contents'
if not os.environ.get('SHIELDSIGNER_PCB_WORKER'):
    env = os.environ.copy()
    env['SHIELDSIGNER_PCB_WORKER'] = '1'
    python = APP / 'Frameworks/Python.framework/Versions/3.9/bin/python3'
    sys.exit(subprocess.call([str(python), __file__, *sys.argv[1:]], env=env))

import wx  # noqa: E402

wx.Log.SetLogLevel(wx.LOG_Error)
app = wx.App(False)
import pcbnew as p  # noqa: E402

PCB = ROOT / 'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
F, B, IN2 = p.F_Cu, p.B_Cu, p.In2_Cu

# (net, layer, [points])
ROUTES = [
    # J702 -> J701 on In2.Cu
    ('LCD_RST', IN2, [(95.04, 80.69), (93.77, 81.96), (89.2, 81.96), (89.2, 95.93), (92.5, 95.93)]),
    ('LCD_DC', IN2, [(95.04, 83.23), (93.77, 84.5), (89.9, 84.5), (89.9, 93.39), (92.5, 93.39)]),
    ('RPI_SPI_CS', IN2, [(95.04, 78.15), (97.9, 78.15), (97.9, 92.78), (97.18, 93.5)]),
    ('RPI_BACKLIGHT', IN2, [(95.04, 90.85), (96.35, 90.85), (96.35, 97.1), (97.05, 97.8),
                            (97.6, 97.8)]),
    # J701 -> Luckfox links that used to cross the J702 column
    ('RPI_SPI_CS', B, [(92.5, 90.85), (93.77, 92.12), (97.18, 92.12), (97.18, 95.53)]),
    ('LCD_DC', B, [(92.5, 93.39), (93.77, 94.66), (96.2, 94.66), (96.2, 96.98)]),
    ('LCD_RST', F, [(93.99, 94.44), (94.21, 94.66), (102.91, 94.66), (103.13, 94.44)]),
    ('RPI_BACKLIGHT', F, [(92.5, 98.47), (93.77, 97.2), (97.0, 97.2), (98.19, 98.39),
                          (113.66, 98.39)]),
    ('LCD_SCLK', F, [(95.04, 88.31), (95.04, 89.36)]),
    # Supplies
    ('LCD_3V3', F, [(92.5, 80.69), (92.5, 76.88), (97.8, 76.88), (97.8, 75.39)]),
    ('+5V', B, [(91.31, 80.24), (91.31, 76.88), (97.43, 76.88), (97.43, 74.12)]),
    # USB +5V up to the Luckfox feed, now passing below J702 pin 14; the diagonal
    # keeps the rear GND pour open around D301's GND pad.
    ('+5V', B, [(97.41, 109.66), (96.5, 108.75), (96.5, 107.6), (94.9, 107.6),
                (91.31095, 104.01095), (91.31095, 103.563)]),
    ('LCD_ALT_VCC', B, [(98.95, 63.6), (98.95, 70.6), (96.48, 73.07), (95.04, 73.07)]),
    ('LCD_3V3', B, [(100.25, 63.6), (100.25, 61.5), (108.0, 61.5)]),
    ('+5V', B, [(100.25, 67.6), (103.36, 67.6), (104.96, 66.0)]),
]
VIAS = [('RPI_SPI_CS', (97.18, 93.5)), ('RPI_BACKLIGHT', (97.6, 97.8))]
# Remnant stubs of the old backlight route that no longer reach anything.
DROP = [('RPI_BACKLIGHT', (92.5, 98.47), (93.65, 98.47)),
        ('RPI_BACKLIGHT', (93.65, 98.47), (93.73, 98.39))]


def vec(x, y):
    return p.VECTOR2I(p.FromMM(x), p.FromMM(y))


def near(a, b):
    return abs(p.ToMM(a.x) - b[0]) < 0.01 and abs(p.ToMM(a.y) - b[1]) < 0.01


def main():
    board = p.LoadBoard(str(PCB))
    if board.FindNet('LCD_ALT_VCC') is None:
        raise SystemExit('Run scripts/add-ili9341-pcb.py first')
    alt = board.FindNet('LCD_ALT_VCC').GetNetCode()
    if any(t.GetNetCode() == alt for t in board.GetTracks()):
        raise SystemExit('ILI9341 routes already present; nothing to do')

    tracks = list(board.GetTracks())
    drop = [t for t in tracks for name, a, b in DROP
            if t.GetNetname() == name and not isinstance(t, p.PCB_VIA)
            and near(t.GetStart(), a) and near(t.GetEnd(), b)]
    if len(drop) != len(DROP):
        raise SystemExit('Expected backlight remnant stubs not found')
    for t in drop:
        board.Remove(t)

    count = 0
    for name, layer, points in ROUTES:
        code = board.FindNet(name).GetNetCode()
        for a, b in zip(points, points[1:]):
            t = p.PCB_TRACK(board)
            t.SetStart(vec(*a))
            t.SetEnd(vec(*b))
            t.SetLayer(layer)
            t.SetWidth(p.FromMM(0.2))
            t.SetNetCode(code)
            board.Add(t)
            count += 1
    for name, at in VIAS:
        v = p.PCB_VIA(board)
        v.SetPosition(vec(*at))
        v.SetWidth(p.FromMM(0.6))
        v.SetDrill(p.FromMM(0.3))
        v.SetNetCode(board.FindNet(name).GetNetCode())
        board.Add(v)
    p.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(str(PCB))
    print('Added %d track segments and %d vias' % (count, len(VIAS)))


if __name__ == '__main__':
    main()
