#!/usr/bin/env python3
"""Execute normal AecUpdateConfig return and inspect its flicker timing fields."""
import hashlib,json,runpy,struct,subprocess,sys,math
from pathlib import Path
from differential import ROOT,BINARY,HEAP,regs
source=runpy.run_path(str(Path(__file__).with_name('ae-configuration.py')))
class OriginalFlicker(source['Prefix']):
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name in ('ceilf','floorf','roundf'):
   value=struct.unpack('<f',struct.pack('<I',uc.reg_read(regs.UC_ARM_REG_S0)))[0]
   if math.isfinite(value):value=math.ceil(value) if name=='ceilf' else (math.floor(value) if name=='floorf' else (math.floor(value+.5) if value>=0 else math.ceil(value-.5)))
   uc.reg_write(regs.UC_ARM_REG_S0,struct.unpack('<I',struct.pack('<f',value))[0]);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if address==(self.symbols['AecUpdateConfig']&~1):
   engine=uc.reg_read(regs.UC_ARM_REG_R0);config=uc.reg_read(regs.UC_ARM_REG_R1);v=self.case
   uc.mem_write(config+0x164,bytes([v['enabled']]));uc.mem_write(config+0x168,struct.pack('<i',v['frequency']));uc.mem_write(config+0x16c,bytes(4));uc.mem_write(config+0x2004,struct.pack('<f',v['detected']))
   for pointer,value in [(config+0x1fd0,1320.),(config+0x1fd4,v['clock']),(config+0x1fd8,v['line']),(engine+0x64c,v['coefficient']),(engine+0x3cc4,v['prior']),(engine+0x576c,v['alternate'])]:uc.mem_write(pointer,struct.pack('<f',value))
  super().hook(uc,address,size,user)
 def run(self,v,seed):
  self.case=v;self.full_call=True
  self.prefix(dict(width=2304,height=1296,input=[0,0,1,1],tone=[.1,.1,.9,.9],hist=5,raw=4,range=1,mask=0,weights=[1]*225),seed)
  engine=HEAP+0x40000;frequency=struct.unpack('<i',self.uc.mem_read(engine+0x23e8,4))[0];q=struct.unpack('<I',self.uc.mem_read(engine+0x3cc4,4))[0];alternate=struct.unpack('<I',self.uc.mem_read(engine+0x576c,4))[0]
  return f'{frequency}:{q:08x}:{alternate:08x}'
def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 init=source['Init']();init.uc.mem_write(HEAP,bytes(8));init.invoke('AecInit',[HEAP,HEAP+0x80000,4]);arm=OriginalFlicker(BINARY)
 cases=[]
 for frequency in [-1,0,1,2,3,4]:
  for period in [0.,1/120,.01,.02,-.01,.01000011,.01000013,.00833344,.00833347]:
   cases.append(dict(enabled=True,frequency=frequency,detected=period,prior=.012345,alternate=.023456,line=2500.,clock=99.,coefficient=1.))
 for coefficient in [1.,2.,.5]:cases.append(dict(enabled=False,frequency=3,detected=.01,prior=.012345,alternate=.023456,line=2500.,clock=72.,coefficient=coefficient))
 expected=[arm.run(v,init.defaults) for v in cases];inputs=''.join('ae-flicker '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  actual=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b)in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
  compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly',image,'/bincheck/numeric-fixture'])
 report=dict(binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='flicker frequency selector and primary/alternate quantums after normal native AecUpdateConfig return under update mask 0x80',limitations=['Calibration timing and prior state are explicitly injected at method entry; complete private-context equivalence is not claimed.','Allocation, memory comparisons, imported integer division and ceilf/floorf/roundf are explicit harness boundaries.','Detected input is a period in seconds; automatic period estimation and shutter min/max policy remain unfinished.'])
 (ROOT/'reverse-engineering/rkaiq/ae-flicker-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
