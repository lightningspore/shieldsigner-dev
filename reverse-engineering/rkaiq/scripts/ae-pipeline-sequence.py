#!/usr/bin/env python3
"""Keep native and Rust pipeline state alive across frame sequences."""
import hashlib,json,runpy,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY
Original=runpy.run_path(str(Path(__file__).with_name('ae-pipeline.py')))['Original']
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'
 runtime_sha=hashlib.sha256((ROOT/'.tools/reverse-engineering/uclibc-runtime/libuClibc-1.0.31.so').read_bytes()).hexdigest();assert runtime_sha==json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text())['uclibcRuntime']['memberSha256']
 cases=[]
 for count in [0,2,5]:
  for dynamic in [False,True]:
   for priming in [False,True]:
    initial=dict(profile=dict(sensor_calib=json.loads(raw)['sensor_calib']),histogram=[0]*256,measured=.390625,exposure=.003,previous=0.,reference=0.,fps=30.,enabled=True,same_mode=True,priming=priming,saturated=False,force=False,index=0,frame=30,sync=28,dynamic=dynamic,dynamic_enabled=True,custom=False,damping_history=[0.]*10,run_wrapper=True,run=True,count=count)
    frames=[]
    for i in range(32):
     mean=[.390625,.390625,3.,3.,45.,45.,120.,120.][i%8];h=[0]*256;h[[3,120,254,255][i%4]]=1000
     frames.append(dict(frame=30+i,measured=mean,exposure=[.003,.02,.1][i%3],histogram=h))
    cases.append(dict(initial=initial,frames=frames))
 cases += [dict(v,frames=[dict(f,effective_from_previous=True) for f in v['frames']]) for v in cases]
 expected=[];processed=0;steps=0
 native=Original()
 for case in cases:
  native.initialize(case['initial']);outputs=[]
  for frame in case['frames']:
   outputs.append(native.step(dict(case['initial'],**frame)));steps+=1;processed+=int(native.last_run)
  expected.append('|'.join(outputs))
 inputs=''.join('ae-pipeline-sequence '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):
   if a!=b:
    for j,(x,y) in enumerate(zip(a.split('|'),b.split('|'))):
     if x!=y:
      xx=x.split(':');yy=y.split(':');print('mismatch sequence/frame',i,j,file=sys.stderr)
      for k,(p,q) in enumerate(zip(xx,yy)):
       if p!=q:print('field',k,[(n,l,r) for n,(l,r) in enumerate(zip(p.split(','),q.split(','))) if l!=r][:20] if k==0 else (p[:60],q[:60]),file=sys.stderr)
      raise AssertionError((i,j))
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,runtimeSha256=runtime_sha,sequences=len(cases),frames=steps,processed=processed,skipped=steps-processed,mismatches=0,armReplayPassed='--arm' in sys.argv,scope='persistent native/Rust standard pipeline state over 32-frame sequences with per-frame outputs and listed state compared',limitations=['Synthetic statistics with two effective-input strategies: explicit scalar/zero codes, or prior converted point and codes supplied on the next frame. This is not a physical exposure-delay model.','Fixed target45 and explicit runtime policy, linear non-iris/DCG-disabled path; preprocessing stops at current-error checkpoint.','Other ISP results/CIS flags/unlisted context excluded; no hardware writes or real latency qualification.'])
 (ROOT/'reverse-engineering/rkaiq/ae-pipeline-sequence-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
