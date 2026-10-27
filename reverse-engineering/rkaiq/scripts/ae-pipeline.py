#!/usr/bin/env python3
"""Native preprocessing checkpoint, complete AecRun, then complete publication."""
import hashlib,json,runpy,struct,subprocess,sys
from pathlib import Path
from unicorn import UC_HOOK_MEM_WRITE
from differential import ROOT,BINARY,HEAP,RETURN,regs
Controller=runpy.run_path(str(Path(__file__).with_name('ae-controller.py')))['Original']
Base=runpy.run_path(str(Path(__file__).with_name('ae-result.py')))['Original']
record=runpy.run_path(str(Path(__file__).with_name('ae-publication.py')))['record']
class Original(Base):
 def __init__(self):
  super().__init__();self.preprocessing=False;self.uc.hook_add(UC_HOOK_MEM_WRITE,self.store,begin=HEAP+0x12c,end=HEAP+0x12f)
 def store(self,uc,access,address,size,value,user):
  if self.preprocessing:self.prepared=True;uc.reg_write(regs.UC_ARM_REG_PC,RETURN);uc.emu_stop()
 def initialize(self,v):
  sensor=self.setup(dict(v,seconds=.0045,gain=2.,isp=1.,dcg=-1,frame=1360,clock=114.24,line=2800,analogue_minimum=1.,isp_range=[1.,32.],time_range=[.00005,.03],gain_range=[1.,512.],automatic=True,suppress=False,flicker=True,quantum=.01))
  c=Controller.setup(self,v)
  for o,n in [(0x638,0x58),(0x6ec,4),(0x778,8),(0x3d14,4)]:c[o:o+n]=sensor[o:o+n]
  struct.pack_into('<I',c,0x63c,HEAP+0x90000);self.uc.mem_write(HEAP+0x90000,struct.pack('<7f',*v['profile']['sensor_calib']['Gain2Reg']['GainRange']));struct.pack_into('<f',c,0x680,8.);struct.pack_into('<I',c,0x22f0,1);c[0x23e4]=1
  struct.pack_into('<II',c,0xec,184,256);struct.pack_into('<i',c,0xe4,-1);c[0x2318]=v['count']
  c[0x4c30:0x4c30+244]=bytes.fromhex(record(0))
  for i,(time,gain) in enumerate([(.003,1.),(.006,1.)]):struct.pack_into('<4f',c,0x4fbc+244*i,time,gain,1.,1.)
  struct.pack_into('<I',c,0x40cc,HEAP+0x30000)
  self.uc.mem_write(HEAP,bytes(c));self.uc.mem_write(HEAP+0x30000,struct.pack('<4I',HEAP+0x31000,2,HEAP+0x32000,2));self.uc.mem_write(HEAP+0x31000,struct.pack('<2f',0.,1.));self.uc.mem_write(HEAP+0x32000,struct.pack('<2f',45.,45.))
 def run(self,v):
  self.initialize(v);return self.step(v)
 def step(self,v):
  stats=bytearray(0x3000);struct.pack_into('<256I',stats,0x788,*v['histogram']);struct.pack_into('<3H',stats,0x2e20,int(v['measured']*256),512,768);self.uc.mem_write(HEAP+0x40000,bytes(stats))
  stack=bytearray(240);struct.pack_into('<f',stack,0,1.);struct.pack_into('<II',stack,232,HEAP+0x40000,v['frame'])
  seconds,gain=v['exposure'],1.
  if v.get('effective_from_previous',False):
   c=bytes(self.uc.mem_read(HEAP,0x6000));seconds=struct.unpack_from('<f',c,0xe8)[0];gain=struct.unpack_from('<f',c,0xdc)[0];isp=struct.unpack_from('<f',c,0xe0)[0];tc,gc=struct.unpack_from('<2I',c,0xec);struct.pack_into('<f',stack,0,isp);struct.pack_into('<2I',stack,20,tc,gc)
  bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
  self.preprocessing=True;self.prepared=False;self.mappings=0
  self.invoke('AecPreProcess',[HEAP,bits(seconds),bits(gain),bits(1.)],stack=bytes(stack),instructions=1000000);assert self.prepared;self.preprocessing=False
  self.last_run=bool(self.uc.mem_read(HEAP+0x22ed,1)[0]);assert self.invoke('AecRun',[HEAP,HEAP+0x60000,HEAP+0x40000],instructions=10000000)==0
  self.uc.mem_write(HEAP+0x50000,struct.pack('<6I',0,HEAP+0x60000,HEAP+0x61000,HEAP+0x62000,0,HEAP+0x80000));self.uc.mem_write(HEAP+0x60000,bytes(0x22000));assert self.invoke('AecGetProcResults',[HEAP,HEAP+0x50000],instructions=3000000)==0
  c=bytes(self.uc.mem_read(HEAP,0x6000));u=lambda o:struct.unpack_from('<I',c,o)[0]
  offsets=[0xd4,0xdc,0xe0,0xe8,0xec,0xf0,0x12c,0x124,0x128,0xd8,0x5574,0x3d40,0x22fc,0x4198]
  words=[int(self.last_run)]+[u(o) for o in offsets]+[c[o] for o in [0x4fb8,0x4fb9,0x5994,0x5995,0x23cf,0x3d3c]]+[u(o) for o in [0x40f4,0x40f8]]+[c[o] for o in [0x40fc,0x40fd]]+[u(o) for o in [0x3ccc,0x3cdc,0x3d00,0x3cec]]+[u(0x2c50+64*i) for i in range(10)]+list(struct.unpack_from('<3H',c,0x404))+[u(0x118)]+list(struct.unpack_from('<3I',c,0x3c8))
  words+=list(struct.unpack('<6I',self.uc.mem_read(HEAP+0x10000,24)))
  prefix=','.join(f'{w:08x}' for w in words);count=struct.unpack('<I',self.uc.mem_read(HEAP+0x80014,4))[0]
  return prefix+f':{count}:'+bytes(self.uc.mem_read(HEAP+0x80018,1464)).hex()+':'+c[0x4fbc:0x4fbc+1464].hex()+':'+c[0x4c30:0x4c30+244].hex()+':'+c[0x3fd8:0x40b4].hex()
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'
 runtime=ROOT/'.tools/reverse-engineering/uclibc-runtime/libuClibc-1.0.31.so';runtime_sha=hashlib.sha256(runtime.read_bytes()).hexdigest();assert runtime_sha==json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text())['uclibcRuntime']['memberSha256']
 cases=[]
 for k in range(48):
  for count in [0,2,5]:
   h=[0]*256;h[[3,120,254,255][k%4]]=1000
   cases.append(dict(profile=dict(sensor_calib=json.loads(raw)['sensor_calib']),histogram=h,measured=[0.,.390625,3.,45.,120.,240.][k%6],exposure=[.003,.02,.1][k%3],previous=[-.5,0.,.5][k%3],reference=[-.5,0.,.5][(k//3)%3],fps=[2.,30.][k%2],enabled=bool(k%2),same_mode=k%5!=0,priming=k%7==0,saturated=bool(k%2),force=k%3==0,index=k%20,frame=30+k,sync=28+k,dynamic=bool(k%2),dynamic_enabled=bool((k//2)%2),custom=False,damping_history=[((i+k)%7-3)*.01 for i in range(10)],run_wrapper=True,run=True,count=count))
 native=Original();expected=[];processed=0
 for v in cases:expected.append(native.run(v));processed+=int(native.last_run)
 inputs=''.join('ae-pipeline '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):
   if a!=b:
    aa=a.split(':');bb=b.split(':');print('mismatch',i,file=sys.stderr)
    for j,(x,y) in enumerate(zip(aa,bb)):
     if x!=y:
      if j==0:print('words',[(k,l,r) for k,(l,r) in enumerate(zip(x.split(','),y.split(','))) if l!=r],file=sys.stderr)
      else:print('field',j,x[:80],y[:80],file=sys.stderr)
    raise AssertionError(i)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,runtimeSha256=runtime_sha,cases=len(cases),processed=processed,skipped=len(cases)-processed,mismatches=0,armReplayPassed='--arm' in sys.argv,scope='native preprocessing current-error checkpoint, complete automatic AecRun with real conversion, then complete result publication on one context',limitations=['Explicit initialized state, profile timing/limits, fixed target45, standard linear mode, no iris/HDR/DCG; preprocessing stops at its documented checkpoint.','Outputs and listed controller/convergence/queue/history/sample state compared; other ISP result fields and unlisted context bytes excluded.','Pinned native math executes; imported integer division, byte comparison and allocation modeled.','No real frame/exposure association, hardware writes or multi-frame sequence qualification.'])
 (ROOT/'reverse-engineering/rkaiq/ae-pipeline-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
