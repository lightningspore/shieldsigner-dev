#!/usr/bin/env python3
"""Verify linear AecUpdateConfig prefix through initial weight publication."""
import hashlib,json,random,runpy,struct,subprocess,sys
from differential import ROOT,BINARY,HEAP,RETURN,regs
Base=runpy.run_path(str(ROOT/'reverse-engineering/rkaiq/scripts/ae-weights.py'))['OriginalWeights']
Init=runpy.run_path(str(ROOT/'reverse-engineering/rkaiq/scripts/ae-defaults.py'))['OriginalInit']
class Prefix(Base):
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name=='memcmp':
   a,b,n=[uc.reg_read(r) for r in [regs.UC_ARM_REG_R0,regs.UC_ARM_REG_R1,regs.UC_ARM_REG_R2]];assert n==225
   x=bytes(uc.mem_read(a,n));y=bytes(uc.mem_read(b,n));value=next((a-b for a,b in zip(x,y) if a!=b),0)
   uc.reg_write(regs.UC_ARM_REG_R0,value&0xffffffff);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if name=='memcpy' and uc.reg_read(regs.UC_ARM_REG_R0)==HEAP+0x40000+0x20fe:
   assert uc.reg_read(regs.UC_ARM_REG_R2)==225
   super().hook(uc,address,size,user);self.reached=True;uc.reg_write(regs.UC_ARM_REG_PC,RETURN);uc.emu_stop();return
  super().hook(uc,address,size,user)
 def prefix(self,v,seed):
  engine=HEAP+0x40000;config=HEAP+0x50000;c=bytearray(0x25a4);c[0x1d3c:0x1fb5]=seed
  for o,value in [(0x1fc0,4),(0x1fc4,0),(0x2008,v['width']),(0x200c,v['height']),(8,v['hist']),(12,v['raw']),(16,v['range'])]:struct.pack_into('<i',c,o,value)
  c[0x25a1]=v["mask"];c[0]=1;c[0x14:0x14+225]=bytes(v['weights']);struct.pack_into('<8f',c,0x180,*v['input'],*v['tone'])
  for o in [0x1fd0,0x1fd4,0x1fd8]:struct.pack_into('<f',c,o,1.)
  self.uc.mem_write(config,bytes(c));self.uc.mem_write(engine,bytes(0x5998));self.uc.mem_write(engine+0x2315,bytes([v['mask']]));self.invoke('AecHwConfig',[config]);self.reached=False
  self.invoke('AecUpdateConfig',[engine,config,0x80],instructions=1000000);assert self.reached
  policy=struct.unpack('<3I',self.uc.mem_read(engine+0x2308,12));mask=bytes(self.uc.mem_read(engine+0x2315,1))[0]
  return ':'.join(map(str,[*policy,mask]))+':'+bytes(self.uc.mem_read(engine+0x2058,633)).hex()
def main():
 init=Init();init.uc.mem_write(HEAP,bytes(8));init.invoke('AecInit',[HEAP,HEAP+0x80000,4]);arm=Prefix(BINARY);rng=random.Random(0x414543);cases=[];expected=[]
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'
 comm=json.loads(raw)['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib']['CommCtrl']
 for i in range(40):
  v=dict(width=2304,height=1296,input=[0,0,1,1],tone=[.1,.1,.9,.9],hist=5 if i==0 else i%8-1,raw=4 if i==0 else i%7-1,range=1 if i==0 else i%5-1,mask=0 if i==0 else rng.randrange(256),weights=comm['AecGridWeight'] if i==0 else list(rng.randbytes(225)))
  expected.append(arm.prefix(v,init.defaults));cases.append('ae-configuration '+json.dumps(v,separators=(',',':')))
 cases.append('ae-profile '+json.dumps(dict(comm=comm,width=2304,height=1296),separators=(',',':')));expected.append(expected[0])
 def compare(command):
  actual=subprocess.run(command,input='\n'.join(cases)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):
   if a!=b:
    aa=a.split(':');bb=b.split(':');delta=[(j,x,y) for j,(x,y) in enumerate(zip(bytes.fromhex(aa[-1]),bytes.fromhex(bb[-1]))) if x!=y]
    raise AssertionError((i,aa[:4],bb[:4],delta[:20]))
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
  compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly',image,'/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='linear AecUpdateConfig prefix under update mask 0x80, ending immediately after histogram-1 initial weight publication; all 633 selected bytes and normalized modes/channel mask',limitations=['Native execution is deliberately stopped at this documented intermediate publication point; no claim of full AecUpdateConfig equivalence.','Nonzero grids only; built-in zero-grid fallback, overrides, subsequent frame processing and publication are unfinished.','Allocation/memory comparisons and imported integer division use explicit harness boundaries.','Full-profile JSON binding verifies the SC3336 Y-mode checked subset; no live measurement configuration or automatic exposure is enabled.'])
 (ROOT/'reverse-engineering/rkaiq/ae-configuration-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
