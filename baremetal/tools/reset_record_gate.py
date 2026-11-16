# SPDX-License-Identifier: MIT
"""RAM-only deliberate DUT1 faults; reload and inspect retained numeric evidence."""

import ast, datetime, hashlib, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / 'build/hello-manifest.json').read_text())
    if manifest['features'] != 'app-ui,fault-probe' or manifest['usbSerial'] != 'rv1103-dut1':
        raise SystemExit('Build explicit DUT1 diagnostic image first')
    image = ROOT / 'build/hello-download.bin'
    digest = hashlib.sha256(image.read_bytes()).hexdigest()
    if digest != manifest['files']['build/hello-download.bin']:
        raise SystemExit('Image changed')
    folder = (
        ROOT
        / 'logs/phase-12'
        / (
            'reset-record-'
            + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        )
    )
    folder.mkdir(parents=True)
    shutil.copyfile(image, folder / 'probe-download.bin')
    shutil.copyfile(ROOT / 'target/armv7a-none-eabi/release/rv1103-bringup', folder / 'probe.elf')
    (folder / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    report = {
        'passed': False,
        'scope': 'DUT1 RAM-only deliberate diagnostics; no storage or REF/DUT0 writes',
        'downloadSha256': digest,
        'cases': [],
    }

    def console(name, code, expected=True):
        script = folder / (name + '.py')
        script.write_text(code)
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / 'tools/usb_console.py'),
                str(script),
                '--serial',
                'rv1103-dut1',
                '--timeout',
                '10',
            ],
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
        (folder / (name + '.txt')).write_text(output)
        if expected and result.returncode:
            raise RuntimeError(name + ' native script failed')
        return output, result.returncode

    def maskrom():
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            env = os.environ.copy()
            env.pop('RKDEVELOPTOOL_RAM_LOCATION', None)
            value = subprocess.run(
                [str(ROOT / '.tools/rkdeveloptool/rkdeveloptool'), 'ld'],
                capture_output=True,
                text=True,
                env=env,
            )
            if re.search(r'Vid=0x2207,Pid=0x110c,LocationID=101\s+Maskrom', value.stdout):
                return
            time.sleep(0.1)
        raise RuntimeError('Expected DUT1 fault reset did not reach maskrom101')

    try:
        console(
            'corrupt',
            "import machine\nassert machine.fault_probes_enabled()\nmachine.clear_reset_record()\nmachine.fault_probe(4)\nassert machine.last_reset() is None\nmachine.clear_reset_record()\nprint('@@PASS damaged-record-rejected')\n",
        )
        report['damagedRecordRejected'] = True
        for kind, reason in ((1, 5), (2, 4), (3, 3)):
            marker = 0x1461000 + kind
            console(
                'arm-' + str(kind),
                f"import machine\nassert machine.fault_probes_enabled()\nmachine.clear_reset_record()\nmachine.set_reset_marker({marker})\nassert machine.last_reset() is None\nprint('@@ARMED', {kind})\n",
            )
            output, code = console(
                'fault-' + str(kind),
                f"import machine\nmachine.fault_probe({kind})\nraise AssertionError('Deliberate fault returned')\n",
                False,
            )
            if not code:
                raise RuntimeError('Fault unexpectedly completed normally')
            maskrom()
            print('Observed actual reset for probe', kind, flush=True)
            if hashlib.sha256(image.read_bytes()).hexdigest() != digest:
                raise RuntimeError('Diagnostic image changed during gate')
            loaded = subprocess.run(
                [sys.executable, str(ROOT / 'tools/usb_only_gate.py')],
                capture_output=True,
                text=True,
            )
            (folder / ('reload-' + str(kind) + '.txt')).write_text(loaded.stdout + loaded.stderr)
            if loaded.returncode:
                raise RuntimeError('DUT1 RAM reload failed')
            output, _ = console(
                'read-' + str(kind),
                f"import machine\nrecord=machine.last_reset()\nassert record is not None\nassert record['format_version']==1 and record['reason']=={reason} and record['marker']=={marker}\n"
                + (
                    "assert record['dfar']==0x01a00000 and record['mode']&31==0x17 and record['dfsr']&15==5\n"
                    if kind == 1
                    else ''
                )
                + "print('@@RETAINED_RECORD',record)\n",
            )
            match = re.search(r'^@@RETAINED_RECORD (.+)\r?$', output, re.M)
            if not match:
                raise RuntimeError('Missing real reset evidence')
            record = ast.literal_eval(match[1])
            case = {'probe': kind, 'record': record}
            if kind == 1:
                address = (record['lr'] & ~1) - 8
                symbols = subprocess.run(
                    [
                        'arm-none-eabi-addr2line',
                        '-f',
                        '-e',
                        str(folder / 'probe.elf'),
                        hex(address),
                    ],
                    capture_output=True,
                    text=True,
                )
                case['faultInstruction'] = hex(address)
                case['symbol'] = symbols.stdout.strip()
            report['cases'].append(case)
            print('Recovered reason', reason, 'marker', marker, flush=True)
        report['passed'] = True
    except Exception as error:
        report['error'] = str(error)
    finally:
        (folder / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
        print('Evidence:', folder)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
