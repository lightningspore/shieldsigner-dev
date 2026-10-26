#!/usr/bin/env python3
"""Execute native dynamic damping, including its context diagnostic writes."""
import argparse,hashlib,json,random,struct,subprocess
from differential import OriginalArm,ROOT,BINARY,HEAP,regs,f32,fhex
class OriginalDamping(OriginalArm):
 def __init__(self):
  super().__init__(BINARY)
  self.symbols['damping']=0xb4025
  self.stubs[self.symbols['xcam_print_log']&~1]='xcam_print_log'
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name=='xcam_print_log':uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if name=='__aeabi_idivmod':
   a=uc.reg_read(regs.UC_ARM_REG_R0);b=uc.reg_read(regs.UC_ARM_REG_R1);assert a<0x80000000 and b==10
   uc.reg_write(regs.UC_ARM_REG_R0,a//b);uc.reg_write(regs.UC_ARM_REG_R1,a%b)
   uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v,hdr,channel):
  data=bytearray(0x6000)
  struct.pack_into('<I',data,0x2300,v['frame']);data[0x23cd]=hdr;data[0x4fb8]=v['enabled']
  struct.pack_into('<Iff',data,0x23f8,2 if v['custom'] else 0,v['custom_scale'],v['middle'])
  for i,value in enumerate(v['history']):struct.pack_into('<f',data,0x2c6c+channel*4+i*64 if hdr else 0x2c50+i*64,value)
  self.uc.mem_write(HEAP,bytes(data))
  self.invoke('damping',[HEAP,channel],floats=[v['coefficient'],v['scale']])
  result=self.uc.reg_read(regs.UC_ARM_REG_S0)
  after=bytearray(self.uc.mem_read(HEAP,len(data)))
  if not v['enabled']:
   assert after==data;return f'{result:08x}:none'
  slot=(v['frame']+1)%10
  offsets=[0x2c54+channel*4+slot*64,0x2c60+channel*4+slot*64,0x2c78+channel*4+slot*64] if hdr else [0x2c44+slot*64,0x2c48+slot*64,0x2c4c+slot*64]
  words=[struct.unpack_from('<I',after,o)[0] for o in offsets]
  for o in offsets:after[o:o+4]=data[o:o+4]
  assert after==data,'Unexpected context mutation'
  return f'{result:08x}:{slot}:'+':'.join(f'{w:08x}' for w in words)
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000);p.add_argument('--emit-dir',type=__import__('pathlib').Path);a=p.parse_args()
 sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());assert sha==next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name)
 arm=OriginalDamping();rng=random.Random(0x44414d50);inputs=[];expected=[];coverage={}
 for i in range(a.cases):
  scale=f32(rng.uniform(1,100));kind=i//8%6
  history=[f32(rng.uniform(-5,5)) for _ in range(10)]
  if kind==1:history=[0.]*10
  elif kind==2:history=[f32((j-5)*.003) for j in range(10)]
  elif kind==3:history=[f32(rng.uniform(-.03,.03)) for _ in range(10)]
  elif kind==4:history=[f32(100 if j%2 else -100) for j in range(10)]
  elif kind==5:history=[f32((i%9-4)*(scale/100))]*10
  v=dict(coefficient=f32(rng.uniform(0,1)),scale=scale,enabled=i%11!=0,custom=bool(i%2),custom_scale=f32(rng.uniform(1,100)),middle=f32(rng.uniform(0,1)),frame=i,history=history)
  if i<578:
   # Full 17x17 grid, knots and half-knots, in both rule modes.
   x=(i%17-8)*.5;y=(i//17%17-8)*.5;v['custom']=bool(i//289);v['enabled']=True
   effective_scale=v['custom_scale'] if v['custom'] else scale
   current=f32(x*f32(effective_scale/100));delta=f32(y*f32(.03));slot=i%10
   history=[0.]*10
   for back in range(10):history[(slot-back)%10]=f32(current-back*delta)
   v['history']=history;kind='lattice'
  hdr=i//2%2;channel=i//4%3;key=f'{int(v["enabled"])}:{int(v["custom"])}:{hdr}:{channel}:{kind}';coverage[key]=coverage.get(key,0)+1
  inputs.append('ae-damping '+json.dumps(v,separators=(',',':')));expected.append(arm.run(v,hdr,channel))
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[dict(case=i,input=inputs[i],expected=x,actual=y) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
 report=dict(binarySha256=sha,seed='0x44414d50',cases=a.cases,mismatchCount=len(mismatches),coverage=coverage,scope='Dynamic damping wrapper/core coefficient f32 bits and all three diagnostic writes; unrelated context bytes preserved',limitations=['Standard signed integer quotient/remainder modeled explicitly for nonnegative frame counters; logging discarded.','Finite checked inputs, positive effective scale, linear and HDR storage layouts; null native contexts outside Rust API.','Outer AE controller, exposure routing, ISP initialization and synchronized application remain incomplete.'])
 if mismatches:report['firstMismatches']=mismatches[:5]
 (ROOT/'reverse-engineering/rkaiq/ae-damping-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='coverage'},indent=2));assert not mismatches
 if a.emit_dir:
  a.emit_dir.mkdir(parents=True,exist_ok=True);(a.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(a.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
