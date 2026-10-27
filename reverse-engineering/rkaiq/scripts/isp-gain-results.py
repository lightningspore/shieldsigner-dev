#!/usr/bin/env python3
"""Ordered persistent WB/exposure converter calls, not parameter-pool policy."""
import hashlib,json,struct,subprocess,sys
from differential import OriginalArm,ROOT,BINARY,HEAP
WB='_ZN5RkCam11Isp32Params30convertAiqAwbGainToIsp32ParamsER20isp32_isp_params_cfgRK20rk_aiq_wb_gain_v32_sb'
EXP='_ZN5RkCam11Isp32Params34convertAiqExpIspDgainToIsp32ParamsER20isp32_isp_params_cfg17RKAiqAecExpInfo_s'
def main():
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text())
 sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert sha==manifest['binaries'][0]['sha256']
 cases=[];expected=[]
 for mode in [0,1,2]:
  for position in [0,1]:
   arm=OriginalArm(BINARY);context=HEAP+0x10000;params=HEAP+0x20000;inputs=HEAP+0x30000;vtable=HEAP+0x50000+12
   arm.uc.mem_write(context,bytes(0x2000));arm.uc.mem_write(context,struct.pack('<I',vtable));arm.uc.mem_write(vtable-12,bytes(4));arm.uc.mem_write(context+0x20,struct.pack('<i',mode));arm.uc.mem_write(params,bytes([0x5a])*11145)
   wb=[2.,1.,1.25,3.,position];changed=[1.5,1.25,1.,2.5,position]
   events=[dict(wb=wb),dict(mode=mode,gain=[2.,3.,4.]),dict(mode=mode,gain=[3.,4.,5.]),dict(mode=mode,gain=[1.,1.,1.]),dict(wb=wb,mode=mode,gain=[1.,1.,1.]),dict(wb=changed,mode=mode,gain=[1.5,2.,2.5]),dict(),dict(mode=mode,gain=[-.5,.5,1.]),dict(wb=wb,mode=mode,gain=[4.,3.,2.]),dict(wb=changed)]
   outputs=[]
   for event in events:
    if 'wb' in event:
     arm.uc.mem_write(inputs,struct.pack('<4fI',*event['wb']));arm.invoke(WB,[context,params,inputs,1])
    if 'gain' in event:
     record=bytearray(244);g=event['gain']
     for offset,value in zip([12,60,108,156],[g[0],*g]):struct.pack_into('<f',record,offset,value)
     arm.invoke(EXP,[context,params,0,0],stack=bytes(record[8:]))
    outputs.append(dict(parameters=bytes(arm.uc.mem_read(params,11145)).hex(),cache=bytes(arm.uc.mem_read(context+0x827,32)).hex()))
   # A unity-only event leaves the preceding boosted output unchanged; a WB
   # result followed by unity restores unscaled bank-0 registers.
   assert outputs[2]==outputs[3]
   assert outputs[3]['parameters'][0x122d*2:0x1245*2]!=outputs[4]['parameters'][0x122d*2:0x1245*2]
   assert outputs[5]==outputs[6]
   cases.append(events);expected.append(outputs)
 inputs=''.join('gain-results '+json.dumps(c,separators=(',',':'))+'\n' for c in cases)
 def compare(command):
  p=subprocess.run(command,input=inputs,text=True,capture_output=True,check=True)
  actual=[json.loads(line) for line in p.stdout.splitlines()]
  assert actual==expected,'Ordered gain result mismatch'
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 arm='--arm' in sys.argv
 if arm:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
  compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=sha,sequences=len(cases),events=sum(map(len,cases)),host=True,arm=arm,mismatches=0,comparison='Complete 11145-byte parameter buffer and unscaled 32-byte WB cache after each ordered event',limitations=['Native WB and exposure converters execute sequentially; C++ list/RTTI dispatch is not executed.','Result inclusion, parameter-pool reuse, frame timing and live driver submission remain outside this test.'])
 (ROOT/'reverse-engineering/rkaiq/isp-gain-results-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
