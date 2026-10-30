#!/usr/bin/env python3
"""Send one named diagnostic button press over existing ADB; wait for release."""
import argparse
import json
import re
import shlex
import subprocess
import time
import uuid
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('key',choices=['KEY_UP','KEY_DOWN','KEY_LEFT','KEY_RIGHT','KEY_PRESS','KEY1','KEY2','KEY3'])
p.add_argument('--hold-ms',type=int,default=120);p.add_argument('--serial',default='0a523b8b23110ffc');a=p.parse_args()
if not 30<=a.hold_ms<=1500:p.error('hold-ms must be 30..1500')
def shell(command):return subprocess.check_output(['adb','-s',a.serial,'shell',command],text=True,timeout=5)
current=json.loads(shell('cat /tmp/shieldsigner-button-control-current.json'));directory=current['directory']
if not re.fullmatch('/tmp/shieldsigner-buttons-[0-9]+',directory):raise SystemExit('Invalid control directory')
request={'key':a.key,'holdMs':a.hold_ms,'id':uuid.uuid4().hex}
shell('umask 077; printf %s '+shlex.quote(json.dumps(request))+' > '+directory+'/request.tmp && mv '+directory+'/request.tmp '+directory+'/request.json')
end=time.monotonic()+20
while time.monotonic()<end:
 status=json.loads(shell('cat '+directory+'/status.json'))
 if status['id']==request['id'] and status['state']=='released':print(json.dumps({'key':a.key,'holdMs':a.hold_ms,'deliveredAndReleased':True,'uiOutcomeRequiresVerification':True}));break
 if status['state']=='rejected':raise SystemExit('Control rejected request')
 time.sleep(.05)
else:raise SystemExit('No release acknowledgement; do not assume navigation succeeded')
