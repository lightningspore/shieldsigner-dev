#!/usr/bin/env python3
"""Run original ARM incomplete-group pruning; never claim ready-stat coalescing."""
import hashlib,json,struct
from differential import OriginalArm, BINARY, BASE, HEAP, ROOT, regs
NAME='_ZN5RkCam18RkAiqAnalyzerGroup12msgReductionERSt3mapIjNS0_12GroupMessageESt4lessIjESaISt4pairIKjS2_EEE'
class Group(OriginalArm):
 def __init__(self):
  super().__init__(BINARY);self.nodes=[];self.erased=[]
 def hook(self,uc,address,size,user):
  name=self.stubs.get(address)
  a,b,c=[uc.reg_read(r) for r in [regs.UC_ARM_REG_R0,regs.UC_ARM_REG_R1,regs.UC_ARM_REG_R2]]
  if name and '_Rb_tree_increment' in name:
   uc.reg_write(regs.UC_ARM_REG_R0,self.nodes[self.nodes.index(a)+1])
  elif address==BASE+0x83516:
   assert a==HEAP+0x28 and b==self.nodes[0]
   self.erased=self.nodes[:self.nodes.index(c)]
  elif address==BASE+0x24304:pass # empty std::string disposal boundary
  else:return super().hook(uc,address,size,user)
  uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR))
def main():
 arm=Group();cases=[]
 for count in range(9):
  arm.nodes=[HEAP+0x1000+i*0x100 for i in range(max(count,1))];arm.erased=[]
  state=bytearray(0x100);struct.pack_into('<I',state,0x34,arm.nodes[0]);struct.pack_into('<I',state,0x3c,count)
  arm.uc.mem_write(HEAP,bytes(state));arm.uc.mem_write(arm.nodes[0],bytes(0x100))
  arm.invoke(NAME,[HEAP,HEAP+0x28],instructions=10000)
  assert len(arm.erased)==max(0,count-2)
  cases.append({'pendingIncompleteGroups':count,'oldestErased':len(arm.erased),'newestRetained':min(count,2)})
 report={'kind':'original-arm-analysis-group-reduction','passed':True,'originalLibrarySha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'functionElfAddress':'0x83574','cases':cases,'emulationScope':'Actual ARM reduction instructions; controlled group-map count/order and required mask0. Standard RB-tree iterator/erase and empty-string disposal are explicit bookkeeping boundaries; not full analyzer execution.','callerEvidence':{'0x838b2-0x838c0':'Compare required-message mask with received-message mask. Mismatch branches to reduction at0x83918.','0x838ea':'Complete mask invokes analysis callback synchronously.','0x838ec-0x83904':'After complete callback, erase pending map entries through the completed frame.','0x8289c-0x8293a':'SafeListEx push appends a message and increments queued count; no latest2 reduction observed here.'},'conclusion':'Newest2 bound applies to incomplete message-assembly groups. This does not prove dropping ready statistics inputs is native behavior.'}
 report['additionalIngressEvidence']={'pushStatsElf':'0x7ea28','pushStatsRule':'For statistic buffers(type1), reject duplicate/regressing frame exceptinitialzero; update lastStats0x928 then invoke analyze only if signed(frame-lastCoreSof0x924)<=3.','pushEvtsElf':'0x7e0cc','pushEvtsRule':'For type4 SOF core events, reject duplicate/regressing frame exceptinitialzero; update lastCoreSof0x924 then invoke events_analyze only if signed(frame-lastStats0x928)<=3.','scope':'Disassembly only for ingress gates; this oracle executes msgReduction, not ingress functions. Core analysis event gating must not be confused with SensorHw hardware SOF/sensor-write handling.'}
 report['policyLimit']='No ready-stat latest2 policy is established. Preserve original statistics frame/parameter IDs and all hardware SOF events; separate control delivery from bulk analysis before considering bounded admission.'
 path=ROOT/'reverse-engineering/rkaiq/native-analysis-group-reduction.json';path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
