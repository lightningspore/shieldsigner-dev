#!/usr/bin/env python3
"""Full native Init/CalibConfig/Prepare execution versus Rust startup binding."""
import copy,hashlib,itertools,json,runpy,struct,subprocess,sys
from pathlib import Path
from differential import OriginalArm,ROOT,BINARY,HEAP,regs
from exposure import RUNTIME
source=runpy.run_path(str(Path(__file__).with_name('ae-initialization.py')))
Base=source['Original']
class Prepare(Base):
 def __init__(self):
  super().__init__();self.math=OriginalArm(RUNTIME,tls=True);self.stubs[self.symbols['xcam_print_log']&~1]='xcam_print_log';self.stages=[];self.math_calls=set();self.stage_addresses={self.symbols[k]&~1:k for k in ['AecStop','AecHwConfig','AecUpdateConfig','AecStart','AecInitEcm']}
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  stage=self.stage_addresses.get(address)
  if stage:self.stages.append(stage)
  if name in ['powf','log10f','floorf','ceilf','roundf']:
   count=2 if name=='powf' else 1;values=[struct.unpack('<f',struct.pack('<I',uc.reg_read(getattr(regs,f'UC_ARM_REG_S{i}'))))[0] for i in range(count)]
   self.math.invoke(name,floats=values);self.math_calls.add(name);uc.reg_write(regs.UC_ARM_REG_S0,self.math.uc.reg_read(regs.UC_ARM_REG_S0))
  elif name=='xcam_print_log':pass
  elif name=='memcmp':
   a,b,n=[uc.reg_read(r) for r in [regs.UC_ARM_REG_R0,regs.UC_ARM_REG_R1,regs.UC_ARM_REG_R2]]
   x=bytes(uc.mem_read(a,n));y=bytes(uc.mem_read(b,n));v=next((a-b for a,b in zip(x,y) if a!=b),0);uc.reg_write(regs.UC_ARM_REG_R0,v&0xffffffff)
  elif name in ['__aeabi_idiv','__aeabi_idivmod','__aeabi_uidiv','__aeabi_uidivmod']:
   a,b=[uc.reg_read(r) for r in [regs.UC_ARM_REG_R0,regs.UC_ARM_REG_R1]]
   if 'uidiv' not in name:a,b=[v if v<0x80000000 else v-0x100000000 for v in (a,b)]
   assert b;v=(abs(a)//abs(b))*(-1 if (a<0)!=(b<0) else 1);uc.reg_write(regs.UC_ARM_REG_R0,v&0xffffffff);uc.reg_write(regs.UC_ARM_REG_R1,(a-v*b)&0xffffffff)
  else:return super().hook(uc,address,size,user)
  uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))

def native_result(v):
 x=Prepare();e=x.initialize(v['profile'])
 a=bytearray(0x300)
 struct.pack_into('<I',a,0,HEAP)
 struct.pack_into('<II',a,0xab*4,v['width'],v['height'])
 struct.pack_into('<3f',a,0xb6*4,float(v['frame']),v['clock'],float(v['line']))
 x.uc.mem_write(HEAP+0x1c0000,bytes(a))
 assert x.invoke('AePrepare',[HEAP+0x1c0000],instructions=10_000_000)==0
 assert x.stages==['AecStop','AecHwConfig','AecUpdateConfig','AecStart','AecInitEcm']
 c=bytes(x.uc.mem_read(e,0x5998));word=lambda o:struct.unpack_from('<I',c,o)[0]
 assert word(0x22dc)==3 and word(0x3d40)==0xffffffff and word(0x5574)==0
 frame=struct.unpack_from('<f',c,0x3d14)[0];assert frame==int(frame)
 words=[int(frame)]+[word(o) for o in [0x5988,0xfc,0x100,0x104,0x108,0x778,0x77c,0x3cc4,0xd4,0xd8,0xdc,0xe0,0xe4,0xe8,0xec,0xf0]]+[c[0x2318]]+list(struct.unpack_from('<45I',c,0x134))
 return ','.join(f'{w:08x}' for w in words),x.math_calls

def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==source['BINARY_SHA']
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text())
 runtime_sha=hashlib.sha256(RUNTIME.read_bytes()).hexdigest();assert runtime_sha==manifest['uclibcRuntime']['memberSha256']
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes()
 assert hashlib.sha256(raw).hexdigest()==source['PROFILE_SHA']
 profile=json.loads(raw);cases=[]
 for i,(seconds,gain,isp,frame,requested_fps,smooth) in enumerate(itertools.product([.003,.005,.03],[1.,2.49],[1.,2.],[1360,20416],[0.,15.],[0,1])):
  p=copy.deepcopy(profile);ae=p['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib']
  ae['LinearAeCtrl']['InitExp'].update(InitTimeValue=seconds,InitGainValue=gain,InitIspDGainValue=isp)
  ae['CommCtrl']['AecSpeed']['SmoothEn']=smooth
  ae['IrisCtrl']['InitAttr']['PIrisGainValue']=[0,512,300,134,100,4096][(i//2)%6]
  ae['CommCtrl']['AecFrameRateMode']['FpsValue']=requested_fps
  delay=[0,2,4][(i//2)%3]
  p['sensor_calib']['CISExpUpdate']['Linear'].update(time_update=delay,gain_update=delay)
  cases.append(dict(profile=p,frame=frame,line=2800,clock=114.24,width=2304 if i%2 else 640,height=1296 if i%2 else 480))
 # Exercise clamp edges, alternate flicker settings and nonexact iris seeds.
 for i in range(12):
  p=copy.deepcopy(profile);ae=p['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib']
  ae['LinearAeCtrl']['InitExp'].update(InitTimeValue=.5 if i%2 else .000001,InitGainValue=900. if i%2 else .5,InitIspDGainValue=3.)
  ae['CommCtrl']['AecFrameRateMode']['FpsValue']=[5.,15.,60.][i%3]
  ae['CommCtrl']['AecAntiFlicker'].update(enable=0 if i%4==0 else 1,Frequency=['AECV2_FLICKER_FREQUENCY_OFF','AECV2_FLICKER_FREQUENCY_50HZ','AECV2_FLICKER_FREQUENCY_60HZ','AECV2_FLICKER_FREQUENCY_AUTO'][i%4],Mode='AECV2_ANTIFLICKER_NORMAL_MODE' if i%2 else 'AECV2_ANTIFLICKER_AUTO_MODE')
  ae['IrisCtrl']['InitAttr']['PIrisGainValue']=[301,299,135][i%3]
  ae['IrisCtrl']['PIrisAttr']['ZeroIsMax']=i%2
  cases.append(dict(profile=p,frame=1360,line=2800,clock=114.24,width=2304,height=1296))
 expected=[];math_calls=set()
 for i,v in enumerate(cases):
  result,calls=native_result(v);expected.append(result);math_calls.update(calls)
  if (i+1)%16==0:print(f'Native preparations: {i+1}/{len(cases)}',file=sys.stderr,flush=True)
 inputs=''.join('ae-preparation '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 replay=ROOT/'dist/reverse-engineering/ae-preparation-replay.json';replay.parent.mkdir(parents=True,exist_ok=True);replay.write_text(json.dumps(dict(inputs=inputs,expected=expected,binarySha256=source['BINARY_SHA'])))
 def compare(command):
  result=subprocess.run(command,input=inputs,text=True,capture_output=True)
  if result.returncode:raise RuntimeError(result.stderr)
  actual=result.stdout.splitlines();assert len(actual)==len(expected),(len(actual),len(expected))
  for i,(a,b) in enumerate(zip(expected,actual)):
   assert a==b,(i,{k:v for k,v in cases[i].items() if k!='profile'},[(j,x,y) for j,(x,y) in enumerate(zip(a.split(','),b.split(','))) if x!=y])
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
  compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=source['BINARY_SHA'],profileSha256=source['PROFILE_SHA'],runtimeSha256=runtime_sha,headerSha256=source['meta'].HEADER_HASHES,cases=len(cases),nativePreparationReturned=True,nativeStages=['AecInit','AecCalibConfig','AecStop','AecHwConfig','AecUpdateConfig','AecStart','AecInitEcm'],nativeRuntimeMath=sorted(math_calls),comparedWordsPerCase=63,mismatches=0,armReplayPassed='--arm' in sys.argv,scope='Fresh ordinary linear auto preparation: complete native lifecycle, selected active timing/limits and initial exposure conversion with all 45 startup smoothing-history words versus Rust profile binding.',limitations=['Native SDK JSON parser is not executed; module lookup returns complete header-derived profile records. Allocation, memory primitives, integer division and diagnostic output use explicit harness boundaries.','Real native uClibc float math executes in a separate isolated emulator.','Fresh mask-zero, fixed-FPS, non-iris, DCG-disabled preparation only. Rust does not yet construct the complete private context or bind all controller/preprocessing/publication state.','No hardware writes, statistics processing or physical exposure application association.'])
 (ROOT/'reverse-engineering/rkaiq/ae-preparation-equivalence.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
