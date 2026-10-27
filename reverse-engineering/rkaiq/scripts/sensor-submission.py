#!/usr/bin/env python3
"""Native ordinary exposure-batch copying and pending-list replacement."""
import hashlib,json,random,runpy,struct,subprocess,sys
from pathlib import Path
from differential import OriginalArm,ROOT,BINARY,HEAP,regs
Writer=runpy.run_path(str(Path(__file__).with_name('sensor-linear.py')))['OriginalSensor']
SYMBOL='_ZN5RkCam8SensorHw17setExposureParamsERN4XCam8SmartPtrINS_15SharedItemProxyI19rk_aiq_isp_params_tINS_24RKAiqAecExpInfoWrapper_sEEEEEE'
class Original(OriginalArm):
 def __init__(self):
  super().__init__(BINARY);self.actions={};self.pool_count=0;self.node_count=0;self.map={};self.insert_key=None;self.written=None;self.writer=Writer();self.fail=0;self.trace=None
  for name,address in self.symbols.items():
   if 'RKAiqSensorExpInfo_t' in name:
    if 'aSERKS5_' in name or 'C1ERKS5_' in name:self.actions[address&~1]='copy'
    elif '7releaseEv' in name:self.actions[address&~1]='release'
    elif 'set_pointer' in name:self.actions[address&~1]='set'
    elif 'SharedItemPool' in name and 'get_item' in name:self.actions[address&~1]='item'
   if 'RKAiqSensorExpInfo_t' in name and '5eraseB5cxx11' in name:self.actions[address&~1]='erase'
   if 'RKAiqSensorExpInfo_t' in name and 'ixEOj' in name:self.actions[address&~1]='insert'
   if 'RKAiqSensorExpInfo_t' in name and 'listISt4pair' in name and 'pop_front' in name:self.actions[address&~1]='pop'
   if 'SensorHw23setLinearSensorExposure' in name:self.actions[address&~1]='write'
   if 'SensorHw13setSensorDpcc' in name:self.actions[address&~1]='ignore'
   if 'BufferPool16has_free_buffersEv' in name:self.actions[address&~1]='free-buffer'
   if 'SmartLockD2Ev' in name or name=='xcam_print_log':self.actions[address&~1]='ignore'
  self.uc.mem_write(HEAP,bytes(0x300));header=HEAP+0x168
  self.uc.mem_write(header,struct.pack('<II',header,header))
  self.uc.mem_write(HEAP+0x284,struct.pack('<I',HEAP+0x80000))
  for o in [0x240,0x24c]:self.uc.mem_write(HEAP+o,struct.pack('<II',HEAP+o,HEAP+o))
  self.uc.mem_write(HEAP+0x190,struct.pack('<I',0xffffffff));self.uc.mem_write(HEAP+0x274,struct.pack('<i',2))
  self.uc.mem_write(HEAP+0x4000,struct.pack('<II',HEAP+0x8000,0));self.uc.mem_write(HEAP+0x8000+0x6c,struct.pack('<I',HEAP+0x10000))
 def hook(self,uc,address,size,user):
  action=self.actions.get(address);name=self.stubs.get(address)
  a,b,c=[uc.reg_read(r) for r in [regs.UC_ARM_REG_R0,regs.UC_ARM_REG_R1,regs.UC_ARM_REG_R2]]
  if name in ('pthread_mutex_lock','pthread_mutex_unlock','_ZdlPv'):action='ignore'
  elif name=='_Znwj':action='node'
  elif name and '_List_node_base7_M_hook' in name:action='hook'
  elif name and '_List_node_base9_M_unhook' in name:action='unhook'
  if action is None:return super().hook(uc,address,size,user)
  result=0
  if action=='copy':
   try:uc.mem_write(a,bytes(uc.mem_read(b,8)));result=a
   except Exception as error:raise AssertionError(('copy',hex(address),hex(a),hex(b),[n for n,p in self.symbols.items() if (p&~1)==address])) from error
  elif action=='release':uc.mem_write(a,bytes(8))
  elif action=='set':uc.mem_write(a,struct.pack('<II',b,c))
  elif action=='free-buffer':result=1
  elif action=='item':
   i=self.pool_count;self.pool_count+=1;proxy=HEAP+0x30000+i*0x100;payload=HEAP+0x40000+i*0x200;assert self.pool_count<100
   uc.mem_write(proxy,bytes(0x100));uc.mem_write(proxy+0x6c,struct.pack('<II',payload,0));uc.mem_write(payload,bytes([0xa5])*0x10c);uc.mem_write(a,struct.pack('<II',proxy,0))
  elif action=='erase':
   del self.map[min(self.map)];self.sync_map()
  elif action=='insert':
   self.insert_key=struct.unpack('<I',uc.mem_read(b,4))[0];result=HEAP+0x78000;uc.mem_write(result,bytes(8))
  elif action=='write':
   record=bytes(uc.mem_read(b,244));self.written=record.hex();word=lambda o:struct.unpack_from('<I',record,o)[0]
   dcg=struct.unpack_from('<i',record,20)[0]
   self.trace=self.writer.run(1360,1296,word(232),dcg,word(36),word(40),word(32),False,0,self.fail)
   result=int(self.trace.split('|')[1])&0xffffffff
  elif action=='pop':
   node=struct.unpack('<I',uc.mem_read(a,4))[0];nxt,previous=struct.unpack('<II',uc.mem_read(node,8));uc.mem_write(previous,struct.pack('<I',nxt));uc.mem_write(nxt+4,struct.pack('<I',previous));count=struct.unpack('<I',uc.mem_read(a+8,4))[0];assert count>0;uc.mem_write(a+8,struct.pack('<I',count-1))
  elif action=='node':
   assert a==0x14;result=HEAP+0x60000+self.node_count*0x20;self.node_count+=1;assert self.node_count<100;uc.mem_write(result,bytes(32))
  elif action=='hook':
   previous=struct.unpack('<I',uc.mem_read(b+4,4))[0];uc.mem_write(a,struct.pack('<II',b,previous));uc.mem_write(previous,struct.pack('<I',a));uc.mem_write(b+4,struct.pack('<I',a))
  elif action=='unhook':
   nxt,previous=struct.unpack('<II',uc.mem_read(a,8));uc.mem_write(previous,struct.pack('<I',nxt));uc.mem_write(nxt+4,struct.pack('<I',previous))
  uc.reg_write(regs.UC_ARM_REG_R0,result);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))
 def sync_map(self):
  header=HEAP+0x178;nodes=[]
  for i,(frame,proxy) in enumerate(sorted(self.map.items())):
   node=HEAP+0x70000+i*32;nodes.append(node);self.uc.mem_write(node,struct.pack('<8I',1,header,0,0,frame,proxy,0,0))
  self.uc.mem_write(HEAP+0x180,struct.pack('<I',nodes[0] if nodes else header));self.uc.mem_write(HEAP+0x188,struct.pack('<I',len(nodes)))
 def seed(self,record):
  proxy=HEAP+0x28000;payload=HEAP+0x29000
  self.uc.mem_write(proxy+0x6c,struct.pack('<II',payload,0));self.uc.mem_write(payload,bytes(0x10c));self.uc.mem_write(payload+4,record)
  for o in [0x258,0x260,0x268]:self.uc.mem_write(HEAP+o,struct.pack('<II',proxy,0))
  self.map={0:proxy};self.sync_map()
 def exposure(self,proxy):
  p=struct.unpack('<I',self.uc.mem_read(proxy+0x6c,4))[0];return bytes(self.uc.mem_read(p+4,244)).hex()
 def sof(self,frame):
  self.written=None;self.insert_key=None;symbol=next(n for n in self.symbols if 'SensorHw10handle_sofExj' in n)
  status=self.invoke(symbol,[HEAP,0,0,0],stack=struct.pack('<I',frame),instructions=2_000_000);status=status if status<0x80000000 else status-0x100000000
  if self.insert_key is not None:
   self.map[self.insert_key]=struct.unpack('<I',self.uc.mem_read(HEAP+0x78000,4))[0];self.sync_map()
  current=struct.unpack('<I',self.uc.mem_read(HEAP+0x258,4))[0]
  return dict(status=status,trace=self.trace if self.written else None,pending=self.pending(),current=self.exposure(current),written=self.written,effective=[dict(frame=k,record=self.exposure(v)) for k,v in sorted(self.map.items())])
 def submit(self,main,selected):
  wrapper=bytearray(0xc00);wrapper[8:8+244]=bytes.fromhex(main)
  struct.pack_into('<I',wrapper,0x618,len(selected))
  for i,r in enumerate(selected):wrapper[0x61c+244*i:0x61c+244*(i+1)]=bytes.fromhex(r)
  wrapper[0xbd8:0xbe8]=bytes(range(16));self.uc.mem_write(HEAP+0x10000,bytes(wrapper))
  assert self.invoke(SYMBOL,[HEAP,HEAP+0x4000],instructions=2_000_000)==0
  after=bytes(self.uc.mem_read(HEAP+0x10000,len(wrapper)));assert after[8:8+244]==wrapper[8:8+244]
  assert struct.unpack_from('<I',after,0x618)[0]==0
  assert after[0xfc]==0
  return self.pending()
 def pending(self):
  result=[];header=HEAP+0x168;node=struct.unpack('<I',self.uc.mem_read(header,4))[0]
  while node!=header:
   assert len(result)<32
   nxt,_,proxy,_=struct.unpack('<4I',self.uc.mem_read(node,16));payload=struct.unpack('<I',self.uc.mem_read(proxy+0x6c,4))[0]
   assert bytes(self.uc.mem_read(payload+0xf8,16))==bytes(range(16))
   result.append(dict(first=bool(self.uc.mem_read(node+16,1)[0]),record=bytes(self.uc.mem_read(payload+4,244)).hex()));node=nxt
  assert len(result)==struct.unpack('<I',self.uc.mem_read(HEAP+0x170,4))[0]
  return result

def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 rng=random.Random(0x42415443);cases=[];expected=[]
 for k in range(12):
  native=Original();native.fail=k%5;native.seed(bytes(244));steps=[];answers=[];frame=0
  for step,count in enumerate([3,0,5,2,1,6,0,4]):
   main=rng.randbytes(244);selected=[rng.randbytes(244).hex() for _ in range(count)]
   sofs=[] if (step+k)%3==0 else [frame+1];frame+=len(sofs)
   steps.append(dict(main=main.hex(),selected=selected,sofs=sofs,fail=k%5));pending=native.submit(main.hex(),selected);answers.append(dict(pending=pending,sofs=[native.sof(n) for n in sofs]))
  cases.append(steps);expected.append(answers)
 inputs=''.join('sensor-submission '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  r=subprocess.run(command,input=inputs,text=True,capture_output=True)
  if r.returncode:raise RuntimeError(r.stderr)
  actual=[json.loads(line) for line in r.stdout.splitlines()];assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,next((j for j,(x,y) in enumerate(zip(a,b)) if x!=y),-1))
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,sequences=len(cases),submissions=sum(len(v) for v in cases),sofEvents=sum(len(step['sofs']) for v in cases for step in v),writerCalls=sum(e['written'] is not None for sequence in expected for step in sequence for e in step['sofs']),writerFailures=sum(e['status']!=0 for sequence in expected for step in sequence for e in step['sofs']),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='Complete native ordinary SensorHw::setExposureParams queue path: 244-byte exposure assembly, first-entry markers, replacement of old intermediate entries and consumed input count, interleaved with real native handle_sof and isolated native linear sensor-writer execution. Native DPCC side payload and input-count reset also asserted.',limitations=['Pool allocation, smart-pointer operations, C++ list links, map slots, locking, delete, DPCC execution and logs are modeled boundaries; native queue/SOF control flow executes. Native sensor writer executes separately with descriptor/ioctl callbacks, including injected failures.','Submission success paths only, sensor already initialized, ordinary non-custom-I2C and non-test mode. Startup immediate writes and pool failures remain separate.','Rust pending capacity is explicitly 32 with preflight rejection; native allocation-failure partial mutation is not emulated.','No sensor writes, physical exposure timing or live feedback qualification.'])
 (ROOT/'reverse-engineering/rkaiq/sensor-submission-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
