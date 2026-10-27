#!/usr/bin/env python3
"""Frame/FPS selection after complete native configuration with cached baseline."""
import copy,hashlib,json,runpy,struct,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,HEAP,regs
source=runpy.run_path(str(Path(__file__).with_name('ae-shutter.py')))
class Original(source['OriginalBounds']):
 def hook(self,uc,address,size,user):
  super().hook(uc,address,size,user)
  if address==(self.symbols['AecUpdateConfig']&~1):
   e=uc.reg_read(regs.UC_ARM_REG_R0);c=uc.reg_read(regs.UC_ARM_REG_R1);v=self.case;d=v['scene']['ae_calib']['CommCtrl']['AecFrameRateMode'];uc.mem_write(c+0x15c,bytes([d['isFpsFix']]));uc.mem_write(c+0x160,struct.pack('<f',d['FpsValue']));uc.mem_write(c+0x1d24,struct.pack('<f',v['minimum_fps']))
   for o,x in [(0x3d24,v['baseline_frame']),(0x3d30,v['baseline_fps']),(0x3d20,2222.),(0x3d34,7.),(0x3d38,8.)]:uc.mem_write(e+o,struct.pack('<f',x))
 def result(self,v,seed):
  self.bounds(v,seed);e=HEAP+0x40000
  assert self.uc.mem_read(e+0x3d24,4)==struct.pack('<f',v['baseline_frame']);assert self.uc.mem_read(e+0x3d30,4)==struct.pack('<f',v['baseline_fps'])
  return ','.join(f'{struct.unpack("<I",self.uc.mem_read(e+o,4))[0]:08x}' for o in [0x3d14,0x5988,0x3d20,0x3d34,0x3d38])
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a';scene=json.loads(raw)['main_scene'][0]['sub_scene'][0]['scene_isp32'];cases=[]
 for fixed in [0,1]:
  for requested in [0.,1.,15.,30.,60.]:
   for minimum in [1.,20.,40.]:
    for frame,line,clock in [(1360.,2800.,114.24),(20416.,2800.,114.24),(1500.,2500.,99.)]:
     s=copy.deepcopy(scene);s['ae_calib']['CommCtrl']['AecFrameRateMode']=dict(isFpsFix=fixed,FpsValue=requested)
     cases.append(dict(scene=s,frame=frame,line=line,clock=clock,minimum_fps=minimum,baseline_frame=1360.,baseline_fps=30.,factors=[0.,0.,1.,.5],minimum=1,maxfactors=[1.,8.],route_min=0.,route_max=.03,override=False,override_min=0.,override_max=0.,enabled=True,mode=0))
 init=source['source']['source']['Init']();init.uc.mem_write(HEAP,bytes(8));init.invoke('AecInit',[HEAP,HEAP+0x80000,4]);native=Original(BINARY);expected=[native.result(v,init.defaults) for v in cases];inputs=''.join('ae-fps '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='selected frame length, effective FPS, variable-frame limit and fixed/variable selected rates after complete native AecUpdateConfig return',limitations=['Cached baseline frame/FPS and runtime timing/minimum FPS are explicit; baseline refresh ownership is external.','Positive finite valid domain, fixed and variable configuration selection only; actual sensor VBLANK writes and dynamic VTS evolution excluded.','Inherited configuration harness models allocation/comparison/division/rounding and diagnostics; complete context equivalence is not claimed.'])
 (ROOT/'reverse-engineering/rkaiq/ae-fps-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
