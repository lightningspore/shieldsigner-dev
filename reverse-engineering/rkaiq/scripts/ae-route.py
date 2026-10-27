#!/usr/bin/env python3
"""Compare complete non-iris EcmExecuteAuto outputs and route-time mutation."""
import hashlib,json,math,runpy,struct,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,HEAP,regs,u32
Base=runpy.run_path(str(Path(__file__).with_name('ae-grid.py')))['OriginalGrid']
class OriginalRoute(Base):
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name in ('floorf','ceilf'):
   value=struct.unpack('<f',struct.pack('<I',uc.reg_read(regs.UC_ARM_REG_S0)))[0];out=math.floor(value) if name=='floorf' else math.ceil(value)
   uc.reg_write(regs.UC_ARM_REG_S0,u32(struct.pack('<f',out)));uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v):
  context=bytearray(0x5998);route=v['route'];count=len(route)
  struct.pack_into('<I',context,0x3c84,count)
  for o,p in [(0x3c8c,HEAP+0x10000),(0x3c90,HEAP+0x11000),(0x3c94,HEAP+0x12000)]:struct.pack_into('<I',context,o,p)
  for o,key in [(0xfc,'tmin'),(0x100,'tmax'),(0x104,'gmin'),(0x108,'gmax'),(0x3cc4,'quantum'),(0x680,'coefficient'),(0x3d18,'clock'),(0x3d1c,'line')]:struct.pack_into('<f',context,o,v[key])
  self.uc.mem_write(HEAP,bytes(context))
  arrays=[]
  for i,p in enumerate([HEAP+0x10000,HEAP+0x11000,HEAP+0x12000]):
   array=struct.pack('<'+'f'*count,*[row[i] for row in route]);arrays.append(array);self.uc.mem_write(p,array)
  self.uc.mem_write(HEAP+0x20000,bytes([0xa5])*16)
  status=self.invoke('_Z14EcmExecuteAutoP12AecContext_sfPfS1_S1_Pi',[HEAP,HEAP+0x20000,HEAP+0x20004,HEAP+0x20008],floats=[v['exposure']],stack=struct.pack('<I',HEAP+0x2000c),instructions=1000000)
  assert status==0 and bytes(self.uc.mem_read(HEAP+0x2000c,4))==bytes(4)
  assert bytes(self.uc.mem_read(HEAP,len(context)))==context
  assert bytes(self.uc.mem_read(HEAP+0x11000,count*4))==arrays[1] and bytes(self.uc.mem_read(HEAP+0x12000,count*4))==arrays[2]
  data=bytes(self.uc.mem_read(HEAP+0x20000,12))+bytes(self.uc.mem_read(HEAP+0x10000,count*4))
  return ','.join(f'{x:08x}' for x in struct.unpack('<'+'I'*(3+count),data))
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'
 p=json.loads(raw)['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib']['LinearAeCtrl']['Route']
 profile=list(map(list,zip(p['TimeDot'],p['GainDot'],p['IspDGainDot'])))
 routes=[profile,[[0,1,1],[.01,1,1],[.01,4,2],[.02,4,4],[.02,16,4]],[[0,1,1],[.0101,1,1],[.0199,1,1],[.03,1,1]],[[.002,2,1],[.002,2,4],[.003,2,4],[.003,8,4]]]
 cases=[]
 for route in routes:
  for exposure in [0,.003,.01,.04,.095,.16,.24,.3,1.,20.]:
   for quantum in [.01,1/120]:cases.append(dict(route=route,exposure=exposure,tmin=.00005,tmax=.03,gmin=1,gmax=778.24,quantum=quantum,coefficient=1.,line=2500.,clock=99.))
 for gmin,gmax in [(2,4),(1,8)]:
  for exposure in [.001,.005,.1,.5,3.]:cases.append(dict(route=profile,exposure=exposure,tmin=.0001,tmax=.02,gmin=gmin,gmax=gmax,quantum=.01,coefficient=1.,line=2500.,clock=72.))
 arm=OriginalRoute(BINARY);expected=[arm.run(v) for v in cases];inputs=''.join('ae-route '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 bound=dict(cases[2]);bound['profile']=p;inputs+='ae-route-profile '+json.dumps(bound,separators=(',',':'))+'\n';expected.append(expected[2])

 def compare(command):
  actual=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i] if i<len(cases) else "profile-binding",a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
  compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly',image,'/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases)+1,mismatches=0,armReplayPassed='--arm' in sys.argv,scope='complete non-iris EcmExecuteAuto and native Brief2 interpolation, returned time/gain/ISP gain, all mutated time knots and preservation of context/gain arrays',limitations=['floorf/ceilf/roundf imports are modeled; original ARM automatic route and interpolation bodies execute.','Runtime limits/quantum/tolerance inputs are explicit controlled values, not a reconstruction of their outer selection.','Iris, simultaneous three-variable interpolation errors, outer EcmExecute caching and live sensor feedback remain outside scope.'])
 (ROOT/'reverse-engineering/rkaiq/ae-route-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
