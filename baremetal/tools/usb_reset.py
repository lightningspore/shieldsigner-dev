# SPDX-License-Identifier: MIT
"""Warm-reset the configured app DUT through its unique USB console, never UART."""

import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import time
import serial
from serial.tools import list_ports

root = Path(__file__).resolve().parents[1]
cfg = json.loads((root / 'devices.json').read_text())
identity = cfg['appDutUsbSerial']
location = cfg['appDutUsbLocation']
ports = [
    p for p in list_ports.comports() if (p.vid, p.pid, p.serial_number) == (0x1209, 3, identity)
]
if len(ports) != 1:
    raise SystemExit('Expected one app DUT USB identity; no reset issued')
folder = (
    root
    / 'logs/phase-11'
    / ('reset-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
)
folder.mkdir(parents=True)
report = {'serial': identity, 'location': location, 'passed': False}
try:
    with serial.Serial(ports[0].device, 115200, timeout=0.1, write_timeout=3, exclusive=True) as s:
        assert s.write(b'\x1d') == 1
        s.flush()
        time.sleep(0.15)
    env = os.environ.copy()
    env.pop('RKDEVELOPTOOL_RAM_LOCATION', None)
    end = time.monotonic() + 8
    while time.monotonic() < end:
        r = subprocess.run(
            [str(root / '.tools/rkdeveloptool/rkdeveloptool'), 'ld'],
            capture_output=True,
            text=True,
            env=env,
            timeout=3,
        )
        report['enumeration'] = r.stdout
        if re.search(
            r'Vid=0x2207,Pid=0x110c,LocationID=' + re.escape(location) + r'\s+Maskrom', r.stdout
        ):
            report['passed'] = True
            break
        time.sleep(0.1)
    if not report['passed']:
        raise TimeoutError('Expected app DUT did not return to maskrom')
except Exception as e:
    report['error'] = str(e)
finally:
    (folder / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    print('Evidence:', folder)
raise SystemExit(0 if report['passed'] else 1)
