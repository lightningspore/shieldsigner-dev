#!/usr/bin/env python3
"""Independently check manufacturer pin assignments against the native pill PCB."""
import collections
import hashlib
import json
import runpy
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sx = runpy.run_path(str(ROOT / 'scripts/kicad-sexpr.py'))
one, children = sx['one'], sx['children']
board = ROOT / 'variants/lcd-module-2.8/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
tree = sx['parse'](board.read_text())
fps = {next(p[2] for p in children(f, 'property') if p[1] == 'Reference'): f
       for f in children(tree, 'footprint')}
nets = collections.defaultdict(set)
pins = {}
for ref, fp in fps.items():
    pins[ref] = {}
    for pad in children(fp, 'pad'):
        net = one(pad, 'net')
        if not net:
            continue
        name = net[-1]
        assert pins[ref].get(pad[1], name) == name, (ref, pad[1], 'duplicate pad disagreement')
        pins[ref][pad[1]] = name
        nets[name].add(f'{ref}.{pad[1]}')

# Manufacturer physical header numbering, NOT Raspberry Pi or global GPIO numbers.
host = ['+5V', 'GND', '+3.3V', 'UART_TX', 'UART_RX', 'Net-(JP203-B)',
        'LCD_SCLK', 'LCD_MOSI', 'LCD_RST', 'LCD_DC', 'Key3', 'JoystickLeft',
        'JoystickUp', 'I2C-SDA', 'I2C-SCL', 'JoystickPress', 'JoystickDown',
        'JoystickRight', 'Key1', 'Key2', 'GND', 'unconnected-(U202-1V8(OUT)-Pad22)']
assert pins['U202'] == {str(i): n for i, n in enumerate(host, 1)}
lcd = ['RPI_BACKLIGHT', 'LCD_RST', 'LCD_DC', 'RPI_SPI_CS', 'LCD_SCLK', 'LCD_MOSI', 'GND', 'LCD_3V3']
assert pins['J701'] == {str(i): n for i, n in enumerate(lcd, 1)}
for ref in ('JP201', 'JP203', 'JP205'):
    assert 'Bridged' in fps[ref][1], ref
for ref in ('JP202', 'JP204', 'JP206'):
    assert '_Open_' in fps[ref][1], ref
graph = collections.defaultdict(set)
for ref in ('JP201', 'JP203', 'JP205'):
    a, b = pins[ref]['1'], pins[ref]['2']
    graph[a].add(b)
    graph[b].add(a)
def connected(a, b):
    seen, todo = set(), [a]
    while todo:
        n = todo.pop()
        if n == b:
            return True
        if n not in seen:
            seen.add(n)
            todo.extend(graph[n])
    return False
assert connected(pins['U202']['6'], pins['J701']['4'])
assert connected('+3.3V', pins['J701']['1'])
assert not connected('+3.3V', 'LCD_3V3')
assert not connected('RPI_SPI_CS', 'GND')
assert nets['LCD_3V3'] == {'J701.8', 'U701.5', 'C702.1', 'TP803.1'}
assert nets['+3.3V'] == {'U202.3', 'JP201.1', 'TP802.1'}
for p, n in {'1': '+5V', '2': 'GND', '3': '+5V', '5': 'LCD_3V3'}.items():
    assert pins['U701'][p] == n
for ref, rail in [('C701', '+5V'), ('C702', 'LCD_3V3')]:
    assert pins[ref] == {'1': rail, '2': 'GND'}
assert pins['J302'] == {'1': '+5V', '2': 'GND'}
for p in ('14', '15', '22'):
    assert nets[pins['U202'][p]] == {f'U202.{p}'}, p
for p, switch in [('19', 'SW506'), ('20', 'SW507')]:
    assert nets[pins['U202'][p]] == {f'U202.{p}', f'{switch}.1'}
    assert pins[switch]['2'] == 'GND'
assert pins['R602']['1'] == pins['U202']['4']
assert pins['R602']['2'] == pins['U601']['11']  # Host TX -> reader RX
assert pins['R603']['1'] == pins['U202']['5']
assert pins['R603']['2'] == pins['U601']['14']  # Host RX <- reader TX

source = ROOT / 'reference/research/firmware/io-config-efdd1cfd.json'
data = json.loads(source.read_text())
profile = next(p for p in data['models'] if p['shortname'] == 'FOX_22')
expected_buttons = {'KEY_UP': (1, 25), 'KEY_DOWN': (1, 23), 'KEY_LEFT': (1, 24),
                    'KEY_RIGHT': (0, 4), 'KEY_PRESS': (1, 22), 'KEY1': (4, 16),
                    'KEY2': (4, 17), 'KEY3': (1, 21)}
for key, (bank, line) in expected_buttons.items():
    assert profile['buttons'][key] == [f'/dev/gpiochip{bank}', line, 'pull_up']
patch = runpy.run_path(str(ROOT / 'scripts/configure-hothmi-display.py'))['configure']
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / 'io_config.json'
    path.write_bytes(source.read_bytes())
    corrected = patch(path)
    patched_once = path.read_bytes()
    patch(path)
    assert path.read_bytes() == patched_once, 'Patch must be idempotent'
    original = json.loads(source.read_text())
    fox = next(p for p in corrected['models'] if p['shortname'] == 'FOX_22')
    assert fox['display'].pop('spi_hz') == 10_000_000
    assert corrected == original, 'Patch changed unrelated configuration'

report = {
    'boardSha256': hashlib.sha256(board.read_bytes()).hexdigest(),
    'scope': 'Manufacturer pin mapping and default electrical topology; not physical qualification',
    'hostPinsChecked': 22, 'lcdPinsChecked': 8,
    'result': 'PCB mapping passes; upstream firmware SPI speed requires correction',
    'checks': ['All U202 pad nets', 'All J701 pad nets', 'Closed/open CS and BL jumper defaults',
               'Separate LCD and host 3.3V outputs', 'LDO supply/enable/decoupling',
               'Unused host I2C and 1.8V output', '1.8V button inputs have no external pull-up',
               'UART crossed through series resistors', 'Pinned FOX_22 display and button settings',
               '10MHz patch changes only FOX_22 SPI speed and is idempotent'],
    'firmware': {'commit': 'efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f',
                 'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                 'upstreamDefaultHz': 40_000_000, 'hothmiMinimumWriteCycleNs': 66,
                 'requiredHz': 10_000_000, 'patchTested': True,
                 'installedOrBuiltImageVerified': False},
    'remaining': ['LCD total current and LDO thermal qualification',
                  'Supply startup/shutdown and logic timing measurements',
                  'Actual module/header revision and orientation continuity check',
                  'Apply 10MHz patch to image; verify live SPI clock and display operation']
}
out = ROOT / 'variants/lcd-module-2.8/pinout-audit.json'
out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
