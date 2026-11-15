# SPDX-License-Identifier: MIT
"""Load the explicitly configured DUT1 into RAM; never use REF UART or storage."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from serial.tools import list_ports

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--leave-app-running',action='store_true',help='Only app-autostart: download without interrupting app; skip console gate')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
cfg=json.loads((root/'devices.json').read_text())
location=cfg['appDutUsbLocation'];identity=cfg['appDutUsbSerial']
folder=root/'logs/phase-11'/('dut1-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
folder.mkdir(parents=True)
manifest=json.loads((root/'build/hello-manifest.json').read_text())
image=root/'build/hello-download.bin'
report={'scope':'DUT1 RAM-only db, no storage commands or REF/DUT0 UART writes','location':location,'serial':identity,'passed':False}
try:
    assert manifest['features'] in ('usb-only','mini-pcb-ui','app-ui','app-ui,fault-probe','app-autostart') and manifest['usbSerial']==identity,'Wrong target build'
    if args.leave_app_running:
        assert manifest['features']=='app-autostart','Leaving app running requires app-autostart profile'
    assert hashlib.sha256(image.read_bytes()).hexdigest()==manifest['files']['build/hello-download.bin'],'Image changed'
    (folder/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    tool=root/'.tools/rkdeveloptool/rkdeveloptool'
    env=os.environ.copy();env.pop('RKDEVELOPTOOL_RAM_LOCATION',None)
    found=subprocess.run([str(tool),'ld'],capture_output=True,text=True,env=env,check=True)
    report['enumeration']=found.stdout
    matches=re.findall(r'Vid=0x2207,Pid=0x110c,LocationID='+re.escape(location)+r'\s+Maskrom',found.stdout)
    assert len(matches)==1,'DUT1 location not uniquely present in maskrom'
    env['RKDEVELOPTOOL_RAM_LOCATION']=location
    load=subprocess.run([str(tool),'db',str(image)],capture_output=True,text=True,env=env,timeout=30)
    report['download']={'exitCode':load.returncode,'stdout':load.stdout,'stderr':load.stderr}
    assert load.returncode==0 and 'Selected RAM download LocationID='+location in load.stdout,'Selected RAM download failed'
    deadline=time.monotonic()+40
    while time.monotonic()<deadline:
        ports=[p for p in list_ports.comports() if (p.vid,p.pid,p.serial_number)==(0x1209,3,identity)]
        if len(ports)==1:break
        time.sleep(.1)
    else:raise TimeoutError('DUT1 USB CDC did not appear')
    report['port']=ports[0].device
    if args.leave_app_running:
        report.update(passed=True,appNotInterrupted=True,consoleGate='skipped; download/enumeration only')
    else:
        autostart=manifest['features']=='app-autostart'
        if autostart:
            # Original native splash completes before interrupting the warning screen.
            time.sleep(5)
        gate='app_autostart_gate.py' if autostart else 'usb_only_gate.py'
        marker=b'@@PASS frozen-app-autostart-status-screen-usb-interrupt-blank-repl' if autostart else b'@@PASS usb-only-pins-released'
        result=subprocess.run(['uv','run','--python','3.13','--with','pyserial==3.5','python',str(root/'tools/usb_console.py'),str(root/'micropython'/gate),'--port',ports[0].device,'--timeout','12'],capture_output=True,timeout=25)
        (folder/'console-host.txt').write_bytes(result.stdout+result.stderr)
        report['passed']=result.returncode==0 and b'\r\n'+marker+b'\r\n' in result.stdout
        if not report['passed']:raise RuntimeError('DUT1 console/pin-release gate failed')
except Exception as e:report['error']=str(e)
finally:
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));print('Evidence:',folder)
raise SystemExit(0 if report['passed'] else 1)
