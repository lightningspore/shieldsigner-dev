#!/usr/bin/env python3
"""Compare AE/histogram dispatcher branches, complete kernel blocks and caches."""
import argparse,hashlib,json,random,struct,subprocess
from pathlib import Path
from differential import OriginalArm,ROOT,BINARY,HEAP,regs
AE=0x41b;AE_SIZE=148;HIST=0x4af;HIST_SIZE=767;PARAMETERS=11145
class OriginalMeasurement(OriginalArm):
 def __init__(self):
  super().__init__(BINARY)
  for symbol in self.symbols:
   if 'SharedItemBaseEE12get_cast_ptr' in symbol and ('rk_aiq_ae_meas_params' in symbol or 'rk_aiq_hist_meas_params' in symbol):self.stubs[self.symbols[symbol]&~1]='measurement-cast'
 def hook(self,uc,address,size,user):
  if self.stubs.get(address)=='measurement-cast':
   uc.reg_write(regs.UC_ARM_REG_R0,HEAP+0x40000);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v,virtual):
  context=HEAP;params=HEAP+0x10000;source=HEAP+0x20000;smart=HEAP+0x30000;proxy=HEAP+0x40000;vtable=HEAP+0x50000+12
  state=v['seed'];data=bytearray()
  for _ in range(PARAMETERS+AE_SIZE+HIST_SIZE):state=(state*1664525+1013904223)&0xffffffff;data.append(state>>24)
  original=bytes(data[:PARAMETERS]);self.uc.mem_write(params,original);self.uc.mem_write(context,bytes([0x77])*0x2000);self.uc.mem_write(context,struct.pack('<I',vtable));self.uc.mem_write(vtable-12,struct.pack('<i',virtual));self.uc.mem_write(context+virtual+0x468,bytes(data[PARAMETERS:]))
  self.uc.mem_write(smart,struct.pack('<II',proxy,0));self.uc.mem_write(proxy,bytes(0x100));self.uc.mem_write(proxy+100,struct.pack('<I',1 if v['kind']=='ae' else 2));self.uc.mem_write(proxy+0x6c,struct.pack('<I',source));record=bytes.fromhex(v['record']);prefix=bytes([0x55])*8;self.uc.mem_write(source,prefix+record)
  before=bytes(self.uc.mem_read(context,0x2000));assert self.invoke('_ZN5RkCam11Isp32Params24convert3aResultsToIspCfgERN4XCam8SmartPtrINS_14SharedItemBaseEEEPvb',[context,smart,params,v['multi']])==1
  out=bytes(self.uc.mem_read(params,PARAMETERS));after=bytearray(self.uc.mem_read(context,0x2000));ae=bytes(after[virtual+0x468:virtual+0x468+AE_SIZE]);histogram=bytes(after[virtual+0x4fc:virtual+0x4fc+HIST_SIZE]);after[virtual+0x468:virtual+0x7fb]=before[virtual+0x468:virtual+0x7fb];assert bytes(after)==before
  assert bytes(self.uc.mem_read(source,len(prefix)+len(record)))==prefix+record
  assert out[24:AE]==original[24:AE] and out[HIST+HIST_SIZE:]==original[HIST+HIST_SIZE:]
  if v['kind']=='ae':assert ae==out[AE:AE+AE_SIZE]
  else:assert histogram==out[HIST:HIST+HIST_SIZE]
  return ':'.join([out[:24].hex(),out[AE:AE+AE_SIZE].hex(),out[HIST:HIST+HIST_SIZE].hex(),ae.hex(),histogram.hex()])
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000,help='Cases per branch');p.add_argument('--emit-dir',type=Path);a=p.parse_args();manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert sha==next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name)
 arm=OriginalMeasurement();rng=random.Random(0x41454d53);inputs=[];expected=[];coverage={}
 for kind,size in [('ae',104),('histogram',529)]:
  for i in range(a.cases):
   record=bytearray(rng.randbytes(size));record[0]=i%2;record[1]=i//2%2
   if i%17==0:record[2:]=bytes(size-2)
   elif i%19==0:record[2:]=bytes([255])*(size-2)
   v=dict(kind=kind,seed=rng.randrange(0xffffffff),record=record.hex(),multi=i//4%2)
   virtual=0x40 if i//8%2 else 0;inputs.append('ae-measurement '+json.dumps(v,separators=(',',':')));expected.append(arm.run(v,virtual));key=f'{kind}:{record[0]}:{record[1]}:{v["multi"]}:{virtual}';coverage[key]=coverage.get(key,0)+1
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[dict(case=i,input=inputs[i],expected=x,actual=y) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
 report=dict(binarySha256=sha,seed='0x41454d53',cases=len(inputs),casesPerBranch=a.cases,mismatchCount=len(mismatches),coverage=coverage,scope='ISP32 AE and histogram measurement branches of convert3aResultsToIspCfg: all masks, four-channel kernel blocks, all cached bytes and preservation',limitations=['Typed-result cast access is a controlled boundary returning the supplied valid SDK record; other dispatcher result types and failed casts are outside this suite.','Standard memcpy executes through the explicit harness helper. Source enable/update flags do not gate these native branches.','Wide raw control/window/weight patterns verify serialization, not physically valid measurement geometry or calibration.','Window/weight selection, outer publication/frame state, AWB measurement configuration, full initial IQ and live frame application remain unfinished.'])
 if mismatches:report['firstMismatches']=mismatches[:3]
 (ROOT/'reverse-engineering/rkaiq/ae-measurement-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='coverage'},indent=2));assert not mismatches
 if a.emit_dir:
  a.emit_dir.mkdir(parents=True,exist_ok=True);(a.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(a.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
