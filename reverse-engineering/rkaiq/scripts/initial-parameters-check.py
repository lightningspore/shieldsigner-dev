#!/usr/bin/env python3
"""Profile assembly checks; not evidence of live camera operation."""
import copy,json,struct,subprocess,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def main():
 binary=ROOT/'firmware/rkaiq-rs/target/release/camera-probe'
 iq_path=ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json'
 iq=json.loads(iq_path.read_text())
 assert hashlib.sha256(iq_path.read_bytes()).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'
 with tempfile.TemporaryDirectory() as d:
  d=Path(d); out=d/'initial.bin'
  run=subprocess.run([str(binary),'make-initial-parameters',str(iq_path),str(out)],text=True,capture_output=True,check=True)
  report=json.loads(run.stdout); data=out.read_bytes();assert len(data)==11145
  en_update,enabled,cfg=struct.unpack_from('<QQQ',data)
  expected=sum(1<<i for i in [1,5,9,35,43,44])
  assert cfg==expected and enabled==expected & ~(1<<1)
  assert en_update==(1<<46)-1
  assert data[24:28]==bytes(4)
  assert data[0x7ae+2]==1
  assert struct.unpack_from('<4h',data,0x7ae+28)==(256,)*4
  assert struct.unpack_from('<I',data,0x7ae+40)==(4096,)
  assert data[0x130a:0x130c]==bytes([0,1])
  assert struct.unpack_from('<49H',data,0x130e)==tuple(iq['main_scene'][0]['sub_scene'][0]['scene_isp32']['agamma_calib_v11']['GammaTuningPara']['Gamma_curve'])
  assert report['iso']==50 and report['sensorExposureApplied'] is False
  before=out.read_bytes()
  assert subprocess.run([str(binary),'make-initial-parameters',str(iq_path),str(out)],capture_output=True).returncode!=0
  assert out.read_bytes()==before
  mutations=[('/debayer_v2',None),('/wb_v32/autoExtPara/lightSourceForFirstFrame','missing'),('/agamma_calib_v11/GammaTuningPara/Gamma_curve',[0]),('/ablcV32_calib/Blc1TuningPara/BLC_Data/R_Channel',[0]*12+[1]),('/ae_calib/LinearAeCtrl/InitExp/InitIspDGainValue',2)]
  for n,(pointer,value) in enumerate(mutations):
   bad=copy.deepcopy(iq);node=bad['main_scene'][0]['sub_scene'][0]['scene_isp32'];parts=pointer.strip('/').split('/')
   for part in parts[:-1]:node=node[part]
   node[parts[-1]]=value; path=d/f'bad{n}.json';path.write_text(json.dumps(bad));dest=d/f'bad{n}.bin'
   assert subprocess.run([str(binary),'make-initial-parameters',str(path),str(dest)],capture_output=True).returncode!=0
   assert not dest.exists()
  print(json.dumps(dict(profileBytes=len(data),parameterSha256=hashlib.sha256(data).hexdigest(),rejectedMalformedProfiles=len(mutations),overwriteRejected=True,scope='Offline assembly invariants; no live frame or complete native startup equivalence')))
if __name__=='__main__':main()
