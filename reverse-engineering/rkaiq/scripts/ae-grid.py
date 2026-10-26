#!/usr/bin/env python3
"""Compare corrected AE0 grid/weighted mean with original ARM instructions."""
import argparse,json,math,random,struct,subprocess,hashlib
from differential import OriginalArm,ROOT,BINARY,HEAP,regs,f32,u32
class OriginalGrid(OriginalArm):
 def hook(self,uc,address,size,user):
  if self.stubs.get(address)=='roundf':
   x=struct.unpack('<f',struct.pack('<I',uc.reg_read(regs.UC_ARM_REG_S0)))[0]
   rounded=math.floor(x+.5) if x>=0 else math.ceil(x-.5)
   uc.reg_write(regs.UC_ARM_REG_S0,u32(struct.pack('<f',rounded)));uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,seed,selection,range_,black,gain,mean):
  state=seed
  def next():
   nonlocal state
   state=(state*1664525+1013904223)&0xffffffff;return state
  raw=[next() for _ in range(25)];initial=[next()>>16 for _ in range(100)];weights=bytes(next()>>24 for _ in range(25))
  a=HEAP;b=HEAP+0x1000;c=HEAP+0x2000;d=HEAP+0x3000
  self.uc.mem_write(a,struct.pack('<25I',*raw));self.uc.mem_write(b,struct.pack('<100H',*initial));self.uc.mem_write(c,struct.pack('<H',mean));self.uc.mem_write(d,weights)
  stack=struct.pack('<ii8h',selection,range_,*black,*gain)
  self.invoke('_ZN5RkCam22calcAecLiteWinStatsV32EP20isp32_rawaelite_statP14rawaelite_statPtPhaa19isp2x_bls_fixed_valS6_',[a,b,c,d],stack=stack)
  return ','.join(map(str,struct.unpack('<100H',self.uc.mem_read(b,200))))+':'+str(struct.unpack('<H',self.uc.mem_read(c,2))[0])
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000);p.add_argument('--emit-dir',type=__import__('pathlib').Path);args=p.parse_args()
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==sha
 arm=OriginalGrid(BINARY);rng=random.Random(0x41454752);inputs=[];expected=[]
 for i in range(args.cases):
  seed=rng.randrange(0xffffffff);selection=[0,1,2,4,8,14][i%6];range_=(i//6)%2
  black=[rng.randrange(-4096,4097) if i%3==0 else rng.randrange(-64,257) for _ in range(4)];gain=[rng.choice([0,256,32767,-32768,rng.randrange(-32768,32768)]) for _ in range(4)];mean=rng.randrange(65536)
  if i%3!=0:gain=[rng.randrange(128,1025) for _ in range(4)]
  inputs.append(f'aegrid {seed} {selection} {range_} '+','.join(map(str,black))+' '+','.join(map(str,gain))+f' {mean}');expected.append(arm.run(seed,selection,2 if range_ else 0,black,gain,mean))
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatch=[{'case':i,'input':inputs[i],'expected':a,'actual':b} for i,(a,b) in enumerate(zip(expected,actual)) if a!=b]
 coverage={}
 for line in inputs:
  parts=line.split();key=parts[2]+':'+parts[3];coverage[key]=coverage.get(key,0)+1
 report=dict(branchCoverage=coverage,binarySha256=sha,seed='0x41454752',cases=len(inputs),mismatchCount=len(mismatch),scope='All six AE0 grid-selection branches, full/limited luma, signed BLS/gain correction, preserved fields and weighted mean',limitations=['Standard roundf is modeled as IEEE single-precision round-to-nearest with ties away from zero; other processing executes original ARM instructions.','Finite inputs with positive weight sum; zero-weight mean is rejected by Rust rather than reproducing the original division/conversion path.','This is a 5x5 measurement helper, not the exposure-control algorithm or full statistics translator.'])
 if mismatch:report['firstMismatches']=mismatch[:3]
 (ROOT/'reverse-engineering/rkaiq/ae-grid-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not mismatch
 if args.emit_dir:
  args.emit_dir.mkdir(parents=True,exist_ok=True)
  (args.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(args.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
