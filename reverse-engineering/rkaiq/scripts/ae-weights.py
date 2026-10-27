#!/usr/bin/env python3
"""Compare native software mean-luma weight selection, including SDK profile."""
import hashlib,json,random,subprocess,sys
from differential import OriginalArm,ROOT,BINARY,HEAP,regs
class OriginalWeights(OriginalArm):
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name=='calloc':
   assert uc.reg_read(regs.UC_ARM_REG_R0)*uc.reg_read(regs.UC_ARM_REG_R1)==225
   uc.mem_write(HEAP+0x30000,bytes(225));uc.reg_write(regs.UC_ARM_REG_R0,HEAP+0x30000)
  elif name=='free':assert uc.reg_read(regs.UC_ARM_REG_R0)==HEAP+0x30000
  elif name in ('__aeabi_idiv','__aeabi_idivmod'):
   a=uc.reg_read(regs.UC_ARM_REG_R0);b=uc.reg_read(regs.UC_ARM_REG_R1);assert a<225 and b==15
   uc.reg_write(regs.UC_ARM_REG_R0,a//b)
   if name.endswith('mod'):uc.reg_write(regs.UC_ARM_REG_R1,a%b)
  else:return super().hook(uc,address,size,user)
  uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))
def main():
 arm=OriginalWeights(BINARY);rng=random.Random(0x574754);cases=[];expected=[]
 path=ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json';raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'
 profile=bytes(json.loads(raw)['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib']['CommCtrl']['AecGridWeight'])
 sources=[profile,bytes(225),bytes([255])*225,bytes(range(225))]+[rng.randbytes(225) for _ in range(56)]
 for source in sources:
  for count in [25,225]:
   arm.uc.mem_write(HEAP,bytes([0xa5])*225);arm.uc.mem_write(HEAP+0x10000,source)
   assert arm.invoke('_ZL25AecSetMeanLumaGridWeightsPhPKhih.constprop.9',[HEAP,HEAP+0x10000,count,0])==0
   expected.append(bytes(arm.uc.mem_read(HEAP,225)).hex());assert bytes(arm.uc.mem_read(HEAP+0x10000,225))==source
   cases.append(f'ae-weights {count} {source.hex()}')
 host=ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture'
 assert subprocess.run([str(host)],input='\n'.join(cases)+'\n',text=True,capture_output=True,check=True).stdout.splitlines()==expected
 if '--arm' in sys.argv:
  binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
  assert subprocess.run(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly',image,'/bincheck/numeric-fixture'],input='\n'.join(cases)+'\n',text=True,capture_output=True,check=True).stdout.splitlines()==expected
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='software 225/25-cell weight selection; all destination bytes including lite tail preservation',limitations=['Zero allocation, free and imported integer quotient/remainder are controlled boundaries.','Outer all-zero-calibration fallback, overrides and AE policy are not implemented by this helper.','Software luma weights differ from initial hardware histogram weights; no live automatic exposure is enabled.'])
 (ROOT/'reverse-engineering/rkaiq/ae-weights-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
