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
  ae_out=d/'initial-ae.bin'
  ae_run=subprocess.run([str(binary),'make-initial-parameters',str(iq_path),str(ae_out),'--ae-measurements'],text=True,capture_output=True,check=True)
  ae_report=json.loads(ae_run.stdout);ae_data=ae_out.read_bytes();assert ae_report['aeMeasurementsConfigured'] and not ae_report['automaticExposure']
  assert abs(ae_report['routeTimeQuantumSeconds']-.01)<1e-8 and not ae_report['minimumShutterTimeDerived']
  measurement_mask=0x003c4000|0x07800008
  for offset in [0,8,16]:assert struct.unpack_from('<Q',ae_data,offset)[0]==struct.unpack_from('<Q',data,offset)[0]|measurement_mask
  assert ae_data[24:0x41b]==data[24:0x41b] and ae_data[0x7ae:]==data[0x7ae:]
  weights=bytes(iq['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib']['CommCtrl']['AecGridWeight'])
  for offset in [58,300,542]:assert ae_data[0x4af+offset:0x4af+offset+225]==weights
  assert ae_data[0x4af+16:0x4af+41]==bytes([1])*25
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
  print(json.dumps(dict(measurementParameterSha256=hashlib.sha256(ae_data).hexdigest(),profileBytes=len(data),parameterSha256=hashlib.sha256(data).hexdigest(),rejectedMalformedProfiles=len(mutations),overwriteRejected=True,scope='Offline assembly invariants; no live frame or complete native startup equivalence')))
if __name__=='__main__':main()
