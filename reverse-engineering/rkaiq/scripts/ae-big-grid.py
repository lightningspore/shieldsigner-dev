#!/usr/bin/env python3
"""Compare entire big-AE output records, including native subwindow arithmetic."""
import argparse,hashlib,importlib.util,json,random,struct,subprocess
from pathlib import Path
from differential import ROOT,BINARY,HEAP
spec=importlib.util.spec_from_file_location('ae_grid',Path(__file__).with_name('ae-grid.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class OriginalBigGrid(module.OriginalGrid):
 def run(self,seed,selection,range_,black,gain,pixels,mean):
  state=seed
  def next():
   nonlocal state
   state=(state*1664525+1013904223)&0xffffffff;return state
  raw=[next() for _ in range(225)];sums=[next() for _ in range(12)];initial=bytes(next()>>24 for _ in range(1928));weights=bytes(next()>>24 for _ in range(225))
  a=HEAP;b=HEAP+0x1000;c=HEAP+0x2000;d=HEAP+0x3000;e=HEAP+0x4000;f=HEAP+0x5000
  self.uc.mem_write(a,struct.pack('<225I',*raw));self.uc.mem_write(b,struct.pack('<12I',*sums));self.uc.mem_write(c,initial);self.uc.mem_write(d,struct.pack('<H',mean));self.uc.mem_write(e,weights);self.uc.mem_write(f,struct.pack('<4I',*pixels))
  stack=struct.pack('<III8hI',e,selection,range_,*black,*gain,f)
  self.invoke('_ZN5RkCam21calcAecBigWinStatsV32EP20isp32_rawaebig_stat0P20isp32_rawaebig_stat1P13rawaebig_statPtPhaa19isp2x_bls_fixed_valS8_Pj',[a,b,c,d],stack=stack)
  return self.uc.mem_read(c,1928).hex()+':'+str(struct.unpack('<H',self.uc.mem_read(d,2))[0])
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000);p.add_argument('--emit-dir',type=Path);args=p.parse_args()
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==sha
 arm=OriginalBigGrid(BINARY);rng=random.Random(0x42494741);inputs=[];expected=[];coverage={}
 for i in range(args.cases):
  seed=rng.randrange(0xffffffff);selection=[0,1,2,4,8,14][i%6];range_=i//6%2
  black=[rng.randrange(-4096,4097) if i%3==0 else rng.randrange(-64,257) for _ in range(4)];gain=[rng.choice([0,256,32767,-32768,rng.randrange(-32768,32768)]) if i%3==0 else rng.randrange(128,1025) for _ in range(4)]
  pixels=[rng.choice([0,1,3,4,8,4096,0xffffffff,rng.randrange(0xffffffff)]) for _ in range(4)];mean=rng.randrange(65536)
  inputs.append(f'aebig {seed} {selection} {range_} '+','.join(map(str,black))+' '+','.join(map(str,gain))+' '+','.join(map(str,pixels))+f' {mean}')
  expected.append(arm.run(seed,selection,2 if range_ else 0,black,gain,pixels,mean));key=f'{selection}:{range_}';coverage[key]=coverage.get(key,0)+1
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatch=[{'case':i,'input':inputs[i],'firstDifferentByte':next((j for j,(a,b) in enumerate(zip(bytes.fromhex(expected[i].split(':')[0]),bytes.fromhex(actual[i].split(':')[0]))) if a!=b),None),'expectedMean':expected[i].split(':')[1],'actualMean':actual[i].split(':')[1]} for i in range(len(expected)) if expected[i]!=actual[i]]
 report=dict(binarySha256=sha,seed='0x42494741',cases=len(inputs),branchCoverage=coverage,mismatchCount=len(mismatch),scope='Full 1928-byte big-AE records: 225 RGB/luma cells, preserved window channels, four subwindow RGB sums, plus weighted mean',limitations=['Standard roundf uses the explicit ties-away stub shared with AE0; remaining processing executes original ARM instructions.','Valid positive weight sum; Rust rejects zero-weight mean atomically.','The helper does not implement exposure selection, calibration loading or sensor programming.'])
 if mismatch:report['firstMismatches']=mismatch[:5]
 (ROOT/'reverse-engineering/rkaiq/ae-big-grid-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not mismatch
 if args.emit_dir:
  args.emit_dir.mkdir(parents=True,exist_ok=True)
  (args.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(args.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
