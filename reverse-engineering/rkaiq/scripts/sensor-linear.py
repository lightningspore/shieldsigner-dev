#!/usr/bin/env python3
"""Compare linear sensor control order/failure behavior with actual ARM method."""
import argparse,hashlib,json,random,struct,subprocess
from pathlib import Path
from differential import OriginalArm,ROOT,BINARY,HEAP,RETURN,regs
class OriginalSensor(OriginalArm):
 def __init__(self):
  super().__init__(BINARY)
  self.stubs[self.symbols['xcam_print_log']&~1]='xcam_print_log'
  for address,name in [(RETURN+0xe000,'descriptor'),(RETURN+0xe010,'sensor_ioctl')]:
   self.uc.mem_write(address,b'\x70\x47');self.stubs[address]=name
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name is None:return
  a,b,c=[uc.reg_read(r) for r in [regs.UC_ARM_REG_R0,regs.UC_ARM_REG_R1,regs.UC_ARM_REG_R2]];result=0
  if name=='descriptor':
   self.trace.append('descriptor');uc.mem_write(b,bytes(64));uc.mem_write(b+30,struct.pack('<H',self.lines));uc.mem_write(b+36,struct.pack('<I',self.height))
  elif name=='sensor_ioctl':
   if b==0xc008561c:
    id,value=struct.unpack('<Ii',uc.mem_read(c,8));self.trace.append(f'control:{id:08x}:{value}')
   elif b==0x400456c6:self.trace.append('dcg:'+str(struct.unpack('<I',uc.mem_read(c,4))[0]))
   else:raise AssertionError(hex(b))
   self.operations+=1
   if self.operations==self.fail:result=0xffffffff
  elif name=='xcam_print_log':pass
  else:return super().hook(uc,address,size,user)
  uc.reg_write(regs.UC_ARM_REG_R0,result);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))
 def run(self,lines,height,requested,dcg,analog,digital,coarse,mirror,initial,fail):
  self.lines=lines;self.height=height;self.fail=fail;self.operations=0;self.trace=[]
  context=HEAP;exposure=HEAP+0x2000;vtable=HEAP+0x4000;cache=HEAP+0x6000
  self.uc.mem_write(context,bytes(0x200));self.uc.mem_write(exposure,bytes(0x300));self.uc.mem_write(vtable,bytes(0x100));self.uc.mem_write(cache,struct.pack('<II',0,initial))
  self.uc.mem_write(context,struct.pack('<I',vtable));self.uc.mem_write(vtable+0x88,struct.pack('<I',(RETURN+0xe000)|1));self.uc.mem_write(vtable+0x30,struct.pack('<I',(RETURN+0xe010)|1))
  self.uc.mem_write(context+0x13b,bytes([mirror]));self.uc.mem_write(context+0x140,struct.pack('<I',cache))
  for offset,value in [(0x14,dcg),(0x20,coarse),(0x24,analog),(0x28,digital),(0xe8,requested)]:self.uc.mem_write(exposure+offset,struct.pack('<I',value&0xffffffff))
  result=self.invoke('_ZN5RkCam8SensorHw23setLinearSensorExposureEP17RKAiqAecExpInfo_s',[context,exposure]);status=struct.unpack('<i',struct.pack('<I',result))[0]
  cached=struct.unpack('<I',self.uc.mem_read(cache+4,4))[0]
  return ';'.join(self.trace)+'|'+str(status)+'|'+(str(cached) if mirror else '-')
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000);p.add_argument('--emit-dir',type=Path);args=p.parse_args()
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==sha
 arm=OriginalSensor();rng=random.Random(0x53454e53);inputs=[];expected=[];coverage={}
 for i in range(args.cases):
  lines=rng.choice([0,1520,1600,65535]);height=rng.choice([0,480,1520,2160]);requested=rng.choice([0,lines,lines+10,0xffffffff,rng.randrange(10000)]);dcg=rng.choice([-1,0,1,2]);analog=rng.randrange(0xffffffff);digital=rng.choice([0,rng.randrange(0xffffffff)]);coarse=rng.choice([0,rng.randrange(0xffffffff)]);mirror=i%2;initial=rng.randrange(0xffffffff);fail=i//2%6
  values=[lines,height,requested,dcg,analog,digital,coarse,mirror,initial,fail]
  inputs.append('sensor-linear '+' '.join(map(str,values)));expected.append(arm.run(*values));key=f'{mirror}:{fail}';coverage[key]=coverage.get(key,0)+1
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatch=[{'case':i,'input':inputs[i],'expected':a,'actual':b} for i,(a,b) in enumerate(zip(expected,actual)) if a!=b]
 report=dict(binarySha256=sha,seed='0x53454e53',cases=len(inputs),branchCoverage=coverage,mismatchCount=len(mismatch),scope='Linear sensor write order, optional DCG/digital/shutter writes, first-error exit and frame-length mirror updates',limitations=['Descriptor retrieval and device ioctl calls are controlled callbacks, not real hardware.','Successful descriptor retrieval is assumed for binary comparison; Rust propagates descriptor failures explicitly.','No real-gain/register conversion, frame-delay scheduling, HDR programming or live ioctl adapter is implemented by this function.'])
 if mismatch:report['firstMismatches']=mismatch[:5]
 (ROOT/'reverse-engineering/rkaiq/sensor-linear-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not mismatch
 if args.emit_dir:
  args.emit_dir.mkdir(parents=True,exist_ok=True)
  (args.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(args.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
