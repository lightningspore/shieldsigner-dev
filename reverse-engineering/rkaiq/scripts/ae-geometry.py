#!/usr/bin/env python3
"""Compare AecHwConfig geometry writes with original ARM instructions."""
import hashlib,json,random,struct,subprocess,sys,runpy
from differential import OriginalArm,ROOT,BINARY,HEAP

def main():
 arm=OriginalArm(BINARY);rng=random.Random(0x414547);cases=[];expected=[]
 init=runpy.run_path(str(ROOT/'reverse-engineering/rkaiq/scripts/ae-defaults.py'))['OriginalInit']();init.uc.mem_write(HEAP,bytes(8));init.invoke('AecInit',[HEAP,HEAP+0x80000,32]);assert init.defaults is not None
 for i in range(120):
  v=dict(width=2304 if i<3 else rng.randrange(1,65536),height=1296 if i<3 else rng.randrange(1,65536),mode=[0,17,18][i%3],input=[0,0,1,1] if i<3 else [rng.uniform(-.5,1.5) for _ in range(4)],tone=[0.1,0.2,0.6,0.5] if i<3 else [rng.uniform(-.5,1.5) for _ in range(4)])
  v['defaults']=bool(i%2)
  context=bytearray([0x5a])*0x25a4
  if v['defaults']:context[0x1d3c:0x1fb5]=init.defaults
  struct.pack_into('<i',context,0x1fc4,v['mode']);struct.pack_into('<ii',context,0x2008,v['width'],v['height']);struct.pack_into('<8f',context,0x180,*v['input'],*v['tone']);arm.uc.mem_write(HEAP,bytes(context))
  assert arm.invoke('AecHwConfig',[HEAP])==0
  out=bytearray(arm.uc.mem_read(HEAP,len(context)));selected=struct.unpack_from('<II',out,0x1fb8)
  expected.append(f'{selected[0]}:{selected[1]}:'+bytes(out[0x1d3c:0x1fb5]).hex());cases.append('ae-geometry '+json.dumps(v,separators=(',',':')))
  out[0x1d3c:0x1fb5]=context[0x1d3c:0x1fb5];out[0x1fb8:0x1fc0]=context[0x1fb8:0x1fc0];assert out==context,'unexpected native context mutation'
 result=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(cases)+'\n',text=True,capture_output=True,check=True).stdout.splitlines()
 assert len(result)==len(expected)
 for i,(a,b) in enumerate(zip(expected,result)):
  assert a==b,(i,cases[i],[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:10])
 if '--arm' in sys.argv:
  binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture'
  image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
  executed=subprocess.run(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly',image,'/bincheck/numeric-fixture'],input='\n'.join(cases)+'\n',text=True,capture_output=True,check=True)
  assert executed.stdout.splitlines()==expected,'ARM geometry differs from native reference'
 report=dict(armReplayPassed='--arm' in sys.argv,binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),nativeDefaultSeedCases=60,mismatches=0,scope='AecHwConfig selected 633 bytes, two mirrored selectors and preservation of other private context bytes',limitations=['Valid supplied modes 0/17/18 and bounded finite geometry only.','Default selected record construction and calibration loading remain separate; remaining source/control bytes are preserved, not initialized.','No live statistics capture, full AE policy or exposure loop is established.'])
 (ROOT/'reverse-engineering/rkaiq/ae-geometry-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
