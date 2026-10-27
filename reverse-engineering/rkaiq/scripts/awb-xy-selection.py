#!/usr/bin/env python3
"""Native gain-mode region selection through its original WP-type classifier."""
import hashlib,json,random,struct,subprocess,sys
from differential import ROOT,BINARY,HEAP,RETURN,regs,f32
from awb_reference import OriginalAwb,RUNTIME
SYMBOL='_Z18AwbCalGainByWbModeP12awb_contex_s';TYPE='_Z12AwbCalWPTypeiiP12awb_contex_s'
class Original(OriginalAwb):
 def __init__(self):super().__init__(stdlib=True);self.finish_pc=None
 def hook(self,uc,address,size,user):
  if address==getattr(self,'finish_pc',None):self.stopped=True;uc.reg_write(regs.UC_ARM_REG_PC,RETURN);return
  if address==(self.symbols[TYPE]&~1):self.finish_pc=uc.reg_read(regs.UC_ARM_REG_LR)&~1
  if address==(self.symbols.get('xcam_print_log',0)&~1):uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  name=self.stubs.get(address)
  if name in ['malloc','free']:
   a=uc.reg_read(regs.UC_ARM_REG_R0)
   if name=='malloc':
    assert 0<a<=255;pointer=self.arena;self.arena+=(a+15)&~15;self.live.add(pointer);uc.mem_write(pointer,bytes(a));uc.reg_write(regs.UC_ARM_REG_R0,pointer)
   else:assert a in self.live;self.live.remove(a)
   uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v):
  n=len(v['normal']);ctx=bytearray([0x5a]*0x4000);cfg=bytearray(0x800);cal=bytearray(0x800);lights=bytearray(n*0xac);results=bytearray(n*0xa0);head=HEAP+0x355c
  def word(data,o,x):struct.pack_into('<I',data,o,x&0xffffffff)
  for o,p in [(0x8c,HEAP+0x8000),(0x80,HEAP+0x9000),(0x134,HEAP+0x10000),(0x33e4,HEAP+0x20000),(0x33bc,10),(0x33c0,20),(0x2d10,v['exclusion']),(0x3480,v['variance'])]:word(ctx,o,p)
  ctx[0x13c]=1;ctx[0x33fc]=v['previous'];cfg[0x138]=n;cfg[0x380]=v['enabled'];word(cfg,0x384,v['target']);struct.pack_into('<f',cfg,0x388,v['variance_threshold']);struct.pack_into('<2f',cfg,0x38c,*v['region_thresholds']);struct.pack_into('<2I',cfg,0x1b8,*v['count_thresholds']);struct.pack_into('<2f',cfg,0x1f0,v['absolute'],v['relative']);word(cal,0x648,1)
  for i,(a,b) in enumerate(zip(v['normal'],v['big'])):
   word(lights,i*0xac,a);word(lights,i*0xac+0x34,b)
   for o,x in zip([0x74,0x78,0x7c,0x80,0x94],[.25,.5,.75,1.,1.25]):struct.pack_into('<f',results,i*0xa0+o,x)
  nodes=[HEAP+0x30000+i*16 for i in range(len(v['history']))];word(ctx,0x355c,nodes[0] if nodes else head);word(ctx,0x3560,nodes[-1] if nodes else head)
  for i,(node,value) in enumerate(zip(nodes,v['history'])):self.uc.mem_write(node,struct.pack('<3I',nodes[i+1] if i+1<len(nodes) else head,nodes[i-1] if i else head,value))
  for o,data in [(0,ctx),(0x8000,cfg),(0x9000,cal),(0x10000,lights),(0x20000,results)]:self.uc.mem_write(HEAP+o,bytes(data))
  self.arena=HEAP+0x40000;self.live=set();self.finish_pc=None;self.stopped=False
  self.invoke(SYMBOL,[HEAP],instructions=2000000);assert self.stopped
  word_at=lambda a:struct.unpack('<I',self.uc.mem_read(a,4))[0]
  values=[];node=word_at(head);previous=head
  while node!=head:
   assert len(values)<32 and word_at(node+4)==previous
   values.append(word_at(node+8));previous=node;node=word_at(node)
  assert word_at(head+4)==previous
  out=dict(selected=self.uc.mem_read(HEAP+0x33fc,1)[0],retained=word_at(HEAP+0x33c8),kind=word_at(HEAP+0x33d0),history=values,probabilities=[[word_at(HEAP+0x20000+i*0xa0+o) for o in [0x74,0x78,0x7c,0x80,0x94]] for i in range(n)])
  assert len(self.live)==len(values)-len(v['history'])
  after=bytearray(self.uc.mem_read(HEAP,len(ctx)))
  for o,size in [(0x33c8,12),(0x33fc,1),(0x33fe,1),(0x33f8,4),(0x3418,1),(0x355c,8)]:after[o:o+size]=ctx[o:o+size]
  assert after==ctx,'Unexpected region-selection context write'
  after=bytearray(self.uc.mem_read(HEAP+0x20000,len(results)))
  for i in range(n):
   for o in [0x94,0x98]:after[i*0xa0+o:i*0xa0+o+4]=results[i*0xa0+o:i*0xa0+o+4]
  assert after==results,'Unexpected per-light result write'
  assert bytes(self.uc.mem_read(HEAP+0x9000,len(cal)))==cal
  assert bytes(self.uc.mem_read(HEAP+0x8000,len(cfg)))==cfg and bytes(self.uc.mem_read(HEAP+0x10000,len(lights)))==lights
  return out
def main():
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert sha==manifest['binaries'][0]['sha256'];assert hashlib.sha256(RUNTIME.read_bytes()).hexdigest()==manifest['gccRuntime']['memberSha256']
 arm=Original();rng=random.Random(0x58595345);cases=[];expected=[]
 for i in range(768):
  n=255 if i%127==0 else 1+i%8
  v=dict(normal=[rng.choice([0,1,100,0xffffffff,rng.randrange(2**32)]) for _ in range(n)],big=[rng.choice([0,1,100,0x80000000,rng.randrange(2**32)]) for _ in range(n)],exclusion=rng.choice([0,1,100,0xffffffff]),absolute=f32(rng.choice([0,1,100,4294967296.])),relative=f32(rng.choice([0.,.1,.5,1.])),region_thresholds=[f32(rng.choice([0.,100.,4294967296.])) for _ in range(2)],count_thresholds=[rng.choice([0,100,0x7fffffff,0x80000000,0xffffffff]) for _ in range(2)],enabled=bool(i%2),target=[0,2,4,8][i//2%4],variance=[0,0x3dcccccd,0x3f800000,0x7fc00000][i//3%4],variance_threshold=[0.,.1,1.][i//12%3],previous=[0,1,3][i//2%3],history=[rng.choice([0,1,3,255]) for _ in range(i%8)])
  if i%9==0:v['normal']=[0]*n;v['big']=[0]*n
  cases.append(v);expected.append(arm.run(v))
 inputs=''.join('awb-xy-selection '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  p=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True);actual=[json.loads(s) for s in p.stdout.splitlines()];assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')]);arm_replay='--arm' in sys.argv
 if arm_replay:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=sha,cases=len(cases),mismatches=0,arm=arm_replay,selected={str(r):sum(e['selected']==r for e in expected) for r in [0,1,3]},scope='Native gain-mode region/count fallback, rolling stabilization, signed WP classification and exact per-light count probabilities',limitations=['Complete-measurement branch with calibration mode 1; execution stops immediately after native AwbCalWPType returns.','Allocation/logging are explicit adapters; original count-filter/list/stabilization/classification bodies execute.','Final illumination probabilities, high/low gain mix and postprocessing remain separate.'])
 (ROOT/'reverse-engineering/rkaiq/awb-xy-selection-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
