#!/usr/bin/env python3
"""Place the alternate 14-pin ILI9341 socket (J702) and its VCC straps on the PCB.

Run after scripts/add-ili9341-schematic.py. Uses KiCad 10's bundled Python.

Geometry (LCDwiki MSP2806/MSP2807 outline, 86 x 50 mm, header 2.00 mm from the
short edge, pin 1 8.49 mm from the long edge, holes 76.08 x 44.00 mm): the module
is mounted landscape with the header on the left, centred vertically on the
HOTHMI hole pattern. J702 sits one 2.54 mm column right of J701. The module's
right-hand holes land 2.06 mm from H702/H704, so those two holes become slots
that accept either module; the 14-pin header carries the left side.

Steps: add J702/JP701/JP702 with schematic paths and nets, slot H702/H704,
relocate J701's pin labels, label J702, and rip up existing tracks that the new
pads obstruct. Routing of the resulting unrouted connections is a separate
step (scripts/route-ili9341.py).
"""

import math
import os
import re
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
SHEET = ROOT / 'kicad/lcd_module.kicad_sch'
ROOT_UUID = '8c9c54c8-0cfa-43ef-b1ba-3cda1bca877f'
LCD_SHEET_UUID = '4fead130-596d-4414-bb04-d5dfc4d319ed'

J701_X, J701_PIN8_Y = 92.5, 80.69
PITCH = 2.54
J702_X = J701_X + PITCH  # 95.04
MODULE_CENTER_Y = (65.679 + 113.479) / 2  # HOTHMI hole pattern centre, 89.579
J702_PIN1_Y = round(MODULE_CENTER_Y - 25.0 + 8.49, 2)  # 73.07
MODULE_LEFT_X = J702_X - 2.0  # header 2.00 mm from the module edge
ALT_HOLE_X = MODULE_LEFT_X + 86.0 - 3.0  # 176.04
ALT_HOLE_DY = 22.0  # 44.00 mm hole pitch

NETS = ['LCD_ALT_VCC', 'GND', 'RPI_SPI_CS', 'LCD_RST', 'LCD_DC', 'LCD_MOSI', 'LCD_SCLK',
        'RPI_BACKLIGHT', 'unconnected-(J702-MISO-Pad9)', 'unconnected-(J702-T_CLK-Pad10)',
        'unconnected-(J702-T_CS-Pad11)', 'unconnected-(J702-T_DIN-Pad12)',
        'unconnected-(J702-T_DO-Pad13)', 'unconnected-(J702-T_IRQ-Pad14)']
LABELS = ['VCC', 'GND', 'CS', 'RST', 'DC', 'MOSI', 'CLK', 'BL', 'NC', 'NC', 'NC', 'NC', 'NC', 'NC']


def mm(v):
    return p.FromMM(v)


def vec(x, y):
    return p.VECTOR2I(mm(x), mm(y))


def symbol_uuids():
    text = SHEET.read_text()
    found = {}
    for ref in ('J702', 'JP701', 'JP702'):
        m = re.search(r'\(symbol \(lib_id "[^"]+"\) \(at [^)]*\)[^(]*(?:\([^()]*\)\s*)*?\(uuid "([^"]+)"\) '
                      r'\(property "Reference" "' + ref + '"', text)
        if not m:
            raise SystemExit('Symbol %s not in %s; run add-ili9341-schematic.py first' % (ref, SHEET))
        found[ref] = m.group(1)
    return found


def net(board, name):
    item = board.FindNet(name)
    if item is None:
        item = p.NETINFO_ITEM(board, name)
        board.Add(item)
    return item


def load(board, lib, name, ref, value, uuid, x, y, angle=0, back=False):
    fp = p.FootprintLoad(str(ROOT / 'kicad/Footprints' / (lib + '.pretty')), name)
    if fp is None:
        raise SystemExit('Footprint %s:%s not found' % (lib, name))
    fp.SetFPIDAsString('%s:%s' % (lib, name))
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPath(p.KIID_PATH('/%s/%s/%s' % (ROOT_UUID, LCD_SHEET_UUID, uuid)))
    board.Add(fp)
    fp.SetPosition(vec(x, y))
    fp.SetOrientationDegrees(angle)
    if back:
        fp.Flip(fp.GetPosition(), p.FLIP_DIRECTION_TOP_BOTTOM)
    return fp


def text(board, body, x, y, layer, size=0.7, thick=0.13, justify=0, angle=0.0):
    t = p.PCB_TEXT(board)
    t.SetText(body)
    t.SetLayer(layer)
    t.SetPosition(vec(x, y))
    t.SetTextSize(p.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(thick))
    t.SetHorizJustify(justify)
    t.SetTextAngleDegrees(angle)
    if layer == p.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)
    return t


def slot(board, ref, target):
    """Turn a round mounting hole into a slot reaching `target` (x, y)."""
    fp = next(f for f in board.GetFootprints() if f.GetReference() == ref)
    pad = next(iter(fp.Pads()))
    cx, cy = p.ToMM(pad.GetPosition().x), p.ToMM(pad.GetPosition().y)
    dx, dy = target[0] - cx, target[1] - cy
    length = math.hypot(dx, dy)
    dia = p.ToMM(pad.GetDrillSize().x)
    pad.SetShape(p.PAD_SHAPE_OVAL)
    pad.SetDrillShape(p.PAD_DRILL_SHAPE_OBLONG)
    pad.SetSize(p.VECTOR2I(mm(dia + length), mm(dia)))
    pad.SetDrillSize(p.VECTOR2I(mm(dia + length), mm(dia)))
    pad.SetOrientationDegrees(-math.degrees(math.atan2(dy, dx)))
    pad.SetPosition(vec(cx + dx / 2, cy + dy / 2))
    return length


def obstructs(track, pads, clearance=0.2):
    """True when a foreign-net track or via comes within clearance of a new pad."""
    if isinstance(track, p.PCB_VIA):
        r = p.ToMM(track.GetWidth(p.F_Cu)) / 2
        segs = [(track.GetPosition(), track.GetPosition())]
    else:
        r = p.ToMM(track.GetWidth()) / 2
        segs = [(track.GetStart(), track.GetEnd())]
    for pad in pads:
        if pad.GetNetCode() == track.GetNetCode():
            continue
        if not (pad.IsOnLayer(track.GetLayer()) or isinstance(track, p.PCB_VIA)):
            continue
        px, py = p.ToMM(pad.GetPosition().x), p.ToMM(pad.GetPosition().y)
        pr = max(p.ToMM(pad.GetSize().x), p.ToMM(pad.GetSize().y)) / 2
        for a, b in segs:
            ax, ay, bx, by = p.ToMM(a.x), p.ToMM(a.y), p.ToMM(b.x), p.ToMM(b.y)
            vx, vy = bx - ax, by - ay
            n = vx * vx + vy * vy
            t = 0 if n == 0 else max(0, min(1, ((px - ax) * vx + (py - ay) * vy) / n))
            d = math.hypot(ax + t * vx - px, ay + t * vy - py)
            if d < pr + r + clearance - 1e-6:
                return True
    return False


def main():
    board = p.LoadBoard(str(PCB))
    if any(f.GetReference() == 'J702' for f in board.GetFootprints()):
        raise SystemExit('J702 already placed; nothing to do')
    uuids = symbol_uuids()

    j702 = load(board, 'ShieldSigner', 'LCD_SPI_14_ILI9341', 'J702', 'ILI9341 SPI 14-pin',
                uuids['J702'], J702_X, J702_PIN1_Y)
    for pad in j702.Pads():
        pad.SetNet(net(board, NETS[int(pad.GetNumber()) - 1]))
    j702.SetDNP(True)  # alternate socket: fitted instead of J701 for ILI9341 modules

    # J702 VCC straps on the rear, clear of the Luckfox body and H701.
    jp1 = load(board, 'Jumper', 'SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm', 'JP701',
               'Jumper_2_Small_Bridged', uuids['JP701'], 99.6, 63.6, 180, back=True)
    jp2 = load(board, 'Jumper', 'SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', 'JP702',
               'Jumper_2_Small_Open', uuids['JP702'], 99.6, 67.6, 180, back=True)
    for fp, source in ((jp1, 'LCD_3V3'), (jp2, '+5V')):
        for pad in fp.Pads():
            pad.SetNet(net(board, source if pad.GetNumber() == '1' else 'LCD_ALT_VCC'))
        fp.SetAttributes(next(
            f for f in board.GetFootprints() if f.GetReference() == 'JP201').GetAttributes())
        next(f for f in fp.GetFields() if f.GetName() == 'Description').SetText('')

    # Slot the right-hand display holes so either module's holes fit.
    slots = {ref: slot(board, ref, (ALT_HOLE_X, y)) for ref, y in
             (('H702', MODULE_CENTER_Y - ALT_HOLE_DY), ('H704', MODULE_CENTER_Y + ALT_HOLE_DY))}

    # J701 labels move left of J701; J702 gets its own labels on the right.
    for d in board.GetDrawings():
        if not isinstance(d, p.PCB_TEXT) or d.GetLayer() != p.F_SilkS:
            continue
        if abs(p.ToMM(d.GetPosition().x) - 95.3) < 0.01:
            d.SetPosition(vec(90.1, p.ToMM(d.GetPosition().y)))
        elif d.GetText() == 'LCD3V3':  # TP803 marker, clear of the J702 labels
            d.SetPosition(vec(100.9, 79.0))
            d.SetTextAngleDegrees(90)
    for i, name in enumerate(LABELS):
        text(board, name, 97.6, J702_PIN1_Y + PITCH * i, p.F_SilkS)
    text(board, 'J701 OR J702', 92.0, 69.0, p.F_SilkS, 0.8, 0.15)
    for fp, y, label, ref_at in ((jp1, 63.6, '3V3*', (99.6, 61.6)), (jp2, 67.6, '5V', (100.6, 69.6))):
        text(board, label, 96.6, y, p.B_SilkS, 0.7, 0.13)
        fp.Reference().SetPosition(vec(*ref_at))
        fp.Reference().SetTextAngleDegrees(0)
    text(board, 'NEVER BOTH', 99.6, 65.6, p.B_SilkS, 0.7, 0.13)

    # J702's VCC/GND pads fall inside the Luckfox's projected microSD marking and
    # its pins 1/12 cross the module outline: drop the marker rectangles, move the
    # MicroSD legend left, and open the outline around the J702 column.
    u202 = next(f for f in board.GetFootprints() if f.GetReference() == 'U202')
    gap = (J702_X - 1.0, J702_X + 1.0)
    for g in list(u202.GraphicalItems()):
        if g.GetLayer() not in (p.F_SilkS, p.B_SilkS):
            continue
        box = g.GetBoundingBox()
        x0, x1 = p.ToMM(box.GetX()), p.ToMM(box.GetRight())
        y0, y1 = p.ToMM(box.GetY()), p.ToMM(box.GetBottom())
        if isinstance(g, p.PCB_TEXT):
            if g.GetText() == 'MicroSD':
                g.SetPosition(vec(88.6, 74.9))
                g.SetTextSize(p.VECTOR2I(mm(0.8), mm(0.8)))
            continue
        if abs(x0 - 89.58) < 0.05 and abs(x1 - 98.68) < 0.05:
            u202.Remove(g)  # projected microSD rectangle
        elif isinstance(g, p.PCB_SHAPE) and x0 < gap[0] and x1 > gap[1] and y1 - y0 < 0.5:
            y = p.ToMM(g.GetStart().y)
            right = g.Duplicate()
            g.SetStart(vec(x0 + p.ToMM(g.GetWidth()) / 2, y))
            g.SetEnd(vec(gap[0], y))
            right.SetStart(vec(gap[1], y))
            right.SetEnd(vec(x1 - p.ToMM(g.GetWidth()) / 2, y))
            u202.Add(right)

    # Rip up foreign-net copper the new pads obstruct; route-ili9341.py reroutes it.
    new_pads = list(j702.Pads()) + list(jp1.Pads()) + list(jp2.Pads())
    for f in board.GetFootprints():
        if f.GetReference() in ('H702', 'H704'):
            new_pads += list(f.Pads())
    ripped = [t for t in board.GetTracks() if obstructs(t, new_pads)]
    for t in ripped:
        board.Remove(t)

    board.Save(str(PCB))
    print('Placed J702 at (%.2f, %.2f), JP701/JP702 on the rear' % (J702_X, J702_PIN1_Y))
    print('Slotted', ', '.join('%s by %.2f mm' % kv for kv in slots.items()))
    print('Ripped up %d obstructing track segments/vias' % len(ripped))


if __name__ == '__main__':
    main()
