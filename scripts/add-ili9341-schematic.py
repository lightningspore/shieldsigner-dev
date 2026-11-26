#!/usr/bin/env python3
"""Add the alternate 14-pin ILI9341 display socket (J702) to the LCD sheet.

J702 follows the common 14-pin "red" SPI TFT order (LCDwiki MSP2806/MSP2807 and
equivalents): VCC GND CS RESET DC MOSI SCK LED MISO T_CLK T_CS T_DIN T_DO T_IRQ.
It shares every LCD net with J701; only one display is fitted, and J702 is
DNP in the default HOTHMI build. JP701 (closed)
feeds J702 VCC from LCD_3V3; JP702 (open) is the 5 V alternative for modules
whose on-board 3.3 V regulator needs headroom. Never close both.

Idempotent: refuses to run twice. Run once, then validate with kicad:check.
"""

import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / 'kicad/lcd_module.kicad_sch'
LIB = ROOT / 'kicad/ShieldSigner.kicad_sym'
RPI = ROOT / 'kicad/rpi_interface.kicad_sch'
PATH = '/8c9c54c8-0cfa-43ef-b1ba-3cda1bca877f/4fead130-596d-4414-bb04-d5dfc4d319ed'
PROJECT = 'SeedSigner-Plus-smartcard-pico'

PINS = ['VCC', 'GND', 'CS', 'RESET', 'DC', 'MOSI', 'SCK', 'LED', 'MISO',
        'T_CLK', 'T_CS', 'T_DIN', 'T_DO', 'T_IRQ']
NETS = ['LCD_ALT_VCC', 'GND', 'RPI_SPI_CS', 'LCD_RST', 'LCD_DC', 'LCD_MOSI', 'LCD_SCLK',
        'RPI_BACKLIGHT', None, None, None, None, None, None]


def uid():
    return str(uuid.uuid4())


def font():
    return '(effects (font (size 1.27 1.27)))'


def symbol_14(prefix=''):
    top = 2.54 * 6.5  # pins at +16.51 .. -16.51
    pins = ''.join(
        f'(pin passive line (at -10.16 {top - 2.54 * i:.2f} 0) (length 2.54) '
        f'(name "{name}" {font()}) (number "{i + 1}" {font()}))'
        for i, name in enumerate(PINS)
    )
    return (
        f'(symbol "{prefix}LCD_SPI_14" (in_bom yes) (on_board yes) '
        f'(property "Reference" "J" (at 0.0 20.32 0) {font()})'
        f'(property "Value" "LCD_SPI_14" (at 0.0 -20.32 0) {font()})'
        f'(symbol "LCD_SPI_14_0_1" (rectangle (start -7.62 19.05) (end 7.62 -19.05) '
        f'(stroke (width 0) (type default)) (fill (type background))))'
        f'(symbol "LCD_SPI_14_1_1" {pins}))'
    )


def block(text, start):
    """Return the balanced s-expression starting at index `start`."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError('unbalanced')


def label(name, x, y, angle):
    justify = 'right' if angle == 180 else 'left'
    return (
        f'(global_label "{name}" (shape bidirectional) (at {x:.5f} {y:.5f} {angle}) '
        f'(effects (font (size 1.27 1.27)) (justify {justify})) (uuid "{uid()}") '
        f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x:.5f} {y:.5f} 0) '
        f'(effects (font (size 1 1)) (hide yes))))'
    )


def instance(lib_id, ref, value, footprint, x, y, pins, extra='', dnp=False):
    pin_text = ''.join(f'(pin "{n}" (uuid "{uid()}"))' for n in pins)
    return (
        f'(symbol (lib_id "{lib_id}") (at {x:.5f} {y:.5f} 0) (unit 1) (body_style 1) '
        f'(in_bom yes) (on_board yes) (dnp {"yes" if dnp else "no"}) (uuid "{uid()}") '
        f'(property "Reference" "{ref}" (at {x:.5f} {y - 3.81:.5f} 0) {font()})'
        f'(property "Value" "{value}" (at {x:.5f} {y + 3.81:.5f} 0) (effects (font (size 1.27 1.27)) (hide yes)))'
        f'(property "Footprint" "{footprint}" (at {x:.5f} {y:.5f} 0) (effects (font (size 1.27 1.27)) (hide yes)))'
        f'{extra} {pin_text} (instances (project "{PROJECT}" (path "{PATH}" (reference "{ref}") (unit 1)))))'
    )


def text(body, x, y, size=1.27, bold=False):
    b = ' (bold yes)' if bold else ''
    body = body.replace('\n', '\\n')
    return (f'(text "{body}" (at {x} {y} 0) (effects (font (size {size} {size}){b}) '
            f'(justify left)) (uuid "{uid()}"))')


def main():
    sheet = SHEET.read_text()
    if 'J702' in sheet:
        raise SystemExit('J702 already present; nothing to do')
    rpi = RPI.read_text()
    jumpers = [block(rpi, rpi.index(f'(symbol "Jumper:Jumper_2_Small_{kind}"'))
               for kind in ('Bridged', 'Open')]
    jumpers = [re.sub(r'\s+', ' ', j) for j in jumpers]

    # Library cache: add the 14-pin symbol and both jumper symbols.
    marker = '(lib_symbols '
    at = sheet.index(marker) + len(marker)
    sheet = sheet[:at] + symbol_14('ShieldSigner:') + ''.join(jumpers) + sheet[at:]

    items = []
    jx, jy = 254.0, 76.2
    items.append(instance('ShieldSigner:LCD_SPI_14', 'J702', 'ILI9341 SPI 14-pin',
                          'ShieldSigner:LCD_SPI_14_ILI9341', jx, jy,
                          [str(i + 1) for i in range(14)], dnp=True))
    for i, net in enumerate(NETS):
        y = jy - 16.51 + 2.54 * i
        x = jx - 10.16
        if net:
            items.append(label(net, x, y, 180))
        else:
            items.append(f'(no_connect (at {x:.5f} {y:.5f}) (uuid "{uid()}"))')

    # VCC selection: JP701 closed (LCD_3V3), JP702 open (+5V).
    for ref, kind, source, y in (('JP701', 'Bridged', 'LCD_3V3', 127.0),
                                 ('JP702', 'Open', '+5V', 134.62)):
        x = 233.68
        fp = f'Jumper:SolderJumper-2_P1.3mm_{kind}_RoundedPad1.0x1.5mm'
        items.append(instance(f'Jumper:Jumper_2_Small_{kind}', ref, f'Jumper_2_Small_{kind}',
                              fp, x, y, ['1', '2']))
        items.append(label(source, x - 2.54, y, 180))
        items.append(label('LCD_ALT_VCC', x + 2.54, y, 0))

    items.append(text('J702: ALTERNATE 14-PIN ILI9341', 233.68, 48.26, 1.5, True))
    items.append(text(
        'Fit J701 OR J702, never both. J702 is DNP\nin the default (HOTHMI) build. J702 matches 14-pin SPI TFT modules:\n'
        'VCC GND CS RESET DC MOSI SCK LED MISO + touch.\n'
        'MISO and touch pins are not connected.\n'
        'Firmware must select the ILI9341 driver.', 220.98, 99.06))
    items.append(text(
        'J702 VCC STRAP\nJP701 closed / JP702 open: LCD_3V3 (default).\n'
        'JP702 closed / JP701 open: +5V, for modules\nwith an on-board 3.3 V regulator.\n'
        'Never close both.', 220.98, 142.24))

    end = sheet.rindex('(embedded_fonts no)')
    sheet = sheet[:end] + '\n'.join(items) + '\n' + sheet[end:]
    for old, new in (
        ('(title "Eight-pin SPI display and regulator")', '(title "SPI display sockets and regulator")'),
        ('(text "Eight-pin SPI display and dedicated 3.3 V supply"',
         '(text "SPI display sockets and dedicated 3.3 V supply"'),
        ('(text "J701 is the module header, not a 40-pin bare-panel FPC.',
         '(text "J701 (HOTHMI / Waveshare order) or J702 (14-pin ILI9341 order) is the module '
         'header, not a 40-pin bare-panel FPC.'),
        ('(property "Reference" "J702" (at 254.00000 72.39000 0)',
         '(property "Reference" "J702" (at 254.00000 55.88000 0)'),
    ):
        sheet = sheet.replace(old, new)
    SHEET.write_text(sheet)

    lib = LIB.read_text()
    if '"LCD_SPI_14"' not in lib:
        close = lib.rindex(')')
        lib = lib[:close] + symbol_14() + '\n' + lib[close:]
        LIB.write_text(lib)
    print('Added J702, JP701, JP702 to', SHEET.relative_to(ROOT))


if __name__ == '__main__':
    main()
