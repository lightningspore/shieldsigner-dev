"""Original full single-ISP translateAwbStats with controlled object access."""
import struct
from differential import OriginalArm,BINARY,HEAP,regs
OBJECT_BYTES=0x2300
SYMBOL='_ZN5RkCam26RkAiqResourceTranslatorV3217translateAwbStatsERKN4XCam8SmartPtrINS1_11VideoBufferEEERNS2_INS_15SharedItemProxyI13RkAiqAwbStatsEEEE'
def data(seed,size):
 result=bytearray()
 for _ in range(size):seed=(seed*1664525+1013904223)&0xffffffff;result.append(seed>>24)
 return result
class OriginalTranslation(OriginalArm):
 def __init__(self):
  super().__init__(BINARY);self.raw_pointer=HEAP+0x20000;self.boundary_calls={}
  for name in self.symbols:
   if ('get_cast_ptr' in name and 'Isp20StatsBuffer' in name) or 'get_v4l2_userptr' in name or 'IsMultiIspMode' in name or name=='xcam_print_log':self.stubs[self.symbols[name]&~1]=name
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name and (('get_cast_ptr' in name and 'Isp20StatsBuffer' in name) or 'get_v4l2_userptr' in name or 'IsMultiIspMode' in name or name=='xcam_print_log'):
   self.boundary_calls[name]=self.boundary_calls.get(name,0)+1
   result=0 if 'IsMultiIspMode' in name else (self.raw_pointer if 'get_v4l2_userptr' in name else HEAP+0x20000)
   if name!='xcam_print_log':uc.reg_write(regs.UC_ARM_REG_R0,result)
   uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
 def run(self,raw,configuration,seed):
  context=HEAP;source=HEAP+0x20000;out=HEAP+0x40000;smart=HEAP+0x50000;proxy=HEAP+0x60000;control=HEAP+0x70000
  ctx=data(seed^0x10,0xc000);ctx[0xb618:0xbacc]=configuration;original=data(seed^0x21,OBJECT_BYTES);original[0x22f0]=bool(seed&1);original[0x22f1]=bool(seed&2)
  proxy_before=data(seed^0x22,0x100);struct.pack_into('<II',proxy_before,0x6c,out,control);control_before=bytearray([0x55])*0x100;struct.pack_into('<II',control_before,0,0,100)
  self.raw_pointer=0 if raw is None else source
  self.uc.mem_write(context,bytes(ctx));self.uc.mem_write(out,bytes(original));self.uc.mem_write(proxy,bytes(proxy_before));self.uc.mem_write(smart,struct.pack('<II',proxy,0));self.uc.mem_write(control,bytes(control_before))
  if raw is not None:self.uc.mem_write(source,bytes(raw))
  status=self.invoke(SYMBOL,[context,0,smart],instructions=1000000);result=bytes(self.uc.mem_read(out,OBJECT_BYTES));proxy_after=bytearray(self.uc.mem_read(proxy,0x100))
  assert bytes(self.uc.mem_read(context,len(ctx)))==ctx and bytes(self.uc.mem_read(control,0x100))==control_before
  if raw is not None:assert bytes(self.uc.mem_read(source,len(raw)))==raw
  unchanged=bytearray(result)
  for offset,size in [(8,0x1e00),(0x22f0,2),(0x22f4,4)]:unchanged[offset:offset+size]=original[offset:offset+size]
  assert unchanged==original
  sequence=struct.unpack_from('<I',proxy_after,0x50)[0];proxy_after[0x50:0x54]=proxy_before[0x50:0x54];assert proxy_after==proxy_before
  return status,result[8:0x1e08],result[0x22f0],result[0x22f1],struct.unpack_from('<I',result,0x22f4)[0],sequence
