#!/usr/bin/env python3
"""ARM first-frame CLI preflight checks; no positive camera-device simulation."""
import copy,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def main():
 binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/camera-probe'
 iq=json.loads((ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json').read_text())
 plan=dict(sensor='/dev/null',isp='/dev/zero',route='cif',raw_tx=['/dev/full'],raw_rx=['/dev/random'],bridges=[],links=[])
 image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
 with tempfile.TemporaryDirectory() as d:
  d=Path(d);(d/'iq.json').write_text(json.dumps(iq));(d/'plan.json').write_text(json.dumps(plan))
  bad=copy.deepcopy(plan);bad['raw_tx']=[];(d/'bad-plan.json').write_text(json.dumps(bad))
  bad_iq=copy.deepcopy(iq);bad_iq['sensor_calib']['resolution']['width']=1;(d/'bad-iq.json').write_text(json.dumps(bad_iq))
  def run(*args):
   return subprocess.run(['docker','run','--rm','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly','--mount',f'type=bind,src={d},dst=/plans,readonly',image,'/bincheck/camera-probe','first-frame-sc3336',*args],text=True,capture_output=True)
  cases=[([], 'first-frame-sc3336'),(['/plans/bad-plan.json','/plans/iq.json','/dev/urandom','/dev/tty','/plans/out'],'one explicit CIF'),(['/plans/plan.json','/plans/bad-iq.json','/dev/urandom','/dev/tty','/plans/out'],'SC3336 2304x1296'),(['/plans/plan.json','/plans/iq.json','/dev/urandom','/dev/tty','/etc/passwd'],'output already exists'),(['/plans/plan.json','/plans/iq.json','/dev/urandom','/dev/tty','/plans/out'],'os error 25')]
  for args,expected in cases:
   result=run(*args)
   assert result.returncode!=0 and expected.lower() in (result.stdout+result.stderr).lower(),(args,result.stdout,result.stderr)
   assert not list(d.glob('out*')),'preflight wrote startup artifacts'
 print(json.dumps(dict(armPreflightCases=len(cases),passed=True,scope='Argument/profile/plan/output rejection and real nonsensor ioctl failure before startup artifacts; no positive hardware startup.')))
if __name__=='__main__':main()
