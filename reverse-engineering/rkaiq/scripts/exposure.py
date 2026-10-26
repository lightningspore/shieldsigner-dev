#!/usr/bin/env python3
"""Compare gain/time codes using original RKAIQ AND original uClibc math code."""
import argparse,hashlib,json,random,struct,subprocess
from pathlib import Path
from differential import OriginalArm,ROOT,BINARY,HEAP,regs,f32,u32
RUNTIME=ROOT/'.tools/reverse-engineering/uclibc-runtime/libuClibc-1.0.31.so'
class OriginalExposure(OriginalArm):
 def __init__(self):
  super().__init__(BINARY);self.math=OriginalArm(RUNTIME,tls=True);self.math_calls=set()
  self.stubs[self.symbols['xcam_print_log']&~1]='xcam_print_log'
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name in ('powf','log10f'):
   count=2 if name=='powf' else 1
   values=[struct.unpack('<f',struct.pack('<I',uc.reg_read(getattr(regs,f'UC_ARM_REG_S{i}'))))[0] for i in range(count)]
   self.math.invoke(name,floats=values);self.math_calls.add(name)
   uc.reg_write(regs.UC_ARM_REG_S0,self.math.uc.reg_read(regs.UC_ARM_REG_S0));uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if name=='xcam_print_log':uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v):
  context=HEAP;table=HEAP+0x10000;time_out=HEAP+0x20000;gain_out=HEAP+0x21000
  self.uc.mem_write(context,bytes(0x400));self.uc.mem_write(context+0x10,struct.pack('<III',v['model'],table,7*len(v['bands'])))
  if v['bands']:self.uc.mem_write(table,b''.join(struct.pack('<7f',*b) for b in v['bands']))
  self.uc.mem_write(context+0x1c,struct.pack('<4f',*v['factors']))
  for key,minimum,step,offset in [('linear',0x50,0x5c,0x60),('hdr2',0x6a,0x7c,0x80),('hdr3',0x8a,0x9c,0xa0)]:
   t=v[key];self.uc.mem_write(context+minimum,struct.pack('<H',t['minimum']));self.uc.mem_write(context+step,struct.pack('<ff',t['step'],t['offset']))
  self.uc.mem_write(context+0xc4,struct.pack('<f',v['linear_ratio']));self.uc.mem_write(context+0xe8,struct.pack('<f',v['hdr_ratio']))
  self.uc.mem_write(context+0x3b0,struct.pack('<3f',v['frame_length'],v['pixel_clock'],v['line_length']))
  self.uc.mem_write(context+0x3d1,bytes([2 if v['mode']==1 else 3,0 if v['mode']==0 else 1]))
  self.uc.mem_write(time_out,bytes(4));self.uc.mem_write(gain_out,bytes(4))
  assert self.invoke('AeReal2RegConv',[context,time_out,gain_out,v['dcg']],[v['time'],v['gain']])==0
  return str(u32(self.uc.mem_read(time_out,4)))+':'+str(u32(self.uc.mem_read(gain_out,4)))
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000);p.add_argument('--emit-dir',type=Path);args=p.parse_args()
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==sha
 runtime_sha=hashlib.sha256(RUNTIME.read_bytes()).hexdigest();assert runtime_sha==manifest['uclibcRuntime']['memberSha256']
 arm=OriginalExposure();rng=random.Random(0x45585052);inputs=[];expected=[];coverage={}
 def timing():return dict(minimum=rng.randrange(0,33),step=f32(rng.choice([1.,2.,4.,.5])),offset=f32(rng.choice([0.,1.,2.,.5])))
 for i in range(args.cases):
  bands=[[1.,4.,16.,0.,1.,16.,255.],[4.,16.,32.,8.,rng.choice([.5,1.,2.]),0.,4095.]]
  if i%7==0:bands=[]
  elif i%11==0:bands[0][2]=0.
  v=dict(time=f32(rng.uniform(0,.1)),gain=f32(rng.choice([1.,4.,16.,.5,20.,rng.uniform(.25,32)])),mode=i%3,dcg=[-1,0,1,2][i//3%4],model=i//12%2,bands=bands,factors=[f32(rng.choice([0.,.01,-.01])),f32(rng.uniform(-4,4)),f32(rng.choice([1.,2.,.5])),f32(rng.uniform(-2,2))],frame_length=f32(rng.choice([1600.,2000.,3000.])),pixel_clock=f32(rng.choice([24.,72.,100.])),line_length=f32(rng.choice([1600.,2400.,3000.])),linear=timing(),hdr2=timing(),hdr3=timing(),linear_ratio=f32(rng.choice([1.,2.,4.])),hdr_ratio=f32(rng.choice([1.,2.,4.])))
  if i in (0,1,2):
   v['gain']=4. if i<2 else 1.;v['dcg']=0;v['model']=0;v['bands']=[[1.,4.,8. if i==0 else (0. if i==1 else 1.),100. if i==2 else 0.,1.,16.,255.],[4.,16.,32.,0.,1.,16.,4095.]]
  inputs.append('exposure '+json.dumps(v,separators=(',',':')));expected.append(arm.run(v));key=f'{v["mode"]}:{v["dcg"]}:{v["model"]}';coverage[key]=coverage.get(key,0)+1
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatch=[{'case':i,'input':inputs[i],'expected':a,'actual':b} for i,(a,b) in enumerate(zip(expected,actual)) if a!=b]
 report=dict(binarySha256=sha,runtimeSha256=runtime_sha,seed='0x45585052',cases=len(inputs),branchCoverage=coverage,mismatchCount=len(mismatch),nativeRuntimeFunctions=sorted(arm.math_calls),nativeRuntimeImportedCalls=sorted(set(arm.math.calls)),scope='AeReal2RegConv gain and integration-time codes; original uClibc powf/log10f execute as ARM instructions',limitations=['Finite valid calibration inputs; arbitrary invalid-pointer and unsupported-model behavior are outside the checked Rust API.','Corpus equivalence of resulting register codes does not prove all transcendental outputs match for every float.','Calibration loading, exposure decisions, frame scheduling and live sensor programming remain separate work.'])
 if mismatch:report['firstMismatches']=mismatch[:5]
 (ROOT/'reverse-engineering/rkaiq/exposure-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not mismatch
 if args.emit_dir:
  args.emit_dir.mkdir(parents=True,exist_ok=True)
  (args.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(args.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
