#!/usr/bin/env python3
"""Compare fixed-frame linear shutter bounds after normal native configuration."""
import hashlib,json,runpy,struct,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,HEAP,regs
source=runpy.run_path(str(Path(__file__).with_name('ae-flicker.py')))
class OriginalBounds(source['OriginalFlicker']):
 def hook(self,uc,address,size,user):
  if self.stubs.get(address)=="printf":
   uc.reg_write(regs.UC_ARM_REG_R0,0);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if self.stubs.get(address)=="vsnprintf":
   # Diagnostics only: suppress formatting; preserve normal configuration execution.
   uc.mem_write(uc.reg_read(regs.UC_ARM_REG_R0),b"\0");uc.reg_write(regs.UC_ARM_REG_R0,0);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
  if address==(self.symbols['AecUpdateConfig']&~1):
   engine=uc.reg_read(regs.UC_ARM_REG_R0);config=uc.reg_read(regs.UC_ARM_REG_R1);v=self.case
   for o,value in [(0x3d24,v['frame']),(0x3d28,v['clock']),(0x3d2c,v['line']),(0x3d30,30.),*list(zip([0x644,0x648,0x64c,0x650],v['factors'])),(0x67c,v['maxfactors'][0]),(0x680,v['maxfactors'][1]),(0x684,1.),(0x688,0.)]:uc.mem_write(engine+o,struct.pack('<f',value))
   uc.mem_write(engine+0x678,struct.pack('<H',v['minimum']))
   for o,value in zip(range(0x654,0x674,4),[1,48.64,1,1,1,16,1,32]):uc.mem_write(engine+o,struct.pack('<f',value))
   uc.mem_write(config+4,struct.pack('<I',1));uc.mem_write(config+0x15c,b'\1');uc.mem_write(config+0x160,bytes(4));uc.mem_write(config+0x1d24,struct.pack('<f',1.));uc.mem_write(config+0x16c,struct.pack('<I',v['mode']))
   uc.mem_write(config+0x1fd0,struct.pack('<f',v['frame']))
   uc.mem_write(config+0x22b4,bytes([v['override']]));uc.mem_write(config+0x22b8,struct.pack('<ff',v['override_min'],v['override_max']))
   for n,(values,offset)in enumerate([([v['route_min'],v['route_max']],0x1dc),([1.,32.],0x1e4),([1.,1.],0x1ec),([512.,512.],0x1f4)]):
    pointer=HEAP+0x80000+n*0x1000;uc.mem_write(pointer,struct.pack('<2f',*values));uc.mem_write(config+offset,struct.pack('<II',pointer,2))
 def bounds(self,v,seed):
  v=dict(v,frequency=1,detected=0.,prior=.012345,alternate=.023456,coefficient=v['factors'][2])
  self.run(v,seed);engine=HEAP+0x40000
  return ','.join(f'{struct.unpack("<I",self.uc.mem_read(engine+o,4))[0]:08x}' for o in [0x780,0x784,0xfc,0x100])
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 init=source['source']['Init']();init.uc.mem_write(HEAP,bytes(8));init.invoke('AecInit',[HEAP,HEAP+0x80000,4]);arm=OriginalBounds(BINARY);cases=[]
 for frame in [1320.,1500.]:
  for route_max in [.005,.0199,.03,.1]:
   for enabled,mode in [(False,0),(True,0),(True,1)]:
    cases.append(dict(frame=frame,line=2500.,clock=99.,factors=[0.,0.,1.,.5],minimum=1,maxfactors=[1.,8.],route_min=0.,route_max=route_max,override=False,override_min=0.,override_max=0.,enabled=enabled,mode=mode))
 for low,high in [(0.,.002),(.02,.001),(.1,.001),(.005,.1)]:
  for enabled in [False,True]:cases.append(dict(frame=1320.,line=2500.,clock=72.,factors=[0.,0.,1.,.5],minimum=2,maxfactors=[1.,8.],route_min=.001,route_max=.03,override=True,override_min=low,override_max=high,enabled=enabled,mode=0))
 for factors in [[.1,.2,2.,.5],[0.,1.,.5,0.]]:
  cases.append(dict(frame=1320.,line=2500.,clock=99.,factors=factors,minimum=2,maxfactors=[1.,8.],route_min=0.,route_max=.0199,override=False,override_min=0.,override_max=0.,enabled=True,mode=0))
 profile=json.loads((ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_text())
 sensor=profile['sensor_calib'];route=profile['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib']['LinearAeCtrl']['Route']
 for frame,clock in [(1320.,99.),(1500.,72.)]:
  cases.append(dict(frame=frame,line=2500.,clock=clock,factors=sensor['Time2Reg']['fCoeff'],minimum=sensor['CISTimeSet']['Linear']['CISTimeRegMin'],maxfactors=sensor['CISTimeSet']['Linear']['CISLinTimeRegMaxFac']['fCoeff'],route_min=route['TimeDot'][0],route_max=route['TimeDot'][-1],override=False,override_min=0.,override_max=0.,enabled=True,mode=0,profile=profile))
 expected=[arm.bounds(v,init.defaults) for v in cases];inputs=''.join('ae-shutter '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  actual=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b)in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
  compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly',image,'/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='physical and final selected linear fixed-frame shutter bounds after normal native AecUpdateConfig return',limitations=['Runtime frame/timing, route endpoints, sensor coefficients and overrides are injected explicitly; complete private-context equivalence is not claimed.','The configuration harness models allocation/comparison/division and imported rounding functions; diagnostic printf/vsnprintf output is suppressed.','FPS choice, variable-frame-rate/HDR policy, gain/DCG bounds and feedback scheduling remain outside scope.'])
 (ROOT/'reverse-engineering/rkaiq/ae-shutter-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
