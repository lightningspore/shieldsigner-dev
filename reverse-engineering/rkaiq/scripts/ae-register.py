#!/usr/bin/env python3
"""Execute complete native ordinary linear register correction/compensation."""
import copy,hashlib,json,random,runpy,struct,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,HEAP,regs,f32
Base=runpy.run_path(str(Path(__file__).with_name('exposure-decode.py')))['Original']
class Original(Base):
 def __init__(self):
  super().__init__();self.map_address=self.symbols['mapSensorExpToHal']&~1
 def hook(self,uc,address,size,user):
  if address==self.map_address:self.mappings+=1
  name=self.stubs.get(address)
  if name in ['roundf','floorf']:
   value=struct.unpack('<f',struct.pack('<I',uc.reg_read(regs.UC_ARM_REG_S0)))[0]
   self.math.invoke(name,floats=[value]);self.math_calls.add(name)
   uc.reg_write(regs.UC_ARM_REG_S0,self.math.uc.reg_read(regs.UC_ARM_REG_S0));uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def setup(self,v):
  s=v['profile']['sensor_calib'];c=bytearray(0x6000);table=HEAP+0x10000
  struct.pack_into('<III',c,0x638,0,table,7);struct.pack_into('<4f',c,0x644,*s['Time2Reg']['fCoeff']);struct.pack_into('<f',c,0x654,v['analogue_minimum']);struct.pack_into('<H',c,0x678,s['CISTimeSet']['Linear']['CISTimeRegMin']);struct.pack_into('<2f',c,0x684,*s['CISTimeSet']['Linear']['CISTimeRegOdevity']['fCoeff']);struct.pack_into('<f',c,0x6ec,s['CISDcgSet']['Linear']['dcg_ratio']);struct.pack_into('<2f',c,0x778,*v['isp_range']);struct.pack_into('<2f',c,0xfc,*v['time_range']);struct.pack_into('<2f',c,0x104,*v['gain_range']);struct.pack_into('<I',c,0x22f0,1 if v['automatic'] else 2);struct.pack_into('<H',c,0x23c0,0x1000 if v['suppress'] else 0);c[0x23e4]=int(v['flicker']);struct.pack_into('<f',c,0x3cc4,v['quantum']);struct.pack_into('<3f',c,0x3d14,v['frame'],v['clock'],v['line'])
  self.uc.mem_write(HEAP,bytes(c));self.uc.mem_write(table,struct.pack('<7f',*s['Gain2Reg']['GainRange']));return c
 def run(self,v):
  c=self.setup(v)
  self.uc.mem_write(HEAP+0x20000,struct.pack('<3fIIi',v['seconds'],v['gain'],v['isp'],0,0,v['dcg']));self.mappings=0
  status=self.invoke('__AecRegConvertion',[HEAP,HEAP+0x20000,HEAP+0x20004,HEAP+0x20008],stack=struct.pack('<III',HEAP+0x2000c,HEAP+0x20010,HEAP+0x20014),instructions=3000000)
  assert status==0;assert bytes(self.uc.mem_read(HEAP,len(c)))==bytes(c);assert struct.unpack('<i',self.uc.mem_read(HEAP+0x20014,4))[0]==v['dcg']
  time,gain,isp,tc,gc=struct.unpack('<5I',self.uc.mem_read(HEAP+0x20000,20));return ','.join(f'{x:08x}' for x in [tc,gc,gain,time,isp,self.mappings])
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 path=ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json';raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'
 profile=dict(sensor_calib=json.loads(raw)['sensor_calib']);rng=random.Random(0x524547);cases=[]
 for i in range(600):
  p=copy.deepcopy(profile)
  if i>=300:
   scale=[1.,2.][i%2];p['sensor_calib']['Gain2Reg']['GainRange']=[1.,778.24,scale,0.,1.,scale,float(round(778.24*scale))]
  cases.append(dict(profile=p,seconds=f32([.003,.03,.5,.000001,.0001,rng.uniform(.00001,.04)][i%6]),gain=f32([1.,1.24,1.76,2.49,15.5,778.,rng.uniform(1.,778.)][i%7]),isp=f32([1.,1.003,2.,.9][i%4]),dcg=-1,frame=[1360,20416][i%2],clock=114.24,line=2800,isp_range=[1.,[32.,1.][(i//3)%2]],time_range=[.000024,.5],gain_range=[1.,778.24],analogue_minimum=1.,quantum=.01,flicker=bool(i%2),automatic=bool((i//2)%2),suppress=bool((i//5)%2)))
 native=Original();expected=[native.run(v) for v in cases];inputs=''.join('ae-register '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,cases[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,cases=len(cases),actualProfileCases=300,coarseBandCases=300,mismatches=0,armReplayPassed='--arm' in sys.argv,maxMappings=max(int(x.split(',')[-1],16) for x in expected),scope='complete native linear __AecRegConvertion and mapSensorExpToHal through normal return, final codes/gain/time/ISP gain and mapping counts',limitations=['Single positive-slope exponent-one band; SC3336 DCG-disabled path. Coarse test bands deliberately exercise correction branches.','Policy is explicit; calibration/runtime binding and caller queue/result publication remain separate.','Allocator/free and integer division modeled; pinned uClibc powf/roundf/floorf execute as ARM instructions.','Finite valid domain only, no hardware writes; malformed/extreme input resource limit is a checked Rust restriction.'])
 (ROOT/'reverse-engineering/rkaiq/ae-register-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
