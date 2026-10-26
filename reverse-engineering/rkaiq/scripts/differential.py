#!/usr/bin/env python3
"""Compare Rust numerical reconstructions with the pinned ARM machine code.

The original library executes only in Unicorn, never as a host shared library.
Dynamic imports are refused except the explicit memcpy/memmove/memset stubs.
"""
from pathlib import Path
import argparse,hashlib,json,random,struct,subprocess
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE
import unicorn.arm_const as regs

ROOT=Path(__file__).resolve().parents[3]
BINARY=ROOT/'.tools/reverse-engineering/rkaiq-original/librkaiq.so'
BASE=0x10000;HEAP=0x2000000;RETURN=0x3000000;STACK=0x4000000
u32=lambda b:struct.unpack('<I',b)[0]
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
fhex=lambda x:f'{u32(struct.pack("<f",x)):08x}'
class OriginalArm:
 def __init__(self,path):
  self.uc=Uc(UC_ARCH_ARM,UC_MODE_ARM|UC_MODE_LITTLE_ENDIAN);self.symbols={};self.stubs={}
  with path.open('rb') as f:
   e=ELFFile(f);segments=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD']
   lo=min(BASE+s['p_vaddr'] for s in segments)&~4095
   hi=(max(BASE+s['p_vaddr']+s['p_memsz'] for s in segments)+4095)&~4095
   self.uc.mem_map(lo,hi-lo)
   for s in segments:self.uc.mem_write(BASE+s['p_vaddr'],s.data())
   for s in e.get_section_by_name('.symtab').iter_symbols():
    if s['st_info']['type']=='STT_FUNC' and s['st_shndx']!='SHN_UNDEF':self.symbols[s.name]=BASE+s['st_value']
   self.uc.mem_map(HEAP,0x100000);self.uc.mem_map(RETURN,0x10000);self.uc.mem_map(STACK,0x100000)
   dyn=e.get_section_by_name('.dynsym')
   for section in e.iter_sections():
    if section['sh_type']!='SHT_REL':continue
    for rel in section.iter_relocations():
     where=BASE+rel['r_offset'];kind=rel['r_info_type'];old=u32(self.uc.mem_read(where,4))
     if kind==23:target=old+BASE
     elif kind in (2,21,22):
      sym=dyn.get_symbol(rel['r_info_sym'])
      if sym['st_shndx']!='SHN_UNDEF':target=BASE+sym['st_value']+(old if kind==2 else 0)
      else:
       target=RETURN+0x100+len(self.stubs)*16
       self.stubs[target]=sym.name
       self.uc.mem_write(target,b'\x70\x47')
       target|=1
     else:raise RuntimeError(f'Unhandled ARM relocation {kind}')
     self.uc.mem_write(where,struct.pack('<I',target&0xffffffff))
  self.uc.reg_write(regs.UC_ARM_REG_C1_C0_2,0xf<<20)
  self.uc.reg_write(regs.UC_ARM_REG_FPEXC,0x40000000)
  self.uc.hook_add(UC_HOOK_CODE,self.hook)
  self.calls=[]
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name is None:return
  self.calls.append(name)
  a,b,c=[uc.reg_read(r) for r in [regs.UC_ARM_REG_R0,regs.UC_ARM_REG_R1,regs.UC_ARM_REG_R2]]
  if name in ('memcpy','memmove'):
   uc.mem_write(a,bytes(uc.mem_read(b,c)))
  elif name=='memset':uc.mem_write(a,bytes([b&255])*c)
  else:raise RuntimeError(f'Unexpected dependency: {name}')
  uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))
 def invoke(self,name,args=(),floats=(),stack=b''):
  self.uc.mem_write(STACK+0xff000,stack or bytes(256))
  for i in range(16):self.uc.reg_write(getattr(regs,f'UC_ARM_REG_S{i}'),0)
  for i in range(4):self.uc.reg_write(getattr(regs,f'UC_ARM_REG_R{i}'),args[i]&0xffffffff if i<len(args) else 0)
  for i,x in enumerate(floats):self.uc.reg_write(getattr(regs,f'UC_ARM_REG_S{i}'),u32(struct.pack('<f',x)))
  self.uc.reg_write(regs.UC_ARM_REG_FPSCR,0)
  self.uc.reg_write(regs.UC_ARM_REG_SP,STACK+0xff000)
  self.uc.reg_write(regs.UC_ARM_REG_LR,RETURN|1)
  self.uc.emu_start(self.symbols[name],RETURN,timeout=5_000_000,count=100_000)
  assert self.uc.reg_read(regs.UC_ARM_REG_PC)==RETURN,'Function did not return within bounds'
  return self.uc.reg_read(regs.UC_ARM_REG_R0)
 def put(self,offset,values,fmt='f'):
  address=HEAP+offset;self.uc.mem_write(address,struct.pack('<'+fmt*len(values),*values));return address
 def bits(self,offset,count):return ','.join(f'{n:08x}' for n in struct.unpack('<'+'I'*count,self.uc.mem_read(HEAP+offset,count*4)))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--emit-dir',type=Path);ap.add_argument('--cases',type=int,default=1000);ap.add_argument('--rust-binary',type=Path,default=ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture');args=ap.parse_args()
 arm=OriginalArm(BINARY);rng=random.Random(0x524b4149);fixtures=[];expected=[];counts={}
 def add(kind,line,want):
  fixtures.append(line);expected.append(want);counts[kind]=counts.get(kind,0)+1
 for i in range(args.cases):
  count=rng.randrange(1,14);knots=[f32(rng.uniform(-10,10))]
  for k in range(count-1):knots.append(f32(knots[-1]+rng.choice([.0001,.0009,.001,.01,1.,10.])))
  values=[f32(rng.uniform(-100,100)) for _ in knots]
  sample=f32(rng.choice([knots[0]-1,knots[-1]+1,knots[rng.randrange(count)],rng.uniform(knots[0],knots[-1])]))
  a=arm.put(0,knots);b=arm.put(0x100,values);out=HEAP+0x200
  arm.invoke('_Z13interpolationPKfS0_ifPf',[a,b,count,out],[sample])
  add('interpolate',f'interp {fhex(sample)} '+','.join(map(fhex,knots))+' '+','.join(map(fhex,values)),arm.bits(0x200,1))
 for i in range(args.cases):
  lo=f32(rng.uniform(0,100));hi=f32(lo+rng.uniform(.01,100));sample=f32(rng.uniform(lo-10,hi+10))
  x=[f32(rng.uniform(-4,4)) for _ in range(12)];y=[f32(rng.uniform(-4,4)) for _ in range(12)]
  a=arm.put(0,[0.,0.,lo,*x]);b=arm.put(0x100,[0.,0.,hi,*y]);out=HEAP+0x200
  for op,symbol,n in [('matrix','SatInterpolateMatrices',9),('offset','SatInterpolateOffset',3)]:
   assert arm.invoke(symbol,[a,b,out],[sample])==0
   add(op,f'{op} {fhex(sample)} {fhex(lo)} {fhex(hi)} '+','.join(map(fhex,x))+' '+','.join(map(fhex,y)),arm.bits(0x200,n))
 for i in range(args.cases):
  knots=[50*(1<<n) for n in range(13)];values=[rng.randrange(0,65536) for _ in knots]
  sample=rng.choice([-1,0,knots[-1]+1,rng.randrange(knots[-1]+1)])
  a=arm.put(0,knots,'i');b=arm.put(0x100,values,'i')
  want=arm.invoke('_Z18AdpccInterpolationiPiS_',[sample,a,b]);want=struct.unpack('<i',struct.pack('<I',want))[0]
  add('defect',f'defect {sample} '+','.join(map(str,knots))+' '+','.join(map(str,values)),str(want))
 for i in range(args.cases):
  value=f32(rng.uniform(-65536,65536));bits=rng.randrange(0,31)
  want=arm.invoke('_Z19gain_float_lim2_intfii',[bits,1],[value]);want=struct.unpack('<i',struct.pack('<I',want))[0]
  add('quant',f'quant {fhex(value)} {bits}',str(want))
 for i in range(args.cases):
  mode=i%3;enable=i%2;scales=[f32(rng.uniform(0,20)) for _ in range(2)]
  times=[f32(rng.uniform(.0001,1)) for _ in range(3)];analog=[f32(rng.uniform(1,64)) for _ in range(3)];digital=[f32(rng.uniform(1,16)) for _ in range(3)];iso=[rng.randrange(50,204801) for _ in range(3)]
  a=HEAP;b=HEAP+0x100;c=HEAP+0x200
  arm.uc.mem_write(a,struct.pack('<B3xff',enable,*scales))
  arm.uc.mem_write(c,struct.pack('<ii12f5i',mode,0,*times,*analog,*digital,*([1.]*3),*iso,0,0))
  arm.uc.mem_write(b,bytes(28))
  name='_Z20gain_fix_transfer_v2P19RK_GAIN_Select_V2_sP16RK_GAIN_Fix_V2_sP18Again_ExpInfo_V2_sf'
  assert arm.invoke(name,[a,b,c],[1.])==0
  want=arm.uc.mem_read(b,28).hex()
  # Verify that the fourth f32 parameter really is unused in this binary.
  arm.uc.mem_write(b,bytes(28));assert arm.invoke(name,[a,b,c],[17.])==0
  assert arm.uc.mem_read(b,28).hex()==want
  add('gain',f'gain {mode} {enable} '+ ' '.join(map(fhex,scales))+' '+','.join(map(fhex,times))+' '+','.join(map(fhex,analog))+' '+','.join(map(fhex,digital))+' '+','.join(map(str,iso)),want)
 for i in range(args.cases):
  gains=[rng.randrange(1,4)]
  for _ in range(12):gains.append(gains[-1]+rng.randrange(1,100))
  knots=[g*50+rng.randrange(0,50) for g in gains]
  short=[f32(rng.uniform(0,20)) for _ in range(13)];middle=[f32(rng.uniform(0,20)) for _ in range(13)];enabled=i%2
  sample=rng.choice([0,1,49,50,*knots,knots[-1]+5000,rng.randrange(knots[-1]+1)])
  table=struct.pack('<B3x13i',enabled,*knots)+b''.join(struct.pack('<B3xff',j%2,short[j],middle[j]) for j in range(13))
  a=HEAP;b=HEAP+0x1000;c=HEAP+0x2000
  arm.uc.mem_write(a,table);arm.uc.mem_write(b,bytes(12));arm.uc.mem_write(c,struct.pack('<ii12f5i',0,0,*([1.]*12),sample,0,0,0,0))
  assert arm.invoke('_Z28gain_select_params_by_ISO_V2P19RK_GAIN_Params_V2_sP19RK_GAIN_Select_V2_sP18Again_ExpInfo_V2_s',[a,b,c])==0
  out=arm.uc.mem_read(b,12);low,high=struct.unpack('<ii',arm.uc.mem_read(c+68,8))
  want=f'{low} {high} {out[0]} {u32(out[4:8]):08x} {u32(out[8:12]):08x}'
  add('iso',f'iso {sample} {enabled} '+','.join(map(str,knots))+' '+','.join(map(fhex,short))+' '+','.join(map(fhex,middle)),want)
 for i in range(args.cases):
  seed=rng.randrange(0xffffffff);state=seed;data=bytearray()
  for _ in range(11145):state=(state*1664525+1013904223)&0xffffffff;data.append(state>>24)
  original=bytes(data);gains=[f32(rng.choice([0.,1.,8.,255.,rng.uniform(0,64)])) for _ in range(4)];position=i%2;update=(i//2)%2
  context=HEAP+0x10000;params=HEAP+0x20000;inputs=HEAP+0x30000;vtable=HEAP+0x50000+12
  arm.uc.mem_write(context,bytes(0x2000));arm.uc.mem_write(vtable-12,struct.pack('<i',0));arm.uc.mem_write(context,struct.pack('<I',vtable))
  arm.uc.mem_write(params,original);arm.uc.mem_write(inputs,struct.pack('<4fI',*gains,position))
  arm.invoke('_ZN5RkCam11Isp32Params30convertAiqAwbGainToIsp32ParamsER20isp32_isp_params_cfgRK20rk_aiq_wb_gain_v32_sb',[context,params,inputs,update])
  out=bytes(arm.uc.mem_read(params,11145));cache=arm.uc.mem_read(context+0x827,32)
  assert out[24:0x1225]==original[24:0x1225] and out[0x1245:]==original[0x1245:],'Original routine altered an unexpected parameter field'
  want=out[:24].hex()+':'+out[0x1225:0x1245].hex()+':'+cache.hex()
  add('awb',f'awb {seed} {update} {position} '+','.join(map(fhex,gains)),want)
 for i in range(args.cases):
  seed=rng.randrange(0xffffffff);state=seed;data=bytearray()
  for _ in range(11145):state=(state*1664525+1013904223)&0xffffffff;data.append(state>>24)
  original=bytes(data);mode=i%3
  gains=[f32(rng.choice([0.,.5,1.,1.0000001192092896,2.,256.,rng.uniform(0,256)])) for _ in range(3)]
  cached=[rng.randrange(65536) for _ in range(16)]
  context=HEAP+0x10000;params=HEAP+0x20000;vtable=HEAP+0x50000+12
  arm.uc.mem_write(context,bytes(0x2000));arm.uc.mem_write(vtable-12,struct.pack('<i',0));arm.uc.mem_write(context,struct.pack('<I',vtable))
  arm.uc.mem_write(context+0x20,struct.pack('<i',mode));arm.uc.mem_write(context+0x827,struct.pack('<16H',*cached));arm.uc.mem_write(params,original)
  # By-value ARM AAPCS aggregate begins in r2/r3, then continues on stack.
  exposure=bytearray(512)
  for offset,value in zip([12,60,108,156],[gains[0],*gains]):struct.pack_into('<f',exposure,offset,value)
  arm.invoke('_ZN5RkCam11Isp32Params34convertAiqExpIspDgainToIsp32ParamsER20isp32_isp_params_cfg17RKAiqAecExpInfo_s',[context,params,0,0],stack=bytes(exposure[8:]))
  out=bytes(arm.uc.mem_read(params,11145))
  assert out[:16]==original[:16] and out[24:0x122d]==original[24:0x122d] and out[0x1245:]==original[0x1245:]
  assert arm.uc.mem_read(context+0x827,32)==struct.pack('<16H',*cached),'Unexpected cache mutation'
  want=out[:24].hex()+':'+out[0x1225:0x1245].hex()
  add('dgain',f'dgain {seed} {mode} '+','.join(map(fhex,gains))+' '+','.join(map(str,cached)),want)
 for i in range(max(12,args.cases//20)):
  alpha=f32(([0.,1.,.5,1/128,.999,.0001]+[rng.random()])[i%7]);seed=rng.randrange(0xffffffff);state=seed;arrays=[]
  for n in range(2):
   values=[]
   for k in range(2187):state=(state*1664525+1013904223)&0xffffffff;values.append(state>>16)
   arrays.append(values)
  a=arm.put(0,arrays[0],'H');b=arm.put(0x2000,arrays[1],'H');out=HEAP+0x4000
  assert arm.invoke('InterpLutbyAlp',[a,b,out],[alpha])==0
  want=','.join(f'{n:04x}' for n in struct.unpack('<'+'H'*2187,arm.uc.mem_read(out,4374)))
  add('lut',f'lut {fhex(alpha)} {seed}',want)
 if args.emit_dir:
  args.emit_dir.mkdir(parents=True,exist_ok=True)
  (args.emit_dir/'inputs.txt').write_text('\n'.join(fixtures)+'\n')
  (args.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
 proc=subprocess.run([str(args.rust_binary)],input='\n'.join(fixtures)+'\n',text=True,capture_output=True,check=True)
 results=proc.stdout.splitlines();assert len(results)==len(expected)
 mismatches=[{'case':i,'input':fixtures[i],'expected':a,'actual':b} for i,(a,b) in enumerate(zip(expected,results)) if a!=b]
 report={'binarySha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'fixtureSeed':'0x524b4149','comparisons':counts,'totalCases':len(expected),'comparison':'Exact IEEE754 f32 output bits or complete integer output; original ARM instructions vs compiled Rust',
  'originalDependencyCalls':sorted(set(arm.calls)),'mismatches':mismatches[:10],'mismatchCount':len(mismatches),'limitations':['Finite, valid-domain calibration inputs only; invalid-pointer ABI behavior is not reproduced.','This verifies ten recovered numerical/parameter routines, not the complete RKAIQ library or camera startup.','Unicorn is an instruction-level reference; real camera/ARM hardware validation remains pending.']}
 out=ROOT/'reverse-engineering/rkaiq/numeric-equivalence.json';out.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='mismatches'},indent=2))
 if mismatches:
  print(json.dumps(mismatches[0],indent=2));raise SystemExit(1)
if __name__=='__main__':main()
