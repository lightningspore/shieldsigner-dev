#!/usr/bin/env python3
"""Launch normal integration with explicit diagnostic button access; no UI skip."""
import json
import runpy
import sys
sys.path[:0]=['/opt/src','/usr/lib/shieldsigner-camera/python']
from button_control import install
control=install('/opt/src')
from seedsigner.gui.renderer import Renderer
original_show=Renderer.show_image

def show_image(self,image=None,alpha_overlay=None,show_direct=False):
    result=original_show(self,image,alpha_overlay,show_direct)
    self._diagnostic_last_image=image if show_direct else self.canvas
    return result

Renderer.show_image=show_image

def capture(path):
    renderer=Renderer.get_instance()
    image=getattr(renderer,'_diagnostic_last_image',None)
    if image is None: image=renderer.canvas
    temporary=path.with_suffix('.tmp')
    image.save(temporary,format='PNG')
    temporary.replace(path)

control.capture=capture
print(json.dumps({'diagnosticButtons' :str(control.directory),'physicalInputsPreserved':True,'gpioWrites':False}),flush=True)
sys.argv=['shieldsigner_integration.py','--app-root','/opt/src','--config','/usr/lib/shieldsigner-camera/owner.json','--qr-reader','/usr/lib/shieldsigner-camera/shieldsigner-qr-reader']
runpy.run_path('/usr/lib/shieldsigner-camera/python/shieldsigner_integration.py',run_name='__main__')
