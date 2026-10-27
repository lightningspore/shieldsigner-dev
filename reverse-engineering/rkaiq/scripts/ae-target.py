#!/usr/bin/env python3
"""Execute AecPreProcess through its linear dynamic-setpoint store."""
import hashlib,json,random,struct,subprocess,sys
from unicorn import UC_HOOK_MEM_WRITE
from differential import OriginalArm,ROOT,BINARY,HEAP,RETURN,regs
class OriginalTarget(OriginalArm):
 def __init__(self):
  super().__init__(BINARY);self.target=None
  for name in self.symbols:
   if 'AecGetRunFlag' in name:self.stubs[self.symbols[name]&~1]='target-run-flag'
  self.uc.hook_add(UC_HOOK_MEM_WRITE,self.store,begin=HEAP+0x130,end=HEAP+0x133)
 def hook(self,uc,address,size,user):
  if self.stubs.get(address)=='target-run-flag':uc.reg_write(regs.UC_ARM_REG_R0,1);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def store(self,uc,access,address,size,value,user):
  assert address==HEAP+0x130 and size==4;self.target=value&0xffffffff;uc.reg_write(regs.UC_ARM_REG_PC,RETURN);uc.emu_stop()
 def run(self,v):
  context=bytearray(0x5998);struct.pack_into('<I',context,0x40cc,HEAP+0x20000);struct.pack_into('<f',context,0x18,v['bias'])
  self.uc.mem_write(HEAP,bytes(context));self.uc.mem_write(HEAP+0x20000,struct.pack('<4I',HEAP+0x30000,len(v['levels']),HEAP+0x31000,len(v['points'])))
  self.uc.mem_write(HEAP+0x30000,struct.pack('<'+'f'*len(v['levels']),*v['levels']) or bytes(4));self.uc.mem_write(HEAP+0x31000,struct.pack('<'+'f'*len(v['points']),*v['points']) or bytes(4))
  stats=bytearray(0x3000);struct.pack_into('<H',stats,0x2e20,45*256);self.uc.mem_write(HEAP+0x50000,bytes(stats))
  stack=bytearray(240);struct.pack_into('<f',stack,0,1.);struct.pack_into('<II',stack,232,HEAP+0x50000,1)
  bits=lambda value:struct.unpack('<I',struct.pack('<f',value))[0]
  self.target=None;self.invoke('AecPreProcess',[HEAP,bits(v['exposure']),bits(1.),bits(1.)],stack=bytes(stack),instructions=1000000)
  assert self.target is not None
  assert bytes(self.uc.mem_read(HEAP+0xd0,4))==struct.pack('<f',v['exposure']),'Exposure ABI/product differs'
  return f'{self.target:08x}'
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'
 control=json.loads(raw)['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib']['LinearAeCtrl'];profile=control['DySetpoint'];cases=[]
 for exposure in [0.,.003,.096,.192,.3,.576,.96,1.344,15.36]:
  for bias in [-100.,0.,100.]:cases.append(dict(levels=profile['ExpLevel'],points=profile['DySetpoint'],exposure=exposure,bias=bias))
 rng=random.Random(0x544152)
 for i in range(60):
  count=i%8;levels=[float(j)+rng.random()*.1 for j in range(count)];points=[rng.uniform(-100,500) for _ in levels]
  cases.append(dict(levels=levels,points=points,exposure=levels[0] if count==1 else rng.uniform(-1,10),bias=rng.uniform(-300,300)))
 arm=OriginalTarget();expected=[arm.run(v) for v in cases];inputs=''.join('ae-target '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 init=control['InitExp'];expected.append(arm.run(dict(levels=profile['ExpLevel'],points=profile['DySetpoint'],exposure=init['InitGainValue']*init['InitTimeValue']*init['InitIspDGainValue'],bias=control['Evbias'])))
 inputs+='ae-initial-target '+json.dumps(dict(ae_calib=dict(LinearAeCtrl=control)),separators=(',',':'))+'\n'

 def compare(command):
  actual=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i] if i<len(cases) else "initial-profile",a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
  compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly',image,'/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases)+1,mismatches=0,armReplayPassed='--arm' in sys.argv,scope='linear AecPreProcess dynamic-target branch through target store at context +0x130, including profile interpolation, bias and clamping',limitations=['The run-flag boundary forces processing; native execution stops at the documented target store, not full AecPreProcess return.','Exposure-info by-value ARM ABI and resulting exposure product are checked with unity other gain factors; full sensor/frame association remains external.','Backlight/overexposure, HDR, iris and flicker paths are disabled; no complete AE controller equivalence is claimed.'])
 (ROOT/'reverse-engineering/rkaiq/ae-target-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
