#!/usr/bin/env python3
"""Compare ISP pad setup against native ARM orchestration with device boundaries recorded."""
import argparse,hashlib,json,random,struct,subprocess
from pathlib import Path
from differential import OriginalArm,ROOT,BINARY,HEAP,RETURN,regs,u32
class OriginalPipeline(OriginalArm):
 def __init__(self):
  super().__init__(BINARY)
  self.symbols['pipeline']=0x3319d
  self.stubs[self.symbols['xcam_print_log']&~1]='xcam_print_log'
  names={
   'tx':'_ZN5RkCam16RawStreamCapUnit13set_tx_formatERK18v4l2_subdev_formatj',
   'rx':'_ZN5RkCam17RawStreamProcUnit13set_rx_formatERK18v4l2_subdev_formatj',
   'bpp':'_ZN5RkCam10CamHwIsp2010pixFmt2BppEjRa',
   'scaler':'_ZN5RkCam12CifSclStream10set_formatERK21v4l2_subdev_selectionji'}
  for name,symbol in names.items():self.stubs[self.symbols[symbol]&~1]=name
  for i,name in enumerate(['get','format','selection']):
   addr=RETURN+0xe000+i*16;self.uc.mem_write(addr,b'\x70\x47');self.stubs[addr]=name
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name is None:return
  a,b,c,d=[uc.reg_read(getattr(regs,'UC_ARM_REG_R'+str(i))) for i in range(4)];result=0
  if name in ['tx','rx']:self.trace.append(f'{name}:{c}:'+bytes(uc.mem_read(b,88)).hex())
  elif name=='bpp':self.trace.append(f'bpp:{b}');uc.mem_write(c,bytes([self.v['bits']&255]))
  elif name=='scaler':
   signed=struct.unpack('<i',struct.pack('<I',d))[0];self.trace.append(f'scaler:{c}:{signed}:'+bytes(uc.mem_read(b,64)).hex())
  elif name in ['get','format','selection']:
   self.operations+=1
   if name=='get':
    which,pad=struct.unpack('<II',uc.mem_read(b,8));assert which==1 and pad in [0,2]
    self.trace.append(f'get:{which}:{pad}')
   else:self.trace.append(name+':'+bytes(uc.mem_read(b,88 if name=='format' else 64)).hex())
   if self.operations==self.v['fail']:result=self.v['error']&0xffffffff
   elif name=='get':uc.mem_write(b,bytes.fromhex(self.v['source' if pad==2 else 'sink']))
   elif name=='selection' and self.v['adjust']:
    adjusted=bytearray(uc.mem_read(b,64))
    for o,mask in [(8,0x1234),(12,0x8000)]:struct.pack_into('<I',adjusted,o,u32(adjusted[o:o+4])^mask)
    for o,delta in [(16,1),(20,2),(24,-2),(28,-4)]:struct.pack_into('<I',adjusted,o,(u32(adjusted[o:o+4])+delta)&0xffffffff)
    for o in range(32,64):adjusted[o]^=0x5a
    uc.mem_write(b,bytes(adjusted))
  elif name=='xcam_print_log':pass
  else:return super().hook(uc,address,size,user)
  uc.reg_write(regs.UC_ARM_REG_R0,result);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))
 def run(self,v):
  self.v=v;self.trace=[];self.operations=0;context=HEAP;selection=HEAP+0x2000;sensor=HEAP+0x3000;device=HEAP+0x4000;vtable=HEAP+0x5000
  data=bytearray(0x1000);struct.pack_into('<I',data,0x2c,device);data[0x2be]=v['shared'];struct.pack_into('<I',data,0x548,HEAP+0x6000 if v['scaler'] else 0)
  self.uc.mem_write(context,bytes(data));self.uc.mem_write(selection,bytes.fromhex(v['crop']));self.uc.mem_write(sensor,bytes.fromhex(v['sensor']));self.uc.mem_write(device,struct.pack('<I',vtable));self.uc.mem_write(vtable,bytes(0x100))
  for offset,addr in [(0x60,RETURN+0xe000),(0x5c,RETURN+0xe010),(0x64,RETURN+0xe020)]:self.uc.mem_write(vtable+offset,struct.pack('<I',addr|1))
  got=u32(self.uc.mem_read(0x3332c,4))+0x331b8;global_pointer=u32(self.uc.mem_read(got+u32(self.uc.mem_read(0x33334,4)),4));self.uc.mem_write(global_pointer+0x80,struct.pack('<I',v['first']))
  original=bytes(self.uc.mem_read(context,len(data)));crop=bytes(self.uc.mem_read(selection,64));fmt=bytes(self.uc.mem_read(sensor,88))
  result=self.invoke('pipeline',[context,selection,sensor,v['pixel']]);signed=struct.unpack('<i',struct.pack('<I',result))[0]
  assert bytes(self.uc.mem_read(context,len(data)))==original and bytes(self.uc.mem_read(selection,64))==crop and bytes(self.uc.mem_read(sensor,88))==fmt
  self.trace.append(f'return:{signed}');return ';'.join(self.trace)
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000);p.add_argument('--emit-dir',type=Path);a=p.parse_args()
 sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());assert sha==next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name)
 arm=OriginalPipeline();rng=random.Random(0x49535050);inputs=[];expected=[];coverage={}
 for i in range(a.cases):
  def record(n):return bytearray(rng.randbytes(n))
  sensor=record(88);crop=record(64);sink=record(88);source=record(88)
  struct.pack_into('<II',sink,0,1,0);struct.pack_into('<II',source,0,1,2)
  w,h=rng.choice([(640,480),(2304,1296),(1920,1080),(1280,720)])
  struct.pack_into('<III',sensor,8,w,h,rng.choice([0x3007,0x300e,0x3013]))
  struct.pack_into('<iiII',crop,16,rng.randrange(0,32),rng.randrange(0,32),w-32,h-32)
  v=dict(adjust=bool(i//56%2),sensor=sensor.hex(),crop=crop.hex(),sink=sink.hex(),source=source.hex(),shared=bool(i%2),first=bool(i//2%2),scaler=bool(i//4%2),pixel=rng.choice([0x30314742,0x32314742,0x36314742]),bits=rng.choice([8,10,12,16,-1]),fail=i//8%7,error=rng.choice([-1,-2,-7,-22,1]))
  key=f'{int(v["shared"])}:{int(v["first"])}:{int(v["scaler"])}:{v["fail"]}:{int(v["adjust"])}';coverage[key]=coverage.get(key,0)+1
  inputs.append('isp-pipeline '+json.dumps(v,separators=(',',':')));expected.append(arm.run(v))
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[dict(case=i,input=inputs[i],expected=x,actual=y) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
 report=dict(binarySha256=sha,seed='0x49535050',cases=a.cases,mismatchCount=len(mismatches),coverage=coverage,scope='setupPipelineFmtIsp raw-stream/scaler call order, complete set-format/selection records, get-format requests and first-error return',limitations=['Device methods, raw-stream format helpers, pixel-format-to-bpp helper and scaler are recorded boundary stubs; their implementations are not proved by this suite.','Get-format responses are controlled native-sized records. Uninitialized request bytes outside which/pad are not compared.','No real ioctl, graph linking, ISP parameter queue, calibrated module setup or independent camera startup is implemented by this routine.'])
 if mismatches:report['firstMismatches']=mismatches[:3]
 (ROOT/'reverse-engineering/rkaiq/isp-pipeline-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='coverage'},indent=2));assert not mismatches
 if a.emit_dir:
  a.emit_dir.mkdir(parents=True,exist_ok=True);(a.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(a.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
