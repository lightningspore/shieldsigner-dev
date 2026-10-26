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
statistics=ROOT/'dist/reverse-engineering/statistics-fixtures'
with (statistics/'inputs.txt').open('rb') as source:
 decoded=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert decoded.stdout==(statistics/'expected.txt').read_bytes(),'ARM AWB measurements differ from original translator'
ae_grid=ROOT/'dist/reverse-engineering/ae-grid-fixtures'
with (ae_grid/'inputs.txt').open('rb') as source:
 corrected=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert corrected.stdout==(ae_grid/'expected.txt').read_bytes(),'ARM AE0 correction differs from original helper'
ae_histogram=ROOT/'dist/reverse-engineering/ae-histogram-fixtures'
with (ae_histogram/'inputs.txt').open('rb') as source:
 histogram=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert histogram.stdout==(ae_histogram/'expected.txt').read_bytes(),'ARM histogram correction differs from original helper'
ae_big_grid=ROOT/'dist/reverse-engineering/ae-big-grid-fixtures'
with (ae_big_grid/'inputs.txt').open('rb') as source:
 big_grid=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert big_grid.stdout==(ae_big_grid/'expected.txt').read_bytes(),'ARM big-AE correction differs from original helper'
sensor_linear=ROOT/'dist/reverse-engineering/sensor-linear-fixtures'
with (sensor_linear/'inputs.txt').open('rb') as source:
 controls=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert controls.stdout==(sensor_linear/'expected.txt').read_bytes(),'ARM sensor-write sequence differs from original method'
exposure=ROOT/'dist/reverse-engineering/exposure-fixtures'
with (exposure/'inputs.txt').open('rb') as source:
 converted=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert converted.stdout==(exposure/'expected.txt').read_bytes(),'ARM exposure conversion differs from original RKAIQ/uClibc'
sensor_descriptor=ROOT/'dist/reverse-engineering/sensor-descriptor-fixtures'
with (sensor_descriptor/'inputs.txt').open('rb') as source:
 described=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert described.stdout==(sensor_descriptor/'expected.txt').read_bytes(),'ARM descriptor differs from original methods'
invalid_sensor=subprocess.run(command('camera-probe','sensor-info','/dev/null'),text=True,capture_output=True)
assert invalid_sensor.returncode==1 and 'os error 25' in invalid_sensor.stderr.lower(),invalid_sensor
iq_calibration=ROOT/'dist/reverse-engineering/iq-calibration-fixtures'
with (iq_calibration/'inputs.txt').open('rb') as source:
 calibrated=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert calibrated.stdout==(iq_calibration/'expected.txt').read_bytes(),'ARM IQ loading/conversion differs from native reference'
plan_command=command('camera-probe','exposure-plan','/iq/sc3336-exposure-subset.json','/iq/synthetic-sensor-info.json','0.01','2')
plan_command[plan_command.index(image):plan_command.index(image)]=['--mount',f'type=bind,src={iq_calibration},dst=/iq,readonly']
plan=json.loads(subprocess.run(plan_command,capture_output=True,check=True).stdout)
assert not plan['writesSensor'] and (plan['integrationTimeCode'],plan['gainCode'])==(288,256)
ae_decision=ROOT/'dist/reverse-engineering/ae-decision-fixtures'
with (ae_decision/'inputs.txt').open('rb') as source:
 decision=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert decision.stdout==(ae_decision/'expected.txt').read_bytes(),'ARM histogram AE solver differs from original instructions'
ae_damping=ROOT/'dist/reverse-engineering/ae-damping-fixtures'
with (ae_damping/'inputs.txt').open('rb') as source:
 damping=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert damping.stdout==(ae_damping/'expected.txt').read_bytes(),'ARM dynamic damping differs from original instructions'
isp_pipeline=ROOT/'dist/reverse-engineering/isp-pipeline-fixtures'
with (isp_pipeline/'inputs.txt').open('rb') as source:
 pipeline=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert pipeline.stdout==(isp_pipeline/'expected.txt').read_bytes(),'ARM ISP pad orchestration differs from original instructions'
isp_black_level=ROOT/'dist/reverse-engineering/isp-black-level-fixtures'
with (isp_black_level/'inputs.txt').open('rb') as source:
 black_level=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert black_level.stdout==(isp_black_level/'expected.txt').read_bytes(),'ARM ISP black-level conversion differs from original instructions'
isp_demosaic=ROOT/'dist/reverse-engineering/isp-demosaic-fixtures'
with (isp_demosaic/'inputs.txt').open('rb') as source:
 demosaic=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert demosaic.stdout==(isp_demosaic/'expected.txt').read_bytes(),'ARM demosaic hardware conversion differs from original instructions'
demosaic_selection=ROOT/'dist/reverse-engineering/demosaic-selection-fixtures'
with (demosaic_selection/'inputs.txt').open('rb') as source:
 demosaic_selected=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert demosaic_selected.stdout==(demosaic_selection/'expected.txt').read_bytes(),'ARM demosaic tuning/quantization differs from original instructions'
parameter_queue=ROOT/'dist/reverse-engineering/parameter-queue-fixtures'
with (parameter_queue/'inputs.txt').open('rb') as source:
 parameter_queued=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert parameter_queued.stdout==(parameter_queue/'expected.txt').read_bytes(),'ARM parameter queue state differs from original instructions'
# Synthetic data below is only for rejection checks against /dev/null/nonexistent
# devices. It is not a usable initial IQ record and is not included in the kit.
parameter_guards=ROOT/'dist/reverse-engineering/parameter-command-guards';parameter_guards.mkdir(parents=True,exist_ok=True)
(parameter_guards/'short.bin').write_bytes(b'0');(parameter_guards/'empty.bin').write_bytes(bytes(11145));(parameter_guards/'oversize.bin').write_bytes(bytes(11146))
synthetic=bytearray(11145);synthetic[0]=2;(parameter_guards/'synthetic-guard-only.bin').write_bytes(synthetic)
def parameter_command(*args):
 c=command('camera-probe','submit-parameters',*args);c[c.index(image):c.index(image)]=['--mount',f'type=bind,src={parameter_guards},dst=/params,readonly'];return c
parameter_invalid=subprocess.run(parameter_command('/dev/null','/params/synthetic-guard-only.bin'),text=True,capture_output=True)
assert parameter_invalid.returncode==1 and 'os error 25' in parameter_invalid.stderr.lower() and not parameter_invalid.stdout,parameter_invalid
for file,message in [('short.bin','exactly 11145'),('empty.bin','no module updates'),('oversize.bin','exactly 11145')]:
 rejected=subprocess.run(parameter_command('/dev/does-not-exist','/params/'+file),text=True,capture_output=True)
 assert rejected.returncode==1 and message in rejected.stderr and not rejected.stdout,rejected
for option,value in [('--hold-ms','300001'),('--timeout-ms','0'),('--buffers','3')]:
 rejected=subprocess.run(parameter_command('/dev/does-not-exist','/params/synthetic-guard-only.bin',option,value),text=True,capture_output=True)
 assert rejected.returncode==1 and 'Unsupported parameter option/range' in rejected.stderr and not rejected.stdout,rejected
ae_measurement=ROOT/'dist/reverse-engineering/ae-measurement-fixtures'
with (ae_measurement/'inputs.txt').open('rb') as source:
 measured=subprocess.run(command('numeric-fixture'),stdin=source,capture_output=True,check=True)
assert measured.stdout==(ae_measurement/'expected.txt').read_bytes(),'ARM AE/histogram parameter blocks differ from original dispatcher'
events_negative=subprocess.run(command('camera-probe','events','/dev/null','--timeout-ms','1'),text=True,capture_output=True)
assert events_negative.returncode==1 and 'os error 25' in events_negative.stderr.lower(),events_negative
listing=subprocess.run(command('camera-probe','list'),text=True,capture_output=True,check=True);nodes=json.loads(listing.stdout)
assert nodes['linksRkaiq'] is False and nodes['devices']==[] and nodes['mediaGraph']==[]
negative=subprocess.run(command('camera-probe','capture','/dev/null','/tmp/should-not-exist'),text=True,capture_output=True)
assert negative.returncode==1 and 'os error 25' in negative.stderr.lower(),negative
stats_negative=subprocess.run(command('camera-probe','capture-statistics','/dev/null','/tmp/should-not-exist'),text=True,capture_output=True)
assert stats_negative.returncode==1 and 'os error 25' in stats_negative.stderr.lower(),stats_negative
for options,expected in [(['--buffers','1'],'at least two buffers'),(['--width','640'],'image dimensions/FourCC options are unsupported')]:
 result=subprocess.run(command('camera-probe','capture-statistics','/dev/null','/tmp/should-not-exist',*options),text=True,capture_output=True)
 assert result.returncode==1 and expected in result.stderr,result
occupied=subprocess.run(command('camera-probe','capture-statistics','/dev/null','/work/camera-probe'),text=True,capture_output=True)
assert occupied.returncode==1 and 'already exists' in occupied.stderr,occupied
write_negative=subprocess.run(command('camera-probe','apply-linear','/dev/null','1600','256','0','100'),text=True,capture_output=True)
assert write_negative.returncode==1 and 'os error 25' in write_negative.stderr.lower(),write_negative
write_report=json.loads(write_negative.stdout);assert not write_report['success'] and write_report['writes']==[]
for values,message in [(['1600','2147483648','0','100'],'nonnegative signed 32-bit'),(['1600','256','0','100','2'],'DCG mode must be')]:
 rejected=subprocess.run(command('camera-probe','apply-linear','/dev/null',*values),text=True,capture_output=True)
 assert rejected.returncode==1 and message in rejected.stderr and not rejected.stdout,rejected
report={'image':image,'platform':'linux/arm/v7','execution':'Docker Desktop ARM emulation; no camera device attached',
 'aeMeasurementReferenceCases':len(measured.stdout.splitlines()),'aeMeasurementMatch':True,
 'parameterQueueReferenceCases':len(parameter_queued.stdout.splitlines()),'parameterQueueMatch':True,
 'parameterSubmitInvalidEndpointRejected':True,'parameterSubmitInputGuardsPassed':True,
 'demosaicSelectionReferenceCases':len(demosaic_selected.stdout.splitlines()),'demosaicSelectionMatch':True,
 'ispDemosaicReferenceCases':len(demosaic.stdout.splitlines()),'ispDemosaicMatch':True,
 'ispBlackLevelReferenceCases':len(black_level.stdout.splitlines()),'ispBlackLevelMatch':True,
 'ispPipelineReferenceCases':len(pipeline.stdout.splitlines()),'ispPipelineMatch':True,
 'aeDampingReferenceCases':len(damping.stdout.splitlines()),'aeDampingMatch':True,
 'aeDecisionReferenceCases':len(decision.stdout.splitlines()),'aeDecisionMatch':True,
 'sensorWriteInvalidEndpointRejected':True,'sensorWriteArgumentGuardsPassed':True,
 'iqCalibrationReferenceCases':len(calibrated.stdout.splitlines()),'iqCalibrationMatch':True,'armOfflinePlanPassed':True,
 'sensorDescriptorReferenceCases':len(described.stdout.splitlines()),'sensorDescriptorMatch':True,'invalidSensorEndpointRejected':True,
 'exposureReferenceCases':len(converted.stdout.splitlines()),'exposureMatch':True,
 'sensorLinearReferenceCases':len(controls.stdout.splitlines()),'sensorLinearMatch':True,
 'aeBigGridReferenceCases':len(big_grid.stdout.splitlines()),'aeBigGridMatch':True,
 'aeHistogramReferenceCases':len(histogram.stdout.splitlines()),'aeHistogramMatch':True,
 'aeGridReferenceCases':len(corrected.stdout.splitlines()),'aeGridMatch':True,
 'statisticsCaptureGuardsPassed':True,'statisticsInvalidEndpointRejected':True,
 'statisticsReferenceCases':len(decoded.stdout.splitlines()),'statisticsMatch':True,
 'bindingReferenceCases':len(selected.stdout.splitlines()),'bindingMatch':True,
 'lifecycleReferenceTraces':len(trace.stdout.splitlines()),'lifecycleMatch':True,'invalidEventEndpointRejected':True,
 'numericalReferenceLines':len(expected.splitlines()),'numericalMatch':True,'cameraSelfTest':selftest.stdout.strip(),
 'nodeInventoryWithoutDevicePassed':True,'invalidVideoEndpointRejected':True,
 'binaries':{name:hashlib.sha256((binaries/name).read_bytes()).hexdigest() for name in ['camera-probe','numeric-fixture','frame-preview']},
 'limitations':['ARM/Linux userspace execution is verified; real camera capture and end-to-end ISP behavior are not tested.']}
(ROOT/'reverse-engineering/rkaiq/arm-smoke.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
