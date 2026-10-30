#!/usr/bin/env python3
"""Launch the actual ScanView with metadata-only diagnostic telemetry.

This bench uses real display/button/camera hardware. Run only after the board
profile is reviewed and with no other camera/application owner. It never fakes
UI cancellation and does not replace the application's animated loading screen.
"""
import argparse
import faulthandler
import json
import math
import os
from pathlib import Path
import signal
import sys
import tempfile
import threading
import time
import traceback
import weakref


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as target:
            json.dump(value, target)
            target.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app-root', type=Path, default=Path('/opt/src'))
    parser.add_argument('--camera-python-root', type=Path, default=Path('/usr/lib/shieldsigner-camera/python'))
    parser.add_argument('--config', type=Path, default=Path('/usr/lib/shieldsigner-camera/owner.json'))
    parser.add_argument('--qr-reader', type=Path, default=Path('/usr/lib/shieldsigner-camera/shieldsigner-qr-reader'))
    parser.add_argument('--rust-lcd', action='store_true', help='Install the reviewed process-local Rust LCD shim before Renderer construction')
    parser.add_argument('--lcd-python-root', type=Path, default=Path('/tmp/lcd-python'))
    parser.add_argument('--small-ram', action='store_true', help='Explicitly enable the existing small-RAM application/integration policy')
    parser.add_argument('--frontend-backend', choices=('python', 'rust'), default='python', help='Explicit camera frame/preview/QR transport backend')
    parser.add_argument('--state-file', type=Path, default=Path('/tmp/shieldsigner-gui-bench-state.json'))
    parser.add_argument('--duration', type=float, help='Terminate the benchmark process after this many seconds, with bounded owner cleanup; not a UI cancel test')
    parser.add_argument('--cleanup-seconds', type=float, default=8, help='Maximum best-effort owner cleanup interval before process exit')
    parser.add_argument('--stack-dump-seconds', type=float, help='Repeat native-watchdog Python stack dumps to stderr, including when Python threads cannot acquire the GIL')
    args = parser.parse_args()
    if args.duration is not None and (not math.isfinite(args.duration) or args.duration <= 0):
        parser.error('--duration must be finite and positive')
    for name in ['cleanup_seconds', 'stack_dump_seconds']:
        value = getattr(args, name)
        if value is not None and (not math.isfinite(value) or value <= 0):
            parser.error('--' + name.replace('_', '-') + ' must be finite and positive')
    os.environ['SHIELDSIGNER_FRONTEND_BACKEND'] = args.frontend_backend
    os.environ['SHIELDSIGNER_SMALL_RAM'] = '1' if args.small_ram else '0'
    os.environ['SHIELDSIGNER_CAMERA_CONFIG'] = str(args.config.resolve())
    os.environ['SHIELDSIGNER_QR_READER'] = str(args.qr_reader.resolve())
    sys.path[:0] = [str(args.camera_python_root.resolve()), '/usr/lib/shieldsigner-camera/python', str(args.app_root.resolve())]
    if args.rust_lcd:
        sys.path.insert(0, str(args.lcd_python_root.resolve()))
        from shieldsigner_lcd_driver import install
        print(json.dumps(install(str(args.app_root.resolve()))), file=sys.stderr, flush=True)

    from shieldsigner_video_stream import PiVideoStream
    lock = threading.Lock()
    write_lock = threading.Lock()
    streams = []
    retired = {'frames': 0, 'reconnects': 0, 'readerErrors': 0}
    renderer = {'successfulCalls': 0, 'errors': 0}
    started = time.monotonic()
    phase = 'starting'
    termination = None
    monitor_stop = threading.Event()
    termination_requested = threading.Event()
    termination_reason = [None]
    old_start, old_update, old_stop = PiVideoStream.start, PiVideoStream._update, PiVideoStream.stop

    def tracked_start(stream):
        if termination_requested.is_set():
            raise RuntimeError("Benchmark process is terminating")
        result = old_start(stream)
        with lock:
            # Keep diagnostic references bounded even if the user navigates
            # away and opens many scans. Finished sessions contribute counters.
            if len(streams) == 4:
                previous = streams.pop(0)
                retired['frames'] += previous['fullFrames']
                retired['reconnects'] += previous['reconnects']
                retired['readerErrors'] += previous['readerErrors']
            streams.append({'reference': weakref.ref(stream), 'fullFrames': 0,
                            'reconnects': 0, 'readerErrors': 0, 'stopped': False})
        return result

    def traced_update(stream):
        try:
            return old_update(stream)
        finally:
            if stream.error is not None:
                print('CAMERA_READER_CAUSE', file=sys.stderr, flush=True)
                traceback.print_exception(type(stream.error), stream.error, stream.error.__traceback__, chain=True, file=sys.stderr)

    def tracked_stop(stream):
        try:
            return old_stop(stream)
        finally:
            with lock:
                for record in streams:
                    if record['reference']() is stream:
                        record.update(fullFrames=stream.frames_received,
                                      reconnects=getattr(stream, 'reconnects', 0),
                                      stopped=stream.is_stopped,
                                      readerErrors=int(stream.error is not None))

    PiVideoStream.start, PiVideoStream._update, PiVideoStream.stop = tracked_start, traced_update, tracked_stop
    from seedsigner.gui.renderer import Renderer
    old_show = Renderer.show_image

    def tracked_show(self, *positional, **keywords):
        try:
            result = old_show(self, *positional, **keywords)
        except Exception:
            with lock:
                renderer['errors'] += 1
            raise
        with lock:
            renderer['successfulCalls'] += 1
        return result

    Renderer.show_image = tracked_show

    def state():
        with lock:
            active = []
            for record in streams:
                item = record['reference']()
                if item is not None:
                    record.update(fullFrames=item.frames_received,
                                  reconnects=getattr(item, 'reconnects', 0),
                                  stopped=item.is_stopped,
                                  readerErrors=int(item.error is not None))
                active.append({key: value for key, value in record.items() if key != 'reference'})
            return {'kind': 'real-scanview-benchmark', 'pid': os.getpid(),
                    'elapsedSeconds': time.monotonic()-started, 'phase': phase,
                    'rustLcd': args.rust_lcd, 'smallRam': args.small_ram, 'frontendBackend': args.frontend_backend,
                    'renderer': dict(renderer), 'streams': active,
                    'qr': {key: value for key, value in getattr(getattr(camera_backend, '__shieldsigner_qr_client__', None), 'stats', {}).items() if key in ('starts', 'calls', 'decoded', 'errors', 'lastRoundTripSeconds')},
                    'retiredCounters': dict(retired), 'termination': termination,
                    'uiCancellationQualified': False,
                    'terminationPolicy': {'durationSeconds': args.duration, 'cleanupBudgetSeconds': args.cleanup_seconds,
                                          'hardFallback': 'with --duration: default SIGALRM at duration + cleanup budget + 1 second; final telemetry may be absent'},
                    'containsImagesOrDecodedQr': False}

    def publish():
        with write_lock:
            atomic_json(args.state_file, state())

    def observe():
        while not monitor_stop.wait(2):
            try:
                publish()
            except OSError:
                traceback.print_exc(file=sys.stderr)
                return

    import shieldsigner_integration as integration
    camera_backend = integration.install_camera_backend(args.app_root.resolve())
    if args.small_ram:
        # These guarded process-local profiles must precede Controller/ScanView
        # imports. integration.main applies them again idempotently.
        print(json.dumps(integration.install_small_ram_profile(args.app_root.resolve())), file=sys.stderr, flush=True)
        print(json.dumps(integration.install_lazy_scan_views(args.app_root.resolve())), file=sys.stderr, flush=True)
    from seedsigner.controller import Controller
    from seedsigner.views.view import Destination
    from seedsigner.views.scan_views import ScanView
    old_controller_start = Controller.start

    def start_scan(self, *positional, **keywords):
        if hasattr(integration, 'import_memory_snapshot'):
            print(json.dumps(integration.import_memory_snapshot('scan-start')), flush=True)
        keywords['initial_destination'] = Destination(ScanView)
        keywords['skip_startup_interstitials'] = True
        return old_controller_start(self, *positional, **keywords)

    Controller.start = start_scan
    previous_signals = {}

    def request_termination(signum, frame):
        # Do not raise into Controller: it catches BaseException and can turn
        # even a sentinel into a new error screen instead of terminating.
        if not termination_requested.is_set():
            termination_reason[0] = signal.Signals(signum).name
            termination_requested.set()
            remaining = signal.getitimer(signal.ITIMER_REAL)[0]
            signal.setitimer(signal.ITIMER_REAL, min(remaining or args.cleanup_seconds + 1,
                                                    args.cleanup_seconds + 1))

    def watchdog():
        nonlocal phase, termination
        if not termination_requested.wait(args.duration):
            termination_reason[0] = 'duration'
            termination_requested.set()
        if monitor_stop.is_set():
            return
        phase = 'terminating'
        termination = {'reason': termination_reason[0], 'isUiCancellationClaim': False,
                       'controllerFinallyClaimed': False, 'processExitRequested': True}
        # Both cleanup and telemetry are best effort. The kernel default
        # SIGALRM remains armed independently of the GIL and Controller catches.
        def cleanup():
            for record in list(streams):
                stream = record['reference']()
                if stream is not None:
                    try:
                        stream.stop()
                    except Exception as exc:
                        cleanup_errors.append(type(exc).__name__)
            client = getattr(camera_backend, '__shieldsigner_qr_client__', None)
            if client is not None:
                try:
                    client.close()
                except Exception as exc:
                    cleanup_errors.append(type(exc).__name__)
        worker = threading.Thread(target=cleanup, daemon=True)
        worker.start()
        worker.join(args.cleanup_seconds)
        termination['ownerCleanupTimedOut'] = worker.is_alive()
        termination['cameraCleanupErrors'] = list(cleanup_errors)
        phase = 'process-exit'
        try:
            publish()
        except Exception:
            pass
        # No Python exception can be swallowed by the application's broad catch.
        os._exit(1 if worker.is_alive() or cleanup_errors else 0)

    old_argv = sys.argv
    monitor = threading.Thread(target=observe, daemon=True)
    cleanup_errors = []
    try:
        for signum in [signal.SIGTERM, signal.SIGINT]:
            previous_signals[signum] = signal.signal(signum, request_termination)
        previous_signals[signal.SIGALRM] = signal.signal(signal.SIGALRM, signal.SIG_DFL)
        phase = 'running'
        publish()
        monitor.start()
        if args.stack_dump_seconds is not None:
            faulthandler.enable(file=sys.stderr, all_threads=True)
            faulthandler.dump_traceback_later(args.stack_dump_seconds, repeat=True, file=sys.stderr)
        if args.duration is not None:
            signal.setitimer(signal.ITIMER_REAL, args.duration + args.cleanup_seconds + 1)
        threading.Thread(target=watchdog, daemon=True).start()
        sys.argv = ['shieldsigner_integration.py', '--app-root', str(args.app_root.resolve()),
                    '--config', str(args.config.resolve()), '--qr-reader', str(args.qr_reader.resolve())]
        if args.rust_lcd:
            sys.argv += ['--lcd-backend', 'rust']
        integration.main()
        termination = {'reason': 'application-returned', 'isUiCancellationClaim': False}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        faulthandler.cancel_dump_traceback_later()
        monitor_stop.set()
        termination_requested.set()
        for signum, handler in previous_signals.items():
            signal.signal(signum, handler)
        # integration.main already stops its camera/QR owner in finally. Cover
        # tracked streams too if an exception occurred before that scope began.
        for record in streams:
            stream = record['reference']()
            if stream is None:
                continue
            try:
                stream.stop()
            except Exception as exc:
                cleanup_errors.append(type(exc).__name__)
                traceback.print_exc(file=sys.stderr)
        monitor_stop.set()
        if monitor.is_alive():
            monitor.join(3)
        phase = 'finished'
        if termination is None:
            termination = {'reason': 'unhandled-exception', 'isUiCancellationClaim': False}
        termination['cameraCleanupErrors'] = cleanup_errors
        publish()
        sys.argv = old_argv
        Controller.start = old_controller_start
        Renderer.show_image = old_show
        PiVideoStream.start, PiVideoStream._update, PiVideoStream.stop = old_start, old_update, old_stop
    return 1 if cleanup_errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
