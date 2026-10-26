#!/usr/bin/env python3
"""Check histogram correction against original ARM, with explicit idiv helper."""
import argparse,hashlib,json,random,struct,subprocess
from pathlib import Path
from differential import OriginalArm,ROOT,BINARY,HEAP,regs
class OriginalHistogram(OriginalArm):
 def hook(self,uc,address,size,user):
  if self.stubs.get(address)=='__aeabi_idiv':
   a,b=[struct.unpack('<i',struct.pack('<I',uc.reg_read(r)))[0] for r in [regs.UC_ARM_REG_R0,regs.UC_ARM_REG_R1]]
   assert b!=0
   result=(abs(a)//abs(b))*(-1 if (a<0)!=(b<0) else 1)
   uc.reg_write(regs.UC_ARM_REG_R0,result&0xffffffff);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,seed,count,mode,rb,green,black,gain,bypass):
  state=seed;values=[]
  for _ in range(count):state=(state*1664525+1013904223)&0xffffffff;values.append(state)
  a=HEAP;b=HEAP+0x2000
  self.uc.mem_write(a,struct.pack('<'+'I'*count,*values));self.uc.mem_write(b,b'\xa5'*(count*4))
  stack=struct.pack('<II8hI',green,count,*black,*gain,bypass)
  self.invoke('_ZN5RkCam22calcAecHistBinStatsV32EPjS0_httt19isp2x_bls_fixed_valS1_b',[a,b,mode,rb],stack=stack)
  return ','.join(f'{v:08x}' for v in struct.unpack('<'+'I'*count,self.uc.mem_read(b,count*4)))
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000);p.add_argument('--emit-dir',type=Path);args=p.parse_args()
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==sha
 arm=OriginalHistogram(BINARY);rng=random.Random(0x48495354);inputs=[];expected=[];coverage={}
 for i in range(args.cases):
  seed=rng.randrange(0xffffffff);mode=[0,2,3,4][i%4];count=[64,256][i//4%2];bypass=i//8%2
  rb=rng.randrange(0,1025);green=rng.randrange(0,4097);black=[rng.randrange(0,2048) for _ in range(4)];gain=[rng.randrange(128,2049) for _ in range(4)]
  if i%3!=0:rb=rng.randrange(0,129);green=rng.randrange(0,513);black=[rng.randrange(0,65) for _ in range(4)]
  if bypass and i%3==0:gain=[0]*4
  inputs.append(f'aehist {seed} {count} {mode} {rb} {green} '+','.join(map(str,black))+' '+','.join(map(str,gain))+f' {bypass}')
  expected.append(arm.run(seed,count,mode,rb,green,black,gain,bypass));key=f'{mode}:{count}:{bypass}';coverage[key]=coverage.get(key,0)+1
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[{'case':i,'input':inputs[i],'expected':a,'actual':b} for i,(a,b) in enumerate(zip(expected,actual)) if a!=b]
 report=dict(binarySha256=sha,seed='0x48495354',cases=len(inputs),branchCoverage=coverage,mismatchCount=len(mismatches),scope='64/256 bins; R/G/B/luma correction and bypass; complete u32 histogram outputs with wrapped counts',limitations=['Standard ARM signed-division helper is explicitly modeled with truncation toward zero; its zero-divisor path is excluded.','Finite valid correction parameters; Rust rejects invalid destination indices/divisors before mutation.','Histogram measurement correction is not the full AE decision loop.'])
 if mismatches:report['firstMismatches']=mismatches[:3]
 (ROOT/'reverse-engineering/rkaiq/ae-histogram-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not mismatches
 if args.emit_dir:
  args.emit_dir.mkdir(parents=True,exist_ok=True)
  (args.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(args.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
