#!/usr/bin/env python3
"""Native standard AWB stability gate, including persistent history updates."""
import hashlib,json,random,struct,subprocess,sys
from differential import ROOT,BINARY,HEAP,f32,regs
from awb_reference import OriginalAwb,RUNTIME
SYMBOL='_Z22IsMeasureResultStable4P12awb_contex_sPK30rk_aiq_awb_stat_blk_res_v201_s'
class OriginalStability(OriginalAwb):
 def hook(self,uc,address,size,user):
  if address==(self.symbols.get('xcam_print_log',0)&~1):
   uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
def main():
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert sha==manifest['binaries'][0]['sha256'];assert hashlib.sha256(RUNTIME.read_bytes()).hexdigest()==manifest['gccRuntime']['memberSha256']
 arm=OriginalStability();rng=random.Random(0x53544142);cases=[];expected=[]
 for i in range(1024):
  count=i%9;slot=[-1,*range(8)][(i//9)%9]
  sums=[rng.choice([0,-1,1,255,2**24+1,2**63-1,rng.randrange(1,2**62)]) for _ in range(3)]
  if i%4==0:sums=[256,512,128]
  current=[f32(f32(sums[1])/f32(sums[0])),1.,1.,f32(f32(sums[1])/f32(sums[2]))] if sums[0]>0 and sums[2]>0 else [0.]*4
  history=[[f32(rng.uniform(-2,8)) for _ in range(4)] for _ in range(8)]
  threshold=[0.,.125,-.125,.5][(i//3)%4]
  if i%4 in [0,1]:history=[current[:] for _ in range(8)]
  if i%4==1 and count:history[count-1][i%2*3]=f32(current[i%2*3]+threshold)
  v=dict(count=count,slot=slot,sums=sums,history=history,threshold=threshold,update=bool(i//2%2));cases.append(v)
  context=bytearray([0x5a]*0x4000);configuration=HEAP+0x10000;metadata=HEAP+0x20000;statistics=HEAP+0x30000
  struct.pack_into('<I',context,0x8c,configuration);struct.pack_into('<I',context,0x2dec,metadata);context[0x3348]=0xa5;context[0x334a]=v['update'];struct.pack_into('<32f',context,0x334c,*sum(history,[]))
  arm.uc.mem_write(HEAP,bytes(context));arm.uc.mem_write(configuration,bytes(0x500));arm.uc.mem_write(configuration+0x398,struct.pack('<i',count));arm.uc.mem_write(configuration+0x4b0,struct.pack('<f',threshold));arm.uc.mem_write(metadata,bytes(0x80));arm.uc.mem_write(metadata+8,struct.pack('<i',slot));arm.uc.mem_write(statistics,struct.pack('<4q',123,*sums))
  arm.invoke(SYMBOL,[HEAP,statistics]);after=bytearray(arm.uc.mem_read(HEAP,len(context)))
  expected.append(dict(matched=after[0x3348],update=bool(after[0x334a]),history=[list(struct.unpack_from('<4I',after,0x334c+j*16)) for j in range(8)]))
  after[0x3348]=context[0x3348];after[0x334a]=context[0x334a];after[0x334c:0x33cc]=context[0x334c:0x33cc];assert after==context,'Unexpected context mutation'
 inputs=''.join('awb-stability '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  p=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True);actual=[json.loads(s) for s in p.stdout.splitlines()];assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')]);arm_replay='--arm' in sys.argv
 if arm_replay:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
  compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=sha,cases=len(cases),mismatches=0,arm=arm_replay,nativeRuntimeCalls=arm.runtime_calls,scope='Exact history f32 bits, matched mask, retained/forced update flag and unrelated context preservation',limitations=['Finite history/threshold; checked count 0..8 and slot -1..7 storage boundary.','Outer preprocessor seeds the update flag; this gate does not reconstruct the full AWB controller.'])
 (ROOT/'reverse-engineering/rkaiq/awb-stability-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
