# SPDX-License-Identifier: MIT
"""RAM-only fast boot observation with REF GPIO timing; no storage operations."""

import base64
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
cfg = json.loads((ROOT / 'devices.json').read_text())
adb = ['adb', '-s', cfg['referenceAdbSerial']]
folder = (
    ROOT
    / 'logs/phase-10'
    / ('gpio-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
)
folder.mkdir(parents=True)
subprocess.run(
    adb + ['push', str(ROOT / 'tools/ref_boot_capture.py'), '/tmp/bm-boot-capture.py'],
    check=True,
    capture_output=True,
)
proc = subprocess.Popen(
    adb + ['shell', 'python3 -u /tmp/bm-boot-capture.py /dev/ttyS3 18 --reset'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
# REF either reports ready or exits at its finite preflight; no second UART reader.
first = proc.stdout.readline()
if first.strip() != b'@@BOOT_CAPTURE_READY':
    out, err = proc.communicate(timeout=25)
    raise SystemExit(repr(first + out + err))
tool = str(ROOT / '.tools/rkdeveloptool/rkdeveloptool')
try:
    for _ in range(30):
        probe = subprocess.run([tool, 'ld'], cwd=ROOT, capture_output=True, text=True, timeout=5)
        lines = [line for line in probe.stdout.splitlines() if 'DevNo=' in line]
        if len(lines) == 1 and re.search(r'Vid=0x2207,Pid=0x110c.*Maskrom', lines[0]):
            break
        time.sleep(0.1)
    else:
        raise RuntimeError('DUT did not return to maskrom; no download issued')
    image = ROOT / 'build/hello-download.bin'
    load = subprocess.run([tool, 'db', str(image)], cwd=ROOT, capture_output=True, timeout=30)
    out, err = proc.communicate(timeout=30)
finally:
    if proc.poll() is None:
        proc.terminate()
        proc.communicate(timeout=5)
(folder / 'transport.bin').write_bytes(first + out)
(folder / 'stderr.txt').write_bytes(err)
serial = b''
reports = []
for line in out.splitlines():
    if line.startswith(b'@@DATA '):
        serial += base64.b64decode(line.split()[1], validate=True)
    elif line.startswith(b'@@BOOT_GPIO '):
        reports.append(json.loads(line.split(b' ', 1)[1]))
(folder / 'serial.bin').write_bytes(serial)
report = {
    'scope': 'RAM-only db; independently polled REF GPIO, not SD/power-on timing',
    'imageSha256': hashlib.sha256(image.read_bytes()).hexdigest(),
    'downloadExitCode': load.returncode,
    'captureExitCode': proc.returncode,
    'gpio': reports[0] if len(reports) == 1 else None,
}
text = serial.decode(errors='replace')
match = re.search(r'@@BOOT payload_entry_to_repl_us=(\d+) excludes_rom_ddr=1', text)
report['dutPayloadToReplUs'] = int(match[1]) if match else None
edges = report['gpio']['edges'] if report['gpio'] else []
report['refHighPulseUs'] = (
    (edges[1]['timeNs'] - edges[0]['timeNs']) / 1000
    if len(edges) == 2 and [row['level'] for row in edges] == [1, 0]
    else None
)
report['passed'] = (
    load.returncode == 0
    and proc.returncode == 0
    and b'@@REPL_READY' in serial
    and b'@@FAIL' not in serial
    and report['dutPayloadToReplUs'] is not None
    and report['refHighPulseUs'] is not None
    and abs(report['refHighPulseUs'] - report['dutPayloadToReplUs']) < 2000
    and len(report['gpio']['highPulseMaxSampleGapsNs']) == 1
    and report['gpio']['highPulseMaxSampleGapsNs'][0] < 2_000_000
)
(folder / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'evidence': str(folder), **report}, indent=2))
raise SystemExit(0 if report['passed'] else 1)
