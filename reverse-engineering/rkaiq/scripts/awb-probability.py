#!/usr/bin/env python3
"""Original white-point filter plus unmodified native total-probability call tree."""
import argparse,hashlib,json,random,struct,subprocess
from pathlib import Path
from awb_reference import OriginalAwb,RUNTIME
from differential import ROOT,BINARY,HEAP,f32
FIELDS=[0x74,0x78,0x7c,0x80,0x94]
def run(arm,v):
 n=len(v['lights']);context=bytearray([0xa7])*0x4000;strategy=bytearray(0x1000);calibration=bytearray(0x800);mode=bytearray(0x200)
 reference=bytearray([0x5b])*(n*0xe4);statistics=bytearray([0x6d])*(n*0xac);priors=bytearray([0x7e])*(n*0xfc);curves=bytearray([0x8f])*(n*0x100)
 state=v['seed'];results=bytearray()
 for _ in range(n*0xa0):state=(state*1664525+1013904223)&0xffffffff;results.append(state>>24)
 for offset,pointer in [(0x80,0x9000),(0x8c,0x8000),(0x134,0x30000),(0x2dec,0xa000),(0x33e4,0x20000)]:struct.pack_into('<I',context,offset,HEAP+pointer)
 struct.pack_into('<If',context,0x33d8,v['brightness'],v['sample'])
 struct.pack_into('<I',context,0x33ac,v['frame']);struct.pack_into('<4f',context,0x353c,*v['gain']);strategy[0x138]=n;struct.pack_into('<I',strategy,0x368,HEAP+0x10000);struct.pack_into('<2f',strategy,0x1c0,v['near'],v['far']);struct.pack_into('<4I',strategy,0x1c8,*v['thresholds']);struct.pack_into('<2f',strategy,0x1f0,v['absolute'],v['relative']);struct.pack_into('<I',calibration,0x43c,HEAP+0x40000)
 text=b'FASTAWBACT\0' if v['fast'] else b'NORMAL\0';mode[0x1c:0x1c+len(text)]=text
 for i,light in enumerate(v['lights']):
  struct.pack_into('<i',reference,i*0xe4+0x64,light['kind']);struct.pack_into('<4f',reference,i*0xe4+0x80,*light['gain']);struct.pack_into('<I',statistics,i*0xac+v['xy']*0x34,light['count']);struct.pack_into('<f',results,i*0xa0+0x7c,light['oldLuma'])
  struct.pack_into('<4f',results,i*0xa0+0x64,*light['statisticGain'])
  struct.pack_into('<III',priors,i*0xfc+0xec,HEAP+0x60000+i*0x100,len(light['knots']),HEAP+0x60000+i*0x100+0x40);struct.pack_into('<'+'f'*len(light['knots']),curves,i*0x100,*light['knots']);struct.pack_into('<'+'f'*len(light['weights']),curves,i*0x100+0x40,*light['weights'])
 blocks=[(0,context),(0x8000,strategy),(0x9000,calibration),(0xa000,mode),(0x10000,reference),(0x20000,results),(0x30000,statistics),(0x40000,priors),(0x60000,curves)]
 for offset,data in blocks:arm.uc.mem_write(HEAP+offset,bytes(data))
 arm.invoke('_Z20AwbCalWpNoProbablityiP12awb_contex_s',[v['xy'],HEAP],instructions=1000000)
 arm.invoke('_Z21AwbCalTotalProbablityiP12awb_contex_s',[v['xy'],HEAP],instructions=1000000)
 arm.invoke('_Z15AwbCalGainTotalP12awb_contex_s',[HEAP],instructions=1000000)
 after=bytearray(arm.uc.mem_read(HEAP,0x4000));count=struct.unpack_from('<I',after,0x33c8)[0];gain=':'.join(f'{x:08x}' for x in struct.unpack_from('<4I',after,0x353c));after[0x33c8:0x33cc]=context[0x33c8:0x33cc];after[0x353c:0x354c]=context[0x353c:0x354c];assert after==context
 after=bytearray(arm.uc.mem_read(HEAP+0x20000,len(results)));out=[]
 for i in range(n):
  out.append(':'.join(f'{struct.unpack_from("<I",after,i*0xa0+o)[0]:08x}' for o in FIELDS))
  for o in FIELDS:after[i*0xa0+o:i*0xa0+o+4]=results[i*0xa0+o:i*0xa0+o+4]
 assert after==results
 for offset,data in blocks:
  if offset not in (0,0x20000):assert bytes(arm.uc.mem_read(HEAP+offset,len(data)))==data
 assert arm.allocation is None
 return f'{count:08x}:'+','.join(out)+'|'+gain
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=2000);p.add_argument('--emit-dir',type=Path);a=p.parse_args();arm=OriginalAwb(stdlib=True);rng=random.Random(0x41575052);inputs=[];expected=[];coverage={}
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();runtime_sha=hashlib.sha256(RUNTIME.read_bytes()).hexdigest();assert sha==next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name);assert runtime_sha==manifest['gccRuntime']['memberSha256']
 for i in range(a.cases):
  n=255 if i%97==0 else rng.randrange(1,9);kind=i%12;thresholds=[100,200,400,800];brightness=[0,99,100,199,200,399,400,401,600,799,800,801,0xffffffff][i//12%13]
  v=dict(seed=rng.randrange(0xffffffff),xy=i//12%4,frame=i+1,fast=kind==0,near=f32(rng.uniform(0,.1)),far=f32(rng.uniform(.1,1)),gain=[f32(rng.uniform(.5,4)) for _ in range(4)],brightness=brightness,thresholds=thresholds,sample=f32(rng.uniform(0,5)),absolute=f32(rng.choice([-1.,0.,1.,100.,4294967296.])),relative=f32(rng.choice([0.,.001,.1,.5,1.])),lights=[])
  if kind==1:v['frame']=0
  elif kind==2:v['gain']=[0.]*4
  elif kind==3:v['near']=0.;v['far']=0.
  elif kind==6:v['absolute']=f32(4294967296.);v['relative']=1.
  elif kind==9:v['near']=.0625;v['far']=.25;v['gain']=[1.]*4
  elif kind==10:v['thresholds']=[0,0,16777216,16777220];v['brightness']=16777216+i//12%6
  elif kind==11:v['gain']=[f32([.00001,.000010001][i//12%2]),1.,1.,1.]
  for j in range(n):
   count=rng.choice([0,1,100,rng.randrange(0xffffffff),0xffffffff]);knots=[0.,f32(rng.uniform(.01,1)),2.,5.];weights=[f32(rng.uniform(0,1)) for _ in knots]
   if kind==4:weights=[f32([0.,.00001/n,.000010001/n,.000009999/n][i//12%4])]*4
   if kind==5:count=0
   light=dict(gain=[f32(rng.uniform(.5,4)) for _ in range(4)],kind=[1,2,3][j%3],count=count,knots=knots,weights=weights,oldLuma=f32(rng.uniform(0,1)))
   light['statisticGain']=[f32(rng.uniform(.5,8)) for _ in range(4)]
   if kind==8:light['kind']=[-1,0,1,2,3,4][j%6]
   if kind==9:light['gain']=[1.+[0.,.25,.375,.5][j%4],1.,1.,1.]
   v['lights'].append(light)
  inputs.append('awb-probability '+json.dumps(v,separators=(',',':')));expected.append(run(arm,v));key=f'{kind}:{n}:{v["xy"]}';coverage[key]=coverage.get(key,0)+1
 assert not arm.calls and not arm.runtime.calls,(arm.calls,arm.runtime.calls)
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[dict(case=i,input=inputs[i],expected=x,actual=y) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
 report=dict(binarySha256=sha,runtimeSha256=runtime_sha,cases=len(inputs),seed='0x41575052',mismatchCount=len(mismatches),nativeRuntimeFunctions=sorted(arm.runtime_functions),nativeRuntimeImportedCalls=arm.runtime.calls,modeledStandardCalls=arm.standard_calls,elfEntries={'whitePointFilter':'0xc62a8','totalProbability':'0xc6588','distance':'0xc5f18','brightness':'0xc60d8','lightPrior':'0xc6458','weightedGain':'0xc696c'},coverage=coverage,scope='Native selected-XY white-point filtering followed by the entire original total-probability call tree: all five f32 values per light, retained-count low word, normalized weighted output gain and input/context/result preservation',limitations=['Bounded strcmp semantics and single successful malloc/free are controlled standard-library boundaries; allocation failure is outside this safe value API.','GCC integer conversion/division and RKAIQ interpolation execute original ARM instructions.','Selected counts/gains, reference gains, light kinds and prior tables are explicit inputs; their upstream calibrated construction and the outer AWB controller remain unfinished.','Wide/unknown light-kind and 255-light cases establish value behavior, not physical sensor calibration or hardware qualification.'])
 if mismatches:report['firstMismatches']=mismatches[:2]
 (ROOT/'reverse-engineering/rkaiq/awb-probability-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('coverage','firstMismatches')},indent=2))
 if mismatches:print(json.dumps(mismatches[:1]));raise SystemExit(1)
 if a.emit_dir:
  a.emit_dir.mkdir(parents=True,exist_ok=True);(a.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(a.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
