#!/usr/bin/env python3
"""Low-overhead in-process census: no tracemalloc, values, keys or image data.

Diagnostic thread and temporary GC object list perturb memory. GC counts miss
untracked strings/bytes. Shallow sizes overlap code/constants views and exclude
referenced contents. No result is an object-by-object ownership attribution.
"""
import collections
import gc
import json
import os
from pathlib import Path
import runpy
import signal
import sys
import threading
import types

OUT = Path('/tmp/python-object-census')
REQUEST = Path('/tmp/python-object-census-request')
SIZED = {dict, list, tuple, set, frozenset, types.FunctionType,
         types.CodeType, types.ModuleType, type}


def memory():
    result = {}
    for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            if v.strip().endswith('kB'): result[k] = int(v.split()[0])
    return result


def census(phase):
    available = next(int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:'))
    result = {'phase': phase, 'pid': os.getpid(), 'availableKiBBefore': available,
              'processBeforeKiB': memory(), 'tracemallocEnabled': False,
              'containsObjectValues': False}
    if available < 8192:
        result['censusSkipped'] = 'Below 8 MiB available-memory guard'
    else:
        objects = gc.get_objects()
        counts = collections.defaultdict(lambda: [0, 0, 0])
        codes = {}
        for obj in objects:
            cls = type(obj)
            row = counts[cls.__module__ + '.' + cls.__qualname__]
            row[0] += 1
            if cls in SIZED:
                row[1] += sys.getsizeof(obj); row[2] += 1
            if cls is types.FunctionType:
                code = obj.__code__
                codes[id(code)] = code
        result['gcTrackedObjects'] = len(objects)
        result['types'] = [{'type': k, 'count': v[0], 'shallowBytes': v[1], 'sizedCount': v[2]}
                           for k, v in sorted(counts.items(), key=lambda r: -r[1][0])]
        result['uniqueFunctionCodeObjects'] = len(codes)
        result['functionCodeShallowBytes'] = sum(sys.getsizeof(c) for c in codes.values())
        del obj, objects, codes, counts
    result['moduleCount'] = len(sys.modules)
    result['threads'] = [{'name': t.name, 'class': type(t).__name__, 'nativeId': t.native_id}
                         for t in threading.enumerate()]
    result['processAfterKiB'] = memory()
    path = OUT/(phase+'.json'); path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'census':phase,'skipped':result.get('censusSkipped')}),flush=True)


def main():
    OUT.mkdir(exist_ok=False)
    signal.alarm(180)  # Kernel-enforced fallback; does not depend on monitor GIL.
    census('baseline')
    def monitor():
        while True:
            threading.Event().wait(1)
            if REQUEST.exists():
                phase = REQUEST.read_text().strip(); REQUEST.unlink()
                if phase in {'idle','scan','after-scan'} and not (OUT/(phase+'.json')).exists(): census(phase)
    threading.Thread(target=monitor,name='object-census-monitor',daemon=True).start()
    sys.path.insert(0,'/usr/lib/shieldsigner-camera/python')
    sys.argv=['shieldsigner_integration.py','--app-root','/opt/src','--config','/usr/lib/shieldsigner-camera/owner.json','--qr-reader','/usr/lib/shieldsigner-camera/shieldsigner-qr-reader']
    runpy.run_path('/usr/lib/shieldsigner-camera/python/shieldsigner_integration.py',run_name='__main__')

if __name__=='__main__': main()
