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
board = ROOT / 'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
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
assert nets['LCD_3V3'] == {'J701.8', 'U701.5', 'C702.1', 'TP803.1', 'TP905.1'}
assert nets['+3.3V'] == {'U202.3', 'JP201.1', 'TP802.1', 'TP903.1'}
for p, n in {'1': '+5V', '2': 'GND', '3': '+5V', '5': 'LCD_3V3'}.items():
    assert pins['U701'][p] == n
for ref, rail in [('C701', '+5V'), ('C702', 'LCD_3V3')]:
    assert pins[ref] == {'1': rail, '2': 'GND'}
assert 'J302' not in pins
for ref,net in [('TP901','+5V'),('TP902','GND'),('TP909','GND'),('TP903','+3.3V'),('TP905','LCD_3V3'),('TP907','UART_TX'),('TP908','UART_RX')]:assert pins[ref]=={'1':net}
for p in ('14', '15', '22'):
    assert nets[pins['U202'][p]] == {f'U202.{p}'}, p
# Check every key, not only the two 1.8 V inputs. Exact net membership rejects
# accidental output/power loads, swapped key semantics and unwanted pull-ups.
button_rows = [
    ('KEY_LEFT','SW501','12','JoystickLeft',1,24,3.3),
    ('KEY_UP','SW502','13','JoystickUp',1,25,3.3),
    ('KEY_PRESS','SW503','16','JoystickPress',1,22,3.3),
    ('KEY_DOWN','SW504','17','JoystickDown',1,23,3.3),
    ('KEY_RIGHT','SW505','18','JoystickRight',0,4,3.3),
    ('KEY1','SW506','19','Key1',4,16,1.8),
    ('KEY2','SW507','20','Key2',4,17,1.8),
    ('KEY3','SW508','11','Key3',1,21,3.3),
]
for key, ref, p, net, bank, line, volts in button_rows:
    assert pins[ref] == {'1':net,'2':'GND'}, (ref,'switch must be NO contact to GND')
    assert nets[net] == {f'U202.{p}',f'{ref}.1'}, (ref,'unexpected load or swapped key')
    assert fps[ref][1].endswith(':CK_PTS636_SK25_G'), (ref,'wrong switch variant')
    assert pins['U202'][p] == net
assert pins['R602']['1'] == pins['U202']['4']
assert pins['R602']['2'] == pins['U601']['11']  # Host TX -> reader RX
assert pins['R603']['1'] == pins['U202']['5']
assert pins['R603']['2'] == pins['U601']['14']  # Host RX <- reader TX

# Connected reader channel: supplies are separate, UART directions crossed,
# and the numbered socket contacts agree with the selected native channel.
sc = '/Smartcard Interface/'
assert pins['U601']['3'] == '+5V' and pins['U601']['25'] == 'GND'
assert pins['U601']['18'] == sc+'SEC1210_VDD33'
assert pins['U601']['9'] == sc+'SEC1210_SC_VCC'
assert not connected(sc+'SEC1210_VDD33', '+3.3V')
assert not connected(sc+'SEC1210_SC_VCC', '+3.3V')
for ref, rail in [('C602','+5V'),('C603',sc+'SEC1210_VDD33'),('C604',sc+'SEC1210_SC_VCC')]:
    assert pins[ref] == {'1':rail,'2':'GND'}
    value = next(p[2] for p in children(fps[ref],'property') if p[1]=='Value')
    assert value == '1u', (ref,'reader requires nominal 1uF decoupling')
assert pins['J601'] == {'C1':sc+'SEC1210_SC_VCC','C2':sc+'SEC1210_SC_RST',
                       'C3':sc+'SEC1210_SC_CLK_PostR','C4':'unconnected-(J601-RFU-PadC4)',
                       'C5':'GND','C6':sc+'SEC1210_SC_VCC','C7':sc+'SEC1210_SC_IO',
                       'C8':'unconnected-(J601-RFU__1-PadC8)',
                       'COM':'GND','NO':sc+'SEC1210_SC_PRSNT'}
assert pins['U601']['6'] == pins['J601']['C7']
assert pins['U601']['8'] == pins['J601']['C2']
assert pins['U601']['10'] == pins['J601']['NO']
assert pins['R604'] == {'1':sc+'SEC1210_SC_CLK_PreR','2':sc+'SEC1210_SC_CLK_PostR'}
assert pins['U601']['7'] == pins['R604']['1']
assert next(p[2] for p in children(fps['U601'],'property') if p[1]=='Value') == 'SEC1210/PV-UR2'

source = ROOT / 'reference/research/firmware/io-config-efdd1cfd.json'
data = json.loads(source.read_text())
profile = next(p for p in data['models'] if p['shortname'] == 'FOX_22')
expected_buttons = {'KEY_UP': (1, 25), 'KEY_DOWN': (1, 23), 'KEY_LEFT': (1, 24),
                    'KEY_RIGHT': (0, 4), 'KEY_PRESS': (1, 22), 'KEY1': (4, 16),
                    'KEY2': (4, 17), 'KEY3': (1, 21)}
for key, (bank, line) in expected_buttons.items():
    assert profile['buttons'][key] == [f'/dev/gpiochip{bank}', line, 'pull_up']
for key, ref, p, net, bank, line, volts in button_rows:
    assert profile['buttons'][key] == [f'/dev/gpiochip{bank}',line,'pull_up']
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

# The pinned upstream embeds bank numbers in cdev paths. Verify the current
# carrier transform separately; upstream paths are not runtime device evidence.
carrier_io=runpy.run_path(str(ROOT/'scripts/configure-image-io-profile.py'))
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/'io_config.json';path.write_bytes(source.read_bytes())
    carrier_receipt=carrier_io['configure'](path,'carrier')
    generated=carrier_io['selected'](json.loads(path.read_text()))
    assert generated['display']['dc']==['/dev/gpiochip-bank1',20]
    assert generated['display']['rst']==['/dev/gpiochip-bank1',19]
    assert generated['display']['spi_hz']==10_000_000
    for key,(bank,line) in expected_buttons.items():
        assert generated['buttons'][key]==[f'/dev/gpiochip-bank{bank}',line,'pull_up']

report = {
    'boardSha256': hashlib.sha256(board.read_bytes()).hexdigest(),
    'scope': 'Manufacturer pin mapping and default electrical topology; not physical qualification',
    'hostPinsChecked': 22, 'lcdPinsChecked': 8, 'buttonsChecked': 8,
    'buttons': [{'key':key,'reference':ref,'hostPin':p,'net':net,
                 'gpioBank':bank,'runtimeDeviceAlias':f'/dev/gpiochip-bank{bank}',
                 'line':line,'domainV':volts,
                 'released':'high with domain-correct pull-up','pressed':'low',
                 'externalPullUp':False} for key,ref,p,net,bank,line,volts in button_rows],
    'result': 'PCB mapping and generated carrier profile pass; packed image and physical operation remain to verify',
    'checks': ['All U202 pad nets', 'All J701 pad nets', 'Closed/open CS and BL jumper defaults',
               'Separate LCD and host 3.3V outputs', 'LDO supply/enable/decoupling',
               'Unused host I2C and 1.8V output', 'All eight normally-open button paths and exact net membership; no external pull-ups',
               'UART crossed through series resistors',
               'Reader VDD5/VDD33/card supply separation and nominal 1uF capacitors',
               'UR2 identity, first socket numbered contacts, presence and series card clock', 'Pinned FOX_22 display and button settings',
               '10MHz patch changes only FOX_22 SPI speed and is idempotent',
               'Generated carrier profile uses kernel bank-label aliases for display and all eight buttons'],
    'firmware': {'commit': 'efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f',
                 'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                 'upstreamDefaultHz': 40_000_000, 'hothmiMinimumWriteCycleNs': 66,
                 'requiredHz': 10_000_000, 'patchTested': True,
                 'carrierIoConfigSha256':carrier_receipt['outputSha256'],
                 'gpioBankSelection':'kernel-label-aliases',
                 'installedOrBuiltImageVerified': False},
    'remaining': ['LCD total current and LDO thermal qualification',
                  'Supply startup/shutdown and logic timing measurements',
                  'Actual module/header revision and orientation continuity check',
                  'Verify packed carrier bank-label profile and 10MHz selection; measure live SPI and display operation']
}
out = ROOT / 'variants/lcd-module-2.8/pinout-audit.json'
out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
