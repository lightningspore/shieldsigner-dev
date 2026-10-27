#!/usr/bin/env python3
"""AWB result publisher against original ARM control flow and record copies."""
import hashlib,itertools,json,struct,subprocess,sys
from differential import OriginalArm,ROOT,BINARY,HEAP
import unicorn.arm_const as regs
SYMBOL='_ZN5RkCam17RkAiqAwbHandleInt12genIspResultEPNS_15RkAiqFullParamsES2_'
class Original(OriginalArm):
 def __init__(self):
  super().__init__(BINARY)
  self.assign={p&~1 for n,p in self.symbols.items() if 'SmartPtr' in n and ('20rk_aiq_wb_gain_v32_s' in n or '25rk_aiq_awb_stat_cfg_v32_s' in n) and 'aSERKS' in n}
  assert len(self.assign)==2
 def hook(self,uc,address,size,user):
  if address in getattr(self,'assign',set()):
   a=uc.reg_read(regs.UC_ARM_REG_R0);b=uc.reg_read(regs.UC_ARM_REG_R1)
   uc.mem_write(a,bytes(uc.mem_read(b,8)));uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if address==(self.symbols.get('xcam_print_log',0)&~1):
   uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v):
  h=HEAP;p=HEAP+0x1000;latest=HEAP+0x2000;flags=HEAP+0x3000;frame=HEAP+0x4000;core=HEAP+0x5000;algo=HEAP+0x6000
  self.uc.mem_write(HEAP,bytes(0x10000))
  def put(a,x):self.uc.mem_write(a,struct.pack('<I',x&0xffffffff))
  def byte(a,x):self.uc.mem_write(a,bytes([x]))
  for offset,value in [(0x14,flags),(0x20,algo),(0x28,core),(0x34,frame),(0xb0,v['gain_sync']),(0xb4,v['config_sync'])]:put(h+offset,value)
  byte(h+0xa0,v['bypass']);put(algo+0x10,v['algorithm_id']);put(frame+4,v['frame']);byte(core+0xd1,v['initial']);byte(flags+8,v['gain_changed']);byte(flags+1,v['config_changed'])
  for base,off,proxy,record,n,fill,yes,sync in [(p,0x40,HEAP+0x7000,HEAP+0x8000,20,0x11,True,v['gain_item_sync']),(p,0x38,HEAP+0x7100,HEAP+0x9000,1204,0x22,True,v['item_sync']),(latest,0x40,HEAP+0x7200,HEAP+0xa000,20,0x33,v['latest_gain'],v['item_sync']),(latest,0x38,HEAP+0x7300,HEAP+0xb000,1204,0x44,v['latest_config'],v['item_sync'])]:
   if yes:put(base+off,proxy)
   put(proxy+0x6c,record);self.uc.mem_write(record+8,bytes([fill])*n);byte(record+4,1);put(record+(0x1c if n==20 else 0x4bc),99);put(record+(0x20 if n==20 else 0x4c0),sync)
  self.invoke(SYMBOL,[h,p,latest])
  def word(a):return struct.unpack('<I',self.uc.mem_read(a,4))[0]
  gain=HEAP+0x8000;cfg=HEAP+0x9000
  def data(proxy,n):return bytes(self.uc.mem_read(word(proxy+0x6c)+8,n)).hex() if proxy else None
  return dict(gain_sync=word(h+0xb0),config_sync=word(h+0xb4),gain_frame=word(gain+0x1c),config_frame=word(cfg+0x4bc),gain_item_sync=word(gain+0x20),config_item_sync=word(cfg+0x4c0),gain_updated=bool(self.uc.mem_read(gain+4,1)[0]),config_updated=bool(self.uc.mem_read(cfg+4,1)[0]),gain_data=bytes(self.uc.mem_read(gain+8,20)).hex(),config_data=bytes(self.uc.mem_read(cfg+8,1204)).hex(),gain_changed=bool(self.uc.mem_read(flags+8,1)[0]),config_changed=bool(self.uc.mem_read(flags+1,1)[0]),latest_gain=data(word(latest+0x40),20),latest_config=data(word(latest+0x38),1204))
def main():
 sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert sha==json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text())['binaries'][0]['sha256']
 original=Original();cases=[];expected=[]
 for i,bits in enumerate(itertools.product([False,True],repeat=7)):
  gc,cc,lg,lc,initial,bypass,equal=bits
  for algo in [0,1]:
   v=dict(gain_changed=gc,config_changed=cc,latest_gain=lg,latest_config=lc,initial=initial,bypass=bypass,algorithm_id=algo,gain_sync=7,config_sync=7 if equal else 8,item_sync=7 if equal else 9,gain_item_sync=[7,9,15][i%3],frame=[0,12,0xffffffff][i%3])
   cases.append(v);expected.append(original.run(v))
 inputs=''.join('awb-publication '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(command):
  p=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True);actual=[json.loads(s) for s in p.stdout.splitlines()]
  assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):
   if a!=b:raise AssertionError((i,cases[i],{k:(a[k],b[k]) for k in a if a[k]!=b[k]}))
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')]);arm='--arm' in sys.argv
 if arm:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
  compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=sha,cases=len(cases),host=True,arm=arm,mismatches=0,comparison='Publisher sync/frame/update fields, consumed controller flags, complete gain/configuration payloads and latest payloads',limitations=['C++ smart-pointer assignment uses an explicit pointer-pair adapter; refcounts and logging are not reconstructed.','AWB numerical controller, manager list ownership and physical ISP submission remain separate.'])
 (ROOT/'reverse-engineering/rkaiq/awb-publication-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
