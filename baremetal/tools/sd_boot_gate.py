# SPDX-License-Identifier: MIT
"""Capture a UART warm reset from DUT's card; never download or write storage."""

import base64
import datetime
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    cfg = json.loads((ROOT / 'devices.json').read_text())
    folder = (
        ROOT
        / 'logs/phase-10'
        / ('sd-boot-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    )
    folder.mkdir(parents=True)
    adb = ['adb', '-s', cfg['referenceAdbSerial']]
    subprocess.run(
        adb + ['push', str(ROOT / 'tools/ref_boot_capture.py'), '/tmp/bm-boot-capture.py'],
        check=True,
        capture_output=True,
    )
    result = subprocess.run(
        adb + ['shell', 'python3 -u /tmp/bm-boot-capture.py /dev/ttyS3 18 --reset'],
        capture_output=True,
        timeout=30,
    )
    (folder / 'transport.txt').write_bytes(result.stdout)
    (folder / 'stderr.txt').write_bytes(result.stderr)
    serial = b''.join(
        base64.b64decode(line.split()[1], validate=True)
        for line in result.stdout.splitlines()
        if line.startswith(b'@@DATA ')
    )
    (folder / 'serial.bin').write_bytes(serial)
    reports = [
        json.loads(line.split(b' ', 1)[1])
        for line in result.stdout.splitlines()
        if line.startswith(b'@@BOOT_GPIO ')
    ]
    gpio = reports[0] if len(reports) == 1 else None
    text = serial.decode(errors='replace')
    elapsed = re.search(r'@@BOOT payload_entry_to_repl_us=(\d+)', text)
    report = {
        'scope': 'UART-requested warm reset with SD inserted; no USB download or storage command',
        'exitCode': result.returncode,
        'uartBytes': len(serial),
        'gpio': gpio,
        'payloadToInitializedInterpreterUs': int(elapsed[1]) if elapsed else None,
        'warmResetRequestToReplMarkerUs': None,
        'coldPowerOnTimingMeasured': False,
    }
    if gpio and gpio['resetRequestNs'] is not None and 'repl' in gpio['uartMarkerObservedNs']:
        report['warmResetRequestToReplMarkerUs'] = (
            gpio['uartMarkerObservedNs']['repl'] - gpio['resetRequestNs']
        ) / 1000
    # Marker ordering must prove a fresh boot, rather than a stale REPL prompt.
    markers = [b'@@RESET', b'DDR ', b'@@PASS hello', b'@@REPL_READY']
    positions = [serial.find(marker) for marker in markers]
    report['passed'] = (
        result.returncode == 0
        and all(at >= 0 for at in positions)
        and positions == sorted(positions)
        and b'@@FAIL' not in serial
        and report['warmResetRequestToReplMarkerUs'] is not None
    )
    (folder / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(serial.decode(errors='replace'))
    print(json.dumps({'evidence': str(folder), **report}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
