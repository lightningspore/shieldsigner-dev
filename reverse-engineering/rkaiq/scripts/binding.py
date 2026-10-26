#!/usr/bin/env python3
"""Execute original sensor-selector instructions over controlled inventories.

Native smart-pointer operations run; OS-facing media operations are stubs.
This does not verify construction of the actual sensor inventory.
"""
from pathlib import Path
import argparse,hashlib,json,random,struct,subprocess
from differential import OriginalArm,BASE,HEAP,u32
import unicorn.arm_const as regs
ROOT=Path(__file__).resolve().parents[3]
BINARY=ROOT/'.tools/reverse-engineering/rkaiq-original/librkaiq.so'
class OriginalBinding(OriginalArm):
 def __init__(self):
  super().__init__(BINARY)
  for name in ['media_device_new','media_device_enumerate','media_get_entity_by_name','media_entity_get_info','media_device_unref']:
   self.stubs[self.symbols[name]&~1]=name
  self.status=0;self.sensor_by_name={}
 def string(self,address):
  output=bytearray()
  for i in range(1024):
   b=self.uc.mem_read(address+i,1)[0]
   if b==0:return output.decode()
   output.append(b)
  raise AssertionError('Unterminated string')
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name is None:return
  a,b,c=[uc.reg_read(getattr(regs,'UC_ARM_REG_R'+str(i))) for i in range(3)];result=0
  if name=='strstr':
   at=self.string(a).find(self.string(b));result=a+at if at>=0 else 0
  elif name=='snprintf':
   assert self.string(c)=='/dev/media%d' and b==64
   index=uc.reg_read(regs.UC_ARM_REG_R3);self.status=self.sensors[index]['media']
   text=f'/dev/media{index}'.encode();uc.mem_write(a,text+b'\0');result=len(text)
  elif name=='access':result=0xffffffff if self.status==-1 else 0
  elif name=='media_device_new':result=0 if self.status==-2 else HEAP+0xd0000
  elif name=='media_device_enumerate':result=0
  elif name=='media_get_entity_by_name':
   result=0 if self.status==-3 else HEAP+0xd1000
   uc.mem_write(HEAP+0xd1000,bytes(0x120));uc.mem_write(HEAP+0xd1100,bytes(32))
   uc.mem_write(HEAP+0xd1100+12,struct.pack('<I',max(0,self.status)))
   uc.mem_write(HEAP+0xd1000+0x108,struct.pack('<I',HEAP+0xd1100))
   uc.mem_write(HEAP+0xd1000+0x110,struct.pack('<I',0 if self.status==-4 else 1))
  elif name in ('media_entity_get_info','media_device_unref'):result=0
  else:return super().hook(uc,address,size,user)
  uc.reg_write(regs.UC_ARM_REG_R0,result);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))
 def run(self,sensors,query):
  self.sensors=sensors
  self.uc.mem_write(BASE+0x1adcdc+8,struct.pack('<I',HEAP+0x1000 if sensors else 0))
  for i,s in enumerate(sensors):
   base=HEAP+0x1000+i*0x1000;info=base+0x100;isp=base+0x400;cif=base+0x600;name=base+0x800;control=base+0xa00
   self.uc.mem_write(base,bytes(0x1000))
   self.uc.mem_write(base,struct.pack('<I',base+0x1000 if i+1<len(sensors) else 0))
   self.uc.mem_write(base+28,struct.pack('<II',info,control));self.uc.mem_write(control+4,struct.pack('<I',100))
   self.uc.mem_write(info,struct.pack('<II',name,len(s['name'])));self.uc.mem_write(name,s['name'].encode()+b'\0')
   self.uc.mem_write(info+0x60,struct.pack('<I',i));self.uc.mem_write(info+0x148,struct.pack('<I',isp if s['isp'] else 0))
   for offset,path in zip([0x94,0xb4],s['paths']):self.uc.mem_write(isp+offset,path.encode()+b'\0')
   if s['cif'] is not None:
    self.uc.mem_write(info+0x150,struct.pack('<I',cif))
    for offset,path in zip([0x45,0x65,0x85,0xa5],s['cif']):self.uc.mem_write(cif+offset,path.encode()+b'\0')
  ptr=HEAP+0xf0000
  if query is not None:self.uc.mem_write(ptr,query.encode()+b'\0')
  result=self.invoke('_ZN5RkCam10CamHwIsp2021getBindedSnsEntNmByVdEPKc',[ptr if query is not None else 0])
  for i in range(len(sensors)):assert u32(self.uc.mem_read(HEAP+0x1000+i*0x1000+0xa04,4))==100,'Reference count imbalance'
  return self.string(result) if result else None

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--cases',type=int,default=1000);parser.add_argument('--emit-dir',type=Path);args=parser.parse_args()
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==sha
 arm=OriginalBinding();rng=random.Random(0x534e5352);inputs=[];expected=[]
 names=['m00_b_sc3336','m01_b_sc3336','m02_s_sc3336','FakeCamera','m00_b_1608','m01_s_FakeCamera']
 paths=['/dev/video0','/dev/video1','/dev/video10','/dev/video11','/dev/video2','']
 for i in range(args.cases):
  sensors=[dict(name=rng.choice(names)+str(j),isp=rng.choice([True,True,False]),paths=rng.sample(paths,2),cif=rng.sample(paths,4) if rng.choice([True,False]) else None,media=rng.choice([-1,-2,-3,-4,0,1,3,5])) for j in range(rng.randrange(0,8))]
  query=rng.choice([None,'','/dev/video','/dev/video1','video0','/dev/video99'])
  input=dict(sensors=sensors,query=query)
  inputs.append('binding '+json.dumps(input,separators=(',',':')));expected.append(json.dumps(arm.run(sensors,query),separators=(',',':')))
 binary=ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture'
 actual=subprocess.run([str(binary)],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[{'case':i,'input':inputs[i],'expected':a,'actual':b} for i,(a,b) in enumerate(zip(expected,actual)) if a!=b]
 report=dict(binarySha256=sha,seed='0x534e5352',cases=len(inputs),mismatchCount=len(mismatches),scope='Sensor binding selection over controlled ordered inventories, ISP/CIF path precedence, special names and media-probe outcomes',limitations=['Inventory population and OS/media probes are not implemented or verified by these controlled inputs.','Finite ASCII strings with no embedded NUL; native invalid-pointer behavior is outside the checked Rust API.'])
 if mismatches:report['firstMismatches']=mismatches[:5]
 (ROOT/'reverse-engineering/rkaiq/binding-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not mismatches
 if args.emit_dir:
  args.emit_dir.mkdir(parents=True,exist_ok=True)
  (args.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(args.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
