#!/usr/bin/env python3
"""Compare matching steady Scan windows from host-side metadata sampling.

CPU uses the target's measured SC_CLK_TCK, not the desktop's clock frequency.
These short diagnostics cannot establish long-run memory reliability.
"""
import argparse
import json
import statistics
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('python',type=Path);p.add_argument('rust',type=Path)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--ticks-per-second',type=int,required=True)
p.add_argument('--start',type=float,default=30);p.add_argument('--end',type=float,default=75)
a=p.parse_args()
if a.ticks_per_second<=0 or a.start<0 or a.end<=a.start:p.error('Invalid clock/window')
roles={'app':lambda n:n=='python3','camera':lambda n:n=='camera-probe','qr':lambda n:n.startswith('shieldsigner-qr')}

def metrics(path,backend):
    all_rows=[json.loads(s) for s in path.read_text().splitlines()]
    rows=[r for r in all_rows if r.get('telemetry',{}).get('phase')=='running' and a.start<=r['telemetry']['elapsedSeconds']<=a.end]
    if len(rows)<10:raise ValueError('Insufficient steady samples: '+backend)
    for r in rows:
        t=r['telemetry']
        assert t['frontendBackend']==backend and t['rustLcd'] and t['smallRam']
        assert t['renderer']['errors']==0 and t['qr'].get('errors')==0
        assert len(t['streams'])==1 and t['streams'][0]['readerErrors']==0 and t['streams'][0]['reconnects']==0
    first,last=rows[0],rows[-1]
    seconds=last['unix']-first['unix']
    telemetry_seconds=last['telemetry']['elapsedSeconds']-first['telemetry']['elapsedSeconds']
    if min(seconds,telemetry_seconds)<25:raise ValueError('Steady window too short')
    process={}
    for role,match in roles.items():
        samples=[];pids=set()
        for r in rows:
            found=[(pid,v) for pid,v in r['processes'].items() if match(v['name'])]
            if len(found)!=1:raise ValueError('Expected exactly one '+role)
            pid,v=found[0];pids.add((pid,v['startTicks']));samples.append(v)
        if len(pids)!=1:raise ValueError('Process restarted during comparison: '+role)
        ticks=lambda v:v['userCpuTicks']+v['systemCpuTicks']
        process[role]={'medianPssKiB':statistics.median(v['Pss'] for v in samples),
                      'medianSwapPssKiB':statistics.median(v.get('SwapPss',0) for v in samples),
                      'medianThreads':statistics.median(v['threads'] for v in samples),
                      'cpuPercentOfOneCore':100*(ticks(samples[-1])-ticks(samples[0]))/a.ticks_per_second/seconds}
    first,last=first['telemetry'],last['telemetry']
    return {'samples':len(rows),'hostWindowSeconds':seconds,'counterWindowSeconds':telemetry_seconds,
            'medianAvailableKiB':statistics.median(r['memory']['MemAvailable'] for r in rows),
            'minimumAvailableKiB':min(r['memory']['MemAvailable'] for r in rows),
            'medianZramAllocatedBytes':statistics.median(r['zram']['allocatedBytes'] for r in rows),
            'processes':process,
            'framesPerSecond':(last['streams'][0]['fullFrames']-first['streams'][0]['fullFrames'])/telemetry_seconds,
            'rendersPerSecond':(last['renderer']['successfulCalls']-first['renderer']['successfulCalls'])/telemetry_seconds,
            'qrCallsPerSecond':(last['qr']['calls']-first['qr']['calls'])/telemetry_seconds}

report={'kind':'matched-real-GUI-frontend-comparison','steadyWindowRequestedSeconds':[a.start,a.end],
        'targetClockTicksPerSecond':a.ticks_per_second,'python':metrics(a.python,'python'),'rust':metrics(a.rust,'rust'),
        'limits':['Same current startup-import policy in both runs; isolates frontend transport/preparation, not older firmware.','One short run per backend, Python first; scene, cache and zram residency can affect results.','Harness telemetry/watchdog threads are diagnostic overhead.','CPU percentages are per single CPU core, derived from target proc counters.','No optical QR fixture or signing workload; duration termination is not UI cancellation.']}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
