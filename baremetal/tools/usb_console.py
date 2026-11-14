# SPDX-License-Identifier: MIT
"""Run a script through the development USB CDC REPL; never accesses storage."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import secrets
import time


def main():
    import serial
    from serial.tools import list_ports
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('script', type=Path)
    parser.add_argument('--serial', help='Exact firmware USB serial identity')
    parser.add_argument('--port', help='Exact CDC port when more than one development board is present')
    parser.add_argument('--timeout', type=float, default=30)
    args = parser.parse_args()
    if not 0 < args.timeout <= 300:
        parser.error('timeout must be in0..300 seconds')
    candidates = [p for p in list_ports.comports() if (p.vid, p.pid) == (0x1209, 0x0003) and (not args.serial or p.serial_number == args.serial)]
    if args.port:
        candidates = [p for p in candidates if p.device == args.port]
    if len(candidates) != 1:
        parser.error('Need exactly one matching development USB console; found ' + repr([p.device for p in candidates]))
    port = candidates[0]
    script = args.script.read_bytes()
    if any(c in script for c in (b'\x03', b'\x04', b'\x05', b'\x1d')):
        parser.error('script contains a console control byte')
    token = secrets.token_hex(12)
    marker = b'\n@@CONSOLE_DONE ' + token.encode() + b'\r\n'
    payload = script + b"\nprint('@@CONSOLE_DONE " + token.encode() + b"')\n\x04"
    root = Path(__file__).resolve().parents[1]
    folder = root / 'logs/phase-11' / ('usb-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    folder.mkdir(parents=True)
    report = {'transport': 'USB CDC', 'port': port.device, 'usbSerial': port.serial_number,
              'location': port.location, 'script': str(args.script),
              'scriptSha256': hashlib.sha256(script).hexdigest(), 'completed': False}
    received = bytearray()
    try:
        with serial.Serial(port.device, 115200, timeout=.1, write_timeout=3, exclusive=True) as console:
            console.dtr = True
            console.write(b'\x03\x02\r')
            time.sleep(.2)
            console.reset_input_buffer()
            console.write(b'\x05')
            deadline = time.monotonic() + 3
            while b'paste mode' not in received:
                received.extend(console.read(4096))
                if time.monotonic() >= deadline:
                    raise TimeoutError('USB REPL did not acknowledge paste mode')
            # Consume paste echo while uploading: firmware RX and TX are bounded.
            for pos in range(0, len(payload), 128):
                chunk = payload[pos:pos+128]
                if console.write(chunk) != len(chunk):
                    raise IOError('short USB script write')
                received.extend(console.read(console.in_waiting))
                time.sleep(.002)
            deadline = time.monotonic() + args.timeout
            while time.monotonic() < deadline:
                received.extend(console.read(4096))
                if marker in received:
                    report['completed'] = True
                    break
            else:
                raise TimeoutError('No USB script completion marker')
            # Only inspect execution output after the paste-mode terminator.
            execution = bytes(received).split(b'=== \r\n', 1)[-1]
            report['traceback'] = b'Traceback (most recent call last)' in execution
            if report['traceback']:
                raise RuntimeError('Script raised an exception')
    except Exception as error:
        report['error'] = str(error)
    finally:
        (folder / 'serial.bin').write_bytes(received)
        (folder / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
        print(bytes(received).decode(errors='replace'))
        print(json.dumps(report, indent=2))
        print('Evidence:', folder)
    return 0 if report['completed'] and 'error' not in report else 1


if __name__ == '__main__':
    raise SystemExit(main())
