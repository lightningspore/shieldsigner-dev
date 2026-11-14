# SPDX-License-Identifier: MIT
"""Cross-compile the locked existing SeedSigner LVGL screen library, no Linux host."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
root=Path(__file__).resolve().parents[1];repo=root.parent
cfg=json.loads((root/'cxx-toolchain.json').read_text())
tools=root/'.tools'/cfg['directory']/'bin'
lock=json.loads((repo/'firmware/lvgl-app/sources.lock.json').read_text())
sources=repo/'dist/firmware/sources/lvgl'
for name in ('application','screens','lvgl'):
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=sources/name,text=True).strip()
    assert actual==lock[name]['commit'],name+' source pin changed'
out=root/'build/ui';out.mkdir(parents=True,exist_ok=True)
original=sources/'screens/components/seedsigner';patched=out/'source'
core=patched/'components/seedsigner'
# Refresh the disposable copy before applying the exact existing portability patches.
if core.exists():shutil.rmtree(core)
shutil.copytree(original,core)
(patched/'third_party').mkdir(exist_ok=True,parents=True)
link=patched/'third_party/lvgl'
if not link.exists():link.symlink_to(sources/'lvgl',target_is_directory=True)
patches=sorted((repo/'firmware/lvgl-app/patches').glob('*.patch'))
for patch in patches:
    subprocess.run(['git','apply','--check','--unsafe-paths','--directory='+str(patched),str(patch)],check=True,cwd=repo)
    subprocess.run(['git','apply','--unsafe-paths','--directory='+str(patched),str(patch)],check=True,cwd=repo)
subprocess.run(['uv','run','--python','3.13','--with','pillow==11.3.0','python',str(repo/'firmware/lvgl-app/assets.py'),str(sources/'application'),str(sources/'screens'),str(out/'branding')],check=True)
lvgl=sources/'lvgl'
fonts=['opensans_western_regular','opensans_western_semibold','seedsigner_icons_24_4bpp','seedsigner_icons_26_4bpp','seedsigner_icons_36_4bpp','seedsigner_icons_48_4bpp','inconsolata_semibold_24_4bpp','inconsolata_semibold_22_4bpp']
c=list(lvgl.joinpath('src').rglob('*.c'))+list(core.glob('*.c'))+list((out/'branding').glob('*.c'))+[core/'fonts'/(n+'.c') for n in fonts]+[core/'images'/(n+'_img.c') for n in ('seedsigner_logo','hrf_logo','btc_logo')]+[root/'ui/syscalls.c']
registry=sorted(p.stem for p in (core/'screens').glob('*_screen.cpp'))
(out/'registry.h').write_text('struct ScreenEntry { const char *name; void (*build)(void*); };\nstatic const ScreenEntry registry[] = {\n'+''.join('{"'+n+'",'+n+'},\n' for n in registry)+'};\n')
cpp=list(core.glob('*.cpp'))+list((core/'screens').glob('*_screen.cpp'))+[root/'ui/bridge.cpp']
flags=['-Os','-mthumb','-mcpu=cortex-a7','-mfloat-abi=soft','-mno-unaligned-access','-ffunction-sections','-fdata-sections','-funwind-tables','-fexceptions','-fno-pie','-DLV_CONF_INCLUDE_SIMPLE','-DSUPPORT_DISPLAY_HEIGHT_240=1','-DJSON_NO_IO=1']
flags+=['-I'+str(p) for p in (lvgl,core,sources/'screens/components/nlohmann_json/include',root/'ui',repo/'firmware/lvgl-app/native',out)]
header_hash=hashlib.sha256()
for base in (core,root/'ui',repo/'firmware/lvgl-app/native',lvgl/'src'):
    for p in sorted(base.rglob('*.h')):header_hash.update(p.read_bytes())
header_hash.update((out/'registry.h').read_bytes())
headers=header_hash.digest()
objects=out/'objects';objects.mkdir(exist_ok=True)
def compile_one(source):
    extra=['-std=c++17','-fno-rtti','-fno-threadsafe-statics'] if source.suffix=='.cpp' else ['-std=gnu11']
    digest=hashlib.sha256(source.read_bytes()+str(flags+extra).encode()+headers+cfg['sha256'].encode()).hexdigest()
    target=objects/(digest+'.o')
    if not target.exists():
        compiler=tools/('arm-none-eabi-g++' if source.suffix=='.cpp' else 'arm-none-eabi-gcc')
        subprocess.run([str(compiler),*flags,*extra,'-c',str(source),'-o',str(target)],check=True)
    return target
with ThreadPoolExecutor(max_workers=4) as pool:built=list(pool.map(compile_one,sorted(c+cpp)))
archive=out/'libsignerui.a'
# Recreate it: retaining old hash-named members would link stale definitions.
archive.unlink(missing_ok=True)
subprocess.run([str(tools/'arm-none-eabi-ar'),'rcs',str(archive),*map(str,built)],check=True)
manifest={'sources':{k:lock[k] for k in ('application','screens','lvgl')},'toolchain':cfg,'flags':flags,'archiveSha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'objects':len(built),'registry':registry,'patches':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in patches},'adapterHeaders':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (repo/'firmware/lvgl-app/native').glob('*.h')},'portSources':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'ui').glob('*') if p.is_file()}}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'archive':str(archive),'objects':len(built),'registry':registry,'sha256':manifest['archiveSha256']},indent=2))
