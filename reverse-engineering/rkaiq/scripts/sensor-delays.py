#!/usr/bin/env python3
"""Compare native delay-policy configuration, including partial error state."""
import hashlib,itertools,json,struct,subprocess,sys
from differential import OriginalArm,ROOT,BINARY,HEAP,regs
class Original(OriginalArm):
 def __init__(self):
  super().__init__(BINARY);self.log=self.symbols['xcam_print_log']&~1
 def hook(self,uc,address,size,user):
  if address==self.log:
   uc.reg_write(regs.UC_ARM_REG_R0,0);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v):
  c=bytearray([0xa5]*0x300)
  struct.pack_into('<ii',c,0x270,11,10);struct.pack_into('<i',c,0x27c,12)
  for o,f in zip([0x278,0x280,0x281],v['flags']):c[o]=f
  self.uc.mem_write(HEAP,bytes(c));name=next(n for n in self.symbols if 'SensorHw18set_exp_delay_info' in n)
  status=self.invoke(name,[HEAP,v['time'],v['gain'],v['dcg']]);status=status if status<0x80000000 else status-0x100000000
  after=bytearray(self.uc.mem_read(HEAP,len(c)))
  values=[struct.unpack_from('<i',after,o)[0] for o in [0x274,0x270,0x27c]]+[after[o] for o in [0x278,0x280,0x281]]
  for o,n in [(0x270,9),(0x27c,6)]:c[o:o+n]=after[o:o+n]
  assert c==after
  return ','.join(map(str,[status,*values]))
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 cases=[dict(time=t,gain=g,dcg=d,flags=f) for t,g,d in itertools.product([-1,0,1,2,3,5],repeat=3) for f in itertools.product([False,True],repeat=3)]
 arm=Original();expected=[arm.run(v) for v in cases];inputs=''.join('sensor-delays '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='complete native set_exp_delay_info return/status and all object changes, including rejected combinations',limitations=['Logging is discarded; native policy arithmetic executes.','Negative test inputs document behavior, not supported camera settings.','SOF queues, effective-frame insertion and physical sensor latency remain separate scheduling work.'])
 (ROOT/'reverse-engineering/rkaiq/sensor-delays-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
