#!/usr/bin/env python3
"""Measure named-button-to-UI/owner outcomes on an already running diagnostic app.

No screenshots, arbitrary app commands, seeds or QR payloads are collected.
Host client launch/ADB/polling overhead is included and is not kernel latency.
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import statistics
import subprocess
import sys
import time

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--backend',choices=['python','rust'],required=True)
p.add_argument('--log',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
p.add_argument('--serial',default='0a523b8b23110ffc');p.add_argument('--cycles',type=int,default=3)
a=p.parse_args()
if not 1<=a.cycles<=5:p.error('cycles must be 1..5')
if not str(a.log).startswith('/tmp/'):p.error('Use a diagnostic /tmp log')
button=Path(__file__).with_name('button.py')
command='''for proc in /proc/[0-9]*; do
 read name < "$proc/comm" || continue
 case "$name" in camera-probe|shieldsigner-qr*) echo OWNER:${proc##*/} ;; esac
done
echo VIEW:
'''+ 'tail -n 60 '+shlex.quote(str(a.log))+''' | grep 'Executing ' | tail -n 1
cat /sys/kernel/debug/dma_buf/bufinfo | tail -n 1
'''
def state():
    raw=subprocess.check_output(['adb','-s',a.serial,'shell',command],text=True,timeout=5)
    dma=re.search(r'Total (\d+) objects, (\d+) bytes',raw)
    if not dma:raise RuntimeError('DMA readback missing')
    return {'owners':sum(line.startswith('OWNER:') for line in raw.splitlines()),
            'home':'Executing MainMenuView()' in raw,'dmaObjects':int(dma[1]),'dmaBytes':int(dma[2])}
def press(key,hold=120):
    subprocess.run([sys.executable,str(button),key,'--hold-ms',str(hold),'--serial',a.serial],check=True,stdout=subprocess.DEVNULL)
def wait(predicate,seconds):
    deadline=time.monotonic()+seconds
    while True:
        result=state()
        if predicate(result):return result
        if time.monotonic()>=deadline:raise TimeoutError('UI/owner outcome not observed')
        time.sleep(.05)
initial=state()
if not initial['home'] or initial['owners'] or initial['dmaObjects']:
    raise RuntimeError('Start from verified Home with no camera/QR owners or DMA')
rows=[]
for _ in range(a.cycles):
    started=time.monotonic();press('KEY_PRESS')
    wait(lambda s:s['owners']==2,15)
    ready=time.monotonic()-started
    time.sleep(2)
    started=time.monotonic();press('KEY_LEFT',500)
    result=wait(lambda s:s['home'] and s['owners']==0 and s['dmaObjects']==0,15)
    rows.append({'buttonToBothCameraQrOwnersSeconds':ready,'backToHomeAndNoOwnersSeconds':time.monotonic()-started,
                 'finalDmaObjects':result['dmaObjects'],'finalDmaBytes':result['dmaBytes']})
report={'kind':'real-diagnostic-button-ui-latency','backend':a.backend,'cycles':rows,
 'medianButtonToOwnersSeconds':statistics.median(r['buttonToBothCameraQrOwnersSeconds'] for r in rows),
 'medianBackToHomeAndNoOwnersSeconds':statistics.median(r['backToHomeAndNoOwnersSeconds'] for r in rows),
 'limits':['Host interpreter/client startup, ADB round trips, 500ms Back hold and polling overhead included.','Opening metric means both camera and QR processes exist, not first rendered or decoded frame.','Diagnostic button inputs test app navigation, not electrical switch latency.','Caller must verify backend configuration and wake any screensaver before starting.']}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
