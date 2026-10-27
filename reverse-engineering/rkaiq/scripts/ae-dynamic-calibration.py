#!/usr/bin/env python3
"""Profile dynamic mode/enables/parameters through complete native control."""
import copy,hashlib,json,runpy,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY
Original=runpy.run_path(str(Path(__file__).with_name('ae-controller.py')))['Original']
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());headers={}
 for name in ['aec_head.h','rk_aiq_comm.h']:
  entry=next(x for x in manifest['headers'] if x['name']==name);raw_header=(ROOT/'.tools/reverse-engineering/headers'/name).read_bytes();assert hashlib.sha256(raw_header).hexdigest()==entry['sha256'];headers[name]=entry['sha256']
 comm=(ROOT/'.tools/reverse-engineering/headers/rk_aiq_comm.h').read_text();assert 'RK_AIQ_OP_MODE_AUTO               = 1' in comm and 'RK_AIQ_OP_MODE_MANUAL             = 2' in comm
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a';scene=json.loads(raw)['main_scene'][0]['sub_scene'][0]['scene_isp32'];cases=[]
 for k in range(64):
  for outer in [False,True]:
   for manual in [False,True]:
    s=copy.deepcopy(scene);d=s['ae_calib']['CommCtrl']['AecSpeed']['DyDamp'];d.update(DyDampEn=int(outer),SlowOPType='RK_AIQ_OP_MODE_MANUAL' if manual else 'RK_AIQ_OP_MODE_AUTO')
    if manual:d.update(SlowRange=[5.,15.][k%2],SlowDamp=[.7,.95][(k//2)%2])
    h=[0]*256;h[[3,120,254,255][k%4]]=1000
    cases.append(dict(policy_scene=s,bind_dynamic=True,alternate=False,histogram=h,measured=[3.,38.25,40.5,45.,49.5,51.75,120.,240.][k%8],exposure=[.003,.02,.1][k%3],previous=[-.5,0.,.5][k%3],reference=[-.5,0.,.5][(k//3)%3],fps=[2.,30.][k%2],enabled=bool(k%2),same_mode=k%5!=0,priming=k%7==0,saturated=bool(k%2),force=k%3==0,index=k%20,frame=30+k,sync=28+k,dynamic=outer,dynamic_enabled=bool((k//2)%2),custom=manual,damping_history=[((i+k)%7-3)*.01 for i in range(10)]))
 native=Original(BINARY);expected=[native.run(v) for v in cases];inputs=''.join('ae-controller '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,headerSha256=headers,cases=len(cases),actualProfileCases=64,mismatches=0,armReplayPassed='--arm' in sys.argv,scope='profile dynamic call-enable, AUTO/MANUAL mode and manual parameters through complete native AecClmExecute including state and damping diagnostics',limitations=['Configuration fields injected into recovered context slots; full native calibration-loader equivalence is not claimed.','Runtime damping enable remains a separate explicit convergence flag; zero manual scale rejected by checked Rust loader.','Manual/disabled profile variants deliberately extend actual AUTO/enabled profile coverage.','Other policy/limits/initialization and hardware writes remain external.'])
 (ROOT/'reverse-engineering/rkaiq/ae-dynamic-calibration-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
