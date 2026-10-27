#!/usr/bin/env python3
"""Execute the complete native numerical prefix, using its missing-metadata exit."""
import hashlib,json,random,struct,subprocess,sys
from differential import ROOT,BINARY,HEAP,RETURN,regs,f32
from awb_reference import OriginalAwb,RUNTIME
SYMBOL='_Z13AwbPreProcV32PK25rk_aiq_awb_stat_res_v32_sP12awb_contex_s'
class Original(OriginalAwb):
 def hook(self,uc,address,size,user):
  if getattr(self,'stop_at_measurements',False) and address==(self.symbols['_Z20PrepareMeasureResultPK25rk_aiq_awb_stat_res_v32_sP12awb_contex_s']&~1):
   self.stopped=True;uc.reg_write(regs.UC_ARM_REG_PC,RETURN);return
  if self.stubs.get(address)=='malloc' and getattr(self,'stop_at_measurements',False):
   assert uc.reg_read(regs.UC_ARM_REG_R0)==12
   pointer=self.arena;self.arena+=16;uc.mem_write(pointer,bytes(12));uc.reg_write(regs.UC_ARM_REG_R0,pointer);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if address==(self.symbols.get('xcam_print_log',0)&~1):
   uc.reg_write(regs.UC_ARM_REG_R0,0);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if self.stubs.get(address)=='__aeabi_uidivmod':
   self.runtime.invoke('__aeabi_uidivmod',[uc.reg_read(regs.UC_ARM_REG_R0),uc.reg_read(regs.UC_ARM_REG_R1)]);self.runtime_calls+=1
   for r in [regs.UC_ARM_REG_R0,regs.UC_ARM_REG_R1]:uc.reg_write(r,self.runtime.uc.reg_read(r))
   uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def configure_curves(self,cfg,cal,curves):
  self.curve_blocks=[]
  def word(data,o,n):struct.pack_into('<I',data,o,n)
  def put(slot,values):
   pointer=HEAP+0x80000+slot*0x100
   data=struct.pack('<'+'f'*len(values),*values)
   self.uc.mem_write(pointer,data);self.curve_blocks.append((pointer,data));return pointer
  for slot,(name,base,keys) in enumerate([('smart',0x4e4,['lvVarTh','wbgainAlgDiffTh','wbgainHwDiffTh']),('points',0x580,['low','high']),('regions',0x61c,['forBigType','forExtraType'])]):
   group=curves[name];word(cal,base,put(slot*4,group['lumaValue']));word(cal,base+4,len(group['lumaValue']))
   for i,key in enumerate(keys):word(cal,base+8+i*8,put(slot*4+i+1,group[key]));word(cal,base+12+i*8,len(group[key]))
  interval=curves['interval'];word(cfg,0xdc,len(interval['lumaValue']))
  for o,key in [(0xe0,'lumaValue'),(0x100,'intervalValue')]:struct.pack_into('<'+'f'*len(interval[key]),cfg,o,*interval[key])
  cfg[0x4a4]=curves['enabled']
 def run(self,v):
  c=bytearray([0x5a]*0x4000);cfg=bytearray(0x600);cal=bytearray(0x700);configuration=HEAP+0x10000;calibration=HEAP+0x20000;arrays=HEAP+0x30000;source=HEAP+0x40000
  def word(data,o,x):struct.pack_into('<I',data,o,x&0xffffffff)
  def floats(data,o,*x):struct.pack_into('<'+'f'*len(x),data,o,*x)
  for o,x in [(0x28,7),(0x2c,v['mode']),(0x34,v['working']),(0x80,calibration),(0x8c,configuration),(0x4c,0 if v['source'] is None else source),(0x2dec,0),(0x33d8,123),(0x33b0,6),(0x33ac,v['frame']),(0x369c,v['scale'])]:word(c,o,x)
  c[0x3349]=v['update'];c[0x334a]=0;c[0x2ece]=v['choice'];c[0x36a0]=v['override_enabled'];c[0x36b8]=v['override_valid'];floats(c,0x36b4,v['override']);floats(c,0x33dc,2.)
  struct.pack_into('<2H',c,0x2ed4,2304,1296);c[0x33b8:0x33ba]=bytes(v['block'])
  cfg[0x4a4]=v['enabled'];word(cfg,0x4b4,v['countdown']);word(cfg,0x188,v['fallback']);floats(cfg,0x4a8,3.,4.,5.);word(cfg,0x1b8,7);word(cfg,0x1bc,8);floats(cfg,0x38c,9.,10.)
  pointer={}
  for i,key in enumerate(['knots','smart0','smart1','smart2','intervals','points0','points1','regions0','regions1']):
   pointer[key]=arrays+i*0x100;self.uc.mem_write(pointer[key],struct.pack('<3f',*v[key]))
  for offset,key in [(0x4e4,'knots'),(0x4ec,'smart0'),(0x4f4,'smart1'),(0x4fc,'smart2'),(0x580,'knots'),(0x590,'points0'),(0x588,'points1'),(0x61c,'knots'),(0x624,'regions0'),(0x62c,'regions1')]:word(cal,offset,pointer[key])
  for o in [0x4e8,0x584,0x620]:word(cal,o,3)
  word(cfg,0xdc,3);floats(cfg,0xe0,*v['knots']);floats(cfg,0x100,*v['intervals'])
  metadata=v.get('metadata');self.stop_at_measurements=metadata is not None;self.stopped=False
  if metadata is not None:
   word(c,0x2dec,HEAP+0x50000);word(c,0x33d4,9);word(c,0x33e0,-7);floats(c,0x3480,.5);c[0x3345]=1;c[0x3346:0x3348]=bytes(metadata['convergence'])
   word(cfg,0x158,metadata['target']);word(cfg,0x164,max(0,len(metadata['boundaries'])-1))
   for i,n in enumerate(metadata['boundaries']):word(cfg,0x168+i*4,n)
   for i,n in enumerate(metadata['thresholds']):word(cfg,0x1a8+i*4,n)
   head=HEAP+0x3478;nodes=[HEAP+0x60000+i*16 for i in range(len(metadata['history']))];self.arena=HEAP+0x60000+len(nodes)*16
   word(c,0x3478,nodes[0] if nodes else head);word(c,0x347c,nodes[-1] if nodes else head)
   for i,(node,value) in enumerate(zip(nodes,metadata['history'])):self.uc.mem_write(node,struct.pack('<3I',nodes[i+1] if i+1<len(nodes) else head,nodes[i-1] if i else head,value))
  self.curve_blocks=[]
  if "curves" in v:self.configure_curves(cfg,cal,v["curves"])
  if "common_iq" in v:
   common=v["common_iq"];word(cfg,0x164,16);struct.pack_into('<16I',cfg,0x168,*common['lumaValueMatrix'])
   struct.pack_into('<4I',cfg,0x1a8,*[common['division'][key] for key in ['lumaValThLow','lumaValThLow2','lumaValThHigh','lumaValThHigh2']])
  self.uc.mem_write(HEAP,bytes(c));self.uc.mem_write(configuration,bytes(cfg));self.uc.mem_write(calibration,bytes(cal));self.uc.mem_write(source,struct.pack('<2f',*(v['source'] or [0.,0.])))
  self.invoke(SYMBOL,[0,HEAP]);after=bytearray(self.uc.mem_read(HEAP,len(c)));newcfg=bytearray(self.uc.mem_read(configuration,len(cfg)))
  w=lambda data,o:struct.unpack_from('<I',data,o)[0]
  out=dict(mode=struct.unpack_from('<i',after,0x28)[0],update=bool(after[0x334a]),integer=w(after,0x33d8),luma=w(after,0x33dc),smart=list(struct.unpack_from('<3I',newcfg,0x4a8)),interval=w(after,0x33b0),points=list(struct.unpack_from('<2I',newcfg,0x1b8)),regions=list(struct.unpack_from('<2I',newcfg,0x38c)),frame=w(after,0x33ac),decision=0 if v['mode']==1 else (1 if w(after,0x33ac)!=v['frame'] else 2))
  if metadata is not None:
   assert self.stopped==(out['decision']==2)
   word_at=lambda a:struct.unpack('<I',self.uc.mem_read(a,4))[0]
   values=[];head=HEAP+0x3478;previous=head;node=word_at(head)
   while node!=head:
    assert len(values)<32 and word_at(node+4)==previous
    values.append(word_at(node+8));previous=node;node=word_at(node)
   assert word_at(head+4)==previous
   out['metadata']=dict(history=values,level=w(after,0x33d4),environment=struct.unpack_from('<i',after,0x33e0)[0],variance=w(after,0x3480),stable=bool(after[0x3345]))
   for o,n in [(0x3345,1),(0x33d4,4),(0x33e0,4),(0x3478,12)]:after[o:o+n]=c[o:o+n]
  for o,n in [(0x28,4),(0x334a,1),(0x33d8,8),(0x33b0,4),(0x33ac,4)]:after[o:o+n]=c[o:o+n]
  for o,n in [(0x4a8,12),(0x1b8,8),(0x38c,8)]:newcfg[o:o+n]=cfg[o:o+n]
  assert after==c and newcfg==cfg and bytes(self.uc.mem_read(calibration,len(cal)))==bytes(cal),'Unexpected prefix mutation'
  for pointer,data in self.curve_blocks:assert bytes(self.uc.mem_read(pointer,len(data)))==data
  return out
def main():
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert sha==manifest['binaries'][0]['sha256'];assert hashlib.sha256(RUNTIME.read_bytes()).hexdigest()==manifest['gccRuntime']['memberSha256']
 arm=Original();rng=random.Random(0x41574250);cases=[];expected=[]
 for i in range(768):
  v=dict(mode=[0,1,2][i%3],update=bool(i//3%2),enabled=bool(i//6%2),countdown=[-1,0,2][i//12%3],source=None if i%5==0 else [f32(rng.uniform(-1,100)),f32(rng.uniform(0,200))],choice=[0,1,2,255][i//3%4],working=[0,1,16][i//12%3],fallback=[0,128,0xffffffff][i//5%3],override_enabled=bool(i//4%2),override_valid=bool(i//8%2),override=f32(rng.uniform(-1,200000)),block=[rng.choice([1,15,255]),rng.choice([1,15,255])],scale=rng.choice([-1,1,1024]),knots=[0.,1000.,200000.],frame=[0,1,2,17,100,0xffffffff][i//3%6])
  for key in ['smart0','smart1','smart2']:v[key]=[f32(rng.uniform(0,.5)) for _ in range(3)]
  v['intervals']=[f32(rng.choice([0.,.49,.5,1.,3.,8.])) for _ in range(3)]
  for key in ['points0','points1','regions0','regions1']:v[key]=[f32(rng.uniform(0,300)) for _ in range(3)]
  cases.append(v);expected.append(arm.run(v))
 inputs=''.join('awb-preprocess '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  p=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True);actual=[json.loads(s) for s in p.stdout.splitlines()];assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')]);arm_replay='--arm' in sys.argv
 if arm_replay:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=sha,cases=len(cases),mismatches=0,arm=arm_replay,decisions={str(n):sum(e['decision']==n for e in expected) for n in range(3)},nativeDivisionCalls=arm.runtime_calls,scope='Standard AWB preprocessor numerical prefix, exact f32/rounded words, mode/update/interval decisions and context preservation',limitations=['Native metadata pointer is null: ordinary metadata/history/classification continuation intentionally not executed.','Finite valid interpolation arrays, nonzero block dimensions and interval below UINT32_MAX.','Logging is intercepted; native interpolation and isolated libgcc unsigned divide/mod instructions execute.'])
 (ROOT/'reverse-engineering/rkaiq/awb-preprocess-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
