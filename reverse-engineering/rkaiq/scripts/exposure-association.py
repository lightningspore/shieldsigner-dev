#!/usr/bin/env python3
"""Execute native effective-exposure lookup with explicit container/ownership boundaries."""
import hashlib,json,struct,subprocess,sys
from differential import OriginalArm,ROOT,BINARY,HEAP,regs
class Original(OriginalArm):
 def __init__(self):
  super().__init__(BINARY)
  self.assign=next(p&~1 for n,p in self.symbols.items() if 'RKAiqSensorExpInfo_t' in n and 'aSERKS5_' in n)
  self.unlock=self.symbols['_ZN4XCam9SmartLockD2Ev']&~1
  self.log=self.symbols['xcam_print_log']&~1
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if address==self.assign:
   a=uc.reg_read(regs.UC_ARM_REG_R0);b=uc.reg_read(regs.UC_ARM_REG_R1);uc.mem_write(a,bytes(uc.mem_read(b,8)));uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if address in [self.unlock,self.log] or name in ['pthread_mutex_lock','pthread_mutex_unlock']:
   uc.reg_write(regs.UC_ARM_REG_R0,0);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if name and '_Rb_tree_decrement' in name:
   node=uc.reg_read(regs.UC_ARM_REG_R0);uc.reg_write(regs.UC_ARM_REG_R0,self.previous[node]);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v):
  c=bytearray(0x300);frames=v['frames'];header=HEAP+0x178;nodes=[HEAP+0x10000+i*32 for i in range(len(frames))]
  struct.pack_into('<5I',c,0x178,0,nodes[0] if nodes else 0,nodes[0] if nodes else header,nodes[-1] if nodes else header,len(nodes))
  self.uc.mem_write(HEAP,bytes(c));self.previous={header:nodes[-1] if nodes else header}
  for i,node in enumerate(nodes):
   self.previous[node]=nodes[i-1] if i else header
   self.uc.mem_write(node,struct.pack('<8I',1,nodes[i-1] if i else header,0,nodes[i+1] if i+1<len(nodes) else 0,frames[i],10+i,0,0))
  self.uc.mem_write(HEAP+0x20000,bytes(8));self.symbols['effective']=next(p for n,p in self.symbols.items() if 'getEffectiveExpParams' in n)
  status=self.invoke('effective',[HEAP,HEAP+0x20000,v['requested']]);status=status if status<0x80000000 else status-0x100000000
  assert self.uc.mem_read(HEAP,len(c))==bytes(c)
  return f'{status},{struct.unpack("<I",self.uc.mem_read(HEAP+0x20000,4))[0]}'
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 cases=[dict(frames=frames,requested=r) for frames in [[],[0],[10],[1,5,10],[0,5,10],[1,2147483648,4294967294],[0,4294967295]] for r in [0,1,2,4,5,6,9,10,11,2147483647,2147483648,4294967294,4294967295]]
 arm=Original();expected=[arm.run(v) for v in cases];inputs=''.join('exposure-association '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='native effective-exposure lookup control flow, selected record and exact/fallback/empty status',limitations=['Explicit ordered map nodes; native find and reverse-iterator bodies execute, while imported tree decrement uses the supplied node ordering.','Smart-pointer assignment, lock lifetime and logging are modeled boundaries, not refcount/concurrency equivalence.','Map insertion, retention, sensor timing and physical frame association remain unimplemented by this selection helper.'])
 (ROOT/'reverse-engineering/rkaiq/exposure-association-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
