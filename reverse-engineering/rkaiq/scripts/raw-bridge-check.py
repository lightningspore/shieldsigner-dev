#!/usr/bin/env python3
"""Build/run actual ARM bridge lifecycle code with a cfg(test)-only ioctl driver."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def main():
 command=['mise','exec','rust@1.93.1','zig@0.15.2','--','uv','run','--python','3.13','--with','cargo-zigbuild==0.23.0','cargo-zigbuild','zigbuild','--locked','--release','--target','armv7-unknown-linux-musleabihf','--manifest-path','firmware/rkaiq-rs/Cargo.toml','--bin','camera-probe','--tests','--message-format=json']
 built=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,check=True)
 artifacts=[json.loads(line) for line in built.stdout.splitlines() if line.startswith('{')]
 matches=[a for a in artifacts if a.get('reason')=='compiler-artifact' and a.get('target',{}).get('name')=='camera-probe' and a.get('profile',{}).get('test') and a.get('executable')]
 assert len(matches)==1
 binary=Path(matches[0]['executable'])
 image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
 run=subprocess.run(['docker','run','--rm','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/tests,readonly',image,'/tests/'+binary.name,'raw_bridge_driver_test','--nocapture','--test-threads=1'],text=True,capture_output=True,check=True)
 events=[json.loads(line[line.index('{'):]) for line in run.stdout.splitlines() if '{"cleanupErrors"' in line]
 assert len(events)==20
 for start in range(0,20,5):
  assert events[start]['completedFrames']==1 and events[start]['sofMatches']==1
  assert all(event['completedFrames']==0 and event['error'] for event in events[start+1:start+5])
 assert all(not event['cleanupErrors'] for event in events)
 report=dict(testBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),platform='linux/arm/v7',storageMismatchRejectedBeforeAllocation=True,endpointApiCombinations=4,casesPerCombination=['successful frame with matched SOF','RX STREAMON failure','RX QBUF failure suppresses trigger','trigger ioctl failure','corrupted RX completion'],passed=True,events=events,limitations=['A cfg(test)-only ioctl boundary simulates the driver; actual ARM bridge logic, FD export ownership, scoped worker and cleanup execute.','No positive device, kernel-driver or original RKAIQ queue-controller equivalence is established.','Image capture and the metadata queue are outside this focused bridge test.'])
 (ROOT/'reverse-engineering/rkaiq/raw-bridge-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(run.stdout,end='')
if __name__=='__main__':main()
