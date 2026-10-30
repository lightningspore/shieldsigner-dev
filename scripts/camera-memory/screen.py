#!/usr/bin/env python3
"""Capture the diagnostic app's latest rendered image on explicit request only.

May contain wallet/QR content. Keep captures private under ignored dist/.
Adds a retained frame reference in the explicit diagnostic launcher only.
"""
import argparse,json,re,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('--serial',default='0a523b8b23110ffc');a=p.parse_args()
def shell(s):return subprocess.check_output(['adb','-s',a.serial,'shell',s],text=True,timeout=5)
d=json.loads(shell('cat /tmp/shieldsigner-button-control-current.json'))['directory']
if not re.fullmatch('/tmp/shieldsigner-buttons-[0-9]+',d):raise SystemExit('Invalid diagnostic directory')
shell('rm -f '+d+'/screen.png; touch '+d+'/screen.request')
for _ in range(100):
 if shell('test -s '+d+'/screen.png && echo READY').strip()=='READY':break
 time.sleep(.1)
else:raise SystemExit('No rendered image captured')
a.output.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['adb','-s',a.serial,'pull',d+'/screen.png',str(a.output)],check=True,stdout=subprocess.DEVNULL)
print(a.output)
