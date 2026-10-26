#!/usr/bin/env python3
"""Compare full descriptor construction, including native helper/format code."""
import argparse,hashlib,json,random,struct,subprocess
from pathlib import Path
from differential import OriginalArm,ROOT,BINARY,HEAP,RETURN,regs
class OriginalDescriptor(OriginalArm):
 def __init__(self):
  super().__init__(BINARY);self.stubs[RETURN+0xe000]='sensor_ioctl';self.uc.mem_write(RETURN+0xe000,b'\x70\x47')
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name=='__errno_location':
   uc.mem_write(HEAP+0xe0000,struct.pack('<i',5));uc.reg_write(regs.UC_ARM_REG_R0,HEAP+0xe0000);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if name!='sensor_ioctl':return super().hook(uc,address,size,user)
  request=uc.reg_read(regs.UC_ARM_REG_R1);payload=uc.reg_read(regs.UC_ARM_REG_R2);v=self.v
  if request==0xc0585604:label='format'
  elif request==0xc0445624:label={0x9e0902:'hblank',0x9e0901:'vblank',0x980911:'exposure'}[struct.unpack('<I',uc.mem_read(payload,4))[0]]
  else:label={0xc0305615:'interval',0xc0185647:'pixel_rate',0x801056c9:'nr',0x800c56d2:'dcg'}[request]
  self.trace.append(label);failed=label in v['fail'].split('+') or (label=='interval' and v['fps_fail'])
  if not failed:
   if label=='format':
    assert struct.unpack('<II',uc.mem_read(payload,8))==(1,0)
    uc.mem_write(payload+8,struct.pack('<III',v['width'],v['height'],v['bus']))
   elif label in ('hblank','vblank','exposure'):uc.mem_write(payload+40,struct.pack('<i',v[label]))
   elif label=='interval':uc.mem_write(payload+4,struct.pack('<II',v['numerator'],v['denominator']))
   elif label=='pixel_rate':
    control=struct.unpack('<I',uc.mem_read(payload+20,4))[0];assert struct.unpack('<I',uc.mem_read(control,4))[0]==0x9f0902
    uc.mem_write(control+12,struct.pack('<q',v['pixel_rate']))
   elif label=='nr':uc.mem_write(payload,struct.pack('<4I',*v['nr']))
   else:uc.mem_write(payload,struct.pack('<3I',*v['dcg']))
  uc.reg_write(regs.UC_ARM_REG_R0,0xffffffff if failed else 0);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))
 def run(self,v):
  self.v=v;self.trace=[];context=HEAP;output=HEAP+0x10000;vtable=HEAP+0x20000
  self.uc.mem_write(context,bytes(0x300));self.uc.mem_write(context,struct.pack('<I',vtable));self.uc.mem_write(vtable,bytes(0x100));self.uc.mem_write(vtable+0x30,struct.pack('<I',(RETURN+0xe000)|1))
  for offset,name in [(0x84,'_ZN5RkCam8SensorHw15get_sensor_descEP33rk_aiq_exposure_sensor_descriptor'),(0x7c,'_ZN5RkCam8SensorHw9get_blankEP33rk_aiq_exposure_sensor_descriptor'),(0x78,'_ZN5RkCam8SensorHw9get_pixelEP33rk_aiq_exposure_sensor_descriptor'),(0x80,'_ZN5RkCam8SensorHw18get_exposure_rangeEP33rk_aiq_exposure_sensor_descriptor')]:self.uc.mem_write(vtable+offset,struct.pack('<I',self.symbols[name]))
  self.uc.mem_write(output,b'\xa5'*172)
  status=self.invoke('_ZN5RkCam8SensorHw21get_sensor_descriptorEP33rk_aiq_exposure_sensor_descriptor',[context,output]);status=struct.unpack('<i',struct.pack('<I',status))[0]
  data=self.uc.mem_read(output,172).hex() if status==0 else '-'
  return ';'.join(self.trace)+'|'+str(status)+'|'+data

def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000);p.add_argument('--emit-dir',type=Path);args=p.parse_args()
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==sha
 arm=OriginalDescriptor();rng=random.Random(0x44455343);inputs=[];expected=[];coverage={}
 codes=[0x2001,0x200a,0x2013,0x3001,0x3002,0x3007,0x3008,0x300a,0x300e,0x300f,0x3010,0x3011,0x3012,0x3013,0x3014,0,0xffffffff]
 for i in range(args.cases):
  fail=['','format','hblank','vblank','pixel_rate','exposure','nr','dcg','nr+dcg'][i//2%9];fps_fail=bool(i%2)
  v=dict(width=rng.choice([640,1280,1920,2304,2688]),height=rng.choice([480,720,1080,1296,1520]),bus=codes[i%len(codes)],hblank=rng.choice([-1,0,100,4095,65535]),vblank=rng.choice([-1,0,80,1000,65535]),exposure=rng.choice([0,1,2,4,65535]),numerator=rng.choice([1,1001,100000,0xffffffff]),denominator=rng.choice([30,30000,1000000,0xffffffff]),pixel_rate=rng.choice([24000000,72000000,384000000,0x80000000,0x100000001]),nr=[rng.randrange(0xffffffff) for _ in range(4)],dcg=[rng.randrange(0xffffffff) for _ in range(3)],fps_fail=fps_fail,fail=fail)
  inputs.append('sensor-descriptor '+json.dumps(v,separators=(',',':')));expected.append(arm.run(v));key=f'{fps_fail}:{fail}';coverage[key]=coverage.get(key,0)+1
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatch=[{'case':i,'input':inputs[i],'expected':a,'actual':b} for i,(a,b) in enumerate(zip(expected,actual)) if a!=b]
 report=dict(binarySha256=sha,seed='0x44455343',cases=len(inputs),branchCoverage=coverage,mismatchCount=len(mismatch),scope='Full 172-byte descriptor on success, query order/status, timing and pixel-clock fallback, format mapping, optional NR/DCG behavior',limitations=['Only device ioctl responses and errno are simulated; native descriptor helpers execute original ARM instructions.','Required failures compare status/query trace, not the original partial error output; Rust returns no descriptor on error.','Real driver queries, internal routing and live sensor operation require hardware validation.'])
 if mismatch:report['firstMismatches']=mismatch[:3]
 (ROOT/'reverse-engineering/rkaiq/sensor-descriptor-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not mismatch
 if args.emit_dir:
  args.emit_dir.mkdir(parents=True,exist_ok=True)
  (args.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(args.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
