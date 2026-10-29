#!/usr/bin/env python3
"""Opt-in standard-kernel zram image hooks; never run on the signing device."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess

SDK_PIN = '0b5c1f30ca6333b7ec5af70d26511da9ef8d39af'
PROFILE = 'zram16-lzo'
RUNTIME_LINES = ['ulimit -l 4096', 'export SHIELDSIGNER_SMALL_RAM=1', 'export SHIELDSIGNER_CAMERA_LOCK_CODE=1']
RUNTIME_POLICY = {'smallRam': True, 'nativeReadOnlyCodeLock': True, 'memlockLimitKiB': 4096}
INSTALL = Path('usr/lib/shieldsigner-camera')
REQUIRED = {'CONFIG_SWAP':'y', 'CONFIG_ZSMALLOC':'m', 'CONFIG_ZRAM':'m',
            'CONFIG_CRYPTO_LZO':'y', 'CONFIG_ZRAM_WRITEBACK':'n',
            'CONFIG_ZRAM_MEMORY_TRACKING':'n', 'CONFIG_ZSMALLOC_STAT':'n'}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def selected(bundle):
    data = json.loads((bundle/'manifest.json').read_text())
    profile = data.get('memoryProfile', 'none')
    if profile not in ['none', PROFILE]:
        raise ValueError('Unknown image memory profile')
    return profile == PROFILE

def sdk_revision(sdk):
    revision = subprocess.check_output(['git','-C',str(sdk),'rev-parse','HEAD'],text=True).strip()
    if revision != SDK_PIN:
        raise ValueError('Unreviewed zram SDK revision')

def states(text):
    result = {}
    for line in text.splitlines():
        match = re.fullmatch(r'(CONFIG_\w+)=(\S+)',line)
        if match:
            key,value = match.groups()
        else:
            match = re.fullmatch(r'# (CONFIG_\w+) is not set',line)
            if not match: continue
            key,value = match[1],'n'
        if key in result:
            raise ValueError('Duplicate kernel option: '+key)
        result[key] = value
    return result

def configure_kernel(sdk):
    sdk_revision(sdk)
    board = (sdk/'.BoardConfig.mk').read_text()
    if not re.search(r'^export RK_KERNEL_DTS=["\']?rv1103g-luckfox-pico-mini.dts["\']?$',board,re.M):
        raise ValueError('Zram profile supports only the reviewed Mini DTS')
    if not re.search(r'^export RK_KERNEL_DEFCONFIG=["\']?luckfox_rv1106_linux_defconfig["\']?$',board,re.M):
        raise ValueError('Unexpected selected kernel defconfig')
    path = sdk/'sysdrv/source/kernel/arch/arm/configs/luckfox_rv1106_linux_defconfig'
    original = path.read_text()
    current = states(original)
    for key,value in REQUIRED.items():
        # Only baseline absent/disabled options or this exact opt-in state.
        if current.get(key) not in [None,'n',value]:
            raise ValueError('Unreviewed zram kernel option: '+key)
    lines = [line for line in original.splitlines()
             if not any(re.match(r'^(?:# )?'+key+r'(?:=| is not set$)',line) for key in REQUIRED)]
    lines.extend(key+'='+value if value!='n' else '# '+key+' is not set' for key,value in REQUIRED.items())
    desired = '\n'.join(lines)+'\n'
    path.write_text(desired)
    return {'memoryProfile':PROFILE,'defconfigBeforeSha256':hashlib.sha256(original.encode()).hexdigest(),
            'defconfigAfterSha256':digest(path),'requiredKernelOptions':REQUIRED}

def module_info(path,name):
    raw = path.read_bytes()
    if len(raw)<20 or raw[:6]!=b'\x7fELF\x01\x01' or struct.unpack_from('<HH',raw,16)!=(1,40):
        raise ValueError('Expected ARM relocatable kernel module: '+name)
    offset = raw.find(b'vermagic=')
    if offset<0: raise ValueError('Module vermagic missing: '+name)
    magic = raw[offset+9:].split(b'\0',1)[0].decode('ascii')
    if not magic.startswith('5.10.160 ') or b'name='+name.encode()+b'\0' not in raw:
        raise ValueError('Wrong module name/kernel: '+name)
    return {'sha256':digest(path),'bytes':len(raw),'vermagic':magic}

def install(root,sdk,bundle):
    sdk_revision(sdk)
    proof = json.loads((bundle/'payload/kernel-camera-abi.json').read_text())
    config = sdk/'sysdrv/source/objs_kernel/.config'
    if digest(config)!=proof['kernelConfigSha256']:
        raise ValueError('Zram requires a new exact compiled-kernel ABI receipt')
    actual = states(config.read_text())
    if any(actual.get(key,'n')!=value for key,value in REQUIRED.items()):
        raise ValueError('Generated kernel does not implement requested zram profile')
    modules = {name:module_info(sdk/'sysdrv/out/kernel_drv_ko'/(name+'.ko'),name)
               for name in ['zsmalloc','zram']}
    if len({row['vermagic'] for row in modules.values()})!=1:
        raise ValueError('Zram module vermagic differs')
    record_path = root/INSTALL/'image-installation.json'
    camera = json.loads(record_path.read_text())
    if camera['kernelInputs']['kernelConfigSha256']!=proof['kernelConfigSha256']:
        raise ValueError('Camera/kernel profile mismatch')
    launcher = root/'usr/bin/shieldsigner-launch'
    original = launcher.read_text()
    if digest(launcher)!=camera['startupSha256']['usr/bin/shieldsigner-launch']:
        raise ValueError('Launcher changed after reviewed camera installation')
    anchor = '#!/bin/sh\nset -eu\n'
    if not original.startswith(anchor) or original.count(anchor)!=1:
        raise ValueError('Unexpected launcher shape')
    additions = {}
    for name,info in modules.items():
        target = root/INSTALL/'zram'/(name+'.ko')
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(sdk/'sysdrv/out/kernel_drv_ko'/(name+'.ko'),target)
        target.chmod(0o644)
        additions[str(target.relative_to(root))] = target
    setup = (bundle/'image-profiles/enable-zram-image.sh.in').read_text()
    replacements = {'@KERNEL_CONFIG_SHA256@':proof['kernelConfigSha256'],
                    '@ZSMALLOC_SHA256@':modules['zsmalloc']['sha256'], '@ZRAM_SHA256@':modules['zram']['sha256']}
    for before,after in replacements.items():
        if setup.count(before)!=1: raise ValueError('Zram template token changed: '+before)
        setup = setup.replace(before,after)
    setup_path = root/INSTALL/'enable-zram-image.sh'
    setup_path.write_text(setup);setup_path.chmod(0o755)
    init = root/'etc/init.d/S20zram'
    if init.exists(): raise ValueError('Foreign S20zram already exists')
    init.write_bytes((bundle/'image-profiles/S20zram').read_bytes());init.chmod(0o755)
    launcher.write_text(original.replace(anchor,anchor+'# Explicit tested Mini memory policy; keep GPIO/display selection separate.\n'+'\n'.join(RUNTIME_LINES)+'\n# Required memory setup; failure holds the application before imports.\n/usr/lib/shieldsigner-camera/enable-zram-image.sh\n',1))
    additions.update({str(path.relative_to(root)):path for path in [setup_path,init,launcher]})
    profile = {'kind':'standard-kernel-zram-image-profile','memoryProfile':PROFILE,
               'kernelConfigSha256':proof['kernelConfigSha256'],'moduleFiles':modules,
               'logicalDiskBytes':16777216,'compressedMemoryLimitBytes':8388608,'algorithm':'lzo',
               'writeback':False,'sdSwap':False,'runtimePolicy':RUNTIME_POLICY,'bootQualified':False,
               'files':{name:{'sha256':digest(path),'mode':path.stat().st_mode&0o777} for name,path in additions.items() if name != 'usr/bin/shieldsigner-launch'}}
    profile_path = root/INSTALL/'zram-image-profile.json'
    profile_path.write_text(json.dumps(profile,indent=2)+'\n');profile_path.chmod(0o644)
    additions[str(profile_path.relative_to(root))] = profile_path
    # Extend the existing trusted build receipt, not the verifier's acceptance
    # rules: its pre-mkfs gate now checks every new file and the guarded launcher.
    for name,path in additions.items():
        camera['startupSha256'][name] = digest(path)
        camera['startupModes'][name] = path.stat().st_mode&0o777
    camera['memoryProfile'] = PROFILE
    camera['memoryRuntimePolicy'] = RUNTIME_POLICY
    record_path.write_text(json.dumps(camera,indent=2)+'\n')
    return profile

def verify(root):
    profile = json.loads((root/INSTALL/'zram-image-profile.json').read_text())
    if profile['memoryProfile']!=PROFILE: raise ValueError('Unexpected installed zram profile')
    if profile.get('runtimePolicy') != RUNTIME_POLICY: raise ValueError('Wrong memory runtime policy')
    launcher_lines=(root/'usr/bin/shieldsigner-launch').read_text().splitlines()
    if any(launcher_lines.count(line)!=1 for line in RUNTIME_LINES): raise ValueError('Memory launcher policy missing/duplicated')
    for name,info in profile['files'].items():
        path=root/name
        if digest(path)!=info['sha256'] or path.stat().st_mode&0o777!=info['mode']:
            raise ValueError('Installed zram asset changed: '+name)
    return {'memoryProfile':PROFILE,'filesVerified':len(profile['files']),'bootQualified':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--kernel',type=Path);group.add_argument('--rootfs',type=Path);group.add_argument('--verify',type=Path)
    p.add_argument('--sdk',type=Path)
    a=p.parse_args();bundle=Path(__file__).resolve().parent
    if not selected(bundle): print(json.dumps({'memoryProfile':'none','changed':False}));return
    if a.kernel: result=configure_kernel(a.kernel)
    elif a.rootfs:
        if not a.sdk:p.error('--sdk required with --rootfs')
        result=install(a.rootfs,a.sdk,bundle)
    else: result=verify(a.verify)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
