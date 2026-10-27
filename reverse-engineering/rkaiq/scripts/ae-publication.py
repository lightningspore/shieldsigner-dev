#!/usr/bin/env python3
"""Compare native linear result queue selection through full result return."""
import hashlib,json,runpy,struct,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,HEAP,regs
Base=runpy.run_path(str(Path(__file__).with_name('ae-conversion-queue.py')))['Original']
class Original(Base):
 def hook(self,uc,address,size,user):
  if self.stubs.get(address)=='memcmp':
   a,b,n=[uc.reg_read(r) for r in [regs.UC_ARM_REG_R0,regs.UC_ARM_REG_R1,regs.UC_ARM_REG_R2]]
   x=bytes(uc.mem_read(a,n));y=bytes(uc.mem_read(b,n));uc.reg_write(regs.UC_ARM_REG_R0,0 if x==y else (1 if x>y else 0xffffffff));uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v):
  c=bytearray(0x6000);proposed=[bytes.fromhex(x) for x in v['proposed']];published=[bytes.fromhex(x) for x in v['published']];last=proposed[-1]
  for o,x in [(0x3d14,1360.),(0x3d18,114.24),(0x3d1c,2800.),(0xd4,.003)]:struct.pack_into('<f',c,o,x)
  for o,x in [(0x2300,v['frame']),(0x22fc,v['sync']),(0x5574,len(published)),(0x22f4,1)]:struct.pack_into('<i',c,o,x)
  c[0x2318]=len(proposed)-1
  for i,r in enumerate(proposed[:-1]):
   for source,dest in [(0,0x184),(4,0x170),(12,0x15c),(20,0x198),(32,0x1ac),(36,0x1c0),(196,0x1d4),(200,0x148)]:c[dest+i*4:dest+i*4+4]=r[source:source+4]
  for source,dest in [(0,0xe8),(4,0xdc),(12,0xe0),(20,0xe4),(32,0xec),(36,0xf0),(196,0x2024),(200,0x2020)]:c[dest:dest+4]=last[source:source+4]
  c[0x4c30:0x4c30+244]=bytes.fromhex(v['previous'])
  for i,r in enumerate(published):c[0x4fbc+244*i:0x4fbc+244*(i+1)]=r
  self.uc.mem_write(HEAP,bytes(c));self.uc.mem_write(HEAP+0x20000,struct.pack('<6I',0,HEAP+0x30000,HEAP+0x31000,HEAP+0x32000,0,HEAP+0x40000));self.uc.mem_write(HEAP+0x30000,bytes(0x11000))
  status=self.invoke('AecGetProcResults',[HEAP,HEAP+0x20000],instructions=3000000);assert status==0
  count=struct.unpack('<I',self.uc.mem_read(HEAP+0x40014,4))[0];sync=struct.unpack('<i',self.uc.mem_read(HEAP+0x22fc,4))[0]
  return f'{count}:{sync}:'+bytes(self.uc.mem_read(HEAP+0x40018,1464)).hex()+':'+bytes(self.uc.mem_read(HEAP+0x30000,244)).hex()
def record(key,frame=1360,iris=0):
 r=bytearray(244)
 for o,x in [(0,.003 if key==0 else .01),(4,float(key+1)),(8,1.),(12,1.),(236,114.24)]:struct.pack_into('<f',r,o,x)
 for o,x in [(20,0xffffffff),(32,122 if key==0 else 408),(36,128*(key+1)),(196,iris),(232,frame)]:struct.pack_into('<I',r,o,x)
 struct.pack_into('<H',r,228,2800);return bytes(r).hex()
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 cases=[]
 for count in range(1,7):
  for old_count in [1,2,6]:
   for delta in [-2,0,1,2,7]:
    for pattern in range(6):
     keys=([0]*count if pattern in [0,3,4,5] else [i//2 for i in range(count)] if pattern==1 else [i%2 for i in range(count)])
     previous=record(keys[-1] if pattern in [0,4,5] else 4,frame=1320 if pattern==4 else 1360,iris=1 if pattern==5 else 0)
     cases.append(dict(proposed=[record(k) for k in keys],published=[record(0 if pattern==3 else (i%3)) for i in range(old_count)],previous=previous,frame=30,sync=30-delta))
 native=Original();expected=[native.run(v) for v in cases];inputs=''.join('ae-publication '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):
   if a!=b:
    aa=a.split(':');bb=b.split(':');print('mismatch',i,cases[i],aa[:2],bb[:2],file=sys.stderr)
    for field in [2,3]:
     x=bytes.fromhex(aa[field]);y=bytes.fromhex(bb[field]);print('field',field,[(j,k,l) for j,(k,l) in enumerate(zip(x,y)) if k!=l][:25],file=sys.stderr)
    raise AssertionError(i)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='linear AecGetProcResults complete native return, comparing selected six-record exposure queue, count, synchronized frame and final record',limitations=['Fixed frame-length mode, explicit proposed/prior records, no HDR or iris hardware control. Iris metadata differences exercise selection policy only.','memcmp, allocation and integer division modeled; complete native result body, CIS feature and environment-history publication execute.','Only exposure queue selection is compared; other result fields and context side effects are not claimed equivalent.','Real frame association and sensor writes remain external.'])
 (ROOT/'reverse-engineering/rkaiq/ae-publication-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
