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
 summaries=[]
 for statistics,multi_tx,automatic in [(False,False,False),(True,False,False),(False,True,False),(True,True,False),(True,False,True),(True,True,True)]:
  command=['docker','run','--rm','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={binary.parent},dst=/tests,readonly','--mount',f'type=bind,src={iq.parent},dst=/iq,readonly','-e','SHIELDSIGNER_TEST_IQ=/iq/'+iq.name]
  if statistics:command+=['-e','SHIELDSIGNER_TEST_STATS=1']
  if multi_tx:command+=['-e','SHIELDSIGNER_TEST_MPLANE_TX=1']
  if automatic:command+=['-e','SHIELDSIGNER_TEST_AUTO_AE=1']
  command += [image,'/tests/'+binary.name,'first_frame_driver','--ignored','--nocapture','--test-threads=1']
  run=subprocess.run(command,text=True,capture_output=True,timeout=30)
  assert run.returncode==0,(run.stdout+run.stderr)[-6000:]
  events=[json.loads(line) for line in run.stdout.splitlines() if line.startswith('{') and line.endswith('}')]
  gain=next(e for e in events if e.get('event')=='runtime-gain-queue-verified');assert gain['queued']==6 and gain['snapshotSubmissions']==3 and gain['poolExhaustionChecked'] and gain['unityNoopChecked']
  summary=next(e for e in events if e.get('event')=='simulated-startup-verified')
  if not automatic:assert summary['sofEvents']>0 and summary['statisticsEvents']==summary['statisticsFrames']
  assert summary['imageFrames']==(33 if automatic else 3) and summary['rawFrames']>=summary['imageFrames'] and not summary['hardwareVerified']
  if automatic:
   ae=next(e for e in events if e.get('event')=='automatic-ae-finished');assert ae['success'] and ae['processedStatistics']>=3 and ae['parameterSnapshots']>=3
   summary['ae']=ae
  assert summary['statisticsEnabled']==statistics and summary['multiPlaneTx']==multi_tx
  if statistics:assert summary['statisticsFrames']>=3
  assert any(e.get('event')=='first-frame-finished' and e['success'] for e in events)
  summaries.append(summary)
 summary=summaries[0]
 report=dict(testBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),platform='linux/arm/v7',passed=True,summary=summary,scenarios=summaries,verified=['runtime effective-exposure gains through persistent MMAP parameter enqueue, pool exhaustion, EAGAIN preservation, ordered completion/reuse, invalid-completion quarantine and unity no-op','owned SOF/statistics transport, single-owner AE/sensor processing and successful gain-submission snapshot registration with failure preservation','fixed first-frame and automatic-exposure capture orchestration, including 33-frame automatic runs on both raw TX APIs','graph format readback and profile loading','active timing conversion and sensor writes','parameter dequeue before raw stream startup','raw readback during three image dequeues','image shutdown before raw shutdown before parameter shutdown','full-sized saved image and 11145-byte initial parameter artifact','optional statistics queue ready before raw startup and retained through camera teardown','metadata frame headers and raw statistics artifact'],limitations=['ioctl, readiness and image/metadata MMAP are test-only simulated boundaries; no actual camera/kernel pipeline is exercised.','Saved pixels are zero-filled synthetic memory, not sensor output or image-quality/QR evidence.','No full original RKAIQ controller equivalence or automatic 3A is established.'])
 (ROOT/'reverse-engineering/rkaiq/first-frame-sequence-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
