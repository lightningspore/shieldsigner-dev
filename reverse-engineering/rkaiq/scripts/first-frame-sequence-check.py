#!/usr/bin/env python3
"""Execute full Rust startup on ARM with explicit test-only device boundaries."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def main():
 command=['mise','exec','rust@1.93.1','zig@0.15.2','--','uv','run','--python','3.13','--with','cargo-zigbuild==0.23.0','cargo-zigbuild','zigbuild','--locked','--release','--target','armv7-unknown-linux-musleabihf','--manifest-path','firmware/rkaiq-rs/Cargo.toml','--bin','camera-probe','--tests','--message-format=json']
 built=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,check=True)
 artifacts=[json.loads(line) for line in built.stdout.splitlines() if line.startswith('{')]
 matches=[a for a in artifacts if a.get('reason')=='compiler-artifact' and a.get('target',{}).get('name')=='camera-probe' and a.get('profile',{}).get('test') and a.get('executable')];assert len(matches)==1
 binary=Path(matches[0]['executable']);iq=ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json'
 assert hashlib.sha256(iq.read_bytes()).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'
 image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
 run=subprocess.run(['docker','run','--rm','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/tests,readonly','--mount',f'type=bind,src={iq.parent},dst=/iq,readonly','-e','SHIELDSIGNER_TEST_IQ=/iq/'+iq.name,image,'/tests/'+binary.name,'first_frame_driver','--ignored','--nocapture'],text=True,capture_output=True,timeout=30,check=True)
 events=[json.loads(line) for line in run.stdout.splitlines() if line.startswith('{') and line.endswith('}')]
 summary=next(e for e in events if e.get('event')=='simulated-startup-verified')
 assert summary['imageFrames']==3 and summary['rawFrames']>=3 and not summary['hardwareVerified']
 assert any(e.get('event')=='first-frame-finished' and e['success'] for e in events)
 report=dict(testBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),platform='linux/arm/v7',passed=True,summary=summary,verified=['actual first-frame-sc3336 userspace orchestration','graph format readback and profile loading','active timing conversion and sensor writes','parameter dequeue before raw stream startup','raw readback during three image dequeues','image shutdown before raw shutdown before parameter shutdown','full-sized saved image and 11145-byte initial parameter artifact'],limitations=['ioctl, readiness and image/metadata MMAP are test-only simulated boundaries; no actual camera/kernel pipeline is exercised.','Saved pixels are zero-filled synthetic memory, not sensor output or image-quality/QR evidence.','No full original RKAIQ controller equivalence or automatic 3A is established.'])
 (ROOT/'reverse-engineering/rkaiq/first-frame-sequence-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
