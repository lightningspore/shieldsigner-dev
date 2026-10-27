#!/usr/bin/env python3
"""Execute AecPreProcess through standard linear history and current-error writes."""
import hashlib,json,runpy,struct,subprocess,sys
from pathlib import Path
from unicorn import UC_HOOK_MEM_WRITE
from differential import ROOT,BINARY,HEAP,RETURN,regs
Base=runpy.run_path(str(Path(__file__).with_name('ae-target.py')))['OriginalTarget']
class Original(Base):
 def __init__(self):
  super().__init__();self.uc.hook_add(UC_HOOK_MEM_WRITE,self.error_store,begin=HEAP+0x12c,end=HEAP+0x12f)
 def store(self,uc,access,address,size,value,user):
  assert address==HEAP+0x130 and size==4;self.target=value
 def error_store(self,uc,access,address,size,value,user):
  assert address==HEAP+0x12c and size==4;self.error=value;uc.reg_write(regs.UC_ARM_REG_PC,RETURN);uc.emu_stop()
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name=='target-run-flag':uc.reg_write(regs.UC_ARM_REG_R0,int(self.case['run']));uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if name=='__aeabi_idivmod':
   a=uc.reg_read(regs.UC_ARM_REG_R0);b=uc.reg_read(regs.UC_ARM_REG_R1);assert a<0x80000000 and b==10
   uc.reg_write(regs.UC_ARM_REG_R0,a//b);uc.reg_write(regs.UC_ARM_REG_R1,a%b);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v):
  self.case=v;c=bytearray(0x5998)
  struct.pack_into('<I',c,0x40cc,HEAP+0x20000)
  for o,x in [(0x130,45.),(0xf4,.00005),(0xf8,15.36),(0x10,10.),(0x14,15.),(0x3cc8,.01)]:struct.pack_into('<f',c,o,x)
  for i,x in enumerate(v['history']):struct.pack_into('<f',c,0x2c50+i*64,x)
  self.uc.mem_write(HEAP,bytes(c));self.uc.mem_write(HEAP+0x20000,struct.pack('<4I',HEAP+0x30000,2,HEAP+0x31000,2));self.uc.mem_write(HEAP+0x30000,struct.pack('<2f',0.,1.));self.uc.mem_write(HEAP+0x31000,struct.pack('<2f',45.,45.))
  stats=bytearray(0x3000);struct.pack_into('<H',stats,0x2e20,int(v['measured']*256));self.uc.mem_write(HEAP+0x50000,bytes(stats))
  stack=bytearray(240);struct.pack_into('<f',stack,0,1.);struct.pack_into('<II',stack,232,HEAP+0x50000,v['frame'])
  bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
  self.target=None;self.error=None;self.invoke('AecPreProcess',[HEAP,bits(.003),bits(1.),bits(1.)],stack=bytes(stack),instructions=1000000);assert self.error is not None
  assert self.uc.mem_read(HEAP+0x130,4)==struct.pack('<f',45.)
  words=[struct.unpack('<I',self.uc.mem_read(HEAP+0x2c50+i*64,4))[0] for i in range(10)]+[self.error]
  return ','.join(f'{w:08x}' for w in words)
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 cases=[dict(frame=frame,run=run,measured=measured,history=[(i-5)*.03 for i in range(10)]) for frame in range(30) for run in [False,True] for measured in [0.,3.,40.5,45.,49.5,120.,255.]]
 arm=Original();expected=[arm.run(v) for v in cases];inputs=''.join('ae-preprocess-history '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='standard linear AecPreProcess error-history/current-error publication checkpoint, active and skipped processing',limitations=['Run-flag decision is controlled; native preprocessing executes through current-error store, not full return.','Fixed target curve 45, standard mean mode, no environment/backlight/overexposure or HDR.','Physical exposure/statistics association and complete preprocessing policy remain external.'])
 (ROOT/'reverse-engineering/rkaiq/ae-preprocess-history-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
