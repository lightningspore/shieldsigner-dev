#!/usr/bin/env python3
"""Compare full ISP32 black-level conversion/cache writes against native ARM."""
import argparse,hashlib,json,random,struct,subprocess
from pathlib import Path
from differential import OriginalArm,ROOT,BINARY,HEAP,f32
OFFSET=0x7ae;SIZE=44;PARAMETERS=11145
class OriginalBlackLevel(OriginalArm):
 def run(self,v,virtual_offset):
  context=HEAP+0x10000;params=HEAP+0x20000;source=HEAP+0x30000;vtable=HEAP+0x5000+12
  self.uc.mem_write(context,bytes([0x77])*0x2000);self.uc.mem_write(vtable-12,struct.pack('<i',virtual_offset));self.uc.mem_write(context,struct.pack('<I',vtable))
  data=bytearray(32);data[0]=v['enabled'];struct.pack_into('<4h',data,2,*v['fixed']);data[10]=v['stage1_enabled'];struct.pack_into('<4h',data,12,*v['stage1']);data[20]=v['ob_enabled'];struct.pack_into('<hfi',data,22,v['offset'],v['gain'],v['maximum'])
  self.uc.mem_write(source,bytes(data));state=v['seed'];original=bytearray()
  for _ in range(PARAMETERS):state=(state*1664525+1013904223)&0xffffffff;original.append(state>>24)
  self.uc.mem_write(params,bytes(original));before=bytes(self.uc.mem_read(context,0x2000))
  self.invoke('_ZN5RkCam11Isp32Params26convertAiqBlcToIsp32ParamsER20isp32_isp_params_cfgR14AblcProc_V32_s',[context,params,source])
  out=bytes(self.uc.mem_read(params,PARAMETERS));cache_offset=virtual_offset+0x7fb;after=bytearray(self.uc.mem_read(context,0x2000));cache=bytes(after[cache_offset:cache_offset+SIZE]);after[cache_offset:cache_offset+SIZE]=before[cache_offset:cache_offset+SIZE]
  assert bytes(after)==before and bytes(self.uc.mem_read(source,32))==bytes(data)
  assert out[24:OFFSET]==original[24:OFFSET] and out[OFFSET+SIZE:]==original[OFFSET+SIZE:]
  assert cache==out[OFFSET:OFFSET+SIZE]
  return out[:24].hex()+':'+out[OFFSET:OFFSET+SIZE].hex()+':'+cache.hex()
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000);p.add_argument('--emit-dir',type=Path);a=p.parse_args()
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert sha==next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name)
 arm=OriginalBlackLevel(BINARY);rng=random.Random(0x424c5332);inputs=[];expected=[];coverage={}
 gains=[0.,-0.,.5,1.,2.,255.,256.,-1.,1e20,1e-30,
  struct.unpack("<f",struct.pack("<I",0x7f7fffff))[0],
  -struct.unpack("<f",struct.pack("<I",0x7f7fffff))[0],
  struct.unpack("<f",struct.pack("<I",1))[0],
  struct.unpack("<f",struct.pack("<I",0x437fffff))[0],
  struct.unpack("<f",struct.pack("<I",0x43800001))[0],.00390625]
 for i in range(a.cases):
  gain=f32(gains[i%len(gains)] if i%3 else rng.uniform(-10,300))
  values=[-32768,-1,0,1,32767]
  fixed=[rng.choice(values) if i%2 else rng.randrange(-32768,32768) for _ in range(4)];stage1=[rng.choice(values) if i%2 else rng.randrange(-32768,32768) for _ in range(4)]
  v=dict(seed=rng.randrange(0xffffffff),enabled=bool(i%2),stage1_enabled=bool(i//2%2),ob_enabled=bool(i//4%2),fixed=fixed,stage1=stage1,offset=rng.choice([-32768,-1,0,1,510,511,512,32767]),gain=gain,maximum=rng.choice([-2147483648,-1,0,1,0xffffe,0xfffff,0x100000,2147483647]))
  key=f'{int(v["enabled"])}:{int(v["stage1_enabled"])}:{int(v["ob_enabled"])}:{"zero" if gain==0 else "negative" if gain<0 else "positive"}';coverage[key]=coverage.get(key,0)+1
  inputs.append('isp-black-level '+json.dumps(v,separators=(',',':')));expected.append(arm.run(v,0x40 if i//8%2 else 0))
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[dict(case=i,input=inputs[i],expected=x,actual=y) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
 report=dict(binarySha256=sha,seed='0x424c5332',cases=a.cases,mismatchCount=len(mismatches),coverage=coverage,scope='ISP32 black-level converter: all three u64 masks, entire 44-byte BLS block/cache, unrelated parameter/context/input preservation',limitations=['Finite predgain inputs; checked Rust rejects NaN/infinity before mutation.','Calibration interpolation/selection and parameter queue submission are separate unfinished stages.','Native optical-black enable input is unused; disabled main input preserves an existing module enable bit.'])
 if mismatches:report['firstMismatches']=mismatches[:5]
 (ROOT/'reverse-engineering/rkaiq/isp-black-level-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not mismatches
 if a.emit_dir:
  a.emit_dir.mkdir(parents=True,exist_ok=True);(a.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(a.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
