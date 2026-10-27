#!/usr/bin/env python3
"""Compare complete single-ISP AWB translation, SDK metadata and bypass writes."""
import argparse,hashlib,json,random,struct,subprocess
from pathlib import Path
from awb_translation_reference import OriginalTranslation,data
from differential import ROOT,BINARY

def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000);p.add_argument('--emit-dir',type=Path);a=p.parse_args();arm=OriginalTranslation();rng=random.Random(0x41575452);inputs=[];expected=[];coverage={}
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert sha==next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name)
 for i in range(a.cases):
  v=dict(seed=rng.randrange(0xffffffff),lights=i%5,valid=i//5%2==0,missing=i%13==0,payload=i//10%2==0,debug=i//20%4)
  seed=v['seed'];raw=data(seed^0x31,13036 if v['payload'] else 13040);flags=struct.unpack_from('<I',raw,0x32e0)[0];struct.pack_into('<I',raw,0x32e0,(flags&~0x20)|(0x20 if v['valid'] else 0));struct.pack_into('<I',raw,0x2af8,v['debug'])
  config=data(seed^0x32,1204);config[0x48]=v['lights'];status,frame,valid,info,frame_id,sequence=arm.run(None if v['missing'] else raw,config,seed)
  expected.append(f'{status}:{valid}:{info}:{frame_id:08x}:{sequence:08x}:'+frame.hex());inputs.append('awb-translation '+json.dumps(v,separators=(',',':')));key=f'{v["lights"]}:{v["valid"]}:{v["missing"]}:{v["payload"]}:{v["debug"]}';coverage[key]=coverage.get(key,0)+1
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatch=[dict(case=i,input=inputs[i],firstDifferingCharacter=next((j for j,(c,d) in enumerate(zip(x,y)) if c!=d),min(len(x),len(y)))) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
 report=dict(binarySha256=sha,cases=len(inputs),seed='0x41575452',mismatchCount=len(mismatch),elfEntry='0x8818c',coverage=coverage,boundaryCalls=arm.boundary_calls,standardImportedCalls=sorted(set(arm.calls)),scope='Full single-ISP AWB SDK frame: all 7680 bytes, metadata/padding, global sums, debug descriptor, conditional validity/frame/proxy fields and preservation',limitations=['Stats-buffer object access and single-ISP predicate are controlled boundaries; united/multi-ISP delegation is outside the RV1106 value API.','Vendor logging is discarded; native refcount instructions execute against a retained controlled owner and return to their initial count.','Configuration is the supplied selected-measurement snapshot, as read by the native translator; frame/application association is not proven or invented.','Missing/invalid input bypass, both supported driver payload lengths and 0-4 physical lights are covered; invalid raw pointers/configured counts above hardware capacity are outside the checked API.'])
 if mismatch:report['firstMismatches']=mismatch[:3]
 (ROOT/'reverse-engineering/rkaiq/awb-translation-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='coverage'},indent=2));assert not mismatch
 if a.emit_dir:
  a.emit_dir.mkdir(parents=True,exist_ok=True);(a.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(a.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
if __name__=='__main__':main()
