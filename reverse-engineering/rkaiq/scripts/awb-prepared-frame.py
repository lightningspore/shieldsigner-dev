#!/usr/bin/env python3
"""Execute standard AWB preprocessor through complete native PrepareMeasureResult."""
import hashlib,json,random,runpy,struct,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,HEAP,RETURN,regs,f32
from awb_reference import OriginalAwb,RUNTIME
reference=runpy.run_path(str(Path(__file__).with_name('awb-preparation.py')))
class Original(OriginalAwb):
 def __init__(self):super().__init__(stdlib=True)
 def hook(self,uc,address,size,user):
  if address==0xd4ae0:uc.reg_write(regs.UC_ARM_REG_PC,RETURN);return
  if address==(self.symbols.get('xcam_print_log',0)&~1):uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  name=self.stubs.get(address)
  if name=='__aeabi_uidivmod':
   self.runtime.invoke(name,[uc.reg_read(regs.UC_ARM_REG_R0),uc.reg_read(regs.UC_ARM_REG_R1)])
   for r in [regs.UC_ARM_REG_R0,regs.UC_ARM_REG_R1]:uc.reg_write(r,self.runtime.uc.reg_read(r))
   uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if name in ['malloc','free']:
   a=uc.reg_read(regs.UC_ARM_REG_R0)
   if name=='malloc':
    assert 0<a<=255;pointer=self.arena;self.arena+=(a+15)&~15;self.live.add(pointer);uc.mem_write(pointer,bytes(a));uc.reg_write(regs.UC_ARM_REG_R0,pointer)
   else:assert a in self.live;self.live.remove(a)
   uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def prepare_outer(self,c,s,cal,v):
  self.arena=HEAP+0x70000;self.live=set()
  def word(b,o,n):struct.pack_into('<I',b,o,n&0xffffffff)
  def floats(b,o,*n):struct.pack_into('<'+'f'*len(n),b,o,*n)
  for o,n in [(0x28,7),(0x2c,0),(0x34,0),(0x4c,0),(0x33ac,0),(0x33b0,0),(0x369c,1),(0x33d4,9),(0x33e0,-7)]:word(c,o,n)
  c[0x3349]=v['update'];c[0x3345]=1;c[0x3346:0x3348]=b'\1\1';c[0x2ece]=0;c[0x36a0]=1;c[0x36b8]=1;floats(c,0x36b4,v['sample']);floats(c,0x3480,.5)
  struct.pack_into('<2H',c,0x2ed4,2304,1296);c[0x33b8:0x33ba]=b'\x0f\x0f';word(c,0x3478,HEAP+0x3478);word(c,0x347c,HEAP+0x3478)
  s[0x4a4]=1;word(s,0x4b4,0);word(s,0x188,0);word(s,0x158,4);word(s,0x164,4);struct.pack_into('<5I',s,0x168,0,128,1024,65536,262144);struct.pack_into('<4I',s,0x1a8,110,200,65536,65600)
  word(s,0xdc,1);floats(s,0xe0,0.);floats(s,0x100,v['outer_interval'])
  values=[0.,.01,.005,v['threshold'],150.,216.]
  for i,value in enumerate(values):self.uc.mem_write(HEAP+0x50000+i*16,struct.pack('<f',value))
  for o,i in [(0x4e4,0),(0x4ec,1),(0x4f4,2),(0x4fc,3),(0x580,0),(0x590,4),(0x588,5),(0x61c,0),(0x624,4),(0x62c,5)]:word(cal,o,HEAP+0x50000+i*16)
  for o in [0x4e8,0x584,0x620]:word(cal,o,1)
 def outer_snapshot(self,c):
  w=lambda o:struct.unpack_from('<I',c,o)[0]
  word_at=lambda a:struct.unpack('<I',self.uc.mem_read(a,4))[0]
  values=[];head=HEAP+0x3478;node=word_at(head);previous=head
  while node!=head:
   assert len(values)<32 and word_at(node+4)==previous
   values.append(word_at(node+8));previous=node;node=word_at(node)
  assert word_at(head+4)==previous and len(self.live)==len(values)
  words=[c[0x334a],w(0x33d8),w(0x33dc),w(0x33b0),w(0x33ac),w(0x33d4),w(0x33e0),w(0x3480),c[0x3345],*values]
  return ','.join(f'{n:08x}' for n in words)
def main():
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert sha==manifest['binaries'][0]['sha256'];assert hashlib.sha256(RUNTIME.read_bytes()).hexdigest()==manifest['gccRuntime']['memberSha256']
 arm=Original();rng=random.Random(0x41574246);cases=[];expected=[]
 for i in range(64):
  n=1+i%6;groups=[1,2,4][i%3]
  v=dict(_outer=True,outer_interval=i%4,seed=rng.randrange(0xffffffff),n=n,groups=groups,group=0,frames=8,indices=list(range(min(n,4))),fast=bool(i//4%2),fast_count=min(n,4),threshold=[0.,.01,10.][i//8%3],sum_mode=i%4,history=i//3%4,names=i//7%3,seen=bool(i//3%2),update=bool(i%2),mode=i%3,rotate=True,rename=bool(i//5%2),zero_grid=bool(i//7%2),zero_lights=bool(i//9%2),direct_counts=False,zero_exclusions=bool(i//11%2),sample=f32([0.,.25,1.,3.][i%4]),exclusion_kind=[rng.randrange(4) for _ in range(4)],weights=[[f32(rng.uniform(0,1)) for _ in range(3)] for _ in range(4)],fast_minus=bool(i//13%2))
  cases.append(v);expected.append(reference['run'](arm,v))
 inputs=''.join('awb-prepared-frame '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  p=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True);actual=p.stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):
   if a!=b:
    j=next((j for j,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)));raise AssertionError((i,j,cases[i],a[max(0,j-40):j+80],b[max(0,j-40):j+80]))
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')]);arm_replay='--arm' in sys.argv
 if arm_replay:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=sha,sequences=len(cases),frames=sum(v['frames'] for v in cases),mismatches=0,arm=arm_replay,scope='Persistent standard AWB preprocessing through complete PrepareMeasureResult, including numerical/luma history and complete measurement cache bytes',limitations=['Execution stops at native caller instruction 0xc4ae0 after PrepareMeasureResult returns; later gain selection/reconfiguration excluded.','Incoming frame counter is explicit per frame; outer publication/counter lifecycle remains separate.','Successful allocation, strings, logging and standard memory are explicit adapters; math and native helper bodies execute.'])
 (ROOT/'reverse-engineering/rkaiq/awb-prepared-frame-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
