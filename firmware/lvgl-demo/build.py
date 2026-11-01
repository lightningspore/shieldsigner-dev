"""Build pinned LVGL as a static ARMv7/musl demo using mise Zig."""
from pathlib import Path
import subprocess
from artifact_paths import ROOT as root, DEMO_WORK as out
lvgl = out / 'lvgl'
pin = '85aa60d18b3d5e5588d7b247abf90198f07c8a63'
out.mkdir(parents=True, exist_ok=True)
if not lvgl.exists():
    subprocess.run(['git','clone','--depth','1','--branch','v9.5.0','https://github.com/lvgl/lvgl.git',str(lvgl)],check=True)
assert subprocess.check_output(['git','-C',str(lvgl),'rev-parse','HEAD'],text=True).strip() == pin
sources = sorted((lvgl/'src').rglob('*.c'))
cmd = ['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-mcpu=cortex_a7','-O2','-static','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-DLV_CONF_INCLUDE_SIMPLE','-I'+str(root/'firmware/lvgl-demo'),'-I'+str(lvgl),str(root/'firmware/lvgl-demo/demo.c'),*map(str,sources),'-lm','-o',str(out/'lvgl-demo')]
subprocess.run(cmd,check=True)
print(out/'lvgl-demo')
