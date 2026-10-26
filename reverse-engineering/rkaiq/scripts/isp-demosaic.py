#!/usr/bin/env python3
"""Native demosaic quantization (including uClibc log) and ISP32 serialization."""
import argparse,hashlib,json,random,struct,subprocess
from pathlib import Path
from differential import OriginalArm,ROOT,BINARY,HEAP,regs,f32
from exposure import RUNTIME
OFFSET=0x1282;SIZE=57;PARAMETERS=11145
class OriginalDemosaic(OriginalArm):
 def __init__(self):
  super().__init__(BINARY);self.math=OriginalArm(RUNTIME,tls=True);self.math_calls=set()
 def hook(self,uc,address,size,user):
  if self.stubs.get(address)=='log':
   value=struct.unpack('<d',struct.pack('<Q',uc.reg_read(regs.UC_ARM_REG_D0)))[0];self.math.invoke('log',doubles=[value]);self.math_calls.add('log')
   uc.reg_write(regs.UC_ARM_REG_D0,self.math.uc.reg_read(regs.UC_ARM_REG_D0));uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v):
  context=HEAP;params=HEAP+0x20000;hardware=HEAP+0x30000;result=HEAP+0x40000
  self.uc.mem_write(context,bytes([0x77])*0x600);previous=bytes.fromhex(v['hardware']);self.uc.mem_write(hardware,previous)
  cached=previous
  if v['kind']=='quantize':
   self.uc.mem_write(context+12,previous);self.uc.mem_write(context+0x444,bytes.fromhex(v['selected']));self.uc.mem_write(result,struct.pack('<I',hardware));before=bytes(self.uc.mem_read(context,0x600))
   assert self.invoke('_Z21AdebayerGetProcResultP17AdebayerContext_sP22AdebayerProcResultV2_s',[context,result])==0
   after=bytearray(self.uc.mem_read(context,0x600));cached=bytes(after[12:124]);after[12:124]=before[12:124];assert bytes(after)==before
   produced=bytes(self.uc.mem_read(hardware,112));assert cached==bytes([0])+produced[1:]
  before=bytes(self.uc.mem_read(context,0x600));original=bytearray();state=v['seed']
  for _ in range(PARAMETERS):state=(state*1664525+1013904223)&0xffffffff;original.append(state>>24)
  self.uc.mem_write(params,bytes(original));hw_before=bytes(self.uc.mem_read(hardware,112))
  self.invoke('_ZN5RkCam11Isp32Params31convertAiqAdebayerToIsp32ParamsER20isp32_isp_params_cfgR20AdebayerHwConfigV2_s',[context,params,hardware])
  out=bytes(self.uc.mem_read(params,PARAMETERS));assert out[24:OFFSET]==original[24:OFFSET] and out[OFFSET+SIZE:]==original[OFFSET+SIZE:]
  assert bytes(self.uc.mem_read(hardware,112))==hw_before and bytes(self.uc.mem_read(context,0x600))==before
  return out[:24].hex()+':'+out[OFFSET:OFFSET+SIZE].hex()+':'+hw_before.hex()+':'+cached.hex()
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000,help='Cases per stage; total is twice this count');p.add_argument('--emit-dir',type=Path);a=p.parse_args()
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();runtime_sha=hashlib.sha256(RUNTIME.read_bytes()).hexdigest();assert sha==next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name);assert runtime_sha==manifest['uclibcRuntime']['memberSha256']
 arm=OriginalDemosaic();rng=random.Random(0x444d5343);inputs=[];expected=[];coverage={}
 for kind in ['quantize','pack']:
  for i in range(a.cases):
   hardware=bytearray(rng.randbytes(112));hardware[0]=i%2;hardware[1]=i//2%2
   v=dict(kind=kind,seed=rng.randrange(0xffffffff),hardware=hardware.hex())
   if kind=='quantize':
    selected=bytearray(rng.randbytes(132));selected[0]=i//2%2
    for o,value in [(92,rng.uniform(.01,10)),(96,rng.uniform(-32,32)),(100,rng.uniform(-4,4)),(104,rng.uniform(.01,16)),(108,rng.uniform(.0001,100)),(120,rng.uniform(-1e4,1e4)),(128,rng.uniform(-1e4,1e4))]:struct.pack_into('<f',selected,o,f32(value))
    if i<64:
     # Exercise exact powers of two and nearby normalization slopes.
     slope=[1,2,3,4,7,8,15,16,31,32,127,128,1023,1024,32768,65535][i%16]
     struct.pack_into('<f',selected,92,f32(78715.2890625/(1024*4096)))
     struct.pack_into('<f',selected,104,slope/128)
    elif i<96:
     # Positive normalization products after the native 32-bit multiply wraps.
     struct.pack_into('<f',selected,92,f32(78715.2890625/((1<<20)*4096)))
     struct.pack_into('<f',selected,104,(4097+i-64)/128)
    elif i<128:
     # Signed ties and saturating float-to-i32 conversion before u32 storage.
     values=[-.00048828125,.00048828125,1e20,-1e20,0.]
     struct.pack_into('<f',selected,120,f32(values[i%5]));struct.pack_into('<f',selected,128,f32(values[(i+1)%5]))
    v['selected']=selected.hex()
   inputs.append('isp-demosaic '+json.dumps(v,separators=(',',':')));expected.append(arm.run(v));key=f'{kind}:{hardware[0]}:{hardware[1]}';coverage[key]=coverage.get(key,0)+1
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[dict(case=i,input=inputs[i],expected=x,actual=y) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
 report=dict(binarySha256=sha,runtimeSha256=runtime_sha,seed='0x444d5343',cases=len(inputs),casesPerStage=a.cases,mismatchCount=len(mismatches),coverage=coverage,nativeRuntimeFunctions=sorted(arm.math_calls),nativeRuntimeImportedCalls=sorted(set(arm.math.calls)),scope='Demosaic selected-value quantization: all 112 hardware/cache bytes; ISP32 conversion: three masks and full 57-byte block, with unrelated context/parameter preservation',limitations=['Selected calibration values are supplied; automatic ISO selection/loading and frame-state integration remain unfinished.','Positive finite inverse-filter inputs and positive wrapped normalization product; checked Rust rejects invalid domains before mutation.','Standard memcpy is explicit in the harness; logarithm executes pinned uClibc ARM instructions.','Resulting integer-register equivalence does not prove logarithm f64 equivalence at every possible input.','No live parameter submission or independent ISP startup is supplied by these functions.'])
 if mismatches:report['firstMismatches']=mismatches[:5]
 (ROOT/'reverse-engineering/rkaiq/isp-demosaic-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not mismatches
 if a.emit_dir:
  a.emit_dir.mkdir(parents=True,exist_ok=True);(a.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(a.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
