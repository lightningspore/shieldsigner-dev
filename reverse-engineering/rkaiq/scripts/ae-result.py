#!/usr/bin/env python3
"""Run native conversion then publication on the same context, without resets."""
import hashlib,json,runpy,struct,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,HEAP,regs
Base=runpy.run_path(str(Path(__file__).with_name('ae-conversion-queue.py')))['Original']
record=runpy.run_path(str(Path(__file__).with_name('ae-publication.py')))['record']
class Original(Base):
 def hook(self,uc,address,size,user):
  if self.stubs.get(address)=='memcmp':
   a,b,n=[uc.reg_read(r) for r in [regs.UC_ARM_REG_R0,regs.UC_ARM_REG_R1,regs.UC_ARM_REG_R2]];x=bytes(uc.mem_read(a,n));y=bytes(uc.mem_read(b,n));uc.reg_write(regs.UC_ARM_REG_R0,0 if x==y else (1 if x>y else 0xffffffff));uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def seed_result(self,c,v):
  c[0x4c30:0x4c30+244]=bytes.fromhex(v['previous']);c[0x4fb8]=v['dynamic'];c[0x4fb9]=v['gating'];struct.pack_into('<I',c,0x3d40,v['index']);struct.pack_into('<I',c,0x22f4,1)
  struct.pack_into('<I',c,0x2434,v['effective'][0]);struct.pack_into('<I',c,0x2438,v['effective'][1]);struct.pack_into('<f',c,0x2420,v['effective'][2])
  for i in range(5):struct.pack_into('<i9fI',c,0x3fd8+44*i,i,.003,.006,.2,.001,.002,.003,.004,.005,.006,2)
 def run(self,v):
  conversion=super().run(v)
  self.uc.mem_write(HEAP+0x50000,struct.pack('<6I',0,HEAP+0x60000,HEAP+0x61000,HEAP+0x62000,0,HEAP+0x80000));self.uc.mem_write(HEAP+0x60000,bytes(0x22000))
  assert self.invoke('AecGetProcResults',[HEAP,HEAP+0x50000],instructions=3000000)==0
  get=lambda o,n:bytes(self.uc.mem_read(HEAP+o,n)).hex()
  integer=lambda o:struct.unpack('<I',self.uc.mem_read(HEAP+o,4))[0]
  return conversion+f':{integer(0x80014)}:{integer(0x22fc)}:'+get(0x80018,1464)+':'+get(0x60000,244)+f':{integer(0x5574)}:{integer(0x4198)}:'+str(self.uc.mem_read(HEAP+0x4fb8,1)[0])+':'+str(self.uc.mem_read(HEAP+0x4fb9,1)[0])+':'+get(0x4fbc,1464)+':'+get(0x4c30,244)+':'+get(0x3fd8,220)
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'
 profile=dict(sensor_calib=json.loads(raw)['sensor_calib']);route=[[0.,1.,1.],[.01,1.,1.],[.01,4.,1.],[.02,8.,1.],[.03,15.5,1.],[.03,512.,1.]];cases=[]
 for count in range(6):
  for delta in [-2,0,1,2,7]:
   for n in [1,2,6]:
    for target in [.003,.12,2.4]:
     i=len(cases);cases.append(dict(result=True,profile=profile,route=route,proposed=[.02,6.,1.],target=target,held=.003,published=[[.005*(i+1),1.+i,1.] for i in range(n)],frame_id=30,sync=30-delta,count=count,previous=record(i%3),effective=[122,128,1.],dynamic=i%4,gating=(i//4)%3,index=i%20))
 native=Original()
 # Build prior-final records from native-converted results, so the unchanged
 # branch is exact even when inverse-mapped shutter differs by a float bit.
 extra=[]
 for v in cases[::9]:
  values=[int(w,16) for w in native.run(v).split(':')[0].split(',')[:5]]
  gain,isp,time,tc,gc=values;r=bytearray(244)
  for o,x in [(0,time),(4,gain),(8,0x3f800000),(12,isp),(20,0xffffffff),(32,tc),(36,gc),(232,1360)]:struct.pack_into('<I',r,o,x)
  struct.pack_into('<H',r,228,2800);struct.pack_into('<f',r,236,114.24)
  extra.append(dict(v,previous=bytes(r).hex(),effective=[tc,gc,struct.unpack('<f',struct.pack('<I',isp))[0]]))
 cases+=extra
 expected=[native.run(v) for v in cases];inputs=''.join('ae-result '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):
   if a!=b:
    aa=a.split(':');bb=b.split(':');print('mismatch',i,file=sys.stderr)
    for j,(x,y) in enumerate(zip(aa,bb)):
     if x!=y:print('field',j,'native',x[:120],'rust',y[:120],file=sys.stderr)
    raise AssertionError(i)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='native register/queue conversion followed by complete result publication on the same context; converted points/codes, selected records, convergence and history state',limitations=['Explicit proposed point, aggregate, history index, effective exposure and prior publication; automatic fixed-timing non-iris DCG-disabled SC3336 path.','All subordinate numerical/conversion/publication bodies execute; imported integer division, byte comparison and allocation boundaries modeled and pinned native math executes.','Other ISP result fields, CIS flags and unlisted context bytes are not compared.','Preprocessing/controller and real statistics/exposure association remain separate; no hardware writes.'])
 (ROOT/'reverse-engineering/rkaiq/ae-result-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
