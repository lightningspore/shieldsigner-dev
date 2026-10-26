#!/usr/bin/env python3
"""Compare Rust orchestration with the original daemon's engine_thread.

Only imported OS/library calls are simulated; ARM control flow remains original.
This verifies call order and arguments, not the stubbed RKAIQ implementation.
"""
from pathlib import Path
import argparse,hashlib,json,random,struct,subprocess
from differential import OriginalArm,BASE,HEAP
import unicorn.arm_const as regs
ROOT=Path(__file__).resolve().parents[3]
BINARY=ROOT/'.tools/reverse-engineering/rkaiq-original/rkaiq_3A_server'
START=0x08000001;STOP=0x08000002
class EndOfInput(Exception):pass
class OriginalEngine(OriginalArm):
 def __init__(self,events,multiple,width,height):
  super().__init__(BINARY);self.events=iter(events);self.trace=[];self.consumed=0
  for address,value in [(0x2412c,multiple),(0x240d4,width),(0x240d8,height)]:self.uc.mem_write(BASE+address,struct.pack('<I',value))
  self.uc.mem_write(HEAP,bytes(0x200));self.uc.mem_write(HEAP+0x40,b'/dev/video9\0');self.uc.mem_write(HEAP+0x100,b'm00_b_sc3336\0')
 def string(self,address):
  output=bytearray()
  for i in range(1024):
   byte=self.uc.mem_read(address+i,1)[0]
   if not byte:return output.decode()
   output.append(byte)
  raise AssertionError('Unterminated string')
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name is None:return
  a,b,c,d=[uc.reg_read(getattr(regs,'UC_ARM_REG_R'+str(i))) for i in range(4)];result=0
  if name=='open64':assert self.string(a)=='/dev/video9' and b==2;result=7
  elif name=='ioctl':
   assert a==7
   if b==0x4020565a:
    event=struct.unpack('<I',uc.mem_read(c,4))[0];self.trace.append(f'subscribe:{event}')
    assert bytes(uc.mem_read(c+4,28))==bytes(28)
   elif b==0x80805659:
    try:event=next(self.events)
    except StopIteration:raise EndOfInput()
    self.consumed+=1;uc.mem_write(c,struct.pack('<I',event))
   else:raise AssertionError(f'Unexpected ioctl {b:x}')
  elif name=='rk_aiq_uapi2_sysctl_init':
   assert c==0;self.iq=self.string(b);self.trace.append('init:'+self.string(a)+':'+self.iq);result=HEAP+0x60000
  elif name.startswith('rk_aiq_uapi2_sysctl_'):
   assert a==HEAP+0x60000
   if name.endswith('_setListenStrmStatus'):assert b==0;self.trace.append('listen:0')
   elif name.endswith('_setMulCamConc'):assert b==1;self.trace.append('multicam:1')
   elif name.endswith('_prepare'):self.trace.append(f'prepare:{b}:{c}:{d}')
   elif name.endswith('_start'):self.trace.append('start')
   elif name.endswith('_stop'):self.trace.append(f'stop:{b}')
   else:raise AssertionError(name)
  elif name in ('printf','puts','fprintf','fwrite'):pass
  else:return super().hook(uc,address,size,user)
  uc.reg_write(regs.UC_ARM_REG_R0,result);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))
 def run(self):
  try:self.invoke('_Z13engine_threadPv',[HEAP])
  except EndOfInput:return ';'.join(self.trace)
  raise AssertionError('Original unexpectedly returned')
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--cases',type=int,default=100);parser.add_argument('--emit-dir',type=Path);args=parser.parse_args()
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());expected_hash=next(a['sha256'] for a in manifest['binaries'] if a['name']==BINARY.name)
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==expected_hash
 rng=random.Random(0x33414556);inputs=[];expected=[]
 for i in range(args.cases):
  multiple=i%2;width,height=rng.choice([(2688,1520),(640,480),(720,480),(1920,1080)])
  events=[] if i==0 else [rng.choice([START,STOP,0,0xffffffff,0x08000003]) for _ in range(rng.randrange(1,100))]
  original=OriginalEngine(events,multiple,width,height);expected.append(original.run());assert original.consumed==len(events)
  inputs.append(f'engine {multiple} {width} {height} m00_b_sc3336 {original.iq} '+(','.join(map(str,events)) or '-'))
 binary=ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture'
 actual=subprocess.run([str(binary)],input='\n'.join(inputs)+'\n',capture_output=True,text=True,check=True).stdout.splitlines()
 assert len(actual)==len(expected)
 mismatches=[{'case':i,'input':inputs[i],'expected':a,'actual':b} for i,(a,b) in enumerate(zip(expected,actual)) if a!=b]
 report={'binarySha256':expected_hash,'seed':'0x33414556','cases':len(inputs),'mismatchCount':len(mismatches),'scope':'Successful single-camera engine_thread initialization, subscription, event filtering and start/stop call sequence; multi-camera flag covered', 'limitations':['Imported RKAIQ routines and OS calls are stubs; their implementations are not verified by this test.','Errors and independent sensor/ISP initialization remain separate work.','Finite event sources stop the original at its next dequeue; no original shutdown path is claimed.']}
 if mismatches:report['firstMismatches']=mismatches[:5]
 (ROOT/'reverse-engineering/rkaiq/lifecycle-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not mismatches
 if args.emit_dir:
  args.emit_dir.mkdir(parents=True,exist_ok=True)
  (args.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(args.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
