#!/usr/bin/env python3
"""Execute native single-ISP linear AE translation with explicit object boundaries."""
import hashlib,json,random,runpy,struct,subprocess,sys,tempfile
from pathlib import Path
from differential import ROOT,BINARY,HEAP,regs
Base=runpy.run_path(str(Path(__file__).with_name('ae-grid.py')))['OriginalGrid']
SYMBOL='_ZN5RkCam26RkAiqResourceTranslatorV3217translateAecStatsERKN4XCam8SmartPtrINS1_11VideoBufferEEERNS2_INS_15SharedItemProxyI13RkAiqAecStatsEEEE'
class OriginalLinear(Base):
 def __init__(self):
  super().__init__(BINARY)
  for name in self.symbols:
   if ('get_cast_ptr' in name and 'Isp20StatsBuffer' in name) or 'get_v4l2_userptr' in name or 'IsMultiIspMode' in name or name=='xcam_print_log' or 'getAeStatsRunFlag' in name:self.stubs[self.symbols[name]&~1]=name
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name=='__aeabi_uldivmod':
   a=uc.reg_read(regs.UC_ARM_REG_R0)|(uc.reg_read(regs.UC_ARM_REG_R1)<<32);b=uc.reg_read(regs.UC_ARM_REG_R2)|(uc.reg_read(regs.UC_ARM_REG_R3)<<32);assert b
   q,r=divmod(a,b)
   for register,value in [(regs.UC_ARM_REG_R0,q&0xffffffff),(regs.UC_ARM_REG_R1,q>>32),(regs.UC_ARM_REG_R2,r&0xffffffff),(regs.UC_ARM_REG_R3,r>>32)]:uc.reg_write(register,value)
  elif name=='__aeabi_idiv':
   a=uc.reg_read(regs.UC_ARM_REG_R0);a=a if a<0x80000000 else a-0x100000000;b=uc.reg_read(regs.UC_ARM_REG_R1);assert b>0;uc.reg_write(regs.UC_ARM_REG_R0,(abs(a)//b*(1 if a>=0 else -1))&0xffffffff)
  elif name and ('get_cast_ptr' in name and 'Isp20StatsBuffer' in name):uc.reg_write(regs.UC_ARM_REG_R0,HEAP+0x38000)
  elif name and 'get_v4l2_userptr' in name:uc.reg_write(regs.UC_ARM_REG_R0,HEAP+0x20000)
  elif name and 'IsMultiIspMode' in name:uc.reg_write(regs.UC_ARM_REG_R0,0)
  elif name and 'getAeStatsRunFlag' in name:uc.reg_write(regs.UC_ARM_REG_R0,1)
  elif name=='xcam_print_log':pass
  else:return super().hook(uc,address,size,user)
  uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))
 def translate(self,raw,p):
  ctx=bytearray(0xc000);ctx[0xb237:0xb237+148]=p[0x41b:0x4af];ctx[0xb2cb:0xb2cb+767]=p[0x4af:0x7ae];ctx[0xb5ca:0xb5ca+44]=p[0x7ae:0x7da];ctx[0xb5f6:0xb5f6+32]=p[0x1225:0x1245]
  ctx[0xbad4:0xbad7]=bytes([1,1,1]);ctx[0xbad7:0xbad7+225]=p[0x4af+58:0x4af+283]
  self.uc.mem_write(HEAP,bytes(ctx));self.uc.mem_write(HEAP+0x20000,raw);self.uc.mem_write(HEAP+0x38000,bytes(0x100));self.uc.mem_write(HEAP+0x40000,bytes(0x3000));self.uc.mem_write(HEAP+0x50000,struct.pack('<II',HEAP+0x60000,0));proxy=bytearray(0x100);struct.pack_into('<II',proxy,0x6c,HEAP+0x40000,HEAP+0x70000);self.uc.mem_write(HEAP+0x60000,bytes(proxy));self.uc.mem_write(HEAP+0x70000,struct.pack('<II',0,100)+bytes(248))
  status=self.invoke(SYMBOL,[HEAP,0,HEAP+0x50000],instructions=1000000)
  if struct.unpack_from('<I',raw,0x32e0)[0]&((1<<8)|(1<<12))!=((1<<8)|(1<<12)):assert status==1;return 'invalid'
  assert status==0
  output=bytes(self.uc.mem_read(HEAP+0x40000,0x3000));return str(struct.unpack_from('<H',output,0x2e28)[0])+':'+output[8:8+1928].hex()+':'+output[0x790:0x790+1024].hex()
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 iq=ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json'
 with tempfile.TemporaryDirectory() as d:
  out=Path(d)/'p.bin';subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/camera-probe'),'make-initial-parameters',str(iq),str(out),'--ae-measurements'],capture_output=True,check=True);parameters=out.read_bytes()
 arm=OriginalLinear();rng=random.Random(0x414554);cases=[];expected=[]
 for i in range(32):
  raw=bytearray(13040);p=bytearray(parameters)
  for j in range(225):struct.pack_into('<I',raw,0x390+j*4,rng.randrange(1<<32))
  for j in range(256):struct.pack_into('<I',raw,0x1400+j*4,rng.randrange(100000))
  for j in range(12):struct.pack_into('<I',raw,0xb98+j*4,rng.randrange(1<<32))
  struct.pack_into('<III',raw,0x32e0,0 if i%5==0 else (1<<8)|(1<<12),i,0)
  if i>1:
   p[0x7ae+2]=i%2;struct.pack_into('<4h',p,0x7ae+28,*[rng.randrange(513) for _ in range(4)]);struct.pack_into('<HH',p,0x7ae+36,rng.randrange(65),[256,512][i%2]);struct.pack_into('<4H',p,0x1225,*[rng.randrange(256,1025) for _ in range(4)])
  expected.append(arm.translate(bytes(raw),bytes(p)));cases.append('ae-linear-translation '+json.dumps(dict(raw=raw.hex(),parameters=p.hex()),separators=(',',':')))
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(cases)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 for i,(a,b) in enumerate(zip(expected,actual)):
  assert a==b,(i,a[:20],b[:20],next((j for j,(x,y)in enumerate(zip(a,b))if x!=y),-1))
 if '--arm' in sys.argv:
  binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
  assert subprocess.run(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly',image,'/bincheck/numeric-fixture'],input='\n'.join(cases)+'\n',text=True,capture_output=True,check=True).stdout.splitlines()==expected
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='native translateAecStats normal return: primary source-1 linear/full-range corrected 1928-byte grid, weighted mean and 256-bin histogram, invalid validity-mask bypass',limitations=['Single-ISP predicate, stats-object access and run-flag result are controlled boundaries; source/config snapshots are explicit.','Imported integer division and roundf are modeled; core native translator/grid/histogram ARM bodies execute.','No HDR, source swap 0, AF stats, iris, cached-frame reuse or full SDK output/context equivalence is claimed.','SDK output is initially zero; arbitrary prior output preservation and frame/configuration association are outside coverage. Live automatic exposure remains unfinished.'])
 (ROOT/'reverse-engineering/rkaiq/ae-linear-translation-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
