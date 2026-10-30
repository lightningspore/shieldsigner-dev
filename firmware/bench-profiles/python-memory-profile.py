#!/usr/bin/env python3
"""Opt-in real-app allocation profiling; exports metadata, never object values.

Diagnostic only: tracemalloc, a monitor thread and snapshots consume RAM/CPU.
Full snapshots proved too heavy for the 64 MiB Mini; main refuses that target.
Start with no other app/camera owner. Write an allowed phase to --request to
request a report. Source file totals and GC shallow sizes overlap: never add
those views or equate either to process PSS. Native allocation is incomplete.
"""
import argparse
import collections
import gc
import json
import os
from pathlib import Path
import runpy
import sys
import threading
import time
import tracemalloc
import types

PHASES = {'baseline', 'idle', 'scan', 'after-scan'}
EXACT_SIZED = {dict, list, tuple, set, frozenset, types.CodeType,
               types.FunctionType, types.ModuleType, type}


def source_name(name):
    for root in ('/opt/src/', '/usr/lib/python3.12/', '/usr/lib/shieldsigner-camera/python/'):
        if name.startswith(root):
            return name[len(root):]
    if name == __file__:
        return '<profiler>'
    return '<runtime-or-other>'


def proc_memory():
    result = {}
    for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            if value.strip().endswith('kB'):
                result[key] = int(value.split()[0])
    return result


def report(phase, output):
    start = time.monotonic()
    before = proc_memory()
    current, peak = tracemalloc.get_traced_memory()
    trace_overhead = tracemalloc.get_tracemalloc_memory()
    snapshot = tracemalloc.take_snapshot()
    statistics = snapshot.statistics('filename')
    files = collections.defaultdict(lambda: [0, 0])
    for stat in statistics:
        row = files[source_name(stat.traceback[0].filename)]
        row[0] += stat.size
        row[1] += stat.count
    del snapshot, statistics
    objects = gc.get_objects()
    counts = collections.defaultdict(lambda: [0, 0, 0])
    for obj in objects:
        cls = type(obj)
        row = counts[cls.__module__ + '.' + cls.__qualname__]
        row[0] += 1
        # Only exact reviewed types: do not invoke application __sizeof__ hooks.
        if cls in EXACT_SIZED:
            row[1] += sys.getsizeof(obj)
            row[2] += 1
    tracked_count = len(objects)
    del obj, objects
    frames = sys._current_frames()
    threads = []
    for thread in threading.enumerate():
        frame = frames.get(thread.ident)
        threads.append({'name': thread.name, 'class': type(thread).__name__,
                        'nativeId': thread.native_id,
                        'source': source_name(frame.f_code.co_filename) if frame else None,
                        'function': frame.f_code.co_name if frame else None})
    del frames, frame
    record = {'kind': 'python-allocation-diagnostic', 'phase': phase,
              'pid': os.getpid(), 'pythonVersion': sys.version.split()[0],
              'tracemallocFrames': 1, 'tracedCurrentBytesBeforeSnapshot': current,
              'tracedPeakBytesBeforeSnapshot': peak,
              'tracemallocMetadataBytesBeforeSnapshot': trace_overhead,
              'processBeforeSnapshotKiB': before, 'processAfterSnapshotKiB': proc_memory(),
              'moduleCount': len(sys.modules), 'gcTrackedObjects': tracked_count,
              'files': [{'source': name, 'liveBytes': values[0], 'liveBlocks': values[1]}
                        for name, values in sorted(files.items(), key=lambda row: -row[1][0])],
              'types': [{'type': name, 'count': values[0], 'shallowBytes': values[1],
                         'shallowSizedCount': values[2]}
                        for name, values in sorted(counts.items(), key=lambda row: -row[1][0])],
              'threads': threads, 'diagnosticSeconds': time.monotonic() - start,
              'containsObjectValuesOrFramePixels': False,
              'limits': ['Tracing starts after profiler imports, before app integration.',
                         'Native Pillow/Rust/kernel allocations are not fully traced.',
                         'GC counts omit many strings/bytes and other untracked objects.',
                         'Shallow container sizes exclude their referenced contents.',
                         'Tracing, report temporaries and monitor thread perturb the app.',
                         'File allocation totals and object sizes overlap; do not sum.']}
    path = output / (phase + '.json')
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(record, indent=2) + '\n')
    temporary.replace(path)
    print(json.dumps({'profile': phase, 'tracedBytes': current, 'traceMetadataBytes': trace_overhead,
                      'report': str(path)}), flush=True)
    tracemalloc.reset_peak()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    args = parser.parse_args()
    memtotal = next(int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemTotal:'))
    if memtotal < 96 * 1024:
        parser.error('Full allocation snapshots exceed the Mini memory budget; use the off-board ARM import profiler')
    args.output.mkdir(parents=True, exist_ok=False)
    tracemalloc.start(1)
    report('baseline', args.output)
    stop = threading.Event()

    def monitor():
        while not stop.wait(1):
            if args.request.exists():
                phase = args.request.read_text().strip()
                args.request.unlink()
                if phase in PHASES and not (args.output / (phase + '.json')).exists():
                    report(phase, args.output)

    threading.Thread(target=monitor, name='memory-profile-monitor', daemon=True).start()
    sys.path.insert(0, '/usr/lib/shieldsigner-camera/python')
    sys.argv = ['shieldsigner_integration.py', '--app-root', '/opt/src',
                '--config', '/usr/lib/shieldsigner-camera/owner.json',
                '--qr-reader', '/usr/lib/shieldsigner-camera/shieldsigner-qr-reader']
    try:
        runpy.run_path('/usr/lib/shieldsigner-camera/python/shieldsigner_integration.py', run_name='__main__')
    finally:
        stop.set()


if __name__ == '__main__':
    main()
