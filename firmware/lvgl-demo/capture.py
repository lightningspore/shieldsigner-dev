"""Pull transmitted LCD pixels; output stays in ignored dist/. Requires Pillow."""
from pathlib import Path
import subprocess
import sys
from PIL import Image
from artifact_paths import DEMO_WORK as out
name=sys.argv[1] if len(sys.argv)>1 else 'screen'
if not name.replace('-','').isalnum(): raise ValueError('Use a simple capture name')
subprocess.run(['adb','pull','/tmp/lvgl-demo.rgb565',str(out/(name+'.rgb565'))],check=True)
p=(out/(name+'.rgb565')).read_bytes()
if len(p)!=115200: raise ValueError('Incomplete screenshot')
rgb=bytearray()
for i in range(0,len(p),2):
    v=int.from_bytes(p[i:i+2],'big')
    rgb.extend(((v>>11)*255//31,((v>>5)&63)*255//63,(v&31)*255//31))
Image.frombytes('RGB',(240,240),bytes(rgb)).resize((720,720),Image.Resampling.NEAREST).save(out/(name+'.png'))
print(out/(name+'.png'))
