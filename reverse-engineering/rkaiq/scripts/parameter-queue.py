#!/usr/bin/env python3
"""Recover META_OUTPUT queue/start/dequeue/return/stop branches with native ARM."""
import argparse,hashlib,json,random,struct,subprocess
from pathlib import Path
from differential import OriginalArm,ROOT,BINARY,HEAP,RETURN,regs,u32
class OriginalQueue(OriginalArm):
 def __init__(self):
  super().__init__(BINARY)
  for symbol,name in [('_ZN4XCam10V4l2Device16init_buffer_poolEv','init'),('_ZN4XCam10V4l2Device16fini_buffer_poolEv','finalize'),('_ZN4XCam9SmartLockD2Ev','unlock'),('_ZNSt6vectorIN4XCam8SmartPtrINS0_10V4l2BufferEEESaIS3_EEixEj','vector'),('_ZN4XCam8SmartPtrINS_10V4l2BufferEEaSERKS2_','assign'),('xcam_print_log','log')]:self.stubs[self.symbols[symbol]&~1]=name
  for i,name in enumerate(['ioctl','close']):
   address=RETURN+0xe000+i*16;self.uc.mem_write(address,b'\x70\x47');self.stubs[address]=name
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name is None:return
  a,b,c=[uc.reg_read(r) for r in [regs.UC_ARM_REG_R0,regs.UC_ARM_REG_R1,regs.UC_ARM_REG_R2]];result=0
  if name=='ioctl':
   if b==0xc0145608:
    self.trace.append('req:'+bytes(uc.mem_read(c,20)).hex());result=self.v['request_result']
    if result>=0:uc.mem_write(c,struct.pack('<I',self.v['returned_count']))
   elif b in [0x40045612,0x40045613]:self.trace.append(('on:' if b==0x40045612 else 'off:')+str(u32(uc.mem_read(c,4))));result=self.v['stream_result']
   elif b in [0xc044560f,0xc0445611]:
    self.trace.append(('qbuf:' if b==0xc044560f else 'dqbuf:')+bytes(uc.mem_read(c,68)).hex());result=self.v['io_result']
    if result>=0:uc.mem_write(c,bytes.fromhex(self.v['mutation' if b==0xc044560f else 'response']))
   else:raise AssertionError(hex(b))
  elif name in ['pthread_mutex_lock','pthread_mutex_unlock','unlock']:
   self.trace.append('lock' if name=='pthread_mutex_lock' else 'unlock')
  elif name in ['init','finalize','close']:
   self.trace.append(name);result=self.v['init_result'] if name=='init' else 0
  elif name=='vector':result=HEAP+0x4000+b*8
  elif name=='assign':uc.mem_write(a,bytes(uc.mem_read(b,8)));result=a
  elif name=='log':pass
  else:return super().hook(uc,address,size,user)
  uc.reg_write(regs.UC_ARM_REG_R0,result&0xffffffff);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))
 def run(self,v):
  self.v=v;self.trace=[];context=HEAP;vtable=HEAP+0x2000;pool=HEAP+0x4000;output=HEAP+0x6000
  data=bytearray([0x55]*0x200)
  for offset,value in [(0,vtable),(0x14,14),(0x1c,v['memory']),(0xfc,pool),(0x100,pool+(8*v['count'] if v['has_pool'] else 0)),(0x108,v['count']),(0x10c,v['queued']),(0x130,1)]:struct.pack_into('<I',data,offset,value)
  data[0x18]=v['cache_sync'];data[0xf8]=v['active'];self.uc.mem_write(context,bytes(data));self.uc.mem_write(vtable,bytes(0x100));self.uc.mem_write(vtable+0x30,struct.pack('<I',(RETURN+0xe000)|1));self.uc.mem_write(vtable+0x18,struct.pack('<I',(RETURN+0xe010)|1));self.uc.mem_write(output,bytes(8))
  objects=[]
  for i,record in enumerate(v['records']):
   pointer=HEAP+0x8000+i*0x200;obj=bytearray([0x66]*0x124);obj[4:72]=bytes.fromhex(record);obj[0x120]=v['buffer_queued'];struct.pack_into('<I',obj,0x114,v['initial_length']);self.uc.mem_write(pointer,bytes(obj));self.uc.mem_write(pool+i*8,struct.pack('<II',pointer,0));objects.append(bytes(obj))
  op=v['op'];symbols={'prepare':'7prepareEv','start':'5startEb','queue':'12queue_bufferERNS_8SmartPtrINS_10V4l2BufferEEEb','dequeue':'14dequeue_bufferERNS_8SmartPtrINS_10V4l2BufferEEE','return':'21return_buffer_to_poolERNS_8SmartPtrINS_10V4l2BufferEEE','stop':'4stopEv'}
  args=[context,v['prepared']] if op=='start' else [context,pool,v['locked']] if op=='queue' else [context,output] if op=='dequeue' else [context,pool] if op=='return' else [context]
  result=self.invoke('_ZN4XCam10V4l2Device'+symbols[op],args);status=struct.unpack('<i',struct.pack('<I',result))[0] if op not in ['return','stop'] else 0
  after=bytearray(self.uc.mem_read(context,len(data)));queued=u32(after[0x10c:0x110]);active=bool(after[0xf8]);requested=u32(after[0x108:0x10c]);after[0x108:0x110]=data[0x108:0x110];after[0xf8]=data[0xf8];assert bytes(after)==bytes(data),'Unexpected device context mutation'
  buffers=[]
  for i,before in enumerate(objects):
   after=bytearray(self.uc.mem_read(HEAP+0x8000+i*0x200,len(before)));buffers.append(dict(record=bytes(after[4:72]).hex(),queued=bool(after[0x120]),length=u32(after[0x114:0x118])))
   after[24:52]=before[24:52];after[0x120]=before[0x120];after[0x114:0x118]=before[0x114:0x118];assert bytes(after)==before,'Unexpected buffer object mutation'
  index=(u32(self.uc.mem_read(output,4))-HEAP-0x8000)//0x200 if op=='dequeue' and status==0 else None
  return json.dumps(dict(status=status,index=index,queued=queued,active=active,requested=requested,trace=self.trace,buffers=buffers),sort_keys=True,separators=(',',':'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000);p.add_argument('--emit-dir',type=Path);a=p.parse_args();manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert sha==next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name)
 arm=OriginalQueue();rng=random.Random(0x51554555);inputs=[];expected=[];coverage={}
 for i in range(a.cases):
  op=['queue','prepare','start','dequeue','return','stop'][i%6];count=rng.randrange(2,5);memory=rng.choice([1,2]);records=[]
  for index in range(count):
   r=bytearray(rng.randbytes(68))
   for o,n in [(0,index),(4,14),(48,memory),(56,rng.randrange(11145,16385))]:struct.pack_into('<I',r,o,n)
   records.append(r.hex())
  response=bytearray(rng.randbytes(68));struct.pack_into('<I',response,0,rng.choice([0,count-1,count+1]));struct.pack_into('<I',response,56,rng.randrange(11145,16385))
  v=dict(op=op,count=count,returned_count=rng.randrange(2,5),memory=memory,records=records,queued=rng.randrange(0,9),active=bool(i//6%2),buffer_queued=bool(i//12%2),initial_length=rng.randrange(0,20000),cache_sync=bool(i//24%2),prepared=bool(i//48%2),locked=bool(i//96%2),has_pool=bool(i//192%2),request_result=rng.choice([-22,0,2]),init_result=rng.choice([-2,0,3]),stream_result=rng.choice([-22,0,2]),io_result=rng.choice([-22,0,2]),mutation=rng.randbytes(68).hex(),response=response.hex())
  inputs.append('parameter-queue '+json.dumps(v,separators=(',',':')));expected.append(arm.run(v));key=f'{op}:{int(v["active"])}:{int(v["cache_sync"])}:{int(v["prepared"])}:{int(v["locked"])}';coverage[key]=coverage.get(key,0)+1
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[dict(case=i,input=inputs[i],expected=x,actual=y) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
 report=dict(binarySha256=sha,seed='0x51554555',cases=a.cases,mismatchCount=len(mismatches),coverage=coverage,scope='Metadata-output V4l2Device prepare/start/QBUF/DQBUF/return/stop branches: ioctl records, lock/call order, counters, active/queued flags, cached buffer fields and preservation',limitations=['Pool allocation/finalization, close, mutex/destructor and smart-pointer/vector boundaries are controlled stubs; their implementations are not proved by this suite.','Original reset, request-buffer wrapper and queue/state-control instructions execute; standard memcpy/memset are explicit helpers.','Valid metadata MMAP/USERPTR descriptors; checked Rust additionally rejects the native one-past-end dequeue index bug.','No real camera or complete ISP startup is proved by these controlled traces.'])
 if mismatches:report['firstMismatches']=mismatches[:3]
 (ROOT/'reverse-engineering/rkaiq/parameter-queue-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='coverage'},indent=2));assert not mismatches
 if a.emit_dir:
  a.emit_dir.mkdir(parents=True,exist_ok=True);(a.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(a.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
