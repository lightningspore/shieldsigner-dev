#!/usr/bin/env python3
"""Compare connected Rust standard controller with complete native AecClmExecute."""
import hashlib,json,random,runpy,struct,subprocess,sys
from pathlib import Path
from unicorn import UC_HOOK_MEM_WRITE
from differential import ROOT,BINARY,HEAP,RETURN,regs
Base=runpy.run_path(str(Path(__file__).with_name('ae-route.py')))['OriginalRoute']
class Original(Base):
 def __init__(self,binary):
  super().__init__(binary);self.actual_run_flag=False;self.preprocessing=False;self.prepared=False;self.running=False;self.conversions=[]
  self.conversion_addresses={p&~1:n for n,p in self.symbols.items() if ('AecLinearDcgConvertion' in n or n=='_ZL21AecRegValueConvertionP12AecContext_s')}
  self.run_flag=next(p&~1 for n,p in self.symbols.items() if 'AecGetRunFlag' in n)
  self.uc.hook_add(UC_HOOK_MEM_WRITE,self.preprocess_store,begin=HEAP+0x12c,end=HEAP+0x12f)
 def preprocess_store(self,uc,access,address,size,value,user):
  if self.preprocessing:
   self.prepared=True;uc.reg_write(regs.UC_ARM_REG_PC,RETURN);uc.emu_stop()
 def hook(self,uc,address,size,user):
  if self.running and address in self.conversion_addresses:
   self.conversions.append(self.conversion_addresses[address]);uc.reg_write(regs.UC_ARM_REG_R0,0);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if self.preprocessing and not self.actual_run_flag and address==self.run_flag:
   uc.reg_write(regs.UC_ARM_REG_R0,1);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if self.stubs.get(address)=='__aeabi_uidiv':
   a=uc.reg_read(regs.UC_ARM_REG_R0);b=uc.reg_read(regs.UC_ARM_REG_R1);assert b
   uc.reg_write(regs.UC_ARM_REG_R0,a//b);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if self.stubs.get(address)=='__aeabi_idivmod':
   a=uc.reg_read(regs.UC_ARM_REG_R0);b=uc.reg_read(regs.UC_ARM_REG_R1);assert a<0x80000000 and b in [5,10]
   uc.reg_write(regs.UC_ARM_REG_R0,a//b);uc.reg_write(regs.UC_ARM_REG_R1,a%b);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def setup(self,v):
  c=bytearray(0x6000)
  for o,x in [(0x130,45.),(0x114,v['measured']),(0xd0,v['exposure']),(0x10,10.),(0x14,10.),(0xf4,.00005),(0xf8,15.36),(0x2404,.4),(0x2408,.5),(0x5988,v['fps']),(0xfc,.00005),(0x100,.03),(0x104,1.),(0x108,512.),(0x3cc4,.01),(0x680,8.),(0x3d18,114.24),(0x3d1c,2800.),(0x124,v['previous']),(0x128,v['reference']),(0xd8,.003),(0x3ccc,.003),(0x3cc8,.01),(0x3cdc,1.),(0x3d00,1.),(0x3cec,.003)]:struct.pack_into('<f',c,o,x)
  for o,x in [(0x22dc,3),(0x2300,v['frame']),(0x22fc,v['sync']),(0x3d40,v['index']),(0x5574,2),(0x22e4,1),(0x22e8,1 if v['same_mode'] else 2),(0x3c84,6)]:struct.pack_into('<i',c,o,x)
  for o,x in [(0x4fb9,v['enabled']),(0x5994,v['priming']),(0x5995,v['saturated']),(0x3d3c,v['force']),(0x40d0,3),(0x40d1,2)]:c[o]=x
  c[0x23f4]=v.get('dynamic',False);c[0x4fb8]=v.get('dynamic_enabled',False)
  struct.pack_into('<Iff',c,0x23f8,2 if v.get('custom',False) else 0,10.,.95)
  for i,x in enumerate(v.get('damping_history',[0.]*10)):struct.pack_into('<f',c,0x2c50+i*64,x)
  for i in range(5):struct.pack_into('<i9fI',c,0x3fd8+44*i,i,.003,.003,.2 if i%2==0 else -.2,.003,.006,.009,.012,.015,.018,2)
  arrays=[[0.,.01,.01,.02,.03,.03],[1.,1.,4.,8.,15.5,512.],[1.]*6]
  for i,(o,p) in enumerate([(0x3c8c,HEAP+0x10000),(0x3c90,HEAP+0x11000),(0x3c94,HEAP+0x12000)]):struct.pack_into('<I',c,o,p);self.uc.mem_write(p,struct.pack('<6f',*arrays[i]))
  if v.get('run_wrapper',False):
   for o,x in [(0xd4,.009),(0xdc,2.),(0xe0,1.),(0xe8,.0045),(0x118,11.),(0x3c8,12.),(0x3cc,13.),(0x3d0,14.),(0x3bc,2.),(0x3c0,3.),(0x3c4,4.)]:struct.pack_into('<f',c,o,x)
   c[0x22ed]=int(v['run']);c[0xc]=1;struct.pack_into('<H',c,6,256);struct.pack_into('<3H',c,0x404,100,200,300)
  if 'policy_scene' in v:
   linear=v['policy_scene']['ae_calib']['LinearAeCtrl'];speed=v['policy_scene']['ae_calib']['CommCtrl']['AecSpeed']
   for o,x in [(0x10,linear['ToleranceIn']),(0x14,linear['ToleranceOut']),(0x2404,speed['DampOver']),(0x2408,speed['DampUnder']),(0x240c,speed['DampDark2Bright']),(0x2410,speed['DampBright2Dark'])]:struct.pack_into('<f',c,o,x)
   c[0x23ce]=int(v['alternate'])
   if v.get('bind_dynamic',False):
    d=speed['DyDamp'];c[0x23f4]=int(d['DyDampEn']);struct.pack_into('<Iff',c,0x23f8,1 if d['SlowOPType']=='RK_AIQ_OP_MODE_AUTO' else 2,d['SlowRange'],d['SlowDamp'])
   if v.get('bind_delay',False):
    d=v['policy_scene']['ae_calib']['CommCtrl']['AecDelay'];assert d['DelayType']=='DELAY_TYPE_FRAME';c[0x40d0]=d['BlackDelay'];c[0x40d1]=d['WhiteDelay']
  return c
 def run(self,v):
  c=self.setup(v)
  self.uc.mem_write(HEAP,bytes(c));self.uc.mem_write(HEAP+0x20000,struct.pack('<256I',*v['histogram']));self.symbols['controller']=0xb40c9
  if v.get('preprocess',False):
   self.uc.mem_write(HEAP+0x40cc,struct.pack('<I',HEAP+0x30000));self.uc.mem_write(HEAP+0x30000,struct.pack('<4I',HEAP+0x31000,2,HEAP+0x32000,2));self.uc.mem_write(HEAP+0x31000,struct.pack('<2f',0.,1.));self.uc.mem_write(HEAP+0x32000,struct.pack('<2f',45.,45.))
   stats=bytearray(0x3000);struct.pack_into('<3H',stats,0x2e20,int(v['measured']*256),512,768);self.uc.mem_write(HEAP+0x40000,bytes(stats))
   stack=bytearray(240);struct.pack_into('<f',stack,0,1.);struct.pack_into('<II',stack,232,HEAP+0x40000,v['frame'])
   bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
   self.actual_run_flag=v.get('full_frame',False);self.preprocessing=True;self.prepared=False;self.invoke('AecPreProcess',[HEAP,bits(v['exposure']),bits(1.),bits(1.)],stack=bytes(stack),instructions=1000000);assert self.prepared;self.preprocessing=False
   c=bytearray(self.uc.mem_read(HEAP,len(c)))
  if v.get('run_wrapper',False):
   assert not v.get('preprocess',False) or v.get('full_frame',False)
   stats=bytearray(0x3000);struct.pack_into('<256I',stats,0x788,*v['histogram']);struct.pack_into('<3H',stats,0x2e20,int(v['measured']*256),512,768);self.uc.mem_write(HEAP+0x40000,bytes(stats))
   self.running=True;self.conversions=[]
   status=self.invoke('AecRun',[HEAP,HEAP+0x60000,HEAP+0x40000],instructions=3000000)
   self.running=False;assert status==0;assert len(self.conversions)==(2 if c[0x22ed] else 0),self.conversions
  else:self.invoke('controller',[HEAP,HEAP+0x20000,256],instructions=3000000)
  self.last_run=bool(c[0x22ed]) if v.get('run_wrapper',False) else True
  after=bytearray(self.uc.mem_read(HEAP,len(c)))
  offsets=[0xd4,0xdc,0xe0,0xe8,0x12c,0x124,0x128,0xd8,0x5574]
  words=[struct.unpack_from('<I',after,o)[0] for o in offsets]+[after[0x5994]]+[struct.unpack_from('<I',after,o)[0] for o in [0x40f4,0x40f8]]+[after[o] for o in [0x40fc,0x40fd,0x23cf]]+[struct.unpack_from('<I',after,o)[0] for o in [0x3ccc,0x3cdc,0x3d00,0x3cec]]+[after[0x3d3c],after[0x5995]]
  words+=list(struct.unpack('<55I',after[0x3fd8:0x40b4]))+list(struct.unpack('<6I',self.uc.mem_read(HEAP+0x10000,24)))
  for o,n in [(0xd4,4),(0xdc,8),(0xe8,4),(0x124,12),(0xd8,4),(0x5574,4),(0x5994,2),(0x40f4,10),(0x23cf,1),(0x3ccc,4),(0x3cdc,4),(0x3d00,4),(0x3cec,4),(0x3d3c,1),(0x3fd8,220)]:c[o:o+n]=after[o:o+n]
  if v.get('dynamic',False) and v.get('dynamic_enabled',False) and (not v.get('run_wrapper',False) or c[0x22ed]):
   slot=(v['frame']+1)%10;offsets=[0x2c44+slot*64,0x2c48+slot*64,0x2c4c+slot*64]
   words+=[slot]+[struct.unpack_from('<I',after,o)[0] for o in offsets]
   for o in offsets:c[o:o+4]=after[o:o+4]
  else:words+=[4294967295,0,0,0]
  words+=[struct.unpack_from('<I',after,0x2c50+i*64)[0] for i in range(10)]
  if v.get('run_wrapper',False):
   words+=[struct.unpack_from('<I',after,0x3d40)[0]]+list(struct.unpack_from('<3H',after,0x404))+[struct.unpack_from('<I',after,0x118)[0]]+list(struct.unpack_from('<3I',after,0x3c8))
   for o,n in [(0x3d40,4),(0x404,6),(0x118,4),(0x3c8,12)]:c[o:o+n]=after[o:o+n]
  assert c==after
  return ','.join(f'{w:08x}' for w in words)
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 cases=[]
 for k in range(160):
  h=[0]*256;h[[3,120,254,255][k%4]]=1000
  cases.append(dict(histogram=h,measured=[0.,3.,40.5,45.,49.5,120.,240.][k%7],exposure=[.003,.02,.1][k%3],previous=[-.5,0.,.5][k%3],reference=[-.5,0.,.5][(k//3)%3],fps=[2.,30.][k%2],enabled=bool(k%2),same_mode=k%5!=0,priming=k%7==0,saturated=bool(k%2),force=k%3==0,index=k%20,frame=30+k,sync=28+k))
 cases=[dict(v,dynamic=called,dynamic_enabled=enabled,custom=custom,damping_history=[((i+v['index'])%7-3)*.01 for i in range(10)]) for v in cases for called,enabled,custom in [(False,False,False),(True,False,False),(True,True,False),(True,True,True)]]
 cases=[dict(v,preprocess=preprocess) for v in cases for preprocess in [False,True]]
 arm=Original(BINARY);expected=[arm.run(v) for v in cases];inputs=''.join('ae-controller '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='active standard preprocessing history checkpoint plus complete native standard linear AecClmExecute through normal return with real solver, history, delay and cached automatic route routines',limitations=['Fixed/dynamic damping, uniform selected tolerance, standard histogram mode, non-iris successful paths only; alternate control modes excluded.','Runtime limits, applied current exposure, policy and initial history remain explicit; active preprocessing run flag is controlled.','Unsigned division, signed division/remainder and imported rounding are modeled; the native control bodies execute.', 'No sensor writes, real frame association or complete AE/AWB service is introduced.'])
 (ROOT/'reverse-engineering/rkaiq/ae-controller-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
