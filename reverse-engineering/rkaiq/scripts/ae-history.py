#!/usr/bin/env python3
"""Compare native current-history and queued-exposure publication routines."""
import hashlib,json,random,runpy,struct,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,HEAP
Base=runpy.run_path(str(Path(__file__).with_name('ae-environment.py')))['Original']
class Original(Base):
 def run(self,v):
  c=bytearray(0x6000)
  for i,r in enumerate(v['history']):struct.pack_into('<i9fI',c,0x3fd8+44*i,r['frame'],r['current'],r['published'],r['error'],*r['queued'],r['count'])
  struct.pack_into('<I',c,0x3d40,v['index']);struct.pack_into('<i',c,0x2300,v['frame'])
  for o,key in [(0xd0,'current'),(0xd4,'published'),(0x12c,'error')]:struct.pack_into('<f',c,o,v[key])
  struct.pack_into('<I',c,0x5574,len(v['queue']))
  for i,p in enumerate(v['queue']):struct.pack_into('<4f',c,0x4fbc+0xf4*i,p[0],p[1],1.,p[2])
  self.uc.mem_write(HEAP,bytes(c));self.symbols['record_current']=0xb0f2d
  self.invoke('record_current',[HEAP,0]);self.invoke('AecClmExpSetForEnv',[HEAP])
  after=bytearray(self.uc.mem_read(HEAP,len(c)));c[0x3fd8:0x40b4]=after[0x3fd8:0x40b4];assert c==after
  return ','.join(f'{w:08x}' for w in struct.unpack('<55I',after[0x3fd8:0x40b4]))
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 rng=random.Random(418);cases=[]
 for index in range(20):
  for count in range(7):
   h=[dict(frame=i,current=.002*(i+1),published=.003*(i+1),error=.1*i,queued=[.01*(i+1)*(j+1) for j in range(6)],count=6) for i in range(5)]
   queue=[[rng.uniform(.0001,.03),rng.uniform(1,32),rng.uniform(1,4)] for _ in range(count)]
   cases.append(dict(index=index,frame=index+25,current=.003,error=[-.5,0.,.5][index%3],published=.02,queue=queue,history=h))
 arm=Original(BINARY);expected=[arm.run(v) for v in cases];inputs=''.join('ae-history '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='complete linear current-history writer and non-iris queued-exposure publisher, all 220 history bytes and unrelated context preservation',limitations=['Linear non-iris, zero through six explicit queued real exposure records.','Ring advancement and queue association with physical frames remain caller obligations.','Signed division/remainder modeled; no live AE scheduler is introduced.'])
 (ROOT/'reverse-engineering/rkaiq/ae-history-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
