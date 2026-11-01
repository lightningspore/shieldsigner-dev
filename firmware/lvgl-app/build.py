"""Cross-build isolated upstream LVGL screen host; no Pi/MicroPython bindings."""
from pathlib import Path
import subprocess
import sys
import hashlib
import shutil
from concurrent.futures import ThreadPoolExecutor
from sources import fetch,DIST,HERE
application=fetch('application');lvgl=fetch('lvgl'); screens=fetch('screens'); core=screens/'components/seedsigner'
subprocess.run(['git','-C',str(screens),'submodule','update','--init','--depth','1','third_party/lvgl'],check=True)
if subprocess.check_output(['git','-C',str(screens/'third_party/lvgl'),'rev-parse','HEAD'],text=True).strip()!=__import__('sources').LOCK['lvgl']['commit']:
    raise RuntimeError('Screen corpus LVGL pin differs from locked library')
out=DIST/('build-host' if '--host' in sys.argv else 'build');out.mkdir(parents=True,exist_ok=True)
subprocess.run(['mise','exec','--','uv','run','--with','pillow==11.3.0','python',str(HERE/'assets.py'),str(application),str(screens),str(out/'branding')],check=True)
# Apply local portability patches to a disposable copy, never the pinned checkout.
patched=out/'source'
shutil.copytree(core,patched/'components/seedsigner',dirs_exist_ok=True)
(patched/'third_party').mkdir(parents=True,exist_ok=True)
link=patched/'third_party/lvgl'
if link.is_symlink() and str(link.readlink())!=str(lvgl):link.unlink()
if not link.exists():link.symlink_to(lvgl,target_is_directory=True)
for patch in sorted((HERE/'patches').glob('*.patch')):
    subprocess.run(['git','apply','--check','--unsafe-paths','--directory='+str(patched),str(patch)],check=True)
    subprocess.run(['git','apply','--unsafe-paths','--directory='+str(patched),str(patch)],check=True)
core=patched/'components/seedsigner'
registry=sorted(p.stem for p in (core/'screens').glob('*_screen.cpp'))
(out/'registry.h').write_text('struct ScreenEntry { const char *name; void (*build)(void*); };\nstatic const ScreenEntry registry[] = {\n'+''.join('{"'+n+'",'+n+'},\n' for n in registry)+'};\n')
font_names=['opensans_western_regular','opensans_western_semibold','seedsigner_icons_24_4bpp','seedsigner_icons_26_4bpp','seedsigner_icons_36_4bpp','seedsigner_icons_48_4bpp','inconsolata_semibold_24_4bpp','inconsolata_semibold_22_4bpp']
c=list((out/'branding').glob('*.c'))+list((lvgl/'src').rglob('*.c'))+[core/'fonts'/(n+'.c') for n in font_names]+[core/'images'/(n+'_img.c') for n in ['seedsigner_logo','hrf_logo','btc_logo']]+list(core.glob('*.c'))
cpp=list(core.glob('*.cpp'))+list((core/'screens').glob('*_screen.cpp'))+[HERE/'native/host.cpp']
flags=['-target','arm-linux-musleabihf','-mcpu=cortex_a7'] if '--host' not in sys.argv else []
flags+=['-O2','-ffunction-sections','-fdata-sections','-DLV_CONF_INCLUDE_SIMPLE','-DSUPPORT_DISPLAY_HEIGHT_240=1',*['-I'+str(p) for p in [lvgl,core,screens/'components/nlohmann_json/include',HERE/'native',out]]]
base=['mise','exec','zig@0.15.2','--','zig']
def compile_one(source):
    compiler='c++' if source.suffix=='.cpp' else 'cc'
    extra=['-std=c++17'] if compiler=='c++' else []
    # Include dependency trees in the cache key; a config/header change cannot
    # accidentally reuse an object built for another configuration.
    digest=hashlib.sha256(source.read_bytes()+str(flags).encode()+headers).hexdigest()
    obj=out/(digest+'.o')
    if not obj.exists():
        subprocess.run([*base,compiler,*flags,*extra,'-c',str(source),'-o',str(obj)],check=True)
    return obj
headers=(HERE/'sources.lock.json').read_bytes()+b''.join(p.read_bytes() for directory in (HERE/'native',core) for p in sorted(directory.glob('*.h')))
with ThreadPoolExecutor(max_workers=4) as pool:
    objects=list(pool.map(compile_one,sorted(c)+sorted(cpp)))
link_flags=['-static','-s','-Wl,--gc-sections'] if '--host' not in sys.argv else []
subprocess.run([*base,'c++',*flags,*link_flags,*map(str,objects),'-o',str(out/'shieldsigner-lvgl')],check=True)
print(out/'shieldsigner-lvgl')

from build_manifest import inputs,sha256
import json
(out/'build-manifest.json').write_text(json.dumps(dict(target='host' if '--host' in sys.argv else 'arm-linux-musleabihf',binarySha256=sha256(out/'shieldsigner-lvgl'),inputs=inputs(HERE)),indent=2)+'\n')
