#!/usr/bin/env python3
"""Compare ordinary linear AecRun control/state orchestration."""
import hashlib,json,runpy,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY
Original=runpy.run_path(str(Path(__file__).with_name('ae-controller.py')))['Original']
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest()
 assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 cases=[]
 for k in range(80):
  h=[0]*256;h[[3,120,254,255][k%4]]=1000
  for run in [False,True]:
   for dynamic,enabled,custom in [(False,False,False),(True,False,False),(True,True,False),(True,True,True)]:
    cases.append(dict(run_wrapper=True,run=run,histogram=h,measured=[0.,3.,40.5,45.,49.5,120.,240.][k%7],exposure=[.003,.02,.1][k%3],previous=[-.5,0.,.5][k%3],reference=[-.5,0.,.5][(k//3)%3],fps=[2.,30.][k%2],enabled=bool(k%2),same_mode=k%5!=0,priming=k%7==0,saturated=bool(k%2),force=k%3==0,index=k%20,frame=30+k,sync=28+k,dynamic=dynamic,dynamic_enabled=enabled,custom=custom,damping_history=[((i+k)%7-3)*.01 for i in range(10)]))
 native=Original(BINARY);expected=[native.run(v) for v in cases]
 inputs=''.join('ae-controller '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='ordinary linear AecRun through normal return including real native AecClmExecute, run/skip bookkeeping, control-index advancement and previous-mean publication',limitations=['DCG and register-value conversion are explicit successful no-op boundaries; call counts are checked.','Preprocessing supplies run flag and current measurements; missing-statistics/manual/HDR/iris branches are excluded.','Successful control paths only; conversion failures and partially mutated error state are not covered.','No live writes or physical frame association are introduced.'])
 (ROOT/'reverse-engineering/rkaiq/ae-run-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
