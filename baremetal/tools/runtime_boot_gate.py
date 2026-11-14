# SPDX-License-Identifier: MIT
"""Five RAM-only runtime boots. Start with DUT in maskrom; UART must be idle."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
cfg=json.loads((ROOT/'devices.json').read_text())
image=ROOT/'build/hello-download.bin'
report={'scope':'Five RAM-only db boots; no storage writes','sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'runs':[]}
for index in range(5):
    if index:
        subprocess.run(['adb','-s',cfg['referenceAdbSerial'],'shell',
                        'printf "\\035" > '+cfg['referenceUart']],check=True)
    result=subprocess.run([sys.executable,str(ROOT/'tools/harness.py'),'--image',str(image),
        '--phase','9','--timeout','18','--baud','115200','--pass-pattern','@@REPL_READY'],capture_output=True,text=True)
    try:run=json.loads(result.stdout)
    except json.JSONDecodeError:run={'passed':False,'stdout':result.stdout,'stderr':result.stderr}
    report['runs'].append(run)
    print(json.dumps({'run':index,'passed':run['passed'],'evidence':run.get('evidence')}),flush=True)
    if result.returncode or not run['passed']:break
report['passed']=len(report['runs'])==5 and all(r['passed'] for r in report['runs'])
(ROOT/'logs/phase-9/runtime-boot-gate.json').write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(0 if report['passed'] else 1)
