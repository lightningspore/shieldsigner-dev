#!/usr/bin/env python3
"""Compare AWB normalization, mixture, coefficient adaptation and temporal gains."""
import argparse, hashlib, json, random, struct, subprocess
from pathlib import Path
from differential import ROOT, BINARY, HEAP, f32
from awb_reference import OriginalAwb, RUNTIME
SYMBOLS={'normalize':'_Z13AwbGainNormalPf','mixture':'_Z14AwbGainMixturePfS_fS_', 'factor':'_Z16AwbCalDampFactorfffffPf','damp':'_Z14AwbCalDampGainP12awb_contex_s', 'ratios':'_Z22AwbGainCalbyRgainBgainxxxPf', 'statistics':'_Z36AwbCalGainForDiffIllumAndDiffXYType229rk_aiq_awb_stat_wp_res_v201_sPfPx'}
def floats(data):return ':'.join(f'{x:08x}' for x in struct.unpack('<'+'I'*(len(data)//4),data))
def run(arm,v):
 first=struct.pack('<4f',*v['first']);second=struct.pack('<4f',*v['second']);arm.uc.mem_write(HEAP,first);arm.uc.mem_write(HEAP+0x100,second);arm.uc.mem_write(HEAP+0x200,bytes([0xa7])*16)
 kind=v['kind']
 if kind in ('ratios','statistics'):
  words=lambda n:struct.unpack('<II',struct.pack('<q',n))
  if kind=='ratios':
   arm.invoke(SYMBOLS[kind],[*words(v['red']),*words(v['blue'])],stack=struct.pack('<qI',v['count'],HEAP));count=v['count']&0xffffffffffffffff
  else:
   arm.invoke(SYMBOLS[kind],[*words(v['count']),*words(v['red'])],stack=struct.pack('<qII',v['blue'],HEAP,HEAP+0x100));count=struct.unpack('<Q',arm.uc.mem_read(HEAP+0x100,8))[0]
  return floats(bytes(arm.uc.mem_read(HEAP,16)))+f':{count:016x}'
 if kind=='normalize':
  arm.invoke(SYMBOLS[kind],[HEAP]);return floats(bytes(arm.uc.mem_read(HEAP,16)))
 if kind=='mixture':
  arm.invoke(SYMBOLS[kind],[HEAP,HEAP+0x100,HEAP+0x200],floats=[v['weight']]);assert bytes(arm.uc.mem_read(HEAP,16))==first and bytes(arm.uc.mem_read(HEAP+0x100,16))==second
  return floats(bytes(arm.uc.mem_read(HEAP+0x200,16)))
 if kind=='factor':
  arm.uc.mem_write(HEAP,struct.pack('<f',v['coefficient']));arm.invoke(SYMBOLS[kind],[HEAP],floats=[v['threshold'],v['step'],v['minimum'],v['maximum'],v['variance']]);return floats(bytes(arm.uc.mem_read(HEAP,4)))
 # Seed unrelated context bytes and verify only the two coefficients/current gain change.
 state=v['seed'];context=bytearray()
 for _ in range(0x4000):state=(state*1664525+1013904223)&0xffffffff;context.append(state>>24)
 struct.pack_into('<f',context,0x3484,v['coefficient']);context[0x352c:0x353c]=first;context[0x353c:0x354c]=second
 arm.uc.mem_write(HEAP,bytes(context));arm.invoke(SYMBOLS[kind],[HEAP]);after=bytearray(arm.uc.mem_read(HEAP,len(context)));output=bytes(after[0x3484:0x348c]+after[0x353c:0x354c]);after[0x3484:0x348c]=context[0x3484:0x348c];after[0x353c:0x354c]=context[0x353c:0x354c];assert after==context
 return floats(output)
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000,help='cases per native function');p.add_argument('--emit-dir',type=Path);a=p.parse_args();arm=OriginalAwb();rng=random.Random(0x41574247);inputs=[];expected=[];coverage={}
 sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());assert sha==next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name)
 runtime_sha=hashlib.sha256(RUNTIME.read_bytes()).hexdigest();assert runtime_sha==manifest['gccRuntime']['memberSha256']
 for kind in SYMBOLS:
  for i in range(a.cases):
   v=dict(kind=kind,seed=rng.randrange(0xffffffff),first=[f32(rng.uniform(.01,16)) for _ in range(4)],second=[f32(rng.uniform(.01,16)) for _ in range(4)],weight=f32(rng.uniform(-.25,1.25)),threshold=f32(rng.uniform(0,1)),step=f32(rng.uniform(0,.1)),minimum=f32(rng.uniform(0,.3)),maximum=f32(rng.uniform(.7,1)),coefficient=f32(rng.uniform(0,1)),variance=f32(rng.uniform(0,1)))
   if kind=='normalize':
    if i%8==0:v['first']=[0.,0.,0.,0.]
    elif i%8==1:v['first']=[6.,7.,8.,9.]
    elif i%8==2:v['first'][i%4]=[0.,-1.,f32(.00001),f32(.000010001)][i//8%4]
    elif i%8==3:v['first']=[1.,1.,1.,1.]
   elif kind=='mixture':
    if i%7<3:v['weight']=[0.,.5,1.][i%7]
    elif i%7==3:v['first']=v['second'][:]
   elif kind=='factor':
    if i%7==0:v['variance']=v['threshold']
    elif i%7==1:v['coefficient']=v['minimum']
    elif i%7==2:v['coefficient']=v['maximum']
    elif i%7==3:v['step']=0.
    elif i%7==4:v['minimum'],v['maximum']=v['maximum'],v['minimum']
   elif kind=='damp':
    mode=i%8
    if mode==0:v['first'][0]=0.
    elif mode==1:v['first'][0]=f32(.00001)
    elif mode==2:v['first'][0]=f32(.000010001)
    elif mode==3:v['second']=v['first'][:]
    elif mode in (4,5,6):
     # Directed curve knots, just below/above the double comparison at 0.3.
     delta=[0.,.005,.01,.03,.05,.075,.1,.125,.15,.225,.29999998,.3,.30000004][i//8%13]
     v['first']=[1.,0.,1.,1.];v['second']=[1.,f32(delta),1.,1.]
    if i%11==0:v['coefficient']=0.
    elif i%11==1:v['coefficient']=1.
   elif kind in ('ratios','statistics'):
    boundary=[0,1,-1,511,512,513,1023,1024,1025,(1<<24)-1,(1<<24)+1,(1<<32)-512,(1<<32)-1,(1<<32),(1<<53)+1,(1<<62)+1,(1<<63)-1,-(1<<63)]
    v['count']=boundary[i%len(boundary)] if i%3 else rng.randrange(-(1<<63),1<<63)
    if i<len(boundary):v['count']=boundary[i]
    elif i%23==0:v['count']=0
    v['red']=boundary[i//len(boundary)%len(boundary)] if i%3==1 else rng.randrange(-(1<<63),1<<63)
    v['blue']=boundary[i//3%len(boundary)] if i%3==2 else rng.randrange(-(1<<63),1<<63)
   inputs.append('awb-gain '+json.dumps(v,separators=(',',':')));expected.append(run(arm,v));key=f'{kind}:{i%8}';coverage[key]=coverage.get(key,0)+1
 assert not arm.calls,arm.calls
 assert not arm.runtime.calls,arm.runtime.calls
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[dict(case=i,input=inputs[i],expected=x,actual=y) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
 report=dict(binarySha256=sha,runtimeSha256=runtime_sha,nativeRuntimeFunctions=['__aeabi_l2f'],nativeRuntimeCalls=arm.runtime_calls,nativeRuntimeImportedCalls=arm.runtime.calls,seed='0x41574247',cases=len(inputs),casesPerFunction=a.cases,mismatchCount=len(mismatches),importedCalls=arm.calls,elfEntries={'normalize':'0xca030','mixture':'0xca080','factor':'0xc9f2c','damp':'0xca0e0','ratios':'0xca7cc','statistics':'0xc99d8'},coverage=coverage,scope='Exact f32 gain/coefficient bits for six original AWB routines, signed weighted-count rounding and temporal context preservation',limitations=['Checked finite inputs and outputs; arbitrary NaN/infinity or native pointer aliasing outside the Rust value API.','This is the original gain/temporal stage, not illumination classification, probability weighting, calibration loading, convergence policy or a complete AWB controller.','No live sensor/ISP frame application or independent camera startup has been verified.'])
 if mismatches:report['firstMismatches']=mismatches[:3]
 (ROOT/'reverse-engineering/rkaiq/awb-gain-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('coverage','firstMismatches')},indent=2))
 if mismatches:print(json.dumps(mismatches[:1]));raise SystemExit(1)
 if a.emit_dir:
  a.emit_dir.mkdir(parents=True,exist_ok=True);(a.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(a.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
