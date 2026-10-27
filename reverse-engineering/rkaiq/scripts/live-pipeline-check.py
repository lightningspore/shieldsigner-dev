#!/usr/bin/env python3
"""Focused CIF pad-record checks and real ARM command failure/preflight checks."""
import json,random,struct,subprocess,hashlib,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('isp_pipeline_reference',Path(__file__).with_name('isp-pipeline.py'))
reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
OriginalPipeline=reference.OriginalPipeline
from differential import ROOT,HEAP,regs,u32
class Cif(OriginalPipeline):
 def __init__(self):
  super().__init__();self.symbols['pipeline']=0x32f91
  for symbol in ['_ZN5RkCam16RawStreamCapUnit13set_tx_formatERK21v4l2_subdev_selectionj','_ZN5RkCam17RawStreamProcUnit13set_rx_formatERK21v4l2_subdev_selectionj']:self.stubs[self.symbols[symbol]&~1]='raw-cif'
  got=u32(self.uc.mem_read(0x3316c,4))+0x32fae;flag=u32(self.uc.mem_read(got+u32(self.uc.mem_read(0x33174,4)),4));self.uc.mem_write(flag,b'\0')
 def hook(self,uc,address,size,user):
  if self.stubs.get(address)=='raw-cif':uc.reg_write(regs.UC_ARM_REG_R0,0);uc.reg_write(regs.UC_ARM_REG_PC,uc.reg_read(regs.UC_ARM_REG_LR));return
  super().hook(uc,address,size,user)
def main():
 arm=Cif();rng=random.Random(0x43494650);inputs=[];expected=[]
 for adjusted in (False,True):
  for fail in range(7):
   sensor=bytearray(rng.randbytes(88));crop=bytearray(rng.randbytes(64));sink=bytearray(rng.randbytes(88));source=bytearray(rng.randbytes(88));struct.pack_into('<II',sink,0,1,0);struct.pack_into('<II',source,0,1,2);struct.pack_into('<III',sensor,8,2304,1296,0x3007);struct.pack_into('<iiII',crop,16,8,4,2288,1280)
   v=dict(adjust=adjusted,fail=fail,error=-22,sensor=sensor.hex(),crop=crop.hex(),sink=sink.hex(),source=source.hex(),shared=False,first=True,scaler=False,pixel=int.from_bytes(b'BG10','little'),bits=10)
   native=arm.run(v);expected.append(';'.join(x for x in native.split(';') if not x.startswith('bpp:')));inputs.append('isp-pad-cif '+json.dumps(v,separators=(',',':')))
 result=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert result==expected,'CIF pad records differ from original setupPipelineFmtCif'
 report=dict(cifPadCases=len(inputs),cifPadMismatches=0,scope='CIF ISP pad records/order/first-error status, including forwarding driver-adjusted sink selection to source pad',limitations=['Raw streams/scaler and disabled optional alignment prelude are controlled boundaries for this pad-only comparison.','Positive real device operations still require hardware.'])
 # Execute the static ARM Linux command itself. /dev/null fails the first sensor
 # read before any link/format mutation; parser failures also precede device I/O.
 base=ROOT/'dist/reverse-engineering/live-pipeline-check';base.mkdir(parents=True,exist_ok=True)
 valid={'sensor':'/dev/null','isp':'/dev/zero','route':'cif'};(base/'valid.json').write_text(json.dumps(valid))
 bad=[({**valid,'unknown':True},'Unknown pipeline field'),({**valid,'isp':'/dev/null'},'must be distinct'),({**valid,'raw_tx':['/dev/a','/dev/b']},'Too many entries'),({**valid,'route':'hdr'},'route must be'),({**valid,'links':[{'media':'/dev/media0','source':0,'source_pad':0,'sink':1,'sink_pad':0,'enabled':True}]},'must be nonzero')]
 for i,(v,_) in enumerate(bad):(base/f'bad-{i}.json').write_text(json.dumps(v))
 (base/'large.json').write_bytes(b' '*65537)
 image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
 binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/camera-probe'
 def command(file,*args):return subprocess.run(['docker','run','--rm','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly','--mount',f'type=bind,src={base},dst=/plans,readonly',image,'/bincheck/camera-probe','configure-pipeline','/plans/'+file,*args],text=True,capture_output=True)
 for args in [(),('--dry-run',)]:
  c=command('valid.json',*args);assert c.returncode==1 and 'os error 25' in c.stderr.lower(),c
  v=json.loads(c.stdout);assert not v['success'] and not v['coldStartProven'] and len(v['operations'])==1 and v['operations'][0]['operation']=='get-subdev-format' and v['operations'][0]['errno']==25 and v['dryRun']==bool(args)
 for i,(_,message) in enumerate(bad):
  c=command(f'bad-{i}.json');assert c.returncode==1 and message in c.stderr and not c.stdout,c
 c=command('large.json');assert c.returncode==1 and 'exceeds 64 KiB' in c.stderr and not c.stdout,c
 report.update(armBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),armInvalidDeviceBeforeMutation=True,armDryRunInvalidDeviceBeforeMutation=True,planRejectionChecks=len(bad)+1)
 (ROOT/'reverse-engineering/rkaiq/live-pipeline-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
