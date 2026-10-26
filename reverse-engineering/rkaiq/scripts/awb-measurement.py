#!/usr/bin/env python3
"""Execute the original AWB measurement converter and compare every written byte."""
import argparse, hashlib, json, random, struct, subprocess
from pathlib import Path
from differential import OriginalArm, ROOT, BINARY, HEAP
SYMBOL='_ZN5RkCam11Isp32Params26convertAiqAwbToIsp32ParamsER20isp32_isp_params_cfgRK25rk_aiq_awb_stat_cfg_v32_sb'
SIZE=11145; OFFSET=0xf4; LENGTH=807

def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=2000);p.add_argument('--emit-dir',type=Path);a=p.parse_args()
 sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());assert sha==next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name)
 arm=OriginalArm(BINARY);rng=random.Random(0x41574232);inputs=[];expected=[];coverage={}
 for i in range(a.cases):
  record=bytearray(rng.randbytes(1204))
  if i%17==0:record[:]=bytes(1204)
  elif i%19==0:record[:]=bytes([255])*1204
  # Real bool representations, with all enable/update combinations exercised.
  for offset in [0,1,2,3,8,12,32,33,34,35,36,37,46,47,48,49,50,60,61,1100]:record[offset]=rng.randrange(2)
  record[0]=i%2;update=bool(i//2%2);mode=[0,1,2,3,4,5,255][i//4%7];record[62]=mode
  for region in range(7):
   for j in [4,5,6]:record[644+region*28+j]=rng.randrange(2)
  exposure=[0,1,65536,65535,0xffff0000,0xffffffff,0x8000][i//28%7];struct.pack_into('<I',record,96,exposure)
  seed=rng.randrange(0xffffffff);state=seed;prior=bytearray()
  for _ in range(SIZE):state=(state*1664525+1013904223)&0xffffffff;prior.append(state>>24)
  context=bytes([0xa7])*1024;arm.uc.mem_write(HEAP,context);arm.uc.mem_write(HEAP+0x10000,bytes(prior));arm.uc.mem_write(HEAP+0x20000,bytes(record));arm.invoke(SYMBOL,[HEAP,HEAP+0x10000,HEAP+0x20000,int(update)])
  result=bytes(arm.uc.mem_read(HEAP+0x10000,SIZE));assert bytes(arm.uc.mem_read(HEAP,1024))==context;assert bytes(arm.uc.mem_read(HEAP+0x20000,1204))==record
  assert result[24:OFFSET]==prior[24:OFFSET] and result[OFFSET+LENGTH:]==prior[OFFSET+LENGTH:]
  if not update:assert result==prior
  v=dict(seed=seed,record=record.hex(),update=update);inputs.append('awb-measurement '+json.dumps(v,separators=(',',':')));expected.append(result[:24].hex()+':'+result[OFFSET:OFFSET+LENGTH].hex());key=f'{record[0]}:{update}:{mode}:{exposure}';coverage[key]=coverage.get(key,0)+1
 assert arm.calls==[],arm.calls
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[dict(case=i,input=inputs[i],expected=x,actual=y) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
 report=dict(binarySha256=sha,elfAddress='0x2b71c',seed='0x41574232',cases=len(inputs),mismatchCount=len(mismatches),importedCalls=arm.calls,coverage=coverage,scope='AWB SDK v32 measurement-to-ISP32 converter: three masks, complete 807-byte block, preservation of unrelated parameters/context/input',limitations=['Wide integer fields verify native narrowing/packing, not calibrated or physically valid measurement geometry.','AWB decisions, scene calibration, full initial ISP configuration and hardware execution remain unfinished.'])
 if mismatches:report['firstMismatches']=mismatches[:2]
 (ROOT/'reverse-engineering/rkaiq/awb-measurement-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('coverage','firstMismatches')},indent=2))
 if mismatches:
  print(json.dumps(mismatches[:1]));raise SystemExit(1)
 if a.emit_dir:
  a.emit_dir.mkdir(parents=True,exist_ok=True);(a.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(a.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
