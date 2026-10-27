#!/usr/bin/env python3
"""Check native AWB prepare default position at its publication checkpoint."""
import hashlib,json,struct,subprocess,sys
from unicorn import UC_HOOK_MEM_WRITE
from differential import OriginalArm,ROOT,BINARY,HEAP,RETURN,regs
class Original(OriginalArm):
 def __init__(self):
  super().__init__(BINARY);self.calib=next(p&~1 for n,p in self.symbols.items() if 'UpdateAwbCalibV2Para' in n)
  self.uc.hook_add(UC_HOOK_MEM_WRITE,self.wrote)
 def wrote(self,uc,access,address,size,value,user):
  if address==HEAP+0x3644:assert size==4;self.result=value
 def hook(self,uc,address,size,user):
  if self.result is not None:uc.reg_write(regs.UC_ARM_REG_PC,RETURN);return
  if address==self.calib:
   uc.reg_write(regs.UC_ARM_REG_R0,0);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,mode):
  c=bytearray(0x36cc);struct.pack_into('<i',c,0x34,mode);struct.pack_into('<I',c,0x80,HEAP+0x10000);struct.pack_into('<I',c,0x130,HEAP+0x20000);struct.pack_into('<I',c,0x33ac,1)
  self.uc.mem_write(HEAP,bytes(c));self.result=None
  name=next(n for n in self.symbols if 'AwbPrepareV32' in n);self.invoke(name,[HEAP]);assert self.result is not None;return str(self.result)
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 modes=[0,1,16,17,18,31,32,33,48,-1];arm=Original();expected=[arm.run(m) for m in modes];inputs=''.join(f'awb-prepare-position {m}\n' for m in modes)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert actual==expected,(expected,actual)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(modes),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='AwbPrepareV32 initial apply-position publication: linear mode zero selects Gain1',limitations=['Calibration-update call is a success boundary; controlled preconfigured context bypasses preceding geometry/bit-depth setup.','Stops immediately after the context position store, not full prepare return.','Later AWB reconfiguration policy and automatic gain calculation remain separate.'])
 (ROOT/'reverse-engineering/rkaiq/awb-prepare-position-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
