#!/usr/bin/env python3
"""Build only zsmalloc/zram against the exact cached kernel, read-only mounted.

No kernel/config rebuild, image build, module loading, or board changes.
"""
import argparse,datetime,json,subprocess,tarfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',default='root@pve-beelink2');a=p.parse_args()
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');remote='/opt/shieldsigner-build/dist/zram/'+stamp
 script=r'''set -eu
repos=/var/lib/docker/volumes/seedsigner-repos/_data
sdk=$repos/luckfox-pico
out=REMOTE
mkdir -p "$out"
cp "$sdk/sysdrv/source/kernel/mm/zsmalloc.c" "$out/"
cp "$sdk/sysdrv/source/kernel/drivers/block/zram/"*.c "$out/"
cp "$sdk/sysdrv/source/kernel/drivers/block/zram/"*.h "$out/"
printf 'obj-m += zsmalloc.o zram.o\nzram-y := zcomp.o zram_drv.o\n' > "$out/Makefile"
sha256sum "$sdk/sysdrv/source/objs_kernel/.config" "$sdk/sysdrv/source/objs_kernel/Module.symvers" > "$out/cache-before.sha256"
docker image inspect seedsigner-builder:latest --format '{{.Id}}' > "$out/builder-image.txt"
docker run --rm --network none --entrypoint /bin/bash --mount type=bind,src="$repos",dst=/build/repos,readonly --mount type=bind,src="$out",dst=/work seedsigner-builder:latest -c '
set -eu
sdk=/build/repos/luckfox-pico
cross=$sdk/tools/linux/toolchain/arm-rockchip830-linux-uclibcgnueabihf/bin/arm-rockchip830-linux-uclibcgnueabihf-
"${cross}gcc" --version | head -1
make -C "$sdk/sysdrv/source/kernel" O="$sdk/sysdrv/source/objs_kernel" M=/work ARCH=arm CROSS_COMPILE="$cross" -j2 modules
"${cross}nm" -u /work/zsmalloc.ko /work/zram.ko > /work/undefined-symbols.txt
"${cross}readelf" -p .modinfo /work/zsmalloc.ko /work/zram.ko > /work/modinfo.txt
' > "$out/build.log" 2>&1
sha256sum -c "$out/cache-before.sha256" > "$out/cache-after-check.txt"
cp "$sdk/sysdrv/source/objs_kernel/Module.symvers" "$out/kernel-Module.symvers"
sha256sum "$out/"*.ko > "$out/module-sha256.txt"
tar -C "$out" -czf "$out/artifacts.tar.gz" zsmalloc.ko zram.ko Makefile zsmalloc.c zcomp.c zcomp.h zram_drv.c zram_drv.h build.log undefined-symbols.txt modinfo.txt cache-before.sha256 cache-after-check.txt builder-image.txt kernel-Module.symvers module-sha256.txt
'''.replace('REMOTE',remote)
 subprocess.run(['ssh','-o','BatchMode=yes',a.host,'pct exec 610 -- bash -s'],input=script,text=True,check=True)
 local=ROOT/'dist/zram'/stamp;local.mkdir(parents=True)
 # Stream the already-created archive without requiring a Proxmox host copy.
 with (local/'artifacts.tar.gz').open('wb') as out:subprocess.run(['ssh','-o','BatchMode=yes',a.host,'pct exec 610 -- cat '+remote+'/artifacts.tar.gz'],stdout=out,check=True)
 with tarfile.open(local/'artifacts.tar.gz') as archive:archive.extractall(local,filter='data')
 print(local)
if __name__=='__main__':main()
