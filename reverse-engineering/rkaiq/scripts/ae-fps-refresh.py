#!/usr/bin/env python3
"""Baseline update-mask behavior followed by FPS selection after native return."""
import copy,hashlib,json,runpy,struct,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,HEAP,regs
source=runpy.run_path(str(Path(__file__).with_name('ae-fps.py')))
class Original(source['Original']):
 def hook(self,uc,address,size,user):
  super().hook(uc,address,size,user)
  if address==(self.symbols['AecUpdateConfig']&~1):
   e=uc.reg_read(regs.UC_ARM_REG_R0);uc.reg_write(regs.UC_ARM_REG_R2,self.case['mask']);uc.mem_write(e+0x3d28,struct.pack('<2f',114.24,2800.))
 def prefix(self,v,seed):
  e=HEAP+0x40000;c=HEAP+0x50000;data=bytearray(0x25a4);data[0x1d3c:0x1fb5]=seed
  for o,x in [(0x1fc0,4),(0x1fc4,0),(0x2008,2304),(0x200c,1296),(8,5),(12,4),(16,1)]:struct.pack_into('<i',data,o,x)
  data[0]=1;data[0x14:0x14+225]=bytes([1]*225);struct.pack_into('<8f',data,0x180,0,0,1,1,.1,.1,.9,.9)
  self.uc.mem_write(c,bytes(data));self.uc.mem_write(e,bytes(0x5998));self.invoke('AecHwConfig',[c]);self.next_malloc=HEAP+0x70000
  assert self.invoke('AecUpdateConfig',[e,c,self.case['mask']],instructions=3000000)==0
 def result(self,v,seed):
  self.bounds(v,seed);e=HEAP+0x40000
  return ','.join(f'{struct.unpack("<I",self.uc.mem_read(e+o,4))[0]:08x}' for o in [0x3d24,0x3d28,0x3d2c,0x3d30,0x3d14,0x5988,0x3d20,0x3d34,0x3d38])
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a';scene=json.loads(raw)['main_scene'][0]['sub_scene'][0]['scene_isp32'];cases=[]
 for mask in [0x80,0x400,0x480,0x10400,0x100400,0x40080]:
  for fixed in [0,1]:
   for requested in [0.,15.,60.]:
    for frame,line,clock in [(1360.,2800.,114.24),(20416.,2800.,114.24),(1500.,2500.,99.)]:
     s=copy.deepcopy(scene);s['ae_calib']['CommCtrl']['AecFrameRateMode']=dict(isFpsFix=fixed,FpsValue=requested)
     cases.append(dict(scene=s,mask=mask,frame=frame,line=line,clock=clock,minimum_fps=1.,baseline_frame=1360.,baseline_fps=30.,factors=[0.,0.,1.,.5],minimum=1,maxfactors=[1.,8.],route_min=0.,route_max=.03,override=False,override_min=0.,override_max=0.,enabled=True,mode=0))
 init=source['source']['source']['source']['Init']();init.uc.mem_write(HEAP,bytes(8));init.invoke('AecInit',[HEAP,HEAP+0x80000,4]);native=Original(BINARY);expected=[native.result(v,init.defaults) for v in cases];inputs=''.join('ae-fps-refresh '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='all four cached baseline timing fields plus selected FPS/frame fields after complete native configuration return across six update masks',limitations=['Explicit initialized timing/configuration and previous cache; full zero-mask initialization is not qualified.','Refresh predicate is ported at the native timing stage; complete outer update-mask dispatch is external.','Inherited harness models allocation/comparison/division/rounding and diagnostics; unrelated private context and sensor writes excluded.'])
 (ROOT/'reverse-engineering/rkaiq/ae-fps-refresh-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
