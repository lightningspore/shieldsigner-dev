#!/usr/bin/env python3
"""Opt-in Buildroot uClibc/ABI3 LCD package and strict image receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess

INSTALL=Path('usr/lib/shieldsigner-camera')
TARGET='armv7-unknown-linux-uclibceabihf'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def manifest(bundle):
    data=json.loads((bundle/'manifest.json').read_text())
    if data.get('lcdBackend','python') not in ['python','rust']:raise ValueError('Unknown LCD backend')
    return data

def configure(buildroot,bundle,data):
    inputs=data['lcdInputs']
    if not re.fullmatch('[0-9a-f]{64}',inputs['buildRecipeSha256']):raise ValueError('Invalid LCD source identity')
    package=buildroot/'package/shieldsigner-lcd'
    if package.is_symlink():raise ValueError('Foreign LCD package symlink')
    package.mkdir(parents=True,exist_ok=True)
    for name in ['Config.in','shieldsigner-lcd.mk']:
        desired=(bundle/'lcd-package'/name).read_text().replace('@LCD_SOURCE_SHA256@',inputs['buildRecipeSha256'])
        path=package/name
        if path.is_symlink():raise ValueError('Foreign LCD package symlink')
        if path.exists() and path.read_text()!=desired:raise ValueError('Foreign LCD package contents')
        path.write_text(desired)
    config_in=buildroot/'package/Config.in';text=config_in.read_text();source='source "package/shieldsigner-lcd/Config.in"'
    if text.count(source)>1:raise ValueError('Duplicate LCD Config.in source')
    if source not in text:config_in.write_text(text+'\n'+source+'\n')
    options={'BR2_PACKAGE_SHIELDSIGNER_LCD':'y','BR2_PACKAGE_HOST_RUSTC':'y','BR2_PACKAGE_HOST_RUST':'y','BR2_PACKAGE_HOST_RUST_BIN':'n'}
    for relative in ['.config','configs/luckfox_pico_defconfig','configs/luckfox_pico_w_defconfig']:
        path=buildroot/relative
        if not path.is_file():raise ValueError('Missing expected Buildroot defconfig: '+relative)
        lines=path.read_text().splitlines()
        for key,value in options.items():
            matches=[line for line in lines if re.match(r'^(?:# )?'+key+r'(?:=| is not set$)',line)]
            if len(matches)>1:raise ValueError('Duplicate Buildroot option: '+key)
            lines=[line for line in lines if line not in matches]
            lines.append(key+'='+value if value!='n' else '# '+key+' is not set')
        path.write_text('\n'.join(lines)+'\n')
    return {'lcdBackend':'rust','sourceManifestSha256':inputs['sourceManifestSha256'],'target':TARGET,'actualBuildPerformed':False}

def elf_info(path):
    raw=path.read_bytes()
    if len(raw)<52 or raw[:6]!=b'\x7fELF\x01\x01':raise ValueError('LCD library is not ELF32 little-endian')
    import struct
    if struct.unpack_from('<HH',raw,16)!=(3,40):raise ValueError('LCD library is not an ARM shared object')
    offset=struct.unpack_from('<I',raw,32)[0];size,count=struct.unpack_from('<HH',raw,46)
    if size<40 or offset+size*count>len(raw):raise ValueError('Invalid LCD ELF section table')
    sections=[struct.unpack_from('<10I',raw,offset+i*size) for i in range(count)]
    needed=[]
    for section in sections:
        if section[1]!=6:continue
        if section[6]>=len(sections):raise ValueError('Invalid LCD dynamic string table')
        strings=sections[section[6]];table=raw[strings[4]:strings[4]+strings[5]]
        for pos in range(section[4],section[4]+section[5],8):
            tag,value=struct.unpack_from('<II',raw,pos)
            if tag==1:
                end=table.find(b'\0',value)
                if end<0:raise ValueError('Invalid LCD dependency name')
                needed.append(table[value:end].decode('ascii'))
    if 'libc.so.0' not in needed or any('musl' in x or x=='libc.so.6' or 'libpython' in x for x in needed):
        raise ValueError('LCD library does not implement the reviewed uClibc extension contract')
    if b'PyInit_shieldsigner_lcd\0' not in raw:raise ValueError('LCD Python module initialization symbol missing')
    return {'sha256':digest(path),'bytes':len(raw),'neededLibraries':needed,'target':TARGET,'abi3MinimumPython':'3.11'}

def record_build(root,source,bundle,data,cc,rustc):
    if digest(source/'Cargo.lock') != data['lcdInputs']['cargoLockSha256']:raise ValueError('Built LCD Cargo.lock differs from immutable input')
    for name,info in data['files'].items():
        if name.startswith('lcd-source/') and digest(source/name[len('lcd-source/'):]) != info['sha256']:
            raise ValueError('Built LCD source differs: '+name)
    library=root/INSTALL/'python/shieldsigner_lcd.abi3.so'
    info=elf_info(library)
    rust_version=subprocess.check_output([str(rustc),'--version'],text=True).strip()
    if not rust_version.startswith('rustc 1.82.0 '):raise ValueError('Unexpected SDK Rust compiler')
    compiler_version=subprocess.check_output(shlex.split(cc)+['--version'],text=True).splitlines()[0]
    if '8.3.0' not in compiler_version:raise ValueError('Unexpected SDK C compiler')
    shim=root/INSTALL/'python/shieldsigner_lcd_driver.py'
    expected=data['files']['lcd-source/python/shieldsigner_lcd_driver.py']['sha256']
    if digest(shim)!=expected:raise ValueError('Installed LCD shim differs from immutable source')
    record={'kind':'buildroot-uclibc-lcd-artifact','lcdBackend':'rust','library':info,
            'shimSha256':digest(shim),'inputs':data['lcdInputs'],'rustCompiler':rust_version,
            'cCompiler':compiler_version,'cargoLocked':True,'cargoOffline':True,'sourceInputsVerified':True,
            'hardwareQualified':False}
    (root/INSTALL/'lcd-build.json').write_text(json.dumps(record,indent=2)+'\n')
    return record

def install(root,bundle,data):
    record_path=root/INSTALL/'image-installation.json';record=json.loads(record_path.read_text())
    build=root/INSTALL/'lcd-build.json';built=json.loads(build.read_text())
    if built['inputs']!=data['lcdInputs']:raise ValueError('Stale LCD build receipt')
    library=root/INSTALL/'python/shieldsigner_lcd.abi3.so';shim=root/INSTALL/'python/shieldsigner_lcd_driver.py'
    if elf_info(library)!=built['library'] or digest(shim)!=built['shimSha256']:raise ValueError('LCD artifact changed after package build')
    launcher=root/'usr/bin/shieldsigner-launch';text=launcher.read_text();anchor='#!/bin/sh\nset -eu\n'
    if digest(launcher)!=record['startupSha256']['usr/bin/shieldsigner-launch'] or not text.startswith(anchor):raise ValueError('Launcher changed before LCD profile')
    launcher.write_text(text.replace(anchor,anchor+'export SHIELDSIGNER_LCD_BACKEND=rust\n',1))
    for path in [library,shim,build,launcher]:
        name=str(path.relative_to(root));record['startupSha256'][name]=digest(path);record['startupModes'][name]=path.stat().st_mode&0o777
    record['lcdBackend']='rust';record_path.write_text(json.dumps(record,indent=2)+'\n')
    return {'lcdBackend':'rust','librarySha256':digest(library),'hardwareQualified':False}

def verify(root,data):
    record=json.loads((root/INSTALL/'image-installation.json').read_text())
    built=json.loads((root/INSTALL/'lcd-build.json').read_text())
    if record.get('lcdBackend')!='rust' or built['inputs']!=data['lcdInputs']:raise ValueError('Wrong installed LCD profile')
    if (root/'usr/bin/shieldsigner-launch').read_text().splitlines().count('export SHIELDSIGNER_LCD_BACKEND=rust')!=1:raise ValueError('LCD launcher selection missing/duplicated')
    if elf_info(root/INSTALL/'python/shieldsigner_lcd.abi3.so')!=built['library']:raise ValueError('LCD ELF changed')
    if digest(root/INSTALL/'python/shieldsigner_lcd_driver.py')!=built['shimSha256']:raise ValueError('LCD shim changed')
    return {'lcdBackend':'rust','verified':True,'hardwareQualified':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--buildroot',type=Path);g.add_argument('--record-build',type=Path);g.add_argument('--install',type=Path);g.add_argument('--verify',type=Path)
    p.add_argument('--rootfs',type=Path);p.add_argument('--cc');p.add_argument('--rustc',type=Path)
    a=p.parse_args();bundle=Path(__file__).resolve().parent;data=manifest(bundle)
    if data.get('lcdBackend','python')!='rust':print(json.dumps({'lcdBackend':'python','changed':False}));return
    if a.record_build:
        if not all([a.rootfs,a.cc,a.rustc]):p.error('--record-build needs --rootfs/--cc/--rustc')
        result=record_build(a.rootfs,a.record_build,bundle,data,a.cc,a.rustc)
    elif a.buildroot:result=configure(a.buildroot,bundle,data)
    elif a.install:result=install(a.install,bundle,data)
    else:result=verify(a.verify,data)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
