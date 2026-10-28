#!/usr/bin/env python3
"""Capture bounded actual SDK inputs after kernel build; never build a rootfs."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__); p.add_argument('sdk',type=Path); p.add_argument('output',type=Path); a=p.parse_args()
bundle=Path(__file__).resolve().parent; manifest=json.loads((bundle/'manifest.json').read_text()); proof=json.loads((bundle/'payload/kernel-camera-abi.json').read_text())
revision=subprocess.check_output(['git','-C',str(a.sdk),'rev-parse','HEAD'],text=True).strip()
if revision!=proof['sdkRevision']: raise ValueError('Probe SDK differs from reviewed revision')
a.output.mkdir(parents=True,exist_ok=False)
files=['sysdrv/source/objs_kernel/.config','sysdrv/source/objs_kernel/include/generated/utsrelease.h','sysdrv/out/bin/board_uclibc_rv1106/rv1103g-luckfox-pico-mini.dtb']
fixed={}
for row in proof['actualSdkHeaderHashes']: fixed['sysdrv/source/kernel/include/uapi/linux/'+row['name']]=row['sha256']
for name,sha in proof['driverSourceSha256'].items(): fixed['sysdrv/source/kernel/'+name]=sha
rows={}
for name in files+list(fixed):
 src=a.sdk/name; sha=hashlib.sha256(src.read_bytes()).hexdigest()
 if name in fixed and sha!=fixed[name]: raise ValueError('Probe ABI source changed:'+name)
 dst=a.output/name; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst); rows[name]=sha
record={'kind':'shieldsigner-compiled-kernel-probe','imageVariant':manifest['imageVariant'],'imageBuilt':False,'sdkRevision':revision,'files':rows}
(a.output/'probe.json').write_text(json.dumps(record,indent=2)+'\n'); print(json.dumps(record,indent=2))
