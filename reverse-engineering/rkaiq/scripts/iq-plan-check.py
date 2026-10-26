#!/usr/bin/env python3
"""Exercise the offline planner against real SDK IQ data and invalid inputs."""
from pathlib import Path
import copy,hashlib,json,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[3]
manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());source=manifest['iqFiles'][0]
raw=ROOT/'.tools/reverse-engineering/iqfiles'/source['name'];assert hashlib.sha256(raw.read_bytes()).hexdigest()==source['sha256']
profile={'sensor_calib':json.loads(raw.read_text())['sensor_calib']}
sensor={'syntheticFixture':True,'width':2304,'height':1296,'linePeriodsPerField':1320,'pixelPeriodsPerLine':2500,'pixelClockMHz':72.}
binary=ROOT/'firmware/rkaiq-rs/target/release/camera-probe';checks=[]
with tempfile.TemporaryDirectory(prefix='shieldsigner-iq-plan-') as temp:
 folder=Path(temp);iq=folder/'profile.json';snapshot=folder/'sensor.json'
 def run(name,profile_data,sensor_data,options=('0.01','2'),error=None):
  iq.write_text(json.dumps(profile_data));snapshot.write_text(json.dumps(sensor_data))
  result=subprocess.run([str(binary),'exposure-plan',str(iq),str(snapshot),*options],text=True,capture_output=True)
  if error is None:
   assert result.returncode==0,result.stderr
   v=json.loads(result.stdout);assert not v['writesSensor'] and not v['automaticExposure'];assert (v['integrationTimeCode'],v['gainCode'])==(288,256);assert v['linearUpdateDelays']==dict(time=2,gain=2,dcg=0)
  else:assert result.returncode==1 and error in result.stderr and 'panicked' not in result.stderr,result
  checks.append(name)
 run('SDK profile plus synthetic descriptor',profile,sensor)
 run('Explicit longer frame',profile,sensor,('0.01','2','1500'))
 run('Reject frame below descriptor minimum',profile,sensor,('0.01','2','1000'),'below the sensor descriptor minimum')
 bad=copy.deepcopy(sensor);bad['width']=1920;run('Reject resolution mismatch',profile,bad,error='does not match')
 bad=copy.deepcopy(profile);bad['sensor_calib']['Gain2Reg']['GainRange_len']=6;run('Reject truncated gain row',bad,sensor,error='GainRange length')
 bad=copy.deepcopy(profile);bad['sensor_calib']['Time2Reg']['fCoeff'][0]=1e100;run('Reject f32 overflow',bad,sensor,error='Nonfinite/out-of-range')
 bad=copy.deepcopy(profile);bad['sensor_calib']['CISTimeSet']['Linear']['CISTimeRegOdevity']['fCoeff'][0]=0;run('Reject zero linear timing step',bad,sensor,error='step must be positive')
 bad=copy.deepcopy(sensor);del bad['pixelClockMHz'];run('Reject missing sensor clock',profile,bad,error='pixelClockMHz')
 run('Reject nonfinite requested time',profile,sensor,('NaN','2'),'Exposure conversion')
 run('Reject zero requested gain',profile,sensor,('0.01','0'),'Exposure conversion')
report={'iqSha256':source['sha256'],'binarySha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'checks':checks,'passed':True,'descriptorSource':'Explicit synthetic fixture; not a real hardware observation'}
(ROOT/'reverse-engineering/rkaiq/iq-plan-validation.json').write_text(json.dumps(report,indent=2)+'\n')
folder=ROOT/'dist/reverse-engineering/iq-calibration-fixtures';folder.mkdir(parents=True,exist_ok=True);(folder/'synthetic-sensor-info.json').write_text(json.dumps(sensor,indent=2)+'\n')
print('PASS:',len(checks),'offline planner checks; no device opened')
