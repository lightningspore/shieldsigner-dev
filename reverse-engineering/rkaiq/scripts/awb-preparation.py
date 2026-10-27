#!/usr/bin/env python3
"""Execute the complete original AWB measurement preparation with persistent caches."""
import argparse,hashlib,json,random,struct,subprocess
from pathlib import Path
from awb_reference import OriginalAwb,RUNTIME
from differential import ROOT,BINARY,HEAP,f32
FRAME=0x1e00;LIGHT=0xac;REGION=0x34

def data(seed,size):
 out=bytearray()
 for _ in range(size):seed=(seed*1664525+1013904223)&0xffffffff;out.append(seed>>24)
 return out
def words(seed,n):return list(struct.unpack('<'+'I'*n,data(seed,n*4)))
def gain(seed):return [.5+(x>>16)/65536 for x in words(seed,4)]
def name(text):
 out=bytearray([0x4b])*64;b=text.encode();out[:len(b)]=b;out[len(b)]=0;return out
def frame(v,step):
 b=data(v['seed']^0xabcdef00^step,FRAME);at=0x1d70;struct.pack_into('<I',b,at,(v['mode']+step)%3);b[at+4]=len(v['indices']);struct.pack_into('<i',b,at+8,-1 if v['fast'] and v['fast_minus'] else (v['group']+step)%v['groups'])
 for i,index in enumerate(v['indices']):
  if v['rotate'] and index<v['n']:index=(index+step*len(v['indices']))%v['n']
  struct.pack_into('<I',b,at+12+i*4,index)
 text='FASTAWBACT' if v['fast'] else ('cfg-B' if v['rename'] and step>0 else 'cfg-A');b[at+28:at+92]=name(text);pg=gain(v['seed']^0xa0);pg[0]+=step*.125;pg[3]+=step*.0625;struct.pack_into('<4f',b,at+92,*pg)
 for i in range(225):
  if v['zero_grid'] and i%3==0:struct.pack_into('<I',b,0xd0+i*32,0)
 for local in range(len(v['indices'])):
  for region in range(2):
   o=local*48+region*24
   if v['zero_lights'] and local%2==0:struct.pack_into('<q',b,o,0)
   elif v['direct_counts']:struct.pack_into('<q',b,o,[0,511,512,513,4294966784,(1<<63)-1][(local+region+step)%6])
 for i in range(4):
  if v['zero_exclusions']:struct.pack_into('<q',b,0x1cf0+i*24,0)
 rgb=[(100,200,100),(0,123,100),(-1,123,100),(1,(1<<63)-1,2)][v['sum_mode']];struct.pack_into('<3q',b,0x1de8,*rgb);return b

def run(arm,v):
 seed=v['seed'];n=v['n'];groups=v['groups'];ctx=bytearray([0xa7])*0x4000;strategy=bytearray([0x5b])*0x1000;calibration=bytearray([0x6c])*0x800;curves=bytearray([0x7d])*0x400
 for offset,pointer in [(0x80,0x9000),(0x8c,0x8000),(0x134,0x10000),(0x138,0x20000),(0x240,0x22000),(0x244,0x21000),(0x2dec,0x40000+0x1d70)]:struct.pack_into('<I',ctx,offset,HEAP+pointer)
 ctx[0x84]=0;ctx[0x334a]=v['update'];ctx[0x3348]=seed&255;ctx[0x13c]=seed&1;ctx[0xf79]=bool(seed&2);ctx[0x1a08]=bool(seed&4);ctx[0x2ba0]=bool(seed&8);struct.pack_into('<f',ctx,0x33dc,v['sample']);struct.pack_into('<4f',ctx,0x3588,*gain(seed^0x99))
 for i in range(4):
  g=[[2.,1.,1.,2.],[1.]*4,([1.]*4 if i==groups-1 else [2.,1.,1.,2.]),[0.]*4][v['history']];struct.pack_into('<4f',ctx,0x334c+i*16,*g)
  text='cfg-A' if v['names']==0 else (('cfg-B' if i==groups-1 else 'cfg-A') if v['names']==1 else '');ctx[0x13d+i*64:0x13d+(i+1)*64]=name(text)
 records=data(seed^0x11,n*LIGHT)
 for i in range(n):
  for region in range(2):struct.pack_into('<4f',records,i*LIGHT+region*REGION+4,*gain(seed^0x1000^(i*4+region)))
  struct.pack_into('<4f',records,i*LIGHT+0x9c,*gain(seed^0x2000^i))
 seen=bytearray([1 if v['seen'] else i%2 for i in range(n)]);second=data(seed^0x22,n*4);totals=data(seed^0x33,max(n,2)*4)
 initial_grid=[.5+(x>>16)/65536 for x in words(seed^0x44,225*3)];struct.pack_into('<675f',ctx,0xf7c,*initial_grid);ctx[0x2ba4:0x2d10]=data(seed^0x55,7*REGION);ctx[0x2d10:0x2d44]=data(seed^0x66,REGION);ctx[0x2d64:0x2de4]=data(seed^0x77,128);ctx[0x2d44:0x2d64]=data(seed^0x88,32)
 struct.pack_into('<I',strategy,4,v['fast_count']);strategy[0x138]=n;strategy[0x139]=n;struct.pack_into('<I',strategy,0x398,groups);struct.pack_into('<f',strategy,0x4b0,v['threshold']);struct.pack_into('<4i',strategy,0x480,*v['exclusion_kind'])
 for i in range(4):
  struct.pack_into('<III',calibration,0x150+i*0x28,HEAP+0x30000+i*0x100,3,HEAP+0x30000+i*0x100+0x40);struct.pack_into('<3f',curves,i*0x100,0.,1.,3.);struct.pack_into('<3f',curves,i*0x100+0x40,*v['weights'][i])
 for offset,b in [(0,ctx),(0x8000,strategy),(0x9000,calibration),(0x10000,records),(0x20000,seen),(0x21000,second),(0x22000,totals),(0x30000,curves)]:arm.uc.mem_write(HEAP+offset,bytes(b))
 out=[]
 allowed=[(0x3348,1),(0x334a,1),(0x334c,64),(0x13d,256),(0x13c,1),(0xf79,1),(0x1a08,1),(0xf7c,2700),(0x2ba0,1),(0x2ba4,364),(0x2d10,52),(0x3588,16),(0x2d44,32),(0x2d64,128)]
 for step in range(v['frames']):
  source=frame(v,step);arm.uc.mem_write(HEAP+0x40000,bytes(source));arm.uc.mem_write(HEAP+0x334a,bytes([v['update']]));before=bytes(arm.uc.mem_read(HEAP,0x4000));strategy_before=bytes(arm.uc.mem_read(HEAP+0x8000,0x1000))
  arm.invoke('_Z20PrepareMeasureResultPK25rk_aiq_awb_stat_res_v32_sP12awb_contex_s',[HEAP+0x40000,HEAP],instructions=2000000)
  after=bytes(arm.uc.mem_read(HEAP,0x4000));check=bytearray(after)
  for offset,size in allowed:check[offset:offset+size]=before[offset:offset+size]
  assert bytes(check)==before,'Unexpected context write'
  st=bytearray(arm.uc.mem_read(HEAP+0x8000,0x1000));active=st[0x138];st[0x138]=strategy_before[0x138];assert bytes(st)==strategy_before
  assert bytes(arm.uc.mem_read(HEAP+0x40000,FRAME))==source and bytes(arm.uc.mem_read(HEAP+0x9000,len(calibration)))==calibration and bytes(arm.uc.mem_read(HEAP+0x30000,len(curves)))==curves and arm.allocation is None
  dump=bytearray([after[0x334a],after[0x3348],active,after[0x13c],after[0xf79],after[0x1a08],after[0x2ba0]])+after[0x334c:0x338c]+after[0x13d:0x23d]
  for pointer,size in [(0x20000,n),(0x10000,n*LIGHT),(0x21000,n*4),(0x22000,max(n,2)*4)]:dump.extend(arm.uc.mem_read(HEAP+pointer,size))
  dump.extend(after[0x3588:0x3598]);dump.extend(after[0xf7c:0x1a08]);dump.extend(after[0x2ba4:0x2d10]);dump.extend(after[0x2d10:0x2d44]);dump.extend(after[0x2d64:0x2de4]);dump.extend(after[0x2d44:0x2d64]);out.append(dump.hex())
 return '|'.join(out)
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=500);p.add_argument('--emit-dir',type=Path);a=p.parse_args();arm=OriginalAwb(stdlib=True);rng=random.Random(0x41575050);inputs=[];expected=[];coverage={}
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();runtime_sha=hashlib.sha256(RUNTIME.read_bytes()).hexdigest();assert sha==next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name) and runtime_sha==manifest['gccRuntime']['memberSha256']
 for i in range(a.cases):
  n=255 if i%127==0 else rng.randrange(1,9);groups=i%4+1;indices=list(range(min(n,4)))
  if i%13==0:indices[-1]=n+1
  elif i%13==1:indices=[0]*len(indices)
  elif i%13==2:indices=[]
  v=dict(seed=rng.randrange(0xffffffff),n=n,groups=groups,group=i//4%groups,frames=[1,2,4][i//16%3],indices=indices,fast=bool(i//4%2),fast_count=min(n,4)+(256 if i//8%2 else 0),threshold=f32([0.,.01,10.][i//32%3]),sum_mode=i//2%4,history=i//8%4,names=i//7%3,seen=bool(i//3%2),update=bool(i%2),mode=i//3%3,rotate=bool(i//5%2),rename=bool(i//17%2),zero_grid=bool(i//11%2),zero_lights=bool(i//19%2),direct_counts=bool(i//23%2),zero_exclusions=bool(i//29%2),sample=f32(rng.uniform(0,4)),exclusion_kind=[rng.randrange(4) for _ in range(4)],weights=[[f32(rng.uniform(0,1)) for _ in range(3)] for _ in range(4)])
  if i%9==0:v['exclusion_kind']=[3]*4
  elif i%9==1:v['exclusion_kind']=[0]*4
  v['fast_minus']=bool(i//31%2)
  if i%15==0:v['weights']=[[0.]*3 for _ in range(4)]
  inputs.append('awb-preparation '+json.dumps(v,separators=(',',':')));expected.append(run(arm,v));key=f'{groups}:{v["fast"]}:{v["update"]}:{v["history"]}:{v["sum_mode"]}:{v["frames"]}';coverage[key]=coverage.get(key,0)+1
  if i%50==0:print('native sequences',i+1,flush=True)
 assert not arm.runtime.calls,arm.runtime.calls
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[dict(case=i,input=inputs[i],expected=x,actual=y) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
 report=dict(binarySha256=sha,runtimeSha256=runtime_sha,cases=len(inputs),frames=sum(json.loads(x.split(' ',1)[1])['frames'] for x in inputs),seed='0x41575050',mismatchCount=len(mismatches),elfEntries={'preparation':'0xc3180','stability':'0xc2f90'},nativeRuntimeFunctions=sorted(arm.runtime_functions),nativeRuntimeImportedCalls=arm.runtime.calls,modeledStandardCalls=arm.standard_calls,standardMemoryCalls=sorted(set(arm.calls)),coverage=coverage,scope='Entire original PrepareMeasureResult with its original stability/gain/interpolation helpers across persistent one/two/four-frame caches: all represented state bytes and unrelated context/calibration/input preservation',limitations=['Caller-provided update flag is reset explicitly before each frame; outer AwbPreProcV32 policy is not part of this suite.','Successful bounded malloc/free, strcmp/strcpy and standard memory operations are modeled boundaries; SDK GCC conversions execute original ARM instructions. Vendor logging/debug formatting is outside the value API.','Checked SDK full-V32 frame, 1-255 total lights and 1-4 groups; FASTAWBACT group -1 and handled out-of-range light mappings are included.','Calibration loading, full upstream translator, outer AWB strategy and live application remain unfinished.'])
 report['fastMinusOneSequences']=sum(json.loads(x.split(' ',1)[1])['fast'] and json.loads(x.split(' ',1)[1])['fast_minus'] for x in inputs)
 if mismatches:
  first=mismatches[0];x=first['expected'];y=first['actual'];first['firstDifferingCharacter']=next((i for i,(a,b) in enumerate(zip(x,y)) if a!=b),min(len(x),len(y)));report['firstMismatches']=[{k:v for k,v in first.items() if k not in ('expected','actual')}]
 (ROOT/'reverse-engineering/rkaiq/awb-preparation-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='coverage'},indent=2));assert not mismatches
 if a.emit_dir:
  a.emit_dir.mkdir(parents=True,exist_ok=True);(a.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(a.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
