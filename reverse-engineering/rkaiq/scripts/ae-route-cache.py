#!/usr/bin/env python3
"""Compare native EcmExecute plus real automatic route splitting and cache publication."""
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
  for o,value in [(0x3ccc,v['prior']),(0x3cc8,v['threshold']),(0x3cdc,2.),(0x3d00,1.5),(0x3cec,.004)]:struct.pack_into('<f',context,o,value)
  context[0x3d3c]=v['force']
  self.uc.mem_write(HEAP,bytes(context))
  arrays=[]
  for i,p in enumerate([HEAP+0x10000,HEAP+0x11000,HEAP+0x12000]):
   array=struct.pack('<'+'f'*count,*[row[i] for row in route]);arrays.append(array);self.uc.mem_write(p,array)
  self.uc.mem_write(HEAP+0x20000,bytes([0xa5])*16)
  status=self.invoke('EcmExecute',[HEAP,HEAP+0x20000,HEAP+0x20004,HEAP+0x20008],floats=[v['exposure']],stack=struct.pack('<I',HEAP+0x2000c),instructions=1000000)
  assert bytes(self.uc.mem_read(HEAP+0x2000c,4))==bytes(4)
  updated=bytearray(self.uc.mem_read(HEAP,len(context)))
  for o,length in [(0x3ccc,4),(0x3cdc,4),(0x3d00,4),(0x3cec,4),(0x3d3c,1)]:context[o:o+length]=updated[o:o+length]
  assert updated==context
  for o,p in [(0x3cdc,0),(0x3d00,4),(0x3cec,8)]:assert self.uc.mem_read(HEAP+o,4)==self.uc.mem_read(HEAP+0x20000+p,4)
  assert bytes(self.uc.mem_read(HEAP+0x11000,count*4))==arrays[1] and bytes(self.uc.mem_read(HEAP+0x12000,count*4))==arrays[2]
  data=bytes(self.uc.mem_read(HEAP+0x20000,12))+bytes(self.uc.mem_read(HEAP+0x10000,count*4))
  data+=bytes(self.uc.mem_read(HEAP+0x3ccc,4))+struct.pack('<f',float(updated[0x3d3c]))
  return ','.join(f'{x:08x}' for x in struct.unpack('<'+'I'*(5+count),data))
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 profile=json.loads((ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_text())['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib']['LinearAeCtrl']['Route']
 route=list(map(list,zip(profile['TimeDot'],profile['GainDot'],profile['IspDGainDot'])))
 cases=[]
 for prior in [0.,.003,.1,1.]:
  for exposure in [0.,.003,.099,.1,.101,.2]:
   for threshold,force in [(0.,False),(.01,False),(.1,False),(.1,True)]:cases.append(dict(route=route,exposure=exposure,prior=prior,threshold=threshold,force=force,tmin=.00005,tmax=.03,gmin=1.,gmax=512.,quantum=.01,coefficient=8.,line=2800.,clock=114.24))
 arm=OriginalRoute(BINARY);expected=[arm.run(v) for v in cases];inputs=''.join('ae-route-cached '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  actual=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='normal-return EcmExecute, EcmExecuteDirect and automatic route bodies, outputs, route mutation and selected cache state',limitations=['Linear automatic non-iris success paths only; native manual and direct-error cache publication are excluded.','Context limits, route and previous cache state are explicit inputs; imported math is modeled.','No live exposure feedback or frame-delay scheduling is added.'])
 (ROOT/'reverse-engineering/rkaiq/ae-route-cache-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
