#!/usr/bin/env python3
"""Complete native AecRegValueConvertion including real intermediate conversion."""
import hashlib,json,runpy,struct,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,HEAP,regs
Base=runpy.run_path(str(Path(__file__).with_name('ae-register.py')))['Original']
class Original(Base):
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name=='pow':
   values=[struct.unpack('<d',struct.pack('<Q',uc.reg_read(getattr(regs,f'UC_ARM_REG_D{i}'))))[0] for i in range(2)]
   self.math.invoke('pow',doubles=values);self.math_calls.add('pow');uc.reg_write(regs.UC_ARM_REG_D0,self.math.uc.reg_read(regs.UC_ARM_REG_D0));uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if name=='ceilf':
   value=struct.unpack('<f',struct.pack('<I',uc.reg_read(regs.UC_ARM_REG_S0)))[0]
   self.math.invoke('ceilf',floats=[value]);self.math_calls.add('ceilf');uc.reg_write(regs.UC_ARM_REG_S0,self.math.uc.reg_read(regs.UC_ARM_REG_S0));uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if name=='__aeabi_idivmod':
   a=uc.reg_read(regs.UC_ARM_REG_R0);b=uc.reg_read(regs.UC_ARM_REG_R1);assert a<0x80000000 and b
   uc.reg_write(regs.UC_ARM_REG_R0,a//b);uc.reg_write(regs.UC_ARM_REG_R1,a%b);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v):
  p=v['proposed'];c=self.setup(dict(v,seconds=p[0],gain=p[1],isp=p[2],dcg=-1,frame=1360,clock=114.24,line=2800,analogue_minimum=1.,isp_range=[1.,32.],time_range=[.00005,.03],gain_range=[1.,512.],automatic=True,suppress=False,flicker=True,quantum=.01))
  for o,x in [(0xdc,p[1]),(0xe0,p[2]),(0xe8,p[0]),(0xd4,v['target']),(0xd8,v['held']),(0x680,8.)]:struct.pack_into('<f',c,o,x)
  struct.pack_into('<i',c,0xe4,-1);struct.pack_into('<i',c,0x2300,v['frame_id']);struct.pack_into('<i',c,0x22fc,v['sync']);struct.pack_into('<I',c,0x5574,len(v['published']));c[0x2318]=v['count']
  for i,(time,gain,isp) in enumerate(v['published']):struct.pack_into('<4f',c,0x4fbc+244*i,time,gain,1.,isp)
  struct.pack_into('<I',c,0x3c84,len(v['route']))
  for col,(o,ptr) in enumerate([(0x3c8c,HEAP+0x30000),(0x3c90,HEAP+0x31000),(0x3c94,HEAP+0x32000)]):struct.pack_into('<I',c,o,ptr);self.uc.mem_write(ptr,struct.pack('<6f',*[p[col] for p in v['route']]))
  if v.get('result',False):self.seed_result(c,v)
  self.uc.mem_write(HEAP,bytes(c));self.mappings=0
  status=self.invoke('_ZL21AecRegValueConvertionP12AecContext_s',[HEAP],instructions=10000000);assert status==0
  after=bytes(self.uc.mem_read(HEAP,len(c)));words=[struct.unpack_from('<I',after,o)[0] for o in [0xdc,0xe0,0xe8,0xec,0xf0]]
  for o in [0xdc,0xe0,0xe8,0xec,0xf0]:c[o:o+4]=after[o:o+4]
  for i in range(v['count']):
   offsets=[0x134,0x170,0x15c,0x184,0x198,0x1ac,0x1c0,0x148]
   words+=[struct.unpack_from('<I',after,o+4*i)[0] for o in offsets]
   for o in offsets:c[o+4*i:o+4*i+4]=after[o+4*i:o+4*i+4]
  assert bytes(c)==after
  words+=list(struct.unpack('<6I',self.uc.mem_read(HEAP+0x30000,24)))
  return ','.join(f'{w:08x}' for w in words)
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'
 profile=dict(sensor_calib=json.loads(raw)['sensor_calib']);route=[[0.,1.,1.],[.01,1.,1.],[.01,4.,1.],[.02,8.,1.],[.03,15.5,1.],[.03,512.,1.]];cases=[]
 for count in range(6):
  for delta in [-2,0,1,2,7]:
   for n in [0,2,6]:
    for target in [.003,.12,2.4]:
     cases.append(dict(profile=profile,route=route,proposed=[.02,6.,1.],target=target,held=.003,published=[[.005*(i+1),1.+i,1.] for i in range(n)],frame_id=30,sync=30-delta,count=count))
 native=Original();expected=[native.run(v) for v in cases];inputs=''.join('ae-conversion-queue '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='complete native AecRegValueConvertion, direct automatic routing, disabled-DCG selection and real sensor/ISP conversion through normal return',limitations=['Zero through five intermediate entries, explicit prior publication and frame inputs; non-iris automatic SC3336 path only.','Native math runtime executes log10f/pow/powf/roundf/floorf/ceilf as needed; allocation and integer division modeled.','Result packaging/publication and real exposure association remain external; no hardware writes.'])
 (ROOT/'reverse-engineering/rkaiq/ae-conversion-queue-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
