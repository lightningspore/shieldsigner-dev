#!/usr/bin/env python3
"""Run the actual static ARM artifacts under Docker's ARM Linux emulation."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[3]
image='alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd'
binaries=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release';fixtures=ROOT/'dist/reverse-engineering/fixtures'
def command(name,*args):return ['docker','run','--rm','-i','--network=none','--platform','linux/arm/v7','--mount',f'type=bind,src={binaries},dst=/work,readonly',image,'/work/'+name,*args]
selftest=subprocess.run(command('camera-probe','self-test'),text=True,capture_output=True,check=True)
with (fixtures/'inputs.txt').open('rb') as source:
 result=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
expected=(fixtures/'expected.txt').read_bytes();assert result.stdout==expected,'ARM executable differs from original-reference corpus'
lifecycle=ROOT/'dist/reverse-engineering/lifecycle-fixtures'
with (lifecycle/'inputs.txt').open('rb') as source:
 trace=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert trace.stdout==(lifecycle/'expected.txt').read_bytes(),'ARM lifecycle differs from original daemon'
binding=ROOT/'dist/reverse-engineering/binding-fixtures'
with (binding/'inputs.txt').open('rb') as source:
 selected=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert selected.stdout==(binding/'expected.txt').read_bytes(),'ARM sensor selector differs from original library'
events_negative=subprocess.run(command('camera-probe','events','/dev/null','--timeout-ms','1'),text=True,capture_output=True)
assert events_negative.returncode==1 and 'os error 25' in events_negative.stderr.lower(),events_negative
listing=subprocess.run(command('camera-probe','list'),text=True,capture_output=True,check=True);nodes=json.loads(listing.stdout)
assert nodes['linksRkaiq'] is False and nodes['devices']==[] and nodes['mediaGraph']==[]
negative=subprocess.run(command('camera-probe','capture','/dev/null','/tmp/should-not-exist'),text=True,capture_output=True)
assert negative.returncode==1 and 'os error 25' in negative.stderr.lower(),negative
report={'image':image,'platform':'linux/arm/v7','execution':'Docker Desktop ARM emulation; no camera device attached',
 'bindingReferenceCases':len(selected.stdout.splitlines()),'bindingMatch':True,
 'lifecycleReferenceTraces':len(trace.stdout.splitlines()),'lifecycleMatch':True,'invalidEventEndpointRejected':True,
 'numericalReferenceLines':len(expected.splitlines()),'numericalMatch':True,'cameraSelfTest':selftest.stdout.strip(),
 'nodeInventoryWithoutDevicePassed':True,'invalidVideoEndpointRejected':True,
 'binaries':{name:hashlib.sha256((binaries/name).read_bytes()).hexdigest() for name in ['camera-probe','numeric-fixture','frame-preview']},
 'limitations':['ARM/Linux userspace execution is verified; real camera capture and end-to-end ISP behavior are not tested.']}
(ROOT/'reverse-engineering/rkaiq/arm-smoke.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
