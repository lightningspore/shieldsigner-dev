#!/usr/bin/env python3
"""Capture native AecInit selected defaults before the calibration boundary."""
import hashlib,json,struct,subprocess,sys
from differential import OriginalArm,ROOT,BINARY,HEAP,regs
class OriginalInit(OriginalArm):
 def __init__(self):
  super().__init__(BINARY);self.next=HEAP+0x10000;self.defaults=None
  self.stubs[self.symbols['AecCalibConfig']&~1]='capture-ae-calibration'
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name=='calloc':
   a=uc.reg_read(regs.UC_ARM_REG_R0);b=uc.reg_read(regs.UC_ARM_REG_R1);n=a*b;assert n<0x10000
   ptr=self.next;self.next+=(n+4095)&~4095;uc.mem_write(ptr,bytes(n));uc.reg_write(regs.UC_ARM_REG_R0,ptr)
  elif name=='capture-ae-calibration':
   context=uc.reg_read(regs.UC_ARM_REG_R1);self.defaults=bytes(uc.mem_read(context+0x1d3c,633));uc.reg_write(regs.UC_ARM_REG_R0,0)
  else:return super().hook(uc,address,size,user)
  uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))
def main():
 arm=OriginalInit();arm.uc.mem_write(HEAP,bytes(8));arm.invoke('AecInit',[HEAP,HEAP+0x80000,32]);assert arm.defaults is not None
 result=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='ae-defaults\n',text=True,capture_output=True,check=True).stdout.strip()
 assert result==arm.defaults.hex(),[(i,a,b) for i,(a,b) in enumerate(zip(bytes.fromhex(result),arm.defaults)) if a!=b][:20]
 if '--arm' in sys.argv:
  binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture'
  image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
  actual=subprocess.run(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly',image,'/bincheck/numeric-fixture'],input='ae-defaults\n',text=True,capture_output=True,check=True).stdout.strip()
  assert actual==arm.defaults.hex()
 report=dict(armReplayPassed='--arm' in sys.argv,binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),bytes=633,mismatches=0,scope='AecInit selected AE/histogram record seed at entry to AecCalibConfig',limitations=['calloc is an explicit zero-allocation boundary; AecCalibConfig is a controlled no-op capturing its incoming selected records.','This verifies pre-calibration defaults only, not complete AecInit calibration, measurement publication or automatic exposure.'])
 (ROOT/'reverse-engineering/rkaiq/ae-defaults-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
