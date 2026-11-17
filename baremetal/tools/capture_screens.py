# SPDX-License-Identifier: MIT
"""Capture documentation screenshots from the device's native LCD framebuffer.

Drives the real ported Views on DUT1 with PUBLIC data (seed abandon x11 about,
the public PSBT fixture from micropython/psbt_flow_gate.py) and saves each
screen as it is drawn: the exact RGB565 framebuffer, not a mock-up. RAM-only:
the build must already be loaded (tools/usb_only_gate.py).

  uv run --python 3.13 --with pyserial==3.5 --with pillow \
      python baremetal/tools/capture_screens.py [--scale 2]
"""

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'docs/images/screens'

DEVICE = r'''
import ui, gc, json
from seedsigner_port.seed import Seed
from seedsigner_port.renderer import Renderer
from seedsigner_port.controller import Controller
from seedsigner_port.navigation import Destination
from seedsigner_port.settings_store import Settings, SettingsConstants as C
from embit import psbt


class Stop(Exception):
    pass


def pulse(key):
    ui.key(key, True)
    ui.key(key, False)


def dump(name):
    for _ in range(5):
        ui.tick()
    raw = ui.framebuffer()
    print('@@SHOT_BEGIN', name)
    for row in range(240):
        print(raw[row * 480:(row + 1) * 480].hex())
    print('@@SHOT_END', name)


class Driver:
    def __init__(self, plan):
        self.plan = list(plan)

    def __getattr__(self, name):
        return getattr(ui, name)

    def render(self, builder, encoded):
        ui.render(builder, encoded)
        if builder == 'loading_spinner_screen' or not self.plan:
            return
        want, name, then = self.plan[0]
        if want != builder:
            return
        self.plan.pop(0)
        if name:
            dump(name)
        if then is None:
            raise Stop()
        then()


def run(view, plan, setup=None, **args):
    Renderer._instance = None
    Renderer.configure_instance(backend=Driver(plan))
    Controller._instance = None
    c = Controller.get_instance()
    seed = Seed(['abandon'] * 11 + ['about'])
    c.storage.set_pending_seed(seed)
    c.storage.finalize_pending_seed()
    if setup:
        setup(c, seed)
    try:
        d = Destination(view, view_args=args)
        for _ in range(8):
            d = d.run()
    except Stop:
        pass
    finally:
        c.discard_seed(seed)
        gc.collect()


ui.init()
ui.overlays(0, 0)
settings = Settings.get_instance()
settings.set_value(C.SETTING__QR_BRIGHTNESS_TIPS, C.OPTION__DISABLED, save=False)
settings.set_value(C.SETTING__QR_BRIGHTNESS, 255, save=False)

from seedsigner_port.view_core import MainMenuView
from seedsigner_port.camera_entropy_views import ToolsMenuView
from seedsigner_port.view_seed import SeedOptionsView
from seedsigner_port.view_psbt import PSBTOverviewView
from seedsigner_port import view_tools_extra as X

run(MainMenuView, [('main_menu_screen', 'home', None)])
run(ToolsMenuView, [('button_list_screen', 'tools', None)])
run(SeedOptionsView, [('button_list_screen', 'seed-options', None)],
    setup=None, seed=Seed(['abandon'] * 11 + ['about']))


def load_psbt(c, seed):
    wire = bytes.fromhex(PUBLIC_FIXTURE['wireHex'])
    c.psbt = psbt.PSBT.parse(wire)
    c.psbt_seed = seed
    c.psbt_parser = None
    c.psbt_sign_with_satochip = False


run(PSBTOverviewView, [('psbt_overview_screen', 'psbt-overview', lambda: pulse(10)),
                       ('psbt_math_screen', 'psbt-math', None)], setup=load_psbt)
run(X.ToolsPasswordReviewView, [('button_list_screen', 'password', None)],
    password='skillet entity numbness affected reveler', password_type='diceware_eff_long',
    strength_bits=64, entropy_source='bip85')
run(X.ToolsTextQRFullScreenModeView, [('qr_display_screen', 'address-qr', None)],
    text='bc1qd30z5a5e50jtgx28rvt64483tq65r9pkj623wh')
print('@@SHOTS_DONE')
'''


def fixture():
    text = (BASE / 'micropython/psbt_flow_gate.py').read_text()
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'PUBLIC_FIXTURE':
            return ast.get_source_segment(text, node)
    raise SystemExit('PUBLIC_FIXTURE not found in psbt_flow_gate.py')


def rgb565(row_hex):
    data = bytes.fromhex(row_hex)
    out = bytearray()
    for i in range(0, len(data), 2):
        v = (data[i] << 8) | data[i + 1]
        out += bytes(((v >> 11) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31))
    return bytes(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--scale', type=int, default=2)
    ap.add_argument('--timeout', type=int, default=200)
    a = ap.parse_args()
    script = BASE / 'build/capture_screens_device.py'
    script.parent.mkdir(exist_ok=True)
    script.write_text(fixture() + '\n' + DEVICE)
    run = subprocess.run(
        [
            sys.executable,
            str(BASE / 'tools/usb_console.py'),
            str(script),
            '--serial',
            'rv1103-dut1',
            '--timeout',
            str(a.timeout),
        ],
        capture_output=True,
        text=True,
        cwd=BASE,
    )
    evidence = re.search(r'logs/phase-11/usb-\S+', run.stdout + run.stderr)
    if not evidence:
        raise SystemExit(run.stdout + run.stderr)
    serial = (BASE / evidence.group(0) / 'serial.bin').read_bytes().decode('latin-1')
    shots = re.findall(r'@@SHOT_BEGIN (\S+)\r?\n(.*?)@@SHOT_END \1', serial, re.S)
    if '@@SHOTS_DONE' not in serial:
        tail = [l for l in serial.splitlines() if 'Error' in l][-3:]
        print('warning: capture incomplete', tail)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, body in shots:
        rows = [r for r in body.split() if len(r) == 960]
        if len(rows) != 240:
            print('skip', name, len(rows), 'rows')
            continue
        img = Image.frombytes('RGB', (240, 240), b''.join(rgb565(r) for r in rows))
        if a.scale > 1:
            img = img.resize((240 * a.scale, 240 * a.scale), Image.NEAREST)
        path = OUT / (name + '.png')
        img.save(path, optimize=True)
        print('saved', path.relative_to(BASE))


if __name__ == '__main__':
    main()
