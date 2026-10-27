#!/usr/bin/env python3
"""Populate complete SDK AE/sensor records, require zero-mask native success."""
import copy,hashlib,json,runpy,struct,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,HEAP,regs
from ae_profile_layout import Packer,layout,verify_arm_layout,HEADER_HASHES
source=runpy.run_path(str(Path(__file__).with_name('ae-fps-refresh.py')))
class Original(source['Original']):
 def __init__(self):
  super().__init__(BINARY);self.uc.mem_map(HEAP+0x100000,0x100000)
 def hook(self,uc,address,size,user):
  super().hook(uc,address,size,user)
  if address==(self.symbols['AecUpdateConfig']&~1):
   e=uc.reg_read(regs.UC_ARM_REG_R0);c=uc.reg_read(regs.UC_ARM_REG_R1);self.uc.mem_write(c,self.packet)
   for p,b in self.blocks:self.uc.mem_write(p,b)
   self.uc.mem_write(e+0x3fd8,bytes([0xa5])*220);self.uc.mem_write(e+0x3d40,struct.pack('<I',23));self.uc.mem_write(e+0x4fb9,b'\x09')
 def result(self,v,seed):
  p=Packer();iq=v['profile'];scene=iq['main_scene'][0]['sub_scene'][0]['scene_isp32'];self.packet=p.pack('CalibDb_Aec_ParaV2_t',scene['ae_calib'])+p.pack('CalibDb_Sensor_ParaV2_t',iq['sensor_calib']);self.blocks=p.blocks;assert len(self.packet)==0x1d2c
  args=dict(v,scene=scene,mask=0,minimum_fps=1.,baseline_frame=1360.,baseline_fps=30.,factors=[0.,0.,1.,.5],minimum=1,maxfactors=[1.,8.],route_min=0.,route_max=.03,override=False,override_min=0.,override_max=0.,enabled=True,mode=0)
  self.bounds(args,seed);e=HEAP+0x40000;c=bytes(self.uc.mem_read(e,0x5998));u=lambda o:struct.unpack_from('<I',c,o)[0]
  offsets=[0x3d24,0x3d28,0x3d2c,0x3d30,0x3d14,0x5988,0x10,0x14,0x2404,0x2408,0x240c,0x2410]
  words=[u(o) for o in offsets]+[c[o] for o in [0x40d0,0x40d1,0x2318,0x2319]]+[u(o) for o in [0xdc,0xe0,0xe8,0xd4,0x3d40]]+[c[0x4fb9],c[0x23f4],u(0x23f8)]+list(struct.unpack_from('<55I',c,0x3fd8))
  return ','.join(f'{w:08x}' for w in words)
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest=='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a';iq=json.loads(raw);assertions=verify_arm_layout();cases=[]
 for smooth in [0,1]:
  for delay in [[0,0],[2,2],[3,1],[9,8]]:
   for frame in [1360.,20416.]:
    for seconds in [.003,.005]:
     p=copy.deepcopy(iq);ae=p['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib'];ae['CommCtrl']['AecSpeed']['SmoothEn']=smooth;ae['LinearAeCtrl']['InitExp']['InitTimeValue']=seconds;p['sensor_calib']['CISExpUpdate']['Linear'].update(time_update=delay[0],gain_update=delay[1])
     cases.append(dict(profile=p,frame=frame,line=2800.,clock=114.24))
 init=runpy.run_path(str(Path(__file__).with_name('ae-initialization.py')))['Original']();init.initialize(iq);_,config=struct.unpack('<2I',init.uc.mem_read(HEAP,8));seed=bytes(init.uc.mem_read(config+0x1d3c,633));native=Original();expected=[native.result(v,seed) for v in cases];inputs=''.join('ae-zero-config '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 def compare(cmd):
  actual=subprocess.run(cmd,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,[(j,x,y) for j,(x,y) in enumerate(zip(a.split(','),b.split(','))) if x!=y])
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  b=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={b.parent},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=digest,headerSha256=HEADER_HASHES,armLayoutAssertions=assertions,aeBytes=0x1c20,sensorBytes=0x10c,pointerArrays=41,cases=len(cases),nativeZeroMaskReturned=True,mismatches=0,armReplayPassed='--arm' in sys.argv,scope='complete zero-mask native configuration success using header-derived AE/sensor profile records; selected FPS/policy/delay/smoothing/initial-exposure/reset fields compared',limitations=['Native profile JSON parser is not executed; explicit header-derived records and zero-padded unused fixed-table storage are supplied.','Runtime geometry is explicit; allocation/comparison/division/rounding/diagnostics use inherited harness boundaries.','Measurement seed now comes from real AecInit/AecCalibConfig execution; configuration still runs in a separate explicitly initialized context, and complete engine-context equivalence remains unqualified.','No hardware writes or physical frame/exposure association.'])
 (ROOT/'reverse-engineering/rkaiq/ae-zero-config-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
