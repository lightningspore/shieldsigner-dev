# SPDX-License-Identifier: MIT
"""Exercise real USB reopen and interruption without touching pins or storage."""
import argparse
import datetime
import json
from pathlib import Path
import time
import subprocess
import re
import serial
from serial.tools import list_ports

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--port')
p.add_argument('--reset-to-maskrom',help='Expected hex LocationID after USB Ctrl-] warm reset')
a=p.parse_args()
ports=[x for x in list_ports.comports() if (x.vid,x.pid)==(0x1209,3) and (not a.port or a.port==x.device)]
if len(ports)!=1:p.error('Select exactly one development USB console')
port=ports[0]
folder=Path(__file__).resolve().parents[1]/'logs/phase-11'/('debug-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
folder.mkdir(parents=True)
seen=bytearray();report={'port':port.device,'location':port.location,'reopens':0,'keyboardInterrupt':False,'passed':False}
def until(s, marker, timeout=5):
    local=bytearray();end=time.monotonic()+timeout
    while time.monotonic()<end:
        data=s.read(4096);seen.extend(data);local.extend(data)
        if marker in local:return bytes(local)
    raise TimeoutError(repr(marker))
try:
    for index in range(3):
        with serial.Serial(port.device,115200,timeout=.1,write_timeout=3,exclusive=True) as s:
            s.write(b'\x03\x02\r');until(s,b'>>> ')
            token=('@@USB_REOPEN_'+str(index)).encode()
            s.write(b"print('"+token+b"')\r")
            response=until(s,b'\r\n'+token+b'\r\n')
            report['reopens']+=1
    with serial.Serial(port.device,115200,timeout=.1,write_timeout=3,exclusive=True) as s:
        s.write(b'\x03\x02\r');until(s,b'>>> ')
        s.write(b'\x05');until(s,b'paste mode')
        s.write(b'while True:\n    pass\n\x04')
        time.sleep(.2)
        s.write(b'\x03')
        until(s,b'KeyboardInterrupt')
        s.write(b"\rprint('@@USB_AFTER_INTERRUPT')\r")
        until(s,b'\r\n@@USB_AFTER_INTERRUPT\r\n')
        report['keyboardInterrupt']=True
    if a.reset_to_maskrom:
        with serial.Serial(port.device,115200,timeout=.1,write_timeout=3,exclusive=True) as s:
            s.write(b'\x1d')
            s.flush()
            time.sleep(.15)
        tool=Path(__file__).resolve().parents[1]/'.tools/rkdeveloptool/rkdeveloptool'
        end=time.monotonic()+8
        while time.monotonic()<end:
            probe=subprocess.run([str(tool),'ld'],capture_output=True,text=True,timeout=3)
            if re.search(r'Vid=0x2207,Pid=0x110c,LocationID='+re.escape(a.reset_to_maskrom)+r'\s+Maskrom',probe.stdout):
                report['usbResetToMaskrom']=True
                report['maskromAfter']=probe.stdout
                break
            time.sleep(.1)
        else:raise TimeoutError('USB reset did not return expected target to maskrom')
    report['passed']=report['reopens']==3 and report['keyboardInterrupt']
except Exception as e:report['error']=str(e)
finally:
    (folder/'serial.bin').write_bytes(seen)
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));print('Evidence:',folder)
raise SystemExit(0 if report['passed'] else 1)
