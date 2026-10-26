#!/usr/bin/env python3
"""Compare complete ClmExecute exposure/flag outputs against actual ARM solver."""
import argparse,hashlib,json,random,struct,subprocess
from pathlib import Path
from differential import OriginalArm,ROOT,BINARY,HEAP,BASE,regs,f32,u32
class OriginalDecision(OriginalArm):
 def __init__(self):
  super().__init__(BINARY);self.stubs[self.symbols['xcam_print_log']&~1]='xcam_print_log'
 def hook(self,uc,address,size,user):
  if address==BASE+0xb6da8:self.iterations+=1
  name=self.stubs.get(address)
  if name=='xcam_print_log':uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if name=='__aeabi_uidiv':
   a=uc.reg_read(regs.UC_ARM_REG_R0);b=uc.reg_read(regs.UC_ARM_REG_R1);assert b
   uc.reg_write(regs.UC_ARM_REG_R0,a//b);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v,index,hdr):
  self.iterations=0
  context=HEAP;histogram=HEAP+0x10000;out=HEAP+0x20000;count=len(v['histogram'])
  self.uc.mem_write(context,bytes(0x6000));self.uc.mem_write(context+0xf4,struct.pack('<ff',v['minimum'],v['maximum']));self.uc.mem_write(context+0x23cd,bytes([hdr]))
  for i in range(3):
   self.uc.mem_write(context+0x350+i*4,struct.pack('<f',v['maximum']));self.uc.mem_write(context+0x35c+i*4,struct.pack('<f',v['minimum']))
  self.uc.mem_write(context+0x5995,bytes([int(v['saturated'])]));original=bytes(self.uc.mem_read(context,0x6000))
  self.uc.mem_write(histogram,struct.pack('<'+'I'*count,*v['histogram']));self.uc.mem_write(out,bytes(4))
  stack=bytearray(0xc1c);struct.pack_into('<4fI',stack,0xc08,v['target'],v['measured'],v['exposure'],v['tolerance'],out)
  assert self.invoke('ClmExecute',[context,index,histogram,count],stack=bytes(stack),instructions=2_000_000)==0
  after=bytes(self.uc.mem_read(context,0x6000));assert after[:0x5995]==original[:0x5995] and after[0x5996:]==original[0x5996:]
  assert self.uc.mem_read(histogram,count*4)==struct.pack('<'+'I'*count,*v['histogram'])
  return f'{u32(self.uc.mem_read(out,4)):08x}:{after[0x5995]}'
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000);p.add_argument('--emit-dir',type=Path);args=p.parse_args()
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==sha
 arm=OriginalDecision();rng=random.Random(0x434c4d45);inputs=[];expected=[];coverage={};iterations={}
 for i in range(args.cases):
  count=[64,256][i%2];kind=i//2%8;hist=[0]*count
  if kind==1:hist=[rng.randrange(1,100) for _ in hist]
  elif kind==2:hist[0]=1000
  elif kind==3:hist[count//2]=1000
  elif kind==4:hist[-1]=1000
  elif kind==5:hist=list(range(1,count+1))
  elif kind==6:hist=[rng.randrange(0,10000) for _ in hist]
  elif kind==7:hist[0]=100;hist[-1]=rng.randrange(1,100)
  target=f32(rng.uniform(8,240));measured=f32(rng.uniform(0,255));exposure=f32(rng.uniform(.0001,1))
  if i//16%4==0:measured=target
  minimum=f32(exposure*.001);maximum=f32(exposure*rng.choice([.8,1.2,100.]))
  v=dict(histogram=hist,target=target,measured=measured,exposure=exposure,tolerance=f32(rng.choice([0.,5.,10.,20.])),minimum=minimum,maximum=maximum,saturated=bool(i//64%2))
  if i==args.cases-1:
   # Deliberately beyond normal brightness range to exercise the native limit.
   hist=[0]*256;hist[-1]=1000;count=256;kind='iteration-limit'
   v=dict(histogram=hist,target=500.,measured=1.,exposure=f32(.01),tolerance=0.,minimum=f32(1e-30),maximum=f32(1e30),saturated=False)
  inputs.append('ae-decision '+json.dumps(v,separators=(',',':')));expected.append(arm.run(v,i%3,i//2%2));iterations[str(arm.iterations)]=iterations.get(str(arm.iterations),0)+1;key=f'{count}:{kind}';coverage[key]=coverage.get(key,0)+1
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[{'case':i,'input':inputs[i],'expected':a,'actual':b} for i,(a,b) in enumerate(zip(expected,actual)) if a!=b]
 report=dict(binarySha256=sha,seed='0x434c4d45',cases=len(inputs),histogramCoverage=coverage,iterationCoverage=iterations,mismatchCount=len(mismatches),scope='ClmExecute final exposure f32 bits and saturation flag; triangle extension and iterative brightness prediction execute original ARM code',limitations=['Unsigned integer division is an explicit standard helper; logging is discarded.','Finite valid targets/exposure/tolerance and 64/256-bin histograms; invalid pointers and zero triangle divisors are outside the checked Rust API.','One beyond-normal-range target explicitly exercises the 51-iteration bound; it is not a proposed camera setting.','Outer damping, routes, gain splitting, calibration/state population and synchronized sensor/ISP application remain incomplete.'])
 if mismatches:report['firstMismatches']=mismatches[:5]
 (ROOT/'reverse-engineering/rkaiq/ae-decision-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not mismatches
 if args.emit_dir:
  args.emit_dir.mkdir(parents=True,exist_ok=True);(args.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(args.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
