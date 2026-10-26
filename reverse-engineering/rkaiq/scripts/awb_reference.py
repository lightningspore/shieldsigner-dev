"""Shared original ARM AWB/runtime executor; stdlib boundaries are explicit."""
from differential import OriginalArm, BINARY, ROOT, HEAP, regs
RUNTIME=ROOT/'.tools/reverse-engineering/uclibc-runtime/libgcc_s.so.1'
class OriginalAwb(OriginalArm):
 def __init__(self,stdlib=False):
  super().__init__(BINARY);self.runtime=OriginalArm(RUNTIME);self.runtime_calls=0;self.runtime_functions=set();self.stdlib=stdlib;self.standard_calls={};self.allocation=None
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  if name in ('__aeabi_l2f','__aeabi_idiv'):
   args=[uc.reg_read(regs.UC_ARM_REG_R0),uc.reg_read(regs.UC_ARM_REG_R1)]
   self.runtime.invoke(name,args);self.runtime_calls+=1;self.runtime_functions.add(name)
   uc.reg_write(regs.UC_ARM_REG_R0,self.runtime.uc.reg_read(regs.UC_ARM_REG_R0));uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  if self.stdlib and name in ('strcmp','malloc','free'):
   a=uc.reg_read(regs.UC_ARM_REG_R0);b=uc.reg_read(regs.UC_ARM_REG_R1);self.standard_calls[name]=self.standard_calls.get(name,0)+1
   if name=='strcmp':
    first=bytes(uc.mem_read(a,256)).split(b'\0')[0];second=bytes(uc.mem_read(b,256)).split(b'\0')[0];assert len(first)<256 and len(second)<256
    uc.reg_write(regs.UC_ARM_REG_R0,((first>second)-(first<second))&0xffffffff)
   elif name=='malloc':
    assert self.allocation is None and 0<a<=255;self.allocation=HEAP+0x90000;uc.mem_write(self.allocation,bytes([0xa7])*a);uc.reg_write(regs.UC_ARM_REG_R0,self.allocation)
   else:assert a==self.allocation;self.allocation=None
   uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
