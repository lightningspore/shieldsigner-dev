#!/usr/bin/env python3
"""Delay counts after complete native configuration, with explicit timing input."""
import copy,hashlib,json,runpy,struct,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,HEAP,regs
source=runpy.run_path(str(Path(__file__).with_name('ae-shutter.py')))
class Original(source['OriginalBounds']):
 def hook(self,uc,address,size,user):
  super().hook(uc,address,size,user)
  if address==(self.symbols['AecUpdateConfig']&~1):
   config=uc.reg_read(regs.UC_ARM_REG_R1);d=self.case['scene']['ae_calib']['CommCtrl']['AecDelay']
   uc.mem_write(config+0x154,struct.pack('<I',0 if d['DelayType']=='DELAY_TYPE_FRAME' else 1));uc.mem_write(config+0x158,bytes([d['BlackDelay'],d['WhiteDelay']]))
 def result(self,v,seed):
  self.bounds(v,seed);e=HEAP+0x40000
  actual=struct.unpack('<3f',self.uc.mem_read(e+0x3d14,12));assert actual==struct.unpack('<3f',struct.pack('<3f',v['frame'],v['clock'],v['line'])),actual
  return ','.join(str(x) for x in self.uc.mem_read(e+0x40d0,2))
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());header=next(x for x in manifest['headers'] if x['name']=='aec_head.h');raw_header=(ROOT/'.tools/reverse-engineering/headers/aec_head.h').read_bytes();assert hashlib.sha256(raw_header).hexdigest()==header['sha256'];assert b'DELAY_TYPE_FRAME = 0' in raw_header and b'DELAY_TYPE_TIME = 1' in raw_header
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a';scene=json.loads(raw)['main_scene'][0]['sub_scene'][0]['scene_isp32']
 init=source['source']['source']['Init']();init.uc.mem_write(HEAP,bytes(8));init.invoke('AecInit',[HEAP,HEAP+0x80000,4]);native=Original(BINARY);cases=[]
 for mode in ['DELAY_TYPE_FRAME','DELAY_TYPE_TIME']:
  for frame in [132.,1360.,3000.,20416.]:
   for line,clock in [(2800.,114.24),(2500.,99.),(3000.,72.)]:
    for black,white in [(0,0),(2,2),(1,3),(255,255),(128,64)]:
     s=copy.deepcopy(scene);s['ae_calib']['CommCtrl']['AecDelay']=dict(DelayType=mode,BlackDelay=black,WhiteDelay=white)
     cases.append(dict(scene=s,frame=frame,line=line,clock=clock,factors=[0.,0.,1.,.5],minimum=1,maxfactors=[1.,8.],route_min=0.,route_max=.03,override=False,override_min=0.,override_max=0.,enabled=True,mode=0))
 expected=[native.result(v,init.defaults) for v in cases];inputs=''.join('ae-delay-calibration '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,{k:cases[i][k] for k in ['frame','line','clock']},a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,headerSha256=header['sha256'],cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='black/white transition delay bytes after complete native AecUpdateConfig return, fixed-frame timing checked',limitations=['Timing/configuration inputs are explicit; inherited native configuration harness models allocation/comparison/division/rounding and diagnostic output.','Frame and time enum values checked against pinned SDK header; other configuration fields/private context not claimed equivalent.','Controller-transition delays only, not sensor exposure-application delay; no hardware writes.'])
 (ROOT/'reverse-engineering/rkaiq/ae-delay-calibration-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
