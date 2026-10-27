#!/usr/bin/env python3
"""Execute the ordinary updateEffParams metadata-copy path against Rust."""
import hashlib,json,struct,subprocess,sys
from differential import OriginalArm,ROOT,BINARY,HEAP,RETURN
import unicorn.arm_const as regs
SYMBOL='_ZN5RkCam10CamHwIsp3215updateEffParamsEPvS1_'
class Original(OriginalArm):
 def __init__(self):
  super().__init__(BINARY);self.map_calls=0
  self.targets={}
  for name,address in self.symbols.items():
   if 'getParamsForEffMapEj' in name:self.targets[address&~1]='allocate'
   if 'rkisp_effect_params_s' in name and 'ixERS' in name:self.targets[address&~1]='map'
   if name=='_ZN4XCam9SmartLockD2Ev':self.targets[address&~1]='unlock'
  self.targets[RETURN+0x900]='previous'
 def hook(self,uc,address,size,user):
  name=getattr(self,'targets',{}).get(address) or self.stubs.get(address)
  a=uc.reg_read(regs.UC_ARM_REG_R0)
  if name in ['allocate','map','unlock','previous','pthread_mutex_lock','pthread_mutex_unlock','__dynamic_cast']:
   value=0
   if name=='allocate':value=1
   if name=='map':value=HEAP+0x70000;self.map_calls+=1
   if name=='previous':value=0xfffffffe
   if name=='__dynamic_cast':value=a
   uc.reg_write(regs.UC_ARM_REG_R0,value);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v):
  self.uc.mem_write(HEAP,bytes(0x80000));self.map_calls=0
  def put(a,x):self.uc.mem_write(a,struct.pack('<I',x&0xffffffff))
  def word(a):return struct.unpack('<I',self.uc.mem_read(a,4))[0]
  context=HEAP+0x10000;params=HEAP+0x20000;vtable=HEAP+0x30000+24;proxy=HEAP+0x40000;record=HEAP+0x50000;awbproxy=HEAP+0x71000;awb=HEAP+0x72000
  put(context,vtable);put(vtable-24,0);put(vtable-12,0);put(vtable+0x9c,RETURN+0x901)
  put(HEAP+0x70000,proxy);put(proxy+0x6c,record)
  self.uc.mem_write(record,bytes([0x5a])*0xbac0)
  self.uc.mem_write(context+0x69,bytes([v['ae']])*0x792);self.uc.mem_write(context+0x7fb,bytes([v['blc']])*44);self.uc.mem_write(context+0x827,bytes([v['wb']])*32)
  if v['present']:put(context+0x60,awbproxy)
  put(awbproxy+0x6c,awb);self.uc.mem_write(awb+8,bytes([v['cfg']])*0x4b4)
  put(params+0x18,v['frame'])
  # Explicitly select single-ISP: split processing is a separate native branch.
  base=(word(0x4a048)+0x4973a)&0xffffffff;offset=word(0x4a05c);flag=word((base+offset)&0xffffffff);self.uc.mem_write(flag,b'\0')
  self.invoke(SYMBOL,[context,params,0])
  assert self.map_calls==(4 if v['present'] else 3),self.map_calls
  return bytes(self.uc.mem_read(record,0xbac0)).hex()
def main():
 sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert sha==json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text())['binaries'][0]['sha256']
 original=Original();cases=[dict(ae=(i*17)&255,blc=(i*29)&255,wb=(i*41)&255,cfg=(i*71)&255,present=bool(i%2),frame=[0,1,31,0xffffffff][i%4]) for i in range(16)];expected=[original.run(v) for v in cases]
 inputs=''.join('isp-effective '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  p=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True);assert p.stdout.splitlines()==expected,'Effective ISP metadata mismatch'
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')]);arm='--arm' in sys.argv
 if arm:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
  compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=sha,cases=len(cases),host=True,arm=arm,mismatches=0,comparison='Complete 47808-byte effective record including preserved unrelated bytes',limitations=['Explicit single-ISP flag; split-ISP merging excluded.','Map allocation, prior-frame lookup, locking and dynamic cast use explicit adapters; map lifetime policy is not recovered here.'])
 (ROOT/'reverse-engineering/rkaiq/isp-effective-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
