#!/usr/bin/env python3
"""Profile tolerance/damping selection through complete native brightness control."""
import copy,hashlib,json,runpy,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY
Original=runpy.run_path(str(Path(__file__).with_name('ae-controller.py')))['Original']
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'
 scene=json.loads(raw)['main_scene'][0]['sub_scene'][0]['scene_isp32'];cases=[]
 for k in range(64):
  for alternate in [False,True]:
   for changed in [False,True]:
    s=copy.deepcopy(scene)
    if changed:
     s['ae_calib']['LinearAeCtrl'].update(ToleranceIn=20.,ToleranceOut=30.);s['ae_calib']['CommCtrl']['AecSpeed'].update(DampOver=.1,DampUnder=.2,DampDark2Bright=.7,DampBright2Dark=.8)
    h=[0]*256;h[[3,120,254,255][k%4]]=1000
    cases.append(dict(policy_scene=s,alternate=alternate,histogram=h,measured=[38.25,40.5,45.,49.5,51.75,3.,120.,58.5][k%8],exposure=[.003,.02,.1][k%3],previous=[-.5,0.,.5][k%3],reference=[-.5,0.,.5][(k//3)%3],fps=[2.,30.][k%2],enabled=bool(k%2),same_mode=k%5!=0,priming=k%7==0,saturated=bool(k%2),force=k%3==0,index=k%20,frame=30+k,sync=28+k,dynamic=bool((k//2)%2),dynamic_enabled=bool((k//4)%2),custom=False,damping_history=[((i+k)%7-3)*.01 for i in range(10)]))
 native=Original(BINARY);expected=[native.run(v) for v in cases];inputs=''.join('ae-controller '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i]['alternate'],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,cases=len(cases),actualProfileCases=len(cases)//2,mismatches=0,armReplayPassed='--arm' in sys.argv,scope='IQ tolerance/damping values selected by native AecClmExecute through complete control return, including controller state and diagnostics',limitations=['Profile fields are injected into their recovered context slots; this is not complete native calibration-loader equivalence.','Runtime alternate flag +0x23ce and convergence gating flag are explicit; alternate-flag producer remains external.','Uniform selected tolerance is bound; other runtime policy, limits, dynamics/delay calibration and hardware writes are not added.','Half the cases deliberately change tolerances and all four damping coefficients to distinguish selector branches.'])
 (ROOT/'reverse-engineering/rkaiq/ae-policy-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
