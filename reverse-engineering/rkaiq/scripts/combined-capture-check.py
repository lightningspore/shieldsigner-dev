#!/usr/bin/env python3
"""Run actual static ARM CLI preflight failures; no simulated positive V4L2 path."""
import subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def main():
 binary=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/camera-probe'
 image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
 cases=[([], 'capture-with-parameters'), (['/dev/null','/missing','--','/dev/null','/tmp/out'],'distinct character devices'),(['/dev/null','/missing','--','/dev/zero','/etc/passwd'],'output or metadata exists'),(['/dev/null','/missing','--','/dev/zero','/tmp/out'],'No such file'),(['/dev/null','/missing','--','/dev/zero'],'Expected two parameter arguments')]
 for args,expected in cases:
  result=subprocess.run(['docker','run','--rm','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/bincheck,readonly',image,'/bincheck/camera-probe','capture-with-parameters',*args],text=True,capture_output=True)
  assert result.returncode!=0 and expected in result.stderr,(args,result.returncode,result.stderr)
 print(json.dumps(dict(armCliPreflightCases=len(cases),passed=True,limitations='No positive hardware queue/capture execution; checks argument, alias, existing-output and missing-payload rejection only.')))
if __name__=='__main__':main()
