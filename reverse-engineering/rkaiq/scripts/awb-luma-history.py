#!/usr/bin/env python3
"""Persistent native AWB brightness list and relative variance against Rust."""
import hashlib,json,random,struct,subprocess,sys
from differential import OriginalArm,ROOT,BINARY,HEAP,regs
UPDATE='_Z17UpdateLvValueListP9list_headii';VARIANCE='_Z21CalculateVarianceLumaP9list_headPf'
class Original(OriginalArm):
 def hook(self,uc,address,size,user):
  if self.stubs.get(address)=='malloc':
   assert uc.reg_read(regs.UC_ARM_REG_R0)==12
   pointer=self.arena;self.arena+=16;self.allocations+=1
   uc.mem_write(pointer,bytes([0xa5])*12);uc.reg_write(regs.UC_ARM_REG_R0,pointer);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def initialize(self,values):
  self.arena=HEAP+0x1000;self.allocations=0;nodes=[self.arena+i*16 for i in range(len(values))];self.arena+=len(values)*16
  self.uc.mem_write(HEAP,struct.pack('<2I',nodes[0] if nodes else HEAP,nodes[-1] if nodes else HEAP))
  for i,(node,value) in enumerate(zip(nodes,values)):self.uc.mem_write(node,struct.pack('<3I',nodes[i+1] if i+1<len(nodes) else HEAP,nodes[i-1] if i else HEAP,value))
 def snapshot(self,grew=False):
  word=lambda a:struct.unpack('<I',self.uc.mem_read(a,4))[0]
  values=[];node=word(HEAP);previous=HEAP
  while node!=HEAP:
   assert len(values)<32 and word(node+4)==previous
   values.append(word(node+8));previous=node;node=word(node)
  assert word(HEAP+4)==previous
  self.invoke(VARIANCE,[HEAP,HEAP+0x800]);return dict(values=values,variance=word(HEAP+0x800),grew=grew)
def main():
 sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert sha==json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text())['binaries'][0]['sha256']
 arm=Original(BINARY);rng=random.Random(0x4c554d41);cases=[];expected=[]
 arm.initialize([42]);node=struct.unpack('<I',arm.uc.mem_read(HEAP,4))[0];arm.invoke(UPDATE,[HEAP,43,1])
 assert struct.unpack('<2I',arm.uc.mem_read(HEAP,8))==(HEAP,node) and struct.unpack('<I',arm.uc.mem_read(node,4))[0]==node,'Singleton defect no longer matches pinned code'
 singleton_guarded=0
 for i in range(64):
  initial=[rng.choice([0,1,255,2**24+1,0xffffffff,rng.randrange(2**32)]) for _ in range(i%9)]
  if i%4==0:initial=[0]*len(initial)
  if i%4==1:initial=[255]*len(initial)
  arm.initialize(initial);events=[];results=[arm.snapshot()]
  for j in range(24):
   value=rng.choice([0,1,-1,-2**31,2**31-1,255,rng.randrange(-2**31,2**31)])
   target=[0,1,2,4,8,16,32][(i+j)%7]
   if target==1 and len(results[-1]['values'])==1:target=2;singleton_guarded+=1
   events.append(dict(value=value,target=target));before=arm.allocations
   arm.invoke(UPDATE,[HEAP,value,target]);results.append(arm.snapshot(arm.allocations>before))
  cases.append(dict(initial=initial,events=events));expected.append(results)
 inputs=''.join('awb-luma-history '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  p=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True);actual=[json.loads(s) for s in p.stdout.splitlines()];assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):
   for j,(x,y) in enumerate(zip(a,b)):assert x==y,(i,j,cases[i],x,y)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')]);arm_replay='--arm' in sys.argv
 if arm_replay:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=sha,sequences=len(cases),updates=sum(len(c['events']) for c in cases),varianceChecks=sum(len(e) for e in expected),mismatches=0,arm=arm_replay,singletonCorruptionVerified=True,singletonCasesGuarded=singleton_guarded,scope='Persistent list order, append-versus-reuse and exact f32 relative-variance bits including native zero-history NaN',limitations=['Native malloc uses an explicit 12-byte node allocator; allocation failure/lifetime cleanup excluded.','Checked Rust storage capacity is 32; negative/out-of-capacity limits and the native singleton/target-1 corruption case are rejected before mutation.','AWB outer brightness interpolation and full controller remain separate.'])
 (ROOT/'reverse-engineering/rkaiq/awb-luma-history-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
