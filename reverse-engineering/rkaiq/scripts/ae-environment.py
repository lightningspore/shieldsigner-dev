#!/usr/bin/env python3
"""Execute complete native linear environment-history correction."""
import hashlib,json,random,struct,subprocess,sys
from differential import OriginalArm,ROOT,BINARY,HEAP,regs
class Original(OriginalArm):
 def hook(self,uc,address,size,user):
  if self.stubs.get(address)=='__aeabi_idivmod':
   a=uc.reg_read(regs.UC_ARM_REG_R0);b=uc.reg_read(regs.UC_ARM_REG_R1);assert a<0x80000000 and b==5
   uc.reg_write(regs.UC_ARM_REG_R0,a//b);uc.reg_write(regs.UC_ARM_REG_R1,a%b);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v):
  c=bytearray(0x6000)
  c[0x5994]=v['priming'];struct.pack_into('<I',c,0x5574,v['count']);struct.pack_into('<f',c,0xd8,v['held']);struct.pack_into('<f',c,0xd0,v['current'])
  for o,key in [(0x3d40,'index'),(0x2300,'frame'),(0x22fc,'sync')]:struct.pack_into('<i',c,o,v[key])
  for i,r in enumerate(v['history']):
   struct.pack_into('<ff',c,0x3fd8+i*44+8,r['published'],r['error']);struct.pack_into('<6f',c,0x3fd8+i*44+16,*r['queued'])
  self.uc.mem_write(HEAP,bytes(c));self.uc.mem_write(HEAP+0x10000,struct.pack('<f',v['candidate']));self.symbols['environment']=0xb379d
  self.invoke('environment',[HEAP,HEAP+0x10000,0]);after=bytearray(self.uc.mem_read(HEAP,len(c)))
  for o,n in [(0x5994,1),(0x5574,4),(0xd8,4)]:c[o:o+n]=after[o:o+n]
  assert c==after
  return f'{struct.unpack("<I",self.uc.mem_read(HEAP+0x10000,4))[0]:08x},{struct.unpack_from("<I",after,0xd8)[0]:08x},{struct.unpack_from("<I",after,0x5574)[0]},{after[0x5994]}'
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 rng=random.Random(317);cases=[]
 for k in range(600):
  history=[dict(error=rng.choice([-.5,0.,.5]),published=.001*(i+1),queued=[.01*(i+1)*(j+1) for j in range(6)]) for i in range(5)]
  cases.append(dict(history=history,priming=k%9==0,count=k%7,index=k%20,frame=rng.choice([0,10,100,2147483647]),sync=rng.choice([0,9,99]),current=.003,candidate=rng.choice([.0001,.004,.03,.4]),held=.02))
 arm=Original(BINARY);expected=[arm.run(v) for v in cases];inputs=''.join('ae-environment '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  actual=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='complete linear AecClmExpChkForEnv return path, candidate/state updates and unrelated context preservation',limitations=['Finite linear history, queue counts 0 through 6 and nonnegative bounded ring index; HDR excluded.','History population, queue-to-frame association and physical sensor delays are explicit inputs, not established by this helper.','Standard signed division/remainder is modeled; no live feedback writes are introduced.'])
 (ROOT/'reverse-engineering/rkaiq/ae-environment-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
