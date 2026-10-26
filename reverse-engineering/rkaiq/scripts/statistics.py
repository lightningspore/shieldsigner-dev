#!/usr/bin/env python3
"""Compare decoded AWB measurements with actual full-ISP32 translator instructions.

Buffer access/multi-ISP predicates are stubs; single-ISP unpacking runs natively.
Calibration/configuration copies in the full translator are not a Rust port yet.
"""
from pathlib import Path
import argparse,hashlib,json,random,struct,subprocess
from differential import OriginalArm,ROOT,BINARY,HEAP,regs
class OriginalStatistics(OriginalArm):
 def __init__(self):
  super().__init__(BINARY)
  for name in self.symbols:
   if ('get_cast_ptr' in name and 'Isp20StatsBuffer' in name) or 'get_v4l2_userptr' in name or 'IsMultiIspMode' in name:self.stubs[self.symbols[name]&~1]=name
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name and ('get_cast_ptr' in name or 'get_v4l2_userptr' in name or 'IsMultiIspMode' in name):
   result=0 if 'IsMultiIspMode' in name else HEAP+0x20000
   uc.reg_write(regs.UC_ARM_REG_R0,result);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,data):
  context=HEAP;raw=HEAP+0x20000;out=HEAP+0x40000;smart=HEAP+0x50000;proxy=HEAP+0x60000;control=HEAP+0x70000
  self.uc.mem_write(context,bytes(0xc000));self.uc.mem_write(context+0xb660,b'\x04')
  self.uc.mem_write(raw,data);self.uc.mem_write(out,bytes(0x3000));self.uc.mem_write(smart,struct.pack('<II',proxy,0));self.uc.mem_write(proxy,bytes(0x100));self.uc.mem_write(proxy+0x6c,struct.pack('<II',out,control));self.uc.mem_write(control,struct.pack('<II',0,100))
  assert self.invoke('_ZN5RkCam26RkAiqResourceTranslatorV3217translateAwbStatsERKN4XCam8SmartPtrINS1_11VideoBufferEEERNS2_INS_15SharedItemProxyI13RkAiqAwbStatsEEEE',[context,0,smart])==0
  frame=struct.unpack('<I',self.uc.mem_read(out+0x22f4,4))[0];assert self.uc.mem_read(proxy+0x50,4)==struct.pack('<I',frame)
  grid=[]
  for i in range(225):
   wp,r,g,b=struct.unpack('<4Q',self.uc.mem_read(out+0xd8+i*32,32));grid.extend([r,g,b,wp])
  sums=[]
  def word(offset):return struct.unpack('<I',self.uc.mem_read(out+offset,4))[0]
  for i in range(4):sums.extend([word(16+i*48),word(24+i*48),word(8+i*48),word(200+i*4),word(40+i*48),word(48+i*48),word(32+i*48)])
  hist=struct.unpack('<8I',self.uc.mem_read(out+0x1d58,32))
  assert struct.unpack('<I',self.uc.mem_read(control+4,4))[0]==100
  return str(frame)+':'+','.join(map(str,grid))+':'+','.join(map(str,sums))+':'+','.join(map(str,hist))
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--cases',type=int,default=100);parser.add_argument('--emit-dir',type=Path);args=parser.parse_args()
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==sha
 arm=OriginalStatistics();rng=random.Random(0x53544154);inputs=[];expected=[]
 for i in range(args.cases):
  seed=rng.randrange(0xffffffff);state=seed;data=bytearray()
  for _ in range(13040):state=(state*1664525+1013904223)&0xffffffff;data.append(state>>24)
  struct.pack_into('<I',data,0x32e0,0x20)
  inputs.append(f'statistics {seed}');expected.append(arm.run(bytes(data)))
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatch=[i for i,(a,b) in enumerate(zip(expected,actual)) if a!=b]
 report=dict(binarySha256=sha,seed='0x53544154',cases=len(inputs),awbBlocksPerCase=225,mismatchCount=len(mismatch),scope='Single-ISP valid AWB raw grid, four light sums, eight expanded luma histogram bins and frame ID from original translateAwbStats',limitations=['Not a port of translator calibration/configuration copies or the complete AE/AWB algorithms.','Buffer-access helpers and multi-ISP predicates are controlled stubs; no live statistics queue is tested.','AE raw grids and AE histograms are checked against kernel layouts, not by this AWB reference comparison.'])
 if mismatch:report['firstMismatches']=mismatch[:5]
 (ROOT/'reverse-engineering/rkaiq/statistics-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not mismatch
 if args.emit_dir:
  args.emit_dir.mkdir(parents=True,exist_ok=True)
  (args.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(args.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
