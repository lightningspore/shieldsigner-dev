#!/usr/bin/env python3
"""Execute mapSensorExpToHal with actual SC3336 calibration and uClibc math."""
import hashlib,json,random,struct,subprocess,sys
from exposure import OriginalExposure,RUNTIME
from differential import ROOT,BINARY,HEAP,regs
class Original(OriginalExposure):
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name in ['malloc','free','__aeabi_uidiv']:
   a=uc.reg_read(regs.UC_ARM_REG_R0);b=uc.reg_read(regs.UC_ARM_REG_R1)
   if name=='malloc':assert a<=4096;uc.reg_write(regs.UC_ARM_REG_R0,HEAP+0x70000)
   elif name=='free':assert a==HEAP+0x70000
   else:assert b;uc.reg_write(regs.UC_ARM_REG_R0,a//b)
   uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,v):
  s=v['profile']['sensor_calib'];c=bytearray(0x6000);table=HEAP+0x10000
  struct.pack_into('<III',c,0x638,0,table,s['Gain2Reg']['GainRange_len']);struct.pack_into('<4f',c,0x644,*s['Time2Reg']['fCoeff']);struct.pack_into('<f',c,0x6ec,s['CISDcgSet']['Linear']['dcg_ratio']);struct.pack_into('<3f',c,0x3d14,v['frame'],v['clock'],v['line'])
  self.uc.mem_write(HEAP,bytes(c));self.uc.mem_write(table,struct.pack('<7f',*s['Gain2Reg']['GainRange']));self.uc.mem_write(HEAP+0x20000,bytes(8))
  assert self.invoke('mapSensorExpToHal',[HEAP,v['gain_code'],v['time_code'],v['dcg']],stack=struct.pack('<II',HEAP+0x20000,HEAP+0x20004),instructions=1000000)==0
  assert bytes(self.uc.mem_read(HEAP,len(c)))==bytes(c)
  return self.bits(0x20000,2)
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());assert hashlib.sha256(RUNTIME.read_bytes()).hexdigest()==manifest['uclibcRuntime']['memberSha256']
 path=ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json';raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'
 profile=dict(sensor_calib=json.loads(raw)['sensor_calib']);cases=[];rng=random.Random(0x444543)
 for i in range(512):
  cases.append(dict(profile=profile,gain_code=[128,129,256,99614,rng.randrange(128,99615)][i%5],time_code=[0,1,122,1224,20400,rng.randrange(20000)][i%6],frame=[1360,20416][i%2],clock=[114.24,24.,72.][i%3],line=[2800,2600,3000][i%3],dcg=[-1,0][i%2]))
 native=Original();expected=[native.run(v) for v in cases];inputs=''.join('exposure-decode '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,cases=len(cases),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='complete native mapSensorExpToHal with actual SC3336 calibration; gain and shutter float bits',limitations=['Linear SC3336 positive-slope calibrated gain band only in this corpus; other model/exponent branches remain unqualified.','Allocator/free and integer division are modeled; native uClibc powf executes.','No register-code correction, ISP compensation, scheduling or live writes are claimed.'])
 (ROOT/'reverse-engineering/rkaiq/exposure-decode-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
