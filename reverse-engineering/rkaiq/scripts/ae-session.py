#!/usr/bin/env python3
"""Full native SDK AE wrappers on persistent, genuinely prepared contexts."""
import copy,hashlib,json,runpy,struct,subprocess,sys
from pathlib import Path
from differential import ROOT,BINARY,HEAP,regs
source=runpy.run_path(str(Path(__file__).with_name('ae-preparation.py')))
class Original(source['Prepare']):
 def __init__(self):
  super().__init__();self.frame_calls={k:0 for k in ['AePreProcess','AecPreProcess','AecGetPreResults','AeProcessing','AecGetEnvLgt','AecRun','AecGetProcResults']};self.frame_entries={self.symbols[k]&~1:k for k in self.frame_calls}
 def hook(self,uc,address,size,user):
  stage=self.frame_entries.get(address)
  if stage:self.frame_calls[stage]+=1
  if self.stubs.get(address)=='pow':
   values=[struct.unpack('<d',struct.pack('<Q',uc.reg_read(getattr(regs,f'UC_ARM_REG_D{i}'))))[0] for i in range(2)]
   self.math.invoke('pow',doubles=values);self.math_calls.add('pow');uc.reg_write(regs.UC_ARM_REG_D0,self.math.uc.reg_read(regs.UC_ARM_REG_D0));uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def prepare(self,v):
  self.engine=self.initialize(v['profile']);a=bytearray(0x300);struct.pack_into('<I',a,0,HEAP)
  struct.pack_into('<2I',a,0xab*4,v['width'],v['height']);struct.pack_into('<3f',a,0xb6*4,float(v['frame']),114.24,2800.)
  self.uc.mem_write(HEAP+0x1c0000,bytes(a));assert self.invoke('AePrepare',[HEAP+0x1c0000],instructions=10_000_000)==0
  self.uc.mem_write(HEAP+0x1f0000,struct.pack('<6I',0,HEAP+0x1e0000,HEAP+0x1e1000,HEAP+0x1e2000,0,HEAP+0x1e3000))
  self.wrappers(0,True,0)
 def wrappers(self,frame,initial,stats):
  call=bytearray(0x40);struct.pack_into('<3I',call,0,HEAP,frame,int(initial));struct.pack_into('<I',call,0x28,stats)
  self.uc.mem_write(HEAP+0x1c0000,bytes(call))
  assert self.invoke('AePreProcess',[HEAP+0x1c0000,HEAP+0x1d4000],instructions=10_000_000)==0
  assert self.invoke('AeProcessing',[HEAP+0x1c0000,HEAP+0x1f0000],instructions=10_000_000)==0
 def exposure(self):
  c=bytes(self.uc.mem_read(self.engine,0x5998));r=bytearray(244)
  for a,b in [(0,0xe8),(4,0xdc),(12,0xe0),(20,0xe4),(32,0xec),(36,0xf0),(196,0x2024),(200,0x2020),(236,0x3d18)]:r[a:a+4]=c[b:b+4]
  struct.pack_into('<f',r,8,1.);struct.pack_into('<H',r,228,int(struct.unpack_from('<f',c,0x3d1c)[0]));struct.pack_into('<I',r,232,int(struct.unpack_from('<f',c,0x3d14)[0]))
  return bytes(r)
 def step(self,frame):
  stats=bytearray(0x3000);stats[0x2e28:0x2e28+244]=bytes.fromhex(frame['effective'])
  struct.pack_into('<4H',stats,0x2e20,*frame['q8']);struct.pack_into('<256I',stats,0x788,*frame['histogram'])
  self.uc.mem_write(HEAP+0x1d0000,bytes(stats));self.wrappers(frame['id'],False,HEAP+0x1d0000)
 def snapshot(self):
  c=bytes(self.uc.mem_read(self.engine,0x5998));u=lambda o:struct.unpack_from('<I',c,o)[0]
  if self.frame_calls['AecGetPreResults']:
   # AePreProcess passes output+4 to AecGetPreResults, whose linear
   # word 12 is c+0x251c. awbProcessing binds this output+0x34.
   assert bytes(self.uc.mem_read(HEAP+0x1d4000+0x34,4))==c[0x251c:0x2520], 'AE/AWB normalized-brightness result binding'
  offsets=[0xd4,0xdc,0xe0,0xe8,0xec,0xf0,0x12c,0x130,0x124,0x128,0xd8,0x5574,0x3d40,0x22fc,0x4198]
  words=[u(o) for o in offsets]+[c[o] for o in [0x4fb8,0x4fb9,0x5994,0x5995,0x23cf,0x3d3c]]+[u(o) for o in [0x40f4,0x40f8]]+[c[o] for o in [0x40fc,0x40fd]]+[u(o) for o in [0x3ccc,0x3cc8,0x3cdc,0x3d00,0x3cec]]
  words+=[u(0x2c50+i*64) for i in range(10)]+list(struct.unpack_from('<3H',c,0x404))+[u(0x118)]+[u(o) for o in [0x3c8,0x3cc,0x3d0]]
  pre=[u(o) for o in [0x2300,0x3b4,0x3b0,0x251c]]+[c[o] for o in [0x4fba,0x4fbb]]+[u(0x23d4),c[0x23ce]]
  return dict(words=words,pre=pre,history=c[0x3fd8:0x40b4].hex(),published=c[0x4fbc:0x4fbc+1464].hex(),previous=c[0x4c30:0x4c30+244].hex(),empty=c[0x4ec8:0x4ec8+244].hex(),exposure=c[0x2414:0x2414+244].hex(),route=list(struct.unpack('<'+'I'*u(0x3c84),self.uc.mem_read(u(0x3c8c),4*u(0x3c84)))))

def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==source['source']['BINARY_SHA']
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==source['source']['PROFILE_SHA'];profile=json.loads(raw)
 assert hashlib.sha256(source['RUNTIME'].read_bytes()).hexdigest()==json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text())['uclibcRuntime']['memberSha256']
 cases=[];expected=[];math_calls=set();processed=0;skipped=0;calls={}
 for k in range(1 if '--probe' in sys.argv else 8):
  p=copy.deepcopy(profile);ae=p['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib'];ae['LinearAeCtrl']['InitExp']['InitTimeValue']=[.003,.005][k%2]
  ae['CommCtrl']['AecSpeed']['SmoothEn']=0 if k%4==3 else 1
  p['sensor_calib']['CISExpUpdate']['Linear'].update(time_update=[0,2,4][k%3],gain_update=[0,2,4][k%3])
  v=dict(profile=p,frame=1360,width=2304 if k%2 else 640,height=1296 if k%2 else 480,frames=[])
  native=Original();native.prepare(v);snapshots=[native.snapshot()]
  for i in range(2 if '--probe' in sys.argv else 16):
   measured=[45.,45.,3.,0.,120.,240.,45.,45.][(i+k)%8];histogram=[0]*256;histogram[min(255,int(measured))]=1000
   frame=dict(id=i,q8=[int(measured*256),512,768,1024],histogram=histogram,effective=native.exposure().hex())
   native.step(frame);v['frames'].append(frame);snapshots.append(native.snapshot())
   if native.uc.mem_read(native.engine+0x22ed,1)[0]:processed+=1
   else:skipped+=1
  assert native.frame_calls['AecPreProcess']==len(v['frames'])
  assert native.frame_calls['AecGetPreResults']==len(v['frames'])
  assert native.frame_calls['AecGetEnvLgt']==len(v['frames'])
  assert native.frame_calls['AecRun']==len(v['frames'])+1
  assert native.frame_calls['AecGetProcResults']==len(v['frames'])+1
  for name,n in native.frame_calls.items():calls[name]=calls.get(name,0)+n
  cases.append(v);expected.append(snapshots);math_calls.update(native.math_calls)
  print(f'Native session {k+1}: {len(v["frames"])} complete frames',file=sys.stderr,flush=True)
 inputs=''.join('ae-session '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 replay=ROOT/'dist/reverse-engineering/ae-session-replay.json';replay.write_text(json.dumps(dict(inputs=inputs,expected=expected)))
 def compare(command):
  result=subprocess.run(command,input=inputs,text=True,capture_output=True)
  if result.returncode:raise RuntimeError(result.stderr)
  actual=[json.loads(line) for line in result.stdout.splitlines()];assert len(actual)==len(expected)
  for i,(aa,bb) in enumerate(zip(expected,actual)):
   assert len(aa)==len(bb)
   for j,(a,b) in enumerate(zip(aa,bb)):
    for key in a:
     if a[key]!=b[key]:
      if isinstance(a[key],list):detail=[(i,f'{x:08x}',f'{y:08x}') for i,(x,y) in enumerate(zip(a[key],b[key])) if x!=y]
      else:detail=[(i,x,y) for i,(x,y) in enumerate(zip(bytes.fromhex(a[key]),bytes.fromhex(b[key]))) if x!=y][:16]
      raise AssertionError((i,j,key,detail))
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
  compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=source['source']['BINARY_SHA'],profileSha256=source['source']['PROFILE_SHA'],runtimeSha256=hashlib.sha256(source['RUNTIME'].read_bytes()).hexdigest(),headerSha256=source['source']['meta'].HEADER_HASHES,processed=processed,skipped=skipped,nativeCalls=calls,sequences=len(cases),frames=sum(len(v['frames']) for v in cases),awbPreResultBrightnessOffset=52,awbPreResultBrightnessChecks=sum(len(v['frames']) for v in cases),nativeMath=sorted(math_calls),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='Real initialization/preparation, initial publication, then complete native AePreProcess/AeProcessing wrappers on persistent contexts versus profile-bound Rust standard linear sessions.',limitations=['Fixed-rate ordinary auto SC3336 profile; backlight/overexposure/lux/automatic-flicker/HDR/iris/DCG modes remain excluded from the Rust session.','Allocation, module lookup, memory primitives, integer division and logs are modeled; native pinned uClibc math executes.','Only listed preprocessing/controller/publication/sample state, full exposure-info record, publication records, control history and route times are compared; AE pre-result normalized brightness at offset 0x34 is additionally checked against its source; other unlisted context and ISP/pre-result structures excluded.','Effective exposure for each frame is the previous native proposal, replayed as an explicit common input; this is not physical application latency or hardware association. No sensor/ISP writes.'])
 if '--probe' not in sys.argv:(ROOT/'reverse-engineering/rkaiq/ae-session-equivalence.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
