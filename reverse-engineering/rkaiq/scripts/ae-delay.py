#!/usr/bin/env python3
"""Compare full native linear delay helper and all context mutations."""
import hashlib,json,random,struct,subprocess,sys
from differential import OriginalArm,ROOT,BINARY,HEAP
class Original(OriginalArm):
 def run(self,v):
  context=bytearray(0x5998)
  for o,k in [(0x124,'previous'),(0x12c,'current'),(0x128,'reference')]:struct.pack_into('<f',context,o,v[k])
  for o,k in [(0x2300,'frame'),(0x40f4,'negative_start'),(0x40f8,'positive_start')]:struct.pack_into('<i',context,o,v[k])
  for o,k in [(0x4fb9,'enabled'),(0x23cf,'changed'),(0x40fc,'negative_count'),(0x40fd,'positive_count'),(0x40d0,'negative_delay'),(0x40d1,'positive_delay')]:context[o]=int(v[k])
  struct.pack_into('<II',context,0x22e4,1,1 if v['same_mode'] else 2)
  self.uc.mem_write(HEAP,bytes(context));self.symbols['delay']=0xb13b9
  result=self.invoke('delay',[HEAP,0]);assert result in [0,1]
  updated=bytearray(self.uc.mem_read(HEAP,len(context)))
  for o,n in [(0x40f4,10),(0x23cf,1)]:context[o:o+n]=updated[o:o+n]
  assert context==updated
  negative,positive=struct.unpack_from('<ii',updated,0x40f4)
  return f'{result},{updated[0x23cf]},{negative},{positive},{updated[0x40fc]},{updated[0x40fd]}'
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 rng=random.Random(613);cases=[]
 for k in range(1000):
  frame=rng.choice([0,1,10,254,255,256,1000,2147483647]);cases.append(dict(frame=frame,enabled=bool(rng.randrange(2)),same_mode=bool(rng.randrange(2)),changed=bool(rng.randrange(2)),previous=rng.choice([0.,-.5,.5]),current=rng.choice([0.,-.5,.5,-.49,.49]),reference=rng.choice([0.,-.5,.5,1.]),negative_delay=rng.choice([0,1,2,5,255]),positive_delay=rng.choice([0,1,2,5,255]),negative_start=rng.choice([0,1,frame]),positive_start=rng.choice([0,1,frame]),negative_count=rng.randrange(256),positive_count=rng.randrange(256)))
 arm=OriginalArm(BINARY);assert struct.unpack('<f',arm.uc.mem_read(0xb16e8,4))[0]==struct.unpack('<f',struct.pack('<f',.98))[0]
 arm=Original(BINARY);expected=[arm.run(v) for v in cases];inputs=''.join('ae-delay '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='complete linear AecCheckDelay helper, boolean return, all state writes and preservation of unrelated context',limitations=['Linear finite-input path; HDR excluded.','Context policy flags, frame IDs, error history and delay thresholds supplied explicitly.','This is a brightness-transition hold gate, not complete sensor-register application latency or live scheduling.'])
 (ROOT/'reverse-engineering/rkaiq/ae-delay-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
