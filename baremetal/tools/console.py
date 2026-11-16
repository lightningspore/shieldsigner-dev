# SPDX-License-Identifier: MIT
"""Run one script through the actual UART REPL and preserve private local evidence."""

import argparse
import base64
import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('script', type=Path)
parser.add_argument('--timeout', type=float, default=30)
args = parser.parse_args()
script = args.script.read_bytes()
cfg = json.loads((ROOT / 'devices.json').read_text())
folder = (
    ROOT
    / 'logs/phase-9'
    / ('console-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
)
folder.mkdir(parents=True)
adb = ['adb', '-s', cfg['referenceAdbSerial']]
subprocess.run(
    adb + ['push', str(ROOT / 'tools/console_uart.py'), '/tmp/baremetal-console.py'],
    check=True,
    capture_output=True,
)
token = hashlib.sha256(script).hexdigest()[:16]
command = shlex.join(
    [
        'python3',
        '/tmp/baremetal-console.py',
        cfg['referenceUart'],
        base64.b64encode(script).decode(),
        token,
        str(args.timeout),
    ]
)
result = subprocess.run(adb + ['shell', command], capture_output=True, timeout=args.timeout + 10)
(folder / 'transport.txt').write_bytes(result.stdout)
serial = b''.join(
    base64.b64decode(line.removeprefix(b'@@DATA '), validate=True)
    for line in result.stdout.splitlines()
    if line.startswith(b'@@DATA ')
)
(folder / 'serial.bin').write_bytes(serial)
(folder / 'stderr.txt').write_bytes(result.stderr)
text = serial.decode(errors='replace')
report = {
    'script': str(args.script),
    'scriptSha256': hashlib.sha256(script).hexdigest(),
    'exitCode': result.returncode,
    'completed': f'\n@@CONSOLE_DONE {token}' in text,
    'evidence': str(folder),
}
(folder / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
print(text)
print(json.dumps(report, indent=2))
raise SystemExit(0 if result.returncode == 0 and report['completed'] else 1)
