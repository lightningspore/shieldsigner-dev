#!/usr/bin/env python3
"""Compare linear non-DCG gain limits after normal native configuration return."""
import hashlib,json,runpy,struct,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,HEAP,regs
source=runpy.run_path(str(Path(__file__).with_name('ae-shutter.py')))
class Original(source['OriginalBounds']):
 def hook(self,uc,address,size,user):
  super().hook(uc,address,size,user)
  if address==(self.symbols['AecUpdateConfig']&~1):
   e=uc.reg_read(regs.UC_ARM_REG_R0);c=uc.reg_read(regs.UC_ARM_REG_R1);v=self.case
   for offset,pair in [(0x654,v['analogue']),(0x664,v['digital']),(0x66c,v['isp'])]:uc.mem_write(e+offset,struct.pack('<2f',*pair))
   uc.mem_write(e+0x6d8,bytes(4)) # DCG support disabled
   uc.mem_write(c+0x22c0,struct.pack('<4f',*v['gain_overrides']))
   for n,key in [(1,'route_gain'),(2,'route_isp')]:uc.mem_write(HEAP+0x80000+n*0x1000,struct.pack('<2f',*v[key]))
 def result(self,v,seed):
  self.bounds(v,seed);e=HEAP+0x40000
  return ','.join(f'{struct.unpack("<I",self.uc.mem_read(e+o,4))[0]:08x}' for o in [0x758,0x75c,0x104,0x108,0x10c,0x110])
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 init=source['source']['source']['Init']();init.uc.mem_write(HEAP,bytes(8));init.invoke('AecInit',[HEAP,HEAP+0x80000,4]);arm=Original(BINARY);cases=[]
 base=dict(frame=1360.,line=2800.,clock=114.24,factors=[0.,0.,1.,.5],minimum=1,maxfactors=[1.,8.],route_min=0.,route_max=.03,override_min=0.,override_max=0.,enabled=True,mode=0)
 for analogue,digital,isp in [([1.,48.64],[1.,16.],[1.,32.]),([2.,8.],[1.,4.],[1.,8.]),([1.5,10.3],[1.1,3.7],[2.,16.])]:
  for route_gain,route_isp in [([1.,512.],[1.,1.]),([.5,1000.],[.5,64.]),([4.,5.],[4.,8.])]:
   for override,values in [(False,[0.,0.,0.,0.]),(True,[0.,0.,0.,0.]),(True,[3.,12.,2.,4.]),(True,[20.,2.,10.,1.])]:cases.append(dict(base,analogue=analogue,digital=digital,isp=isp,route_gain=route_gain,route_isp=route_isp,override=override,gain_overrides=values))
 expected=[arm.result(v,init.defaults) for v in cases];inputs=''.join('ae-gain-limits '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  actual=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='physical sensor gain and final selected linear sensor/ISP gain bounds after normal AecUpdateConfig return',limitations=['DCG-disabled linear mode with nonzero valid calibration ranges only.','Route endpoints, calibration ranges and overrides are explicit inputs.','Inherited configuration harness models allocation, comparison, division, rounding and diagnostic output; complete private context equivalence is not claimed.','No live automatic exposure scheduling is introduced.'])
 (ROOT/'reverse-engineering/rkaiq/ae-gain-limits-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
