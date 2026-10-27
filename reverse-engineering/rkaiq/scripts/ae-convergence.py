#!/usr/bin/env python3
"""Native linear AecGetProcResults convergence-flag publication checkpoint."""
import hashlib,itertools,json,random,struct,subprocess,sys
from unicorn import UC_HOOK_MEM_WRITE
from differential import OriginalArm,ROOT,BINARY,HEAP,RETURN,regs,f32
class Original(OriginalArm):
 def __init__(self):
  super().__init__(BINARY);self.uc.hook_add(UC_HOOK_MEM_WRITE,self.store,begin=HEAP+0x4fb8,end=HEAP+0x4fb9)
 def store(self,uc,access,address,size,value,user):
  assert (address,size) in [(HEAP+0x4fb8,2),(HEAP+0x4fb9,1)]
  self.writes.append((address-HEAP,size,value));uc.reg_write(regs.UC_ARM_REG_PC,RETURN);uc.emu_stop()
 def run(self,v):
  c=bytearray(0x6000);c[0x4fb8]=v['dynamic'];c[0x4fb9]=v['gating']
  for key,time,gain,isp in [('effective',0x2434,0x2438,0x2420),('proposed',0xec,0xf0,0xe0),('published',0x4c50,0x4c54,0x4c3c)]:
   a,b,x=v[key];struct.pack_into('<I',c,time,a);struct.pack_into('<I',c,gain,b);struct.pack_into('<f',c,isp,x)
  self.uc.mem_write(HEAP,bytes(c));self.uc.mem_write(HEAP+0x20000,struct.pack('<4I',0,0,HEAP+0x30000,HEAP+0x31000));self.writes=[]
  self.invoke('AecGetProcResults',[HEAP,HEAP+0x20000],instructions=1000000)
  assert len(self.writes)==1
  after=bytes(self.uc.mem_read(HEAP,len(c)));assert after[:0x4fb8]==c[:0x4fb8] and after[0x4fba:]==c[0x4fba:]
  return f'{after[0x4fb8]},{after[0x4fb9]}'
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 native=Original();assert struct.unpack('<d',native.uc.mem_read(0xc2ac8,8))[0]==.001
 cases=[]
 for dynamic,gating in itertools.product([0,1,3],[0,1,4]):
  for baseline in [0.,1.,16.,32.]:
   for value in [baseline,f32(baseline*.999),f32(baseline*1.001),f32(baseline*.9989),f32(baseline*1.0011)]:
    for who in ['effective','proposed','published']:
     v=dict(dynamic=dynamic,gating=gating,effective=[122,128,baseline],proposed=[122,128,baseline],published=[122,128,baseline]);v[who][2]=value;cases.append(v)
  for who in ['effective','proposed','published']:
   for slot in [0,1]:
    v=dict(dynamic=dynamic,gating=gating,effective=[122,128,1.],proposed=[122,128,1.],published=[122,128,1.]);v[who][slot]+=1;cases.append(v)
 rng=random.Random(0x434f4e56)
 for _ in range(300):
  x=f32(rng.uniform(.1,32));v=dict(dynamic=rng.randrange(4),gating=rng.randrange(4),effective=[122,128,x],proposed=[122,128,f32(x*rng.uniform(.998,1.002))],published=[122,128,f32(x*rng.uniform(.998,1.002))]);cases.append(v)
 expected=[native.run(v) for v in cases];inputs=''.join('ae-convergence '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='linear AecGetProcResults convergence flag store checkpoint, sensor-code equality and ISP-gain tolerance',limitations=['Native execution stops after the flag store, not full result publication.','Effective/proposed/prior-published exposure records are seeded explicitly; their stream association remains external.','Nonnegative finite gain domain, linear mode only; unrelated context bytes checked for preservation.'])
 (ROOT/'reverse-engineering/rkaiq/ae-convergence-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
