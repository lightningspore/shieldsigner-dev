#!/usr/bin/env python3
"""Execute real AE construction/calibration and compare Rust activation rules.

Only allocation and profile module lookup are modeled during construction.
All profile copying and start/stop instructions execute in the original ELF.
"""
import copy,ctypes,hashlib,json,random,struct,subprocess,sys
from differential import OriginalArm,ROOT,BINARY,HEAP,regs
import ae_profile_layout as meta
ACCESSOR='_ZL24calibdbV2_get_module_ptrPvP19calibdb_ctx_infos_sPKc.constprop.10'
BINARY_SHA='ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
PROFILE_SHA='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'

class Original(OriginalArm):
 def __init__(self):
  super().__init__(BINARY)
  self.uc.mem_map(HEAP+0x100000,0x100000)
  self.next=HEAP+0x10000;self.owned={};self.queries=[]
  try:self.resolve_symbol(ACCESSOR)
  except RuntimeError:pass
  else:raise AssertionError('Duplicate helper must require explicit entry')
  self.module_address=self.resolve_symbol(ACCESSOR,entry=0xb6b5c)&~1
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if address==getattr(self,'module_address',None):
   query=bytes(uc.mem_read(uc.reg_read(regs.UC_ARM_REG_R1),100)).split(b'\0')[0].decode()
   self.queries.append(query)
   pointer={'ae_calib':HEAP+0x180000,'sensor_calib':HEAP+0x190000,'module_calib':HEAP+0x1a0000}[query]
   uc.reg_write(regs.UC_ARM_REG_R0,pointer)
  elif name in ('calloc','malloc'):
   a=uc.reg_read(regs.UC_ARM_REG_R0);n=a*uc.reg_read(regs.UC_ARM_REG_R1) if name=='calloc' else a
   assert 0<n<0x10000
   pointer=self.next;self.next+=(n+4095)&~4095
   assert self.next<HEAP+0x100000,'Allocator/profile arenas must not overlap'
   self.owned[pointer]=n
   # Poison malloc so missing initialization cannot accidentally pass as zero.
   uc.mem_write(pointer,bytes(n) if name=='calloc' else bytes([0xa5])*n)
   uc.reg_write(regs.UC_ARM_REG_R0,pointer)
  elif name=='free':
   pointer=uc.reg_read(regs.UC_ARM_REG_R0);assert pointer==0 or pointer in self.owned
   if pointer:del self.owned[pointer]
  else:return super().hook(uc,address,size,user)
  uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))
 def canonical(self,name,blob):
  """Normalize pointer addresses while preserving complete pointed contents."""
  out=bytearray(blob);payloads={};t=meta.layout(name)
  for base,pointer,key,count in meta.fields.get(name,[]):
   offset=getattr(t,key).offset
   if pointer:
    n=struct.unpack_from('<i',blob,getattr(t,key+'_len').offset)[0]
    address=struct.unpack_from('<I',blob,offset)[0]
    assert 0<=n<=4096
    out[offset:offset+4]=bytes(4)
    size=n*ctypes.sizeof(meta.layout(base))
    payloads[key]=(address,bytes(self.uc.mem_read(address,size)) if size else b'')
   elif base in meta.fields:
    n=int(meta.macros.get(count,count)) if count else 1;size=ctypes.sizeof(meta.layout(base))
    for i in range(n):
     part,children=self.canonical(base,blob[offset+i*size:offset+(i+1)*size])
     out[offset+i*size:offset+(i+1)*size]=part
     payloads.update({f'{key}[{i}].{k}':v for k,v in children.items()})
  return bytes(out),payloads
 def initialize(self,profile):
  packer=meta.Packer()
  records=[('CalibDb_Aec_ParaV2_t',profile['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib'],0x180000,0),('CalibDb_Sensor_ParaV2_t',profile['sensor_calib'],0x190000,0x1c20),('CalibDb_Module_ParaV2_t',profile['module_calib'],0x1a0000,0x1d2c)]
  packets=[packer.pack(name,value) for name,value,_,_ in records]
  assert list(map(len,packets))==[7200,268,16]
  for (_,_,source,_),packet in zip(records,packets):self.uc.mem_write(HEAP+source,packet)
  for address,blob in packer.blocks:self.uc.mem_write(address,blob)
  self.uc.mem_write(HEAP,bytes(8))
  assert self.invoke('AecInit',[HEAP,HEAP+0x1b0000,4],instructions=3_000_000)==0
  engine,config=struct.unpack('<2I',self.uc.mem_read(HEAP,8))
  assert self.owned[engine]==0x5998 and self.owned[config]==0x25a4
  assert self.queries==['ae_calib','sensor_calib','module_calib']
  pointers=0
  for (name,_,source_offset,offset),packet in zip(records,packets):
   expected,payloads=self.canonical(name,packet)
   actual,copies=self.canonical(name,bytes(self.uc.mem_read(config+offset,len(packet))))
   if offset==0x1c20:
    # Native calibration deliberately leaves the sensor resolution word zero.
    assert actual[:4]==bytes(4);expected=bytes(4)+expected[4:]
   assert actual==expected,(name,'fixed record mismatch')
   assert payloads.keys()==copies.keys()
   for key,(source,data) in payloads.items():
    target,copied=copies[key];assert copied==data,(name,key)
    if data:
     assert target!=source and self.owned[target]==len(data),(name,key,'not an owned deep copy')
     pointers+=1
   assert bytes(self.uc.mem_read(HEAP+source_offset,len(packet)))==packet,'Input root modified'
  assert pointers==41 and len(self.owned)==43
  for address,blob in packer.blocks:assert bytes(self.uc.mem_read(address,len(blob)))==blob,'Input table modified'
  assert struct.unpack('<I',self.uc.mem_read(engine+0x22dc,4))[0]==1
  assert struct.unpack('<I',self.uc.mem_read(engine+0x3d40,4))[0]==0xffffffff
  assert bytes(self.uc.mem_read(engine+0x3fd8,220))==bytes(220)
  return engine

def sequence(native,engine,initial,present,operations):
 native.uc.mem_write(engine+0x22dc,struct.pack('<I',initial))
 output=[]
 for op in operations:
  before=bytes(native.uc.mem_read(engine,0x5998))
  result=native.invoke('AecStart' if op=='s' else 'AecStop',[engine if present else 0])
  after=bytes(native.uc.mem_read(engine,0x5998))
  assert before[:0x22dc]==after[:0x22dc] and before[0x22e0:]==after[0x22e0:],'Unexpected context mutation'
  output.append(f'{result:02x}:{struct.unpack_from("<I",after,0x22dc)[0]:08x}')
 return ','.join(output)

def main():
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==BINARY_SHA
 raw=(ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_bytes()
 assert hashlib.sha256(raw).hexdigest()==PROFILE_SHA
 profile=json.loads(raw);assertions=meta.verify_arm_layout();lines=[];expected=[]
 for i in range(8):
  p=copy.deepcopy(profile);ae=p['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib']
  ae['LinearAeCtrl']['InitExp']['InitTimeValue']=.003+i*.001
  p['module_calib']['sensor_module']['FNumber']=1.6+i*.1
  native=Original();engine=native.initialize(p)
  operations='ssttsts';lines.append(f'ae-lifecycle 00000001 1 {operations}')
  expected.append(sequence(native,engine,1,True,operations))
 # Include malformed numeric states to retain the actual permissive predicates.
 rng=random.Random(0x4145494e);states=list(range(9))+[0xfffffffe,0xffffffff]+[rng.getrandbits(32) for _ in range(32)]
 native=OriginalArm(BINARY);engine=HEAP+0x1000
 native.uc.mem_write(engine,bytes(rng.randrange(256) for _ in range(0x5998)))
 for initial in states:
  for present in (False,True):
   for operations in ('st','ts','ssttsts'):
    lines.append(f'ae-lifecycle {initial:08x} {int(present)} {operations}')
    expected.append(sequence(native,engine,initial,present,operations))
 inputs='\n'.join(lines)+'\n'
 def compare(command):
  actual=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True).stdout.splitlines()
  assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,(i,lines[i],a,b)
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
  compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=BINARY_SHA,profileSha256=PROFILE_SHA,headerSha256=meta.HEADER_HASHES,armLayoutAssertions=assertions,constructorCases=8,ownedDeepCopiesPerConstructor=41,allocationsPerConstructor=43,aeBytes=7200,sensorBytes=268,moduleBytes=16,lifecycleSequences=len(lines),lifecycleCalls=sum(len(line.split()[-1]) for line in lines),mismatches=0,armReplayPassed='--arm' in sys.argv,scope='Native AecInit and AecCalibConfig execution, deep-copy ownership and complete copied profile records; native start/stop status and context mutation compared with Rust.',boundaries=['Allocation and profile module lookup are modeled; memory primitives use explicit harness implementations. malloc memory is poisoned, calloc memory zeroed.','Native JSON parser is not executed. Sensor resolution is deliberately left zero by calibration; runtime geometry is a later preparation input.','Rust lifecycle reproduces algorithm activation only; full Rust constructor, preparation, runtime binding and live control remain incomplete.','No hardware writes or physical frame association.'])
 (ROOT/'reverse-engineering/rkaiq/ae-initialization-equivalence.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
