#!/usr/bin/env python3
"""Check IQ loading plus exposure conversion against native SDK-calibrated calls."""
import argparse,hashlib,json,random,subprocess
from pathlib import Path
from exposure import OriginalExposure
from differential import ROOT,f32

def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=100);p.add_argument('--emit-dir',type=Path);args=p.parse_args()
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());source=manifest['iqFiles'][0];path=ROOT/'.tools/reverse-engineering/iqfiles'/source['name'];assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
 profile={'sensor_calib':json.loads(path.read_text())['sensor_calib']};s=profile['sensor_calib'];arm=OriginalExposure();rng=random.Random(0x49514341);inputs=[];expected=[]
 def rule(value):return {'minimum':value['CISTimeRegMin'],'step':value['CISTimeRegOdevity']['fCoeff'][0],'offset':value['CISTimeRegOdevity']['fCoeff'][1]}
 for i in range(args.cases):
  seconds=f32(rng.uniform(0,.1));gain=f32(rng.choice([1.,2.,48.64,778.24,.5,rng.uniform(.25,800)]));frame=rng.choice([1320,1600,3000]);clock=rng.choice([24.,72.]);line=rng.choice([2500,2600,3000])
  v=dict(time=seconds,gain=gain,mode=0,dcg=0,model=0,bands=[s['Gain2Reg']['GainRange'][j:j+7] for j in range(0,s['Gain2Reg']['GainRange_len'],7)],factors=s['Time2Reg']['fCoeff'],frame_length=float(frame),pixel_clock=clock,line_length=float(line),linear=rule(s['CISTimeSet']['Linear']),hdr2=rule(s['CISTimeSet']['Hdr'][0]),hdr3=rule(s['CISTimeSet']['Hdr'][1]),linear_ratio=s['CISDcgSet']['Linear']['dcg_ratio'],hdr_ratio=s['CISDcgSet']['Hdr']['dcg_ratio'])
  inputs.append('iq-exposure '+json.dumps(dict(profile=profile,time=seconds,gain=gain,frame=frame,clock=clock,line=line),separators=(',',':')));expected.append(arm.run(v))
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[i for i,(a,b) in enumerate(zip(expected,actual)) if a!=b]
 report={'iqFile':source['name'],'iqSha256':source['sha256'],'cases':len(inputs),'mismatchCount':len(mismatches),'scope':'Actual SDK SC3336 sensor_calib JSON parsed by Rust, followed by gain/time conversion vs original RKAIQ and original uClibc math','limitations':['Exposure subset only; ISP scene tuning, automatic controls and native binary IQ loading are not implemented.','The profile is a pinned SDK reference, not a claim of camera-module/lens qualification.','No live driver writes or frame scheduling are performed.']}
 if mismatches:report['firstMismatches']=mismatches[:5]
 (ROOT/'reverse-engineering/rkaiq/iq-calibration-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not mismatches
 if args.emit_dir:
  args.emit_dir.mkdir(parents=True,exist_ok=True);(args.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(args.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n')
  (args.emit_dir/'sc3336-exposure-subset.json').write_text(json.dumps({'_source':source,**profile},indent=2)+'\n')
if __name__=='__main__':main()
