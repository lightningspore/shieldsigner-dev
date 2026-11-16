# SPDX-License-Identifier: MIT
"""Capture one owned native camera snapshot in checksummed, bounded USB row chunks."""

import argparse, datetime, json, subprocess, sys
from pathlib import Path
from decode_camera_luma import decode_snapshot

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True, choices=('rv1103-dut1', 'rv1103-dev-001'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ae-target', type=int)
    parser.add_argument('--exposure-seed', type=int)
    parser.add_argument('--frames', type=int, default=12)
    parser.add_argument('--rows-per-chunk', type=int, default=80)
    args = parser.parse_args()
    if not 1 <= args.frames <= 32:
        parser.error('frames must be1..32')
    if not 1 <= args.rows_per_chunk <= 120:
        parser.error('rows-per-chunk must be1..120')
    if args.ae_target is not None and args.ae_target != 0 and not 8 <= args.ae_target <= 200:
        parser.error('ae-target must be0 or8..200')
    if args.exposure_seed is not None and not 1 <= args.exposure_seed <= 1352:
        parser.error('exposure-seed must be1..1352')
    folder = (
        ROOT
        / 'logs/phase-12'
        / ('capture-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'))
    )
    folder.mkdir(parents=True)
    report = {
        'device': args.serial,
        'output': str(args.output),
        'evidence': str(folder),
        'passed': False,
        'steps': [],
    }

    def step(name, code, timeout=20):
        script = folder / (name + '.py')
        script.write_text(code)
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / 'tools/usb_console.py'),
                str(script),
                '--serial',
                args.serial,
                '--timeout',
                str(timeout),
            ],
            capture_output=True,
        )
        output = folder / (name + '.txt')
        output.write_bytes(result.stdout + result.stderr)
        report['steps'].append({'name': name, 'exitCode': result.returncode, 'log': str(output)})
        if result.returncode:
            raise RuntimeError('Native ' + name + ' failed; see ' + str(output))
        return output

    params = {
        k: v
        for k, v in [('ae_target', args.ae_target), ('exposure_seed', args.exposure_seed)]
        if v is not None
    }
    report.update(requestedSettings=params, frames=args.frames, rowsPerChunk=args.rows_per_chunk)
    try:
        step(
            'snapshot',
            f'''import camera,hashlib,binascii
_diagnostic_previous=camera.settings()
camera.init()
_diagnostic_started=False
try:
    camera.settings(**{params!r})
    camera.start_preview()
    _diagnostic_started=True
    for _diagnostic_index in range({args.frames}):
        _diagnostic_frame=camera.next_preview()
    _diagnostic_luma=bytes(_diagnostic_frame[:640*480])
    _diagnostic_settings=camera.settings()
    del _diagnostic_frame
finally:
    if _diagnostic_started:camera.stop_preview()
    camera.settings(ae_target=_diagnostic_previous['ae_target'],exposure_seed=_diagnostic_previous['exposure_seed'])
assert camera.preview_status()==(False,0)
assert camera.settings()['ae_target']==_diagnostic_previous['ae_target']
assert camera.settings()['exposure_seed']==_diagnostic_previous['exposure_seed']
_diagnostic_id=hashlib.sha256(_diagnostic_luma).hexdigest()
print('@@SNAPSHOT_READY',_diagnostic_id,_diagnostic_settings)
''',
        )
        chunks = []
        for start in range(0, 480, args.rows_per_chunk):
            end = min(480, start + args.rows_per_chunk)
            output = step(
                'rows-' + str(start),
                f'''assert hashlib.sha256(_diagnostic_luma).hexdigest()==_diagnostic_id
print('@@LUMA_BEGIN 640 480 SHA256',_diagnostic_id)
for _diagnostic_row in range({start},{end}):
    print('@@LUMA',_diagnostic_row,binascii.hexlify(_diagnostic_luma[_diagnostic_row*640:(_diagnostic_row+1)*640]).decode())
print('@@LUMA_END')
''',
            )
            chunks.append(output)
            print('Captured rows', start, 'through', end - 1, flush=True)
        pixels, identity = decode_snapshot(chunks, require_digest=True)
        from PIL import Image

        args.output.parent.mkdir(parents=True, exist_ok=True)
        Image.frombytes('L', (640, 480), pixels).save(args.output)
        report.update(passed=True, sha256=identity, width=640, height=480)
    except Exception as error:
        report['error'] = str(error)
    finally:
        try:
            step(
                'cleanup',
                "from seedsigner_port.secure_delete import wipe_bytes\nif '_diagnostic_luma' in globals():\n    wipe_bytes(_diagnostic_luma)\n    del _diagnostic_luma\nif '_diagnostic_id' in globals():del _diagnostic_id\nif '_diagnostic_frame' in globals():del _diagnostic_frame\nprint('@@SNAPSHOT_RELEASED')\n",
                10,
            )
        except Exception as error:
            report['cleanupError'] = str(error)
            report['passed'] = False
        (folder / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
