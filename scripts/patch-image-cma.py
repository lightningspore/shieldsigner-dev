#!/usr/bin/env python3
"""Create a bounded UNSIGNED Luckfox SD-image derivative changing CMA1M to12M.

No block devices or existing outputs accepted. The sole mutable region is the
32KiB CRC32 U-Boot environment at offset zero; kernel/rootfs stay byte-exact.
"""
import argparse,hashlib,json,re,shutil,stat,struct,zlib
from pathlib import Path

ALLOWED_UNSIGNED_SOURCE_SHA256 = "d4fdfa0be754764092cfeb67c0d78336ed83186644f562952dccb6ff6ad8e0c2"

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while b:=f.read(8*1024*1024): h.update(b)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__); p.add_argument('--source',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--expected-sha256',required=True); p.add_argument('--report',type=Path,required=True); a=p.parse_args()
 if not re.fullmatch('[0-9a-f]{64}',a.expected_sha256): p.error('Expected a lowercase SHA256')
 if not a.source.is_file() or not stat.S_ISREG(a.source.stat().st_mode): p.error('Source must be a regular image file, never a block device')
 if a.output.exists() or a.output.is_symlink() or a.report.exists() or a.report.is_symlink(): p.error('Choose new output/report paths')
 if a.expected_sha256 != ALLOWED_UNSIGNED_SOURCE_SHA256: p.error('Only the reviewed unsigned development base image is allowlisted')
 if digest(a.source)!=a.expected_sha256: p.error('Source image SHA256 mismatch')
 with a.source.open('rb') as f: original=f.read(32768)
 if len(original)!=32768 or struct.unpack_from('<I',original)[0] != zlib.crc32(original[4:]) & 0xffffffff: p.error('Invalid fixed32KiB environment CRC')
 payload=original[4:]; end=payload.find(b'\0\0')
 if end<0 or any(payload[end+2:]): p.error('Unexpected environment termination/padding')
 entries=payload[:end].split(b'\0'); selected=[i for i,s in enumerate(entries) if s.startswith(b'sys_bootargs=')]
 if len(selected)!=1: p.error('Expected exactly one sys_bootargs entry')
 index=selected[0]; before=entries[index]
 if before.count(b'rk_dma_heap_cma=1M')!=1 or re.findall(rb'rk_dma_heap_cma=\S+',before)!=[b'rk_dma_heap_cma=1M']: p.error('Expected exactly one CMA1M token')
 # Signed command-line lockdown does not import this env field. This bounded
 # tool supports only the reviewed unsigned SD layout, with rootfs at p6.
 if b'root=/dev/mmcblk1p6 rootfstype=squashfs' not in before or entries[0] != b'blkdevparts=mmcblk1:32K(env),512K@32K(idblock),256K(uboot),32M(boot),256M(userdata),6656M(rootfs)': p.error('Unexpected unsigned Mini SD environment layout')
 after=before.replace(b'rk_dma_heap_cma=1M',b'rk_dma_heap_cma=12M'); entries[index]=after; new_payload=b'\0'.join(entries)+b'\0\0'; new_payload=new_payload.ljust(32764,b'\0')
 if len(new_payload)!=32764: p.error('Environment capacity exceeded')
 patched=struct.pack('<I',zlib.crc32(new_payload)&0xffffffff)+new_payload
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.source.open('rb') as src,a.output.open('xb') as dst:
  assert src.read(32768)==original; dst.write(patched); shutil.copyfileobj(src,dst,8*1024*1024)
 original_tail=hashlib.sha256(); patched_tail=hashlib.sha256()
 with a.source.open('rb') as src,a.output.open('rb') as dst:
  src.seek(32768); dst.seek(32768)
  while b:=src.read(8*1024*1024): original_tail.update(b); patched_tail.update(dst.read(len(b)))
  assert not dst.read(1)
 assert original_tail.digest()==patched_tail.digest(); assert a.source.stat().st_size==a.output.stat().st_size
 report={'kind':'shieldsigner-unsigned-cma12-image-derivative','sourceArtifactId':'e69de65-unsigned-diagnostic-dev-cma1','sourceSha256':a.expected_sha256,'patchToolSha256':digest(Path(__file__)),'outputSha256':digest(a.output),'bytes':a.output.stat().st_size,'environmentOffset':0,'environmentBytes':32768,'originalEnvironmentCrc32':hex(struct.unpack_from('<I',original)[0]),'patchedEnvironmentCrc32':hex(struct.unpack_from('<I',patched)[0]),'sysBootargsBefore':before.decode(),'sysBootargsAfter':after.decode(),'onlyLogicalEnvironmentChange':'rk_dma_heap_cma=1M -> rk_dma_heap_cma=12M','allBytesAfterEnvironmentSha256':original_tail.hexdigest(),'allBytesAfterEnvironmentUnchanged':True,'kernelRootfsRuntimeUnchanged':True,'unsignedOnly':True,'cardModified':False,'imageBootQualified':False}
 a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
