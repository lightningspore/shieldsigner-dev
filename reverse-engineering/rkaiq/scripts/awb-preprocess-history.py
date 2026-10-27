#!/usr/bin/env python3
"""Join native AWB numerical prefix, environment and luma history to measurement entry."""
import hashlib,json,random,runpy,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,f32
reference=runpy.run_path(str(Path(__file__).with_name('awb-preprocess.py')));Original=reference['Original'];RUNTIME=reference['RUNTIME']
def main():
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==manifest['binaries'][0]['sha256'];assert hashlib.sha256(RUNTIME.read_bytes()).hexdigest()==manifest['gccRuntime']['memberSha256']
 arm=Original();rng=random.Random(0x41574248);cases=[];expected=[]
 for i in range(512):
  history=[rng.choice([0,255,1000,0xffffffff]) for _ in range(i%8)]
  if i%3==0:history=[0]*len(history)
  v=dict(mode=[0,1,2][i%3],update=bool(i//3%2),enabled=bool(i//6%2),countdown=[0,2][i//12%2],source=None if i%3==0 else [f32(rng.uniform(0,100)),f32(rng.uniform(0,200))],choice=i%4,working=[0,16][i//4%2],fallback=[0,110,200,65536,65600,0xffffffff][i//3%6],override_enabled=False,override_valid=False,override=0.,block=[15,15],scale=1,knots=[0.,1000.,200000.],frame=[0,1,2,17,100,0xffffffff][i//3%6],metadata=dict(history=history,target=[0,2,4,8][i//8%4],boundaries=[] if i%7==0 else [0,128,1024,65536,262144],thresholds=[110,200,65536,65600],convergence=[bool(i//2%2),bool(i//4%2)]))
  if i%13==0:v['metadata']['boundaries']=[128,1024,65536,262144]
  for key in ['smart0','smart1','smart2']:v[key]=[f32(rng.choice([0.,.001,.05,.5])) for _ in range(3)]
  v['intervals']=[float(i%5)]*3
  for key in ['points0','points1','regions0','regions1']:v[key]=[150.,216.,300.]
  cases.append(v);expected.append(arm.run(v))
 inputs=''.join('awb-preprocess '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  p=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True);actual=[json.loads(s) for s in p.stdout.splitlines()];assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')]);arm_replay='--arm' in sys.argv
 if arm_replay:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,arm=arm_replay,measurementEntries=sum(e['decision']==2 for e in expected),scope='Joined numerical prefix, native environment classification, list updates, exact variance and update flags up to PrepareMeasureResult entry',limitations=['Execution stops at the first PrepareMeasureResult instruction; measurement classification and later gain/reconfiguration do not execute.','Native malloc uses an explicit node allocator; storage/lifetime failures excluded.','Test inputs are synthetic finite valid calibration curves; no complete IQ loader or live AWB service.'])
 (ROOT/'reverse-engineering/rkaiq/awb-preprocess-history-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
