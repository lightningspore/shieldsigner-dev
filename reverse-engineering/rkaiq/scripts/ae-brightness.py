#!/usr/bin/env python3
"""Execute native histogram/damping prefix before environment adjustment."""
import hashlib,json,random,runpy,struct,subprocess,sys
from differential import ROOT,BINARY,HEAP,RETURN,regs
Base=runpy.run_path(str(__import__('pathlib').Path(__file__).with_name('ae-decision.py')))['OriginalDecision']
class Original(Base):
 def hook(self,uc,address,size,user):
  if address==0xb4446:
   ptr=uc.reg_read(regs.UC_ARM_REG_R5)
   self.result=f'{struct.unpack("<I",uc.mem_read(ptr,4))[0]:08x},{struct.unpack("<I",uc.mem_read(HEAP+0x12c,4))[0]:08x},{uc.mem_read(HEAP+0x5995,1)[0]}'
   uc.reg_write(regs.UC_ARM_REG_PC,RETURN);return
  super().hook(uc,address,size,user)
 def run(self,v):
  self.iterations=0;self.result=None;c=bytearray(0x6000)
  for o,key in [(0x130,'target'),(0x114,'measured'),(0xd0,'exposure'),(0x10,'tolerance'),(0xf4,'minimum'),(0xf8,'maximum'),(0x2404,'over'),(0x2408,'under'),(0x5988,'fps')]:struct.pack_into('<f',c,o,v[key])
  c[0x5995]=v['saturated'];struct.pack_into('<I',c,0x22dc,3)
  self.uc.mem_write(HEAP,bytes(c));self.uc.mem_write(HEAP+0x10000,struct.pack('<256I',*v['histogram']));self.symbols['brightness']=0xb40c9
  self.invoke('brightness',[HEAP,HEAP+0x10000,256],instructions=2000000);assert self.result is not None
  return self.result
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 rng=random.Random(19);cases=[]
 for n in range(160):
  h=[0]*256
  if n%4==0:h=[100]*256
  else:h[[0,3,120,254,255][n%5]]=1000
  cases.append(dict(histogram=h,target=45.,measured=[0.,3.,40.5,45.,49.5,120.,240.][n%7],exposure=rng.uniform(.001,.1),tolerance=[0.,10.][n%2],minimum=.00005,maximum=15.,saturated=bool(n%2),under=[0.,.3,.5,1.][n%4],over=[0.,.4,.7,1.][n%4],fps=[2.,15.,30.,60.][n%4]))
 arm=Original();expected=[arm.run(v) for v in cases];inputs=''.join('ae-brightness '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  actual=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='native standard linear AecClmExecute prefix through histogram solver, deadband, fixed directional damping, saturation cap and exposure clamp',limitations=['Stops at ELF 0xa4446 before environment-history adjustment; not complete AecClmExecute.','Dynamic damping, alternate tolerance/policy modes, environment corrections, delay/route dispatch and live scheduling remain separate.','Histogram division/logging boundaries inherited from solver harness.'])
 (ROOT/'reverse-engineering/rkaiq/ae-brightness-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
