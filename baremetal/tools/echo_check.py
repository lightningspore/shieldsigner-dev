"""Check DUT interrupt-only UART echo via REF, with byte-exact evidence."""

import base64
import datetime
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
cfg = json.loads((ROOT / 'devices.json').read_text())
payload = b'irq-echo:0123456789abcdefghijklmnopqrstuvwxyz\r\n'
script = '''import os,termios,select,time,base64
f=os.open(%r,os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
a=termios.tcgetattr(f)
a[0]=a[1]=a[3]=0; a[2]=termios.CS8|termios.CLOCAL|termios.CREAD
a[4]=a[5]=termios.B115200; a[6][termios.VMIN]=0; a[6][termios.VTIME]=0
termios.tcsetattr(f,termios.TCSANOW,a); termios.tcflush(f,termios.TCIFLUSH)
payload=%r
os.write(f,payload); termios.tcdrain(f)
received=b''; end=time.monotonic()+3
while time.monotonic()<end and len(received)<len(payload):
 if select.select([f],[],[],0.1)[0]: received+=os.read(f,4096)
os.close(f)
print('@@ECHO '+base64.b64encode(received).decode())
''' % (cfg['referenceUart'], payload)
r = subprocess.run(
    ['adb', '-s', cfg['referenceAdbSerial'], 'shell', 'python3 -c ' + shlex.quote(script)],
    capture_output=True,
    text=True,
    timeout=10,
)
lines = [
    line.strip().split(' ', 1)[1] for line in r.stdout.splitlines() if line.startswith('@@ECHO ')
]
received = base64.b64decode(lines[0]) if len(lines) == 1 else b''
report = {
    'passed': r.returncode == 0 and received == payload,
    'sentBase64': base64.b64encode(payload).decode(),
    'receivedBase64': base64.b64encode(received).decode(),
    'stdout': r.stdout,
    'stderr': r.stderr,
    'exitCode': r.returncode,
    'note': 'cpu-base payload has no polling RX path; UART bytes are echoed only by INTID 59 handler.',
}
folder = ROOT / 'logs/phase-3'
path = folder / (
    'echo-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json'
)
path.write_text(json.dumps(report, indent=2) + '\n')
print(
    json.dumps(
        {'passed': report['passed'], 'bytes': len(received), 'evidence': str(path)}, indent=2
    )
)
sys.exit(0 if report['passed'] else 1)
