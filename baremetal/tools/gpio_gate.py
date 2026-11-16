"""Host runner for the sixteen-transition bidirectional hardware GPIO gate."""

import datetime
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
cfg = json.loads((ROOT / 'devices.json').read_text())
if not cfg.get('gpioWiringConfirmed'):
    raise SystemExit('GPIO wiring not confirmed; no commands issued')
adb = ['adb', '-s', cfg['referenceAdbSerial']]
subprocess.run(
    adb + ['push', str(ROOT / 'tools/ref_gpio_gate.py'), '/tmp/baremetal-gpio-gate.py'],
    check=True,
    capture_output=True,
)
r = subprocess.run(
    adb + ['shell', 'python3 /tmp/baremetal-gpio-gate.py'],
    capture_output=True,
    text=True,
    timeout=30,
)
lines = [
    line.split(' ', 1)[1] for line in r.stdout.splitlines() if line.startswith('@@GPIO_REPORT ')
]
report = (
    json.loads(lines[0]) if len(lines) == 1 else {'passed': False, 'error': 'No unique REF result'}
)
report.update(stdout=r.stdout, stderr=r.stderr, exitCode=r.returncode)
report['passed'] = (
    report['passed']
    and r.returncode == 0
    and report.get('release') == '@@GPIO_RELEASED'
    and not report.get('cleanupError')
)
folder = ROOT / 'logs/phase-4'
folder.mkdir(parents=True, exist_ok=True)
p = folder / (
    'gpio-gate-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json'
)
p.write_text(json.dumps(report, indent=2) + '\n')
print(
    json.dumps(
        {
            'passed': report['passed'],
            'transitions': len(report.get('records', [])),
            'evidence': str(p),
        },
        indent=2,
    )
)
sys.exit(0 if report['passed'] else 1)
