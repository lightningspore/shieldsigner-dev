#!/usr/bin/env python3
"""Execute original gamma/CSM/CGC dispatcher bodies, controlling only typed casts."""
import json, struct, subprocess, random, hashlib
from differential import OriginalArm, ROOT, BINARY, HEAP, regs
class OriginalColor(OriginalArm):
 def __init__(self):
  super().__init__(BINARY)
  for name, address in self.symbols.items():
   if 'SharedItemBaseEE12get_cast_ptr' in name:
    self.stubs[address & ~1] = 'color-cast'
 def hook(self, uc, address, size, user):
  if self.stubs.get(address) == 'color-cast':
   uc.reg_write(regs.UC_ARM_REG_R0, HEAP+0x40000)
   uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR)); return
  super().hook(uc,address,size,user)
 def run(self,v):
  kind=v['kind']; mode=v['mode']
  if kind=='gamma':
   record=struct.pack('<IIII49I', int(mode!=0),v['segment'],int(v['dense']),v['offset'],*v['curve']); type_id=18
  elif kind=='csm':
   record=struct.pack('<iBBBB9f',mode,1,2,3,0,*v['coefficients']);type_id=21
  else:record=struct.pack('<iBBxx',mode,1,0);type_id=22
  context=HEAP;params=HEAP+0x10000;source=HEAP+0x20000;smart=HEAP+0x30000;proxy=HEAP+0x40000;vtable=HEAP+0x5000c
  self.uc.mem_write(context,bytes(0x3000));self.uc.mem_write(context,struct.pack('<I',vtable));self.uc.mem_write(vtable-12,bytes(4))
  self.uc.mem_write(params,bytes([0x5a])*11145);self.uc.mem_write(source,bytes(8)+record)
  self.uc.mem_write(smart,struct.pack('<II',proxy,0));self.uc.mem_write(proxy,bytes(0x100));self.uc.mem_write(proxy+100,struct.pack('<I',type_id));self.uc.mem_write(proxy+0x6c,struct.pack('<I',source))
  assert self.invoke('_ZN5RkCam11Isp32Params24convert3aResultsToIspCfgERN4XCam8SmartPtrINS_14SharedItemBaseEEEPvb',[context,smart,params,0])==1
  return bytes(self.uc.mem_read(params,11145)).hex()
def main():
 rng=random.Random(0x434f4c);cases=[]
 for kind in ['gamma','csm','cgc']:
  for i in range(40):
   cases.append(dict(kind=kind,mode=i%4,segment=i%3,dense=bool(i%2),offset=rng.randrange(65536),curve=[rng.randrange(65536) for _ in range(49)],coefficients=[rng.uniform(-2,2) for _ in range(9)]))
 arm=OriginalColor();expected=[arm.run(v) for v in cases]
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input=''.join('isp-color '+json.dumps(v,separators=(',',':'))+'\n' for v in cases),text=True,capture_output=True,check=True).stdout.splitlines()
 assert len(actual)==len(expected)
 for i,(x,y) in enumerate(zip(expected,actual)):
  if x!=y:
   offsets=[j for j,(a,b) in enumerate(zip(bytes.fromhex(x),bytes.fromhex(y))) if a!=b]
   raise AssertionError((i,cases[i],offsets[:30]))
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,seed='0x434f4c',scope='Full 11145-byte output; selected gamma/CSM/CGC dispatcher branches; controlled valid typed casts',limitations=['Calibration selection and AgammaProcessing are not covered.', 'No live ISP application or image quality qualification.', 'Finite CSM coefficients are restricted by the Rust API to magnitude <=255; native out-of-domain conversions are outside this comparison.'])
 (ROOT/'reverse-engineering/rkaiq/isp-color-equivalence.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main()
