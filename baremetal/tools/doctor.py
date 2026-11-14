#!/usr/bin/env python3
"""Read-only Phase 0 inventory. No code download, storage writes or REF configuration."""
import argparse
import datetime
import json
import platform
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def command(argv, timeout=10):
    try:
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return {'argv': argv, 'exitCode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'argv': argv, 'exitCode': None, 'error': str(exc)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'devices.json')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    tool = ROOT/'.tools/rkdeveloptool/rkdeveloptool'
    report = {'checkedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'host': {'system': platform.system(), 'release': platform.release(), 'machine': platform.machine()},
              'tools': {n: shutil.which(n) for n in ['adb', 'arm-none-eabi-gcc', 'mise', 'uv']},
              'scope': 'Read-only access checks; no UART transmission, RAM loading or persistent device writes.'}
    report['adb'] = command(['adb', 'devices', '-l'])
    connected = {line.split()[0] for line in report['adb'].get('stdout', '').splitlines()
                 if len(line.split()) >= 2 and line.split()[1] == 'device'}
    serial = config['referenceAdbSerial']
    if serial in connected:
        report['reference'] = command(['adb', '-s', serial, 'shell',
            'printf "MODEL="; tr "\\000" "\\n" < /proc/device-tree/model; printf "KERNEL="; uname -r'])
        # Opening an existing port and reading its attributes does not configure or transmit on it.
        script = ('import os,termios,json; f=os.open("'+config['referenceUart']+'",'
                  'os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK); a=termios.tcgetattr(f); '
                  'print(json.dumps({"opened":True,"speedCodes":[a[4],a[5]]})); os.close(f)')
        import shlex
        report['uart'] = command(['adb', '-s', serial, 'shell', 'python3 -c '+shlex.quote(script)])
    report['maskrom'] = command([str(tool), 'ld'])
    lines = report['maskrom'].get('stdout', '').splitlines()
    candidates = [line for line in lines if re.search(r'Vid=0x2207,Pid=0x110c.*Maskrom', line)]
    checks = {'referenceShell': report.get('reference', {}).get('exitCode') == 0,
              'referenceUartOpens': report.get('uart', {}).get('exitCode') == 0,
              'singleDutMaskrom': len(candidates) == 1 and sum('DevNo=' in line for line in lines) == 1,
              'bridgeWiringConfirmed': config['bridgeWiringConfirmed']}
    report['checks'] = checks
    report['phase0Passed'] = all(checks.values())
    folder = ROOT/'logs/phase-0'
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = folder/f'doctor-{stamp}.json'
    destination.write_text(json.dumps(report, indent=2)+'\n')
    (folder/'latest-doctor.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'checks': checks, 'phase0Passed': report['phase0Passed'], 'evidence': str(destination)}, indent=2))
    return 0 if report['phase0Passed'] else 2

if __name__ == '__main__':
    sys.exit(main())
