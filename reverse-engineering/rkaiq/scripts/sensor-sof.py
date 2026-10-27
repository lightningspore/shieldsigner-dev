#!/usr/bin/env python3
"""Execute native ordinary unsplit SOF scheduler with explicit container/I/O boundaries."""
import hashlib,json,struct,subprocess,sys
from differential import OriginalArm,ROOT,BINARY,HEAP,regs
class Original(OriginalArm):
 def __init__(self):
  super().__init__(BINARY);self.actions={}
  for n,p in self.symbols.items():
   if 'RKAiqSensorExpInfo_t' in n:
    if 'aSERKS5_' in n:self.actions[p&~1]='assign'
    elif 'SharedItemProxy' in n and '7releaseEv' in n:self.actions[p&~1]='release'
    elif '5eraseB5cxx11' in n:self.actions[p&~1]='erase'
    elif 'ixEOj' in n:self.actions[p&~1]='insert'
    elif 'listISt4pair' in n and 'pop_front' in n:self.actions[p&~1]='pop'
   if 'SensorHw23setLinearSensorExposureEP17RKAiqAecExpInfo_s' in n:self.actions[p&~1]='write'
   if 'SensorHw13setSensorDpcc' in n:self.actions[p&~1]='dpcc'
  self.actions[self.symbols['xcam_print_log']&~1]='log'
 def sync_map(self):
  header=HEAP+0x178
  nodes=[]
  for i,(key,value) in enumerate(sorted(self.map.items())):
   node=HEAP+0x60000+i*32;nodes.append(node);self.uc.mem_write(node,struct.pack('<8I',1,header,0,0,key,self.obj(value),0,0))
  for o,x in [(0x180,nodes[0] if nodes else header),(0x188,len(nodes))]:self.uc.mem_write(HEAP+o,struct.pack('<I',x))
 def obj(self,id):return HEAP+0x10000+id*0x200
 def hook(self,uc,address,size,user):
  action=self.actions.get(address);name=self.stubs.get(address)
  if name in ['pthread_mutex_lock','pthread_mutex_unlock']:action='lock'
  if action is None:return super().hook(uc,address,size,user)
  a=uc.reg_read(regs.UC_ARM_REG_R0);b=uc.reg_read(regs.UC_ARM_REG_R1);out=a
  if action=='assign':uc.mem_write(a,bytes(uc.mem_read(b,8)))
  elif action=='release':uc.mem_write(a,bytes(8))
  elif action=='pop':
   assert a==HEAP+0x168;node=struct.unpack('<I',uc.mem_read(a,4))[0];nextnode=struct.unpack('<I',uc.mem_read(node,4))[0];uc.mem_write(a,struct.pack('<I',nextnode))
  elif action=='erase':
   del self.map[min(self.map)];self.sync_map()
  elif action=='insert':
   key=struct.unpack('<I',uc.mem_read(b,4))[0]
   # Native assignment follows immediately; keep a stable slot then collect it.
   self.insert_key=key;out=HEAP+0x70000;uc.mem_write(out,bytes(8))
  elif action=='write':
   self.written=(b-HEAP-0x10000-0x84)//0x200;assert self.written>=1
   out=0xfffffffb if self.written==self.fail else 0
  else:out=0
  uc.reg_write(regs.UC_ARM_REG_R0,out);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))
 def run(self,v):
  self.map={0:1};self.fail=v['fail'];c=bytearray(0x300)
  for o in [0x168,0x240,0x24c]:struct.pack_into('<II',c,o,HEAP+o,HEAP+o)
  struct.pack_into('<I',c,0x190,0xffffffff);struct.pack_into('<i',c,0x274,v['delay'])
  for o in [0x258,0x260,0x268]:struct.pack_into('<II',c,o,self.obj(1),0)
  c[0x2bf]=v['shorten'];c[0x2c4]=v['all'];struct.pack_into('<I',c,0x2c0,v['designated'])
  for id in set([1,*v['requests']]):
   ptr=self.obj(id);ucdata=bytearray(0x200);struct.pack_into('<I',ucdata,0x6c,ptr+0x80);self.uc.mem_write(ptr,bytes(ucdata))
  nodes=[HEAP+0x50000+i*32 for i in range(len(v['requests']))]
  if nodes:struct.pack_into('<I',c,0x168,nodes[0])
  for i,(node,id) in enumerate(zip(nodes,v['requests'])):self.uc.mem_write(node,struct.pack('<8I',nodes[i+1] if i+1<len(nodes) else HEAP+0x168,0,self.obj(id),0,0,0,0,0))
  self.uc.mem_write(HEAP,bytes(c));self.sync_map();results=[]
  symbol=next(n for n in self.symbols if 'SensorHw10handle_sofExj' in n)
  for frame in v['frames']:
   self.written=0;self.insert_key=None
   status=self.invoke(symbol,[HEAP,0,0,0],stack=struct.pack('<I',frame),instructions=1000000);status=status if status<0x80000000 else status-0x100000000
   if self.insert_key is not None:
    ptr=struct.unpack('<I',self.uc.mem_read(HEAP+0x70000,4))[0];self.map[self.insert_key]=(ptr-HEAP-0x10000)//0x200;self.sync_map()
   current=(struct.unpack('<I',self.uc.mem_read(HEAP+0x258,4))[0]-HEAP-0x10000)//0x200
   results.append(f'{status},{frame},{current},{self.written}:'+ ';'.join(f'{k}={v}' for k,v in sorted(self.map.items())))
  return '|'.join(results)
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 cases=[]
 for delay in [0,1,2,5]:
  for shorten,allframes,designated in [(False,False,0),(True,False,2),(True,True,0)]:
   for frames,requests in [(list(range(1,18)),list(range(2,17))),([1,1,2,3,4],[2,3,4]),([4294967294,4294967295,0,1,2],[2,3,4,5]),([1,2,3],[])]:
    for fail in [0,3]:cases.append(dict(delay=delay,shorten=shorten,all=allframes,designated=designated,frames=frames,requests=requests,fail=fail))
 cases.append(dict(delay=2,shorten=False,all=False,designated=0,frames=list(range(1,39)),requests=list(range(2,34)),fail=17))
 arm=Original();expected=[arm.run(v) for v in cases];inputs=''.join('sensor-sof '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='native ordinary unsplit linear handle_sof through normal return: dequeue/write decisions, effective frame keys, retention, current snapshot and writer errors',limitations=['C++ containers, smart-pointer ownership, locking, DPCC and sensor writer are modeled boundaries.','Split gain/DCG, HDR, mirror changes, internal split-I2C path and native queue capacity are excluded.','Fixed Rust pending capacity is 32; effective records include failed writer attempts and do not establish physical application.'])
 (ROOT/'reverse-engineering/rkaiq/sensor-sof-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
