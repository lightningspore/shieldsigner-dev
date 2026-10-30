#!/usr/bin/env python3
"""Read-only ADB verification of a flashed native image against local receipts.

This verifies boot/file/runtime identity, not a physical power-cycle event.
No interpreter, GPIO writes, image captures or settings changes run on target.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import stat
import time

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--bundle',type=Path,required=True)
p.add_argument('--installation',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--serial',default='0a523b8b23110ffc')
p.add_argument('--previous-boot-id')
a=p.parse_args()
if a.output.exists():p.error('Choose a new immutable boot receipt path')
manifest_path=a.bundle/'manifest.json';manifest=json.loads(manifest_path.read_text())
installation=json.loads(a.installation.read_text())
identity=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
if installation['bundleManifestSha256']!=identity:raise ValueError('Local receipts disagree')
if manifest.get('frontendBackend')!='rust':raise ValueError('Expected native frontend bundle')
def shell(command):return subprocess.check_output(['adb','-s',a.serial,'shell',command],text=True,timeout=30).strip()
report={'kind':'native-image-read-only-boot-identity','passed':False,'expectedBundleSha256':identity,
        'coldPowerCycleAttestedByThisTool':False,'containsImagesSeedsOrDecodedQr':False}
def save():
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
try:
    release=shell('cat /etc/seedsigner-os-release')
    match=re.search(r'^SHIELDSIGNER_CAMERA_BUNDLE_SHA256="([0-9a-f]{64})"$',release,re.M)
    report['observedBundleSha256']=match[1] if match else None
    report['bootId']=shell('cat /proc/sys/kernel/random/boot_id')
    report['bootIdChanged']=bool(a.previous_boot_id and report['bootId']!=a.previous_boot_id)
    if report['observedBundleSha256']!=identity:raise ValueError('Booted image identity differs; temporary helpers do not qualify')
    if a.previous_boot_id and not report['bootIdChanged']:raise ValueError('Boot ID did not change')
    kernel=shell('uname -r');model=shell('cat /proc/device-tree/model').strip('\0')
    if kernel!=installation['kernelInputs']['kernelVersion'] or model!='Luckfox Pico Mini':raise ValueError('Wrong kernel/board')
    report.update(kernelRelease=kernel,deviceTreeModel=model)
    mounts=[line.split() for line in shell('cat /proc/mounts').splitlines()]
    roots=[row for row in mounts if len(row)>3 and row[1]=='/']
    if not any(row[2]=='squashfs' and 'ro' in row[3].split(',') for row in roots):raise ValueError('Expected read-only squashfs root')
    expected={}
    for name,info in manifest['files'].items():
        if name.startswith('payload/'):
            expected['/usr/lib/shieldsigner-camera/'+name[len('payload/'):]]=(info['sha256'],info['mode'])
    for name,sha in installation['startupSha256'].items():expected['/'+name]=(sha,installation['startupModes'][name])
    expected['/'+installation['cameraSource']]=(installation['cameraSourceSha256'],0o644)
    if any(row[1]!='/' and any(name==row[1] or name.startswith(row[1].rstrip('/')+'/') for name in expected) for row in mounts):raise ValueError('Verified runtime path has a temporary mount overlay')
    files=[]
    # Batching keeps target work in shell utilities, with no extra Python heap.
    names=list(expected)
    for offset in range(0,len(names),20):
        batch=names[offset:offset+20]
        raw=shell('sha256sum '+' '.join(shlex.quote(name) for name in batch))
        hashes={line.split(maxsplit=1)[1]:line.split()[0] for line in raw.splitlines()}
        raw=shell('ls -ldn '+' '.join(shlex.quote(name) for name in batch))
        raw=re.sub(r'\x1b\[[0-9;]*m','',raw)
        modes={}
        for line in raw.splitlines():
            matches=[name for name in batch if line.endswith(name)]
            if len(matches)==1:modes[matches[0]]=line.split()[0]
        for name in batch:
            sha,mode=expected[name]
            if hashes.get(name)!=sha or modes.get(name)!=stat.filemode(stat.S_IFREG|mode):raise ValueError('Installed file differs: '+name)
            files.append({'path':name.lstrip('/'),'sha256':sha,'mode':mode})
    report['files']=files
    if shell('cat /proc/device-tree/serial@ff4c0000/status').strip('\0')!='disabled':raise ValueError('UART2 not disabled')
    cmdline=shell('cat /proc/cmdline')
    if re.findall(r'(?:^|\s)rk_dma_heap_cma=(\S+)',cmdline)!=['12M']:raise ValueError('Expected CMA12')
    mm_stat=shell('cat /sys/block/zram0/mm_stat').split()
    if shell('cat /sys/block/zram0/disksize')!='16777216' or len(mm_stat)<4 or mm_stat[3]!='8388608':raise ValueError('Wrong zram limits')
    if '[lzo]' not in shell('cat /sys/block/zram0/comp_algorithm'):raise ValueError('Wrong zram algorithm')
    swaps=[line.split()[0] for line in shell('cat /proc/swaps').splitlines()[1:]]
    if swaps!=['/dev/zram0']:raise ValueError('Unexpected swap device(s)')
    raw=shell(r'''for proc in /proc/[0-9]*; do
 read name < "$proc/comm" || continue
 if test "$name" = python3; then
  echo PID:${proc##*/}
  tr '\000' ' ' < "$proc/cmdline"
  echo
 fi
done''')
    candidates=[]
    for block in raw.split('PID:')[1:]:
        pid,_,command=block.partition('\n')
        if '/usr/lib/shieldsigner-camera/python/shieldsigner_integration.py' in command:candidates.append(pid.strip())
    if len(candidates)!=1:raise ValueError('Expected one normally launched packaged app')
    maps=shell('cat /proc/'+candidates[0]+'/maps')
    library='/usr/lib/shieldsigner-camera/python/shieldsigner_lcd.abi3.so'
    if library not in maps or '/tmp/native-' in maps:raise ValueError('App did not map the packaged native extension')
    report.update(passed=True,verifiedFileCount=len(files),readOnlyRoot=True,temporaryRuntimeOverlays=False,
                  cmaSize='12M',zramPolicyVerified=True,normalPackagedApp=True,packagedNativeLibraryMapped=True)
except Exception as error:
    report['failure']=str(error);save();raise
save();print(json.dumps({'passed':True,'verifiedFileCount':len(files),'bootIdChanged':report['bootIdChanged'],
                       'physicalPowerCycleRequiresSeparateEvidence':True},indent=2))
