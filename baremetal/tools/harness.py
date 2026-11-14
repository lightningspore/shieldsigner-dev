"""RAM-only DUT harness. Captures REF UART before issuing the sole load command: db."""
import argparse
import base64
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image', required=True, type=Path)
    p.add_argument('--build', nargs='+', help='Build argv, executed in baremetal before loading')
    p.add_argument('--phase', type=int, default=1)
    p.add_argument('--timeout', type=float, default=15)
    p.add_argument('--baud', type=int, help='Override provisional capture baud for diagnosis')
    p.add_argument('--pass-pattern', default=r'@@PASS[^\r\n]*')
    args = p.parse_args()
    if args.timeout <= 0:
        p.error('--timeout must be positive')
    re.compile(args.pass_pattern)
    cfg = json.loads((ROOT/'devices.json').read_text())
    if not cfg['bridgeWiringConfirmed']:
        p.error('Physical bridge wiring is not confirmed')
    folder = ROOT/'logs'/f'phase-{args.phase}'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder.mkdir(parents=True)
    report = {'phase': args.phase, 'scope': 'RAM-only db; no storage commands', 'build': args.build}
    def run(argv, timeout=30):
        started=time.monotonic()
        env = os.environ.copy()
        env.pop('RKDEVELOPTOOL_RAM_LOCATION', None)
        if len(argv) > 1 and str(argv[0]).endswith('/rkdeveloptool') and argv[1] == 'db':
            env['RKDEVELOPTOOL_RAM_LOCATION'] = cfg['dutUsbLocation']
        r = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout, env=env)
        return {'argv': list(map(str, argv)), 'exitCode': r.returncode,
                'wallTimeSeconds':time.monotonic()-started,
                'stdout': r.stdout.decode(errors='replace'), 'stderr': r.stderr.decode(errors='replace')}
    if args.build:
        report['buildResult'] = run(args.build, 300)
        if report['buildResult']['exitCode']:
            (folder/'result.json').write_text(json.dumps(report, indent=2)+'\n')
            return 2
    image = args.image.resolve()
    report['image'] = str(image)
    report['sha256'] = hashlib.sha256(image.read_bytes()).hexdigest()
    manifest = image.with_name('hello-manifest.json')
    if manifest.exists():
        content = manifest.read_bytes()
        parsed = json.loads(content)
        if parsed.get('files', {}).get('build/hello-download.bin') == report['sha256']:
            (folder/'build-manifest.json').write_bytes(content)
            report['buildManifestSha256'] = hashlib.sha256(content).hexdigest()
            target_features=set(parsed.get('features','').split(','))
            if target_features & {'usb-only','bench-ui','mini-pcb-ui','app-ui'} or parsed.get('usbSerial') not in (None,'rv1103-dev-001'):
                report['error']='DUT1/app pin profile rejected by wired DUT0 harness; build native-ui or use the explicit DUT1 loader'
                (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')
                raise SystemExit(report['error'])
    tool = str(ROOT/'.tools/rkdeveloptool/rkdeveloptool')
    enumeration_start=time.monotonic()
    replug_reported=False
    while True:
        devices = run([tool, 'ld'])
        lines = [x for x in devices['stdout'].splitlines() if 'DevNo=' in x]
        targets = [line for line in lines if re.search(r'Vid=0x2207,Pid=0x110c,LocationID=' + re.escape(cfg['dutUsbLocation']) + r'\s+Maskrom', line)]
        if devices['exitCode'] == 0 and len(targets) == 1:
            report['maskromBefore'] = devices
            break
        if time.monotonic()-enumeration_start<5:
            time.sleep(0.5)
        else:
            if not replug_reported:
                print('Replug DUT only, leaving its microSD out; waiting for configured DUT location in maskrom.', flush=True)
                replug_reported=True
            time.sleep(5)
    adb = ['adb', '-s', cfg['referenceAdbSerial']]
    check = run(adb+['get-state'])
    if check['exitCode'] or check['stdout'].strip() != 'device':
        raise RuntimeError('Configured REF is not reachable')
    push = run(adb+['push', str(ROOT/'tools/capture_uart.py'), '/tmp/baremetal-capture.py'])
    if push['exitCode']:
        raise RuntimeError(push)
    report['baud'] = args.baud or cfg['provisionalBaud']
    remote = 'python3 -u /tmp/baremetal-capture.py '+shlex.join([cfg['referenceUart'], str(report['baud']), str(args.timeout)])
    capture_started=time.monotonic()
    milestones={}
    proc = subprocess.Popen(adb+['shell', remote], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ready = threading.Event()
    transport_errors = []
    def copy(stream, filename, notify=False):
        recent=b''
        with (folder/filename).open('wb') as out:
            while True:
                data = stream.readline()
                if not data:
                    break
                if not notify:
                    if data.strip() == b'@@CAPTURE_READY':
                        ready.set()
                    elif data.startswith(b'@@DATA '):
                        try:
                            decoded=base64.b64decode(data.split()[1], validate=True)
                            out.write(decoded); out.flush()
                            recent=(recent+decoded)[-4096:]
                            for name,marker in [('hello',b'@@PASS hello'),('heap',b'@@PASS heap'),('irqStart',b'@@IRQ starting'),('timer',b'@@PASS timer-irq'),('repl',b'@@REPL_READY')]:
                                if name not in milestones and marker in recent:
                                    milestones[name]=time.monotonic()-capture_started
                        except (ValueError, IndexError) as exc:
                            transport_errors.append(str(exc))
                    else:
                        with (folder/'transport.txt').open('ab') as transport:
                            transport.write(data)
                else:
                    out.write(data); out.flush()
    readers = [threading.Thread(target=copy, args=(proc.stdout, 'serial.bin'), daemon=True),
               threading.Thread(target=copy, args=(proc.stderr, 'capture-stderr.txt', True), daemon=True)]
    for reader in readers: reader.start()
    try:
        if not ready.wait(8):
            report['error'] = 'UART capture did not report ready; no download issued'
            (folder/'result.json').write_text(json.dumps(report, indent=2)+'\n')
            raise RuntimeError(report['error'])
        report['download'] = run([tool, 'db', str(image)], 30)
        proc.wait(timeout=args.timeout+10)
    except Exception as exc:
        report['error'] = str(exc)
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
        for reader in readers: reader.join(timeout=5)
    serial = (folder/'serial.bin').read_bytes().decode('utf-8', errors='replace')
    (folder/'serial.txt').write_text(serial)
    report['captureExitCode'] = proc.returncode
    report['uartObservedSecondsFromCaptureStart']=milestones
    report['passPattern'] = args.pass_pattern
    report['matched'] = bool(re.search(args.pass_pattern, serial))
    report['failedMarker'] = '@@FAIL' in serial
    report['transportErrors'] = transport_errors
    report['passed'] = (report.get('download', {}).get('exitCode') == 0 and proc.returncode == 0
                        and not report.get('error') and not transport_errors
                        and report['matched'] and not report['failedMarker'])
    (folder/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'passed': report['passed'], 'evidence': str(folder), 'serialBytes': len((folder/'serial.bin').read_bytes()), 'serialPreview': serial[:200]}, indent=2))
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())
