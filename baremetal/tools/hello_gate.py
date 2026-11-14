"""Ten consecutive hardware hello captures with DUT recovery through the existing UART."""
import datetime
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
cfg = json.loads((ROOT/'devices.json').read_text())
tool = str(ROOT/'.tools/rkdeveloptool/rkdeveloptool')
records = []
folder = ROOT/'logs/phase-2'
folder.mkdir(parents=True, exist_ok=True)
def run(argv, timeout=60):
    return subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
for index in range(1, 11):
    result = run([sys.executable, str(ROOT/'tools/harness.py'), '--image', str(ROOT/'build/hello-download.bin'),
                  '--phase','2','--timeout','3','--baud','115200','--pass-pattern','@@PASS hello'], 50)
    record = {'run':index, 'exitCode':result.returncode, 'stdout':result.stdout, 'stderr':result.stderr}
    records.append(record)
    if result.returncode:
        print('Hello gate failed at run',index,flush=True)
        break
    # UART recovery is part of this payload, rather than a persistent boot change.
    remote = "python3 -c 'import os,termios; f=os.open(\"/dev/ttyS3\",os.O_RDWR|os.O_NOCTTY); print(os.write(f,b\"R\")); termios.tcdrain(f); os.close(f)'"
    reset = run(['adb','-s',cfg['referenceAdbSerial'],'shell',remote],10)
    record['reset'] = {'exitCode':reset.returncode,'stdout':reset.stdout,'stderr':reset.stderr}
    ready = False
    for _ in range(30):
        state = run([tool,'ld'],10)
        lines = [line for line in state.stdout.splitlines() if 'DevNo=' in line]
        if state.returncode == 0 and len(lines)==1 and 'Vid=0x2207,Pid=0x110c' in lines[0] and 'Maskrom' in lines[0]:
            ready = True
            break
        time.sleep(0.2)
    record['maskromRecovered'] = ready
    print(f'Run {index}/10 hello passed; UART reset recovery: {ready}',flush=True)
    if reset.returncode or not ready:
        break
passed = len(records)==10 and all(r['exitCode']==0 and r.get('maskromRecovered') and r['reset']['exitCode']==0 for r in records)
report={'passed':passed,'runs':records,'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
path=folder/('hello-gate-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
path.write_text(json.dumps(report,indent=2)+'\n')
print('Evidence:',path,flush=True)
sys.exit(0 if passed else 1)
