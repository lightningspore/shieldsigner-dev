#!/usr/bin/env python3
"""Launch normal integration with explicit diagnostic button access; no UI skip."""
import json
import runpy
import sys
sys.path[:0]=['/opt/src','/usr/lib/shieldsigner-camera/python']
from button_control import install
control=install('/opt/src')
print(json.dumps({'diagnosticButtons':str(control.directory),'physicalInputsPreserved':True,'gpioWrites':False}),flush=True)
sys.argv=['shieldsigner_integration.py','--app-root','/opt/src','--config','/usr/lib/shieldsigner-camera/owner.json','--qr-reader','/usr/lib/shieldsigner-camera/shieldsigner-qr-reader']
runpy.run_path('/usr/lib/shieldsigner-camera/python/shieldsigner_integration.py',run_name='__main__')
