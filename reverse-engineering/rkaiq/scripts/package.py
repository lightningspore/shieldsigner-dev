#!/usr/bin/env python3
"""Assemble a checksummed hardware-test kit, excluding vendor binaries/pseudocode."""
from pathlib import Path
import hashlib,json,os,platform,shutil,subprocess,sys,tempfile,zipfile,tomllib
from elftools.elf.elffile import ELFFile
ROOT=Path(__file__).resolve().parents[3]
version=tomllib.loads((ROOT/'firmware/rkaiq-rs/Cargo.toml').read_text())['package']['version']
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
subprocess.run([sys.executable,str(ROOT/'reverse-engineering/rkaiq/scripts/release-preflight.py')],cwd=ROOT,check=True)
if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():
 raise SystemExit('Commit source and test evidence before freezing a versioned kit')
base=ROOT/'dist/reverse-engineering';base.mkdir(parents=True,exist_ok=True)
staging=tempfile.TemporaryDirectory(prefix='rkaiq-kit-staging-',dir=base)
kit=Path(staging.name)/('rkaiq-camera-test-'+version);kit.mkdir()
arm=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
smoke=json.loads((ROOT/'reverse-engineering/rkaiq/arm-smoke.json').read_text())
proof=json.loads((ROOT/'reverse-engineering/rkaiq/numeric-equivalence.json').read_text());assert proof['mismatchCount']==0
assert smoke['numericalReferenceLines']==proof['totalCases'] and smoke['numericalMatch']
items=[]
def copy(source,name):
 target=kit/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);items.append(name);return target
for name in ['camera-probe','numeric-fixture','frame-preview']:
 source=arm/name;assert hashlib.sha256(source.read_bytes()).hexdigest()==smoke['binaries'][name],'Smoke-test binary is stale'
 with source.open('rb') as f:
  elf=ELFFile(f);assert elf['e_machine']=='EM_ARM';assert not any(s['p_type']=='PT_INTERP' for s in elf.iter_segments())
  dynamic=elf.get_section_by_name('.dynamic');assert dynamic is None or not any(t.entry.d_tag=='DT_NEEDED' for t in dynamic.iter_tags()),'Unexpected dynamic dependency'
 copy(source,'bin/'+name).chmod(0o755)
qr_source=ROOT/'dist/reverse-engineering/qr-native-build/cmake/shieldsigner-qr-reader'
copy(qr_source,'bin/shieldsigner-qr-reader').chmod(0o755)
qr_proof=json.loads((ROOT/'reverse-engineering/rkaiq/native-qr-integration-hardware-validation.json').read_text())
for name in ['inputs.txt','expected.txt']:copy(base/'fixtures'/name,'fixtures/'+name)
for name in ['README.md','HARDWARE-TEST.md','FUNCTIONS.md','LIFECYCLE.md','DISCOVERY.md','STATISTICS.md','AE.md','AWB.md','ISP.md','PARAMETERS.md','SENSOR.md','CALIBRATION.md','iq-calibration-equivalence.json','iq-plan-validation.json','sensor-descriptor-equivalence.json','exposure-equivalence.json','sensor-linear-equivalence.json','ae-decision-equivalence.json','ae-damping-equivalence.json','isp-pipeline-equivalence.json','isp-black-level-equivalence.json','isp-demosaic-equivalence.json','demosaic-selection-equivalence.json','parameter-queue-equivalence.json','ae-measurement-equivalence.json','awb-measurement-equivalence.json','awb-gain-equivalence.json','awb-probability-equivalence.json','awb-preparation-equivalence.json','ae-big-grid-equivalence.json','ae-histogram-equivalence.json','ae-grid-equivalence.json','statistics-equivalence.json','binding-equivalence.json','lifecycle-equivalence.json','numeric-equivalence.json','arm-smoke.json','artifacts.json']:
 copy(ROOT/'reverse-engineering/rkaiq'/name,'HARDWARE-TEST.md' if name=='HARDWARE-TEST.md' else 'research/'+name)
for name in ['isp-color-equivalence.json','awb-translation-equivalence.json','raw-bridge-validation.json']:
 copy(ROOT/'reverse-engineering/rkaiq'/name,'research/'+name)
for name in ['first-frame-sequence-validation.json','ae-runtime-equivalence.json','ae-session-equivalence.json','sensor-submission-equivalence.json','isp-gain-results-equivalence.json','awb-publication-equivalence.json','isp-effective-equivalence.json']:
 copy(ROOT/'reverse-engineering/rkaiq'/name,'research/'+name)
sequence=json.loads((ROOT/'reverse-engineering/rkaiq/first-frame-sequence-validation.json').read_text())
automatic=[s for s in sequence['scenarios'] if s.get('automaticAe')]
assert sequence['passed'] and len(automatic)==2 and all(s['imageFrames']==33 and s['ae']['success'] for s in automatic)
copy(ROOT/'reverse-engineering/rkaiq/examples/pipeline-linear.template.json','examples/pipeline-linear.template.json')
for name in ['pipeline-luckfox-sc3336-observed.json','public-address-qr.png']:
 copy(ROOT/'reverse-engineering/rkaiq/examples'/name,'examples/'+name)
for name in ['verify_kit.py','configure_camera.py','optical_camera_check.py','shieldsigner_video_stream.py','shieldsigner_process_log.py','shieldsigner_camera_compat.py','shieldsigner_integration.py','shieldsigner_qr_decoder.py','native_qr_hardware_check.py','pinned_scan_loop_hardware_check.py','stream_hardware_check.py','managed_hardware_check.py','integration_hardware_check.py','restart_hardware_check.py','scan_loop_hardware_check.py','image_artifact_hardware_check.py']:
 copy(ROOT/'firmware/rkaiq-rs/python'/name,'python/'+name)
copy(ROOT/'firmware/rkaiq-rs/python/sc3336-owner.example.json','examples/sc3336-owner.example.json')
for name in ['server.py','index.html']:
 copy(ROOT/'firmware/rkaiq-rs/demo'/name,'demo/'+name)
for name in ['cold-camera-modules.sh','prepare-cold-boot.py','verify-cold-boot.py']:
 copy(ROOT/'reverse-engineering/rkaiq/scripts'/name,'tools/'+name)
for name in ['awb-live-hardware-validation.json','managed-camera-hardware-validation.json','clean-reboot-camera-hardware-validation.json','rgb-colorimetry-hardware-validation.json','application-integration-hardware-validation.json']:
 copy(ROOT/'reverse-engineering/rkaiq'/name,'research/'+name)
for name in ['awb-scene-sequence-validation.json','exposure-step-latency-validation.json','gain-step-latency-validation.json','live-ae-write-timing-validation.json','camera-restart-hardware-validation.json','scan-loop-hardware-validation.json','ae-startup-convergence-validation.json','demosaic-frame-equivalence.json','demosaic-live-validation.json','stream-image-artifact-validation.json','scan-demosaic-hardware-validation.json']:
 copy(ROOT/'reverse-engineering/rkaiq'/name,'research/'+name)
application=json.loads((ROOT/'reverse-engineering/rkaiq/application-integration-hardware-validation.json').read_text())
assert application['passed'] and application['cameraBinarySha256']==smoke['binaries']['camera-probe']
for name,digest in application['sourceSha256'].items():
 assert hashlib.sha256((ROOT/'firmware/rkaiq-rs/python'/name).read_bytes()).hexdigest()==digest,'Application hardware evidence is stale'
assert hashlib.sha256((ROOT/'reverse-engineering/rkaiq/examples/public-address-qr.png').read_bytes()).hexdigest()==application['fixture']['sha256']
# Include the complete committed public evidence/docs directory. This keeps new
# live-module evidence and relative research links with the implementation;
# ignored captures, full IQ files, vendor code and binary caches stay excluded.
research_root=ROOT/'reverse-engineering/rkaiq'
public_files=subprocess.check_output(['git','ls-files','-z','--','reverse-engineering/rkaiq'],cwd=ROOT).decode().split('\0')
for name in sorted(filter(None,public_files)):
 path=ROOT/name
 if path.parent==research_root and path.suffix in ('.json','.md'):
  target='research/'+path.name
  if target not in items:copy(path,target)


for name in ['inputs.txt','expected.txt']:copy(base/'lifecycle-fixtures'/name,'lifecycle-fixtures/'+name)
for name in ['inputs.txt','expected.txt']:copy(base/'binding-fixtures'/name,'binding-fixtures/'+name)
for name in ['inputs.txt','expected.txt']:copy(base/'statistics-fixtures'/name,'statistics-fixtures/'+name)
for name in ['inputs.txt','expected.txt']:copy(base/'ae-grid-fixtures'/name,'ae-grid-fixtures/'+name)
for name in ['inputs.txt','expected.txt']:copy(base/'ae-histogram-fixtures'/name,'ae-histogram-fixtures/'+name)
for name in ['inputs.txt','expected.txt']:copy(base/'ae-big-grid-fixtures'/name,'ae-big-grid-fixtures/'+name)
for name in ['inputs.txt','expected.txt']:copy(base/'sensor-linear-fixtures'/name,'sensor-linear-fixtures/'+name)
for name in ['inputs.txt','expected.txt']:copy(base/'exposure-fixtures'/name,'exposure-fixtures/'+name)
for name in ['inputs.txt','expected.txt']:copy(base/'sensor-descriptor-fixtures'/name,'sensor-descriptor-fixtures/'+name)
for name in ['inputs.txt','expected.txt']:copy(base/'iq-calibration-fixtures'/name,'iq-calibration-fixtures/'+name)
copy(base/'iq-calibration-fixtures/sc3336-exposure-subset.json','reference/sc3336-exposure-subset.json')
copy(base/'iq-calibration-fixtures/synthetic-sensor-info.json','examples/synthetic-sensor-info.json')
assert smoke['iqCalibrationReferenceCases']==100 and smoke['iqCalibrationMatch'] and smoke['armOfflinePlanPassed']
assert smoke['sensorDescriptorReferenceCases']==1000 and smoke['sensorDescriptorMatch']
assert smoke['exposureReferenceCases']==1000 and smoke['exposureMatch']
assert smoke['sensorLinearReferenceCases']==1000 and smoke['sensorLinearMatch']
for name in ['inputs.txt','expected.txt']:copy(base/'ae-decision-fixtures'/name,'ae-decision-fixtures/'+name)
assert smoke['aeDecisionReferenceCases']==1000 and smoke['aeDecisionMatch']
for name in ['inputs.txt','expected.txt']:copy(base/'ae-damping-fixtures'/name,'ae-damping-fixtures/'+name)
assert smoke['aeDampingReferenceCases']==1000 and smoke['aeDampingMatch']
for name in ['inputs.txt','expected.txt']:copy(base/'isp-pipeline-fixtures'/name,'isp-pipeline-fixtures/'+name)
assert smoke['ispPipelineReferenceCases']==1000 and smoke['ispPipelineMatch']
for name in ['inputs.txt','expected.txt']:copy(base/'isp-black-level-fixtures'/name,'isp-black-level-fixtures/'+name)
assert smoke['ispBlackLevelReferenceCases']==1000 and smoke['ispBlackLevelMatch']
for name in ['inputs.txt','expected.txt']:copy(base/'isp-demosaic-fixtures'/name,'isp-demosaic-fixtures/'+name)
assert smoke['ispDemosaicReferenceCases']==2000 and smoke['ispDemosaicMatch']
for name in ['inputs.txt','expected.txt']:copy(base/'demosaic-selection-fixtures'/name,'demosaic-selection-fixtures/'+name)
copy(base/'demosaic-selection-fixtures/sc3336-demosaic-subset.json','reference/sc3336-demosaic-subset.json')
assert smoke['demosaicSelectionReferenceCases']==1000 and smoke['demosaicSelectionMatch']
for name in ['inputs.txt','expected.txt']:copy(base/'parameter-queue-fixtures'/name,'parameter-queue-fixtures/'+name)
assert smoke['parameterQueueReferenceCases']==1000 and smoke['parameterQueueMatch']
assert smoke['parameterSubmitInvalidEndpointRejected'] and smoke['parameterSubmitInputGuardsPassed']
for name in ['inputs.txt','expected.txt']:copy(base/'ae-measurement-fixtures'/name,'ae-measurement-fixtures/'+name)
assert smoke['aeMeasurementReferenceCases']==2000 and smoke['aeMeasurementMatch']
for name in ['inputs.txt','expected.txt']:copy(base/'awb-measurement-fixtures'/name,'awb-measurement-fixtures/'+name)
assert smoke['awbMeasurementReferenceCases']==2000 and smoke['awbMeasurementMatch']
for name in ['inputs.txt','expected.txt']:copy(base/'awb-gain-fixtures'/name,'awb-gain-fixtures/'+name)
awb_gain_proof=json.loads((ROOT/'reverse-engineering/rkaiq/awb-gain-equivalence.json').read_text())
assert awb_gain_proof['cases']>=6000 and awb_gain_proof['mismatchCount']==0
assert smoke['awbGainReferenceCases']==awb_gain_proof['cases'] and smoke['awbGainMatch']
for name in ['inputs.txt','expected.txt']:copy(base/'awb-probability-fixtures'/name,'awb-probability-fixtures/'+name)
assert smoke['awbProbabilityReferenceCases']==2000 and smoke['awbProbabilityMatch']
for name in ['inputs.txt','expected.txt']:copy(base/'awb-preparation-fixtures'/name,'awb-preparation-fixtures/'+name)
assert smoke['awbPreparationReferenceCases']==500 and smoke['awbPreparationMatch']
assert smoke['aeBigGridReferenceCases']==1000 and smoke['aeBigGridMatch']
assert smoke['aeHistogramReferenceCases']==1000 and smoke['aeHistogramMatch']
assert smoke['aeGridReferenceCases']==1000 and smoke['aeGridMatch']
assert smoke['statisticsReferenceCases']==100 and smoke['statisticsMatch']
assert smoke['bindingReferenceCases']==1000 and smoke['bindingMatch']
assert smoke['lifecycleReferenceTraces']==100 and smoke['lifecycleMatch']
# Copy source so the Rust implementation can be reviewed alongside the binary.
source=ROOT/'firmware/rkaiq-rs'
tracked=subprocess.check_output(['git','ls-files','-z','--','firmware/rkaiq-rs'],cwd=ROOT).decode().split('\0')
for name in sorted(filter(None,tracked)):
 path=ROOT/name
 if path.is_file() and path.name!='.gitignore':copy(path,'source/rkaiq-rs/'+str(path.relative_to(source)))
for name in ['shieldsigner-qr-reader.cpp','qr-native-bench.cpp','qr-native-threshold.cpp','build-qr-native-bench.py','release-preflight.py','collect-runtime-notices.py']:
 copy(ROOT/'reverse-engineering/rkaiq/scripts'/name,'source/qr-reader/'+name)
if platform.system()=='Darwin' and platform.machine()=='arm64':
 for name in ['frame-preview','camera-probe']:
  host=source/'target/release'/name
  if host.exists():copy(host,'host/'+name+'-macos-arm64').chmod(0o755)
readme=r'''Experimental Rust SC3336 camera kit 0.0.1

Start with this quickstart, then research/HARDWARE-TEST.md for evidence and detailed scope.
The ARM camera binary, managed Python adapter, native QR worker and opt-in
application launcher are included. The QR worker is open-source ZXing-C++;
the camera control/ISP replacement is Rust and does not call RKAIQ userspace.
Development adds live ISO-dependent demosaic batches and default streaming
without a final scene-image dump; explicit diagnostic saving remains available.
Current development also includes live defect-pixel correction, color
correction, lens shading, Bayer spatial and temporal noise reduction, luma and
chroma noise reduction, and sharpening. All eight advanced blocks run together
on SC3336 hardware with live AE/AWB and demosaic. The combined result and its
scope are recorded in research/combined-isp-hardware-validation.json.
Earlier isolated-CNR startup failures remain historical diagnostic evidence;
they do not describe the default full-group configuration.
Calibration, statistics and logs are still retained.
The current source passed real AE/AWB capture, owner restart/crash cleanup,
full-range RGB delivery and application preview/decoder integration. A controlled
clean reboot was also tested; its separately bundled report identifies that build.
The exact included evidence reports define optical qualification. This is not
complete RKAIQ ABI parity or physical power-cycle/full-UI qualification.
No vendor binary, full IQ profile, private scene image or device credential is bundled.

Local desktop dashboard (after forwarding the owner's Unix stream socket):
  uv run --python 3.13 --with pillow python demo/server.py --camera-port 60366
Open http://127.0.0.1:8765/ on that desktop for live preview and snapshots.
The bridge uses one camera connection and fans frames out to browser clients.
Optional recorded telemetry is not a per-frame measurement.

Prerequisites on the Luckfox:
- Matching installed SeedSigner application and its Python/Pillow/QR dependencies.
- Camera kernel drivers loaded; no competing UI/vendor camera process.
- Verified media graph plan and the matching full SC3336 IQ file already on-device.
- Persistent results storage. /tmp is RAM-backed and is cleared at reboot.
The observed graph example is specific to the tested image/module order; inspect
bin/camera-probe list before using it on another image. The generic template is
not runnable until filled. tools/cold-camera-modules.sh is the pinned driver-only
loader; controlled one-boot skip helpers are documented in HARDWARE-TEST.md.

After extracting this folder to persistent SD storage on the board:

  camera_kit_dir=/shieldsigner-camera-tests/rkaiq-camera-test-0.0.1
  python3 "$camera_kit_dir/python/verify_kit.py" --restore-modes "$camera_kit_dir"
  chmod +x "$camera_kit_dir"/bin/*
  python3 "$camera_kit_dir/python/configure_camera.py" \
    --kit "$camera_kit_dir" \
    --plan "$camera_kit_dir/examples/pipeline-luckfox-sc3336-observed.json" \
    --iq /oem/usr/share/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json \
    --results /shieldsigner-camera-tests/results \
    --output /shieldsigner-camera-tests/camera-kit.json

The configurator uses explicit absolute paths and refuses to overwrite an existing
configuration. The default parameter/image/statistics nodes are 20/11/19; override
its flags if your verified inventory differs. The full original IQ file is NOT
included. First inspect the process-local patch without launching the UI:

  python3 "$camera_kit_dir/python/shieldsigner_integration.py" \
    --app-root /seedsigner --print-patch

Run the headless, real-camera integration test (includes clearly synthetic QR cases):

  python3 "$camera_kit_dir/python/integration_hardware_check.py" \
    --app-root /seedsigner --config /shieldsigner-camera-tests/camera-kit.json \
    --report /shieldsigner-camera-tests/integration-UNIQUE.json

For an actual optical check, display or print examples/public-address-qr.png,
point the camera at it, then run:

  python3 "$camera_kit_dir/python/optical_camera_check.py" \
    --app-root /seedsigner --config /shieldsigner-camera-tests/camera-kit.json \
    --report /shieldsigner-camera-tests/optical-UNIQUE.json --seconds 60

The image encodes the known public test address 1BoatSLRHtKNngkdXEeobR76b53LETtpyT;
it is a camera fixture, not a payment request. The optical tool has no synthetic
input path. Exit 0 means that target decoded and cleanup succeeded; exit 2 means
no match by the deadline, 1 means an error and 130 means interruption. Unrelated
QR/seed/wallet contents are not written to its report. Measurement/log artifacts remain in the configured private results directory;
streamed scene images are saved only with SHIELDSIGNER_CAMERA_SAVE_IMAGE=1. A timeout is not optical success.

For the actual app UI, with original UI/vendor services stopped:

  python3 "$camera_kit_dir/python/shieldsigner_integration.py" \
    --app-root /seedsigner --config /shieldsigner-camera-tests/camera-kit.json \
    --qr-reader "$camera_kit_dir/bin/shieldsigner-qr-reader"

The launcher verifies the installed Camera source, swaps the backend and preserves
complete rotated previews in memory. Installed Camera source and boot services
are unchanged. Full UI rendering/button interaction is not qualified by headless
integration tests. Append -- --help to test the real main.py import/argument path.

All bin/ programs are static ARMv7 Linux executables. Optional host/ programs target
macOS ARM64; frame-preview produces an uncalibrated PGM. Run numerical corpora
with an explicit persistent output directory (the board has little RAM):

  sh "$camera_kit_dir/run-numeric-test.sh" /shieldsigner-camera-tests/numeric-UNIQUE

run-numeric-test.sh runs original-reference numerical corpora on-board; its PASS is not optical/UI evidence.
manifest.json hashes every kit file and identifies committed source. Source and
dependency/runtime notices are included. Full research and mise tasks:
https://github.com/lightningspore/shieldsigner-dev/tree/main/reverse-engineering/rkaiq

The source/ files are review snapshots, not a standalone repository checkout.
To rebuild, clone that repository, checkout manifest.json sourceRevision, then
run mise run camera:rust:arm and mise run camera:qr:native-build. The pinned
upstream QR source revision and runtime notices are in licenses/. A package
freeze also requires exact current ARM smoke/application/native-QR evidence;
mise run camera:release:preflight reports missing or stale release inputs.
'''
(kit/'README.txt').write_text(readme.replace('0.0.1',version));items.append('README.txt')
script='''#!/bin/sh
set -eu
kit_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
result_dir=${1:?Pass a persistent results directory; /tmp is RAM-backed}
mkdir -p "$result_dir"
"$kit_dir/bin/camera-probe" self-test
"$kit_dir/bin/numeric-fixture" < "$kit_dir/fixtures/inputs.txt" > "$result_dir/numeric-actual.txt"
if cmp -s "$kit_dir/fixtures/expected.txt" "$result_dir/numeric-actual.txt"; then
    echo "PASS: all numerical results exactly match the original-reference corpus."
else
    echo "FAIL: numerical output differs; preserve $result_dir/numeric-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/lifecycle-fixtures/inputs.txt" > "$result_dir/lifecycle-actual.txt"
if cmp -s "$kit_dir/lifecycle-fixtures/expected.txt" "$result_dir/lifecycle-actual.txt"; then
    echo "PASS: service call traces match the original daemon reference. ISP backend remains incomplete."
else
    echo "FAIL: lifecycle output differs; preserve $result_dir/lifecycle-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/binding-fixtures/inputs.txt" > "$result_dir/binding-actual.txt"
if cmp -s "$kit_dir/binding-fixtures/expected.txt" "$result_dir/binding-actual.txt"; then
    echo "PASS: sensor selection matches the original controlled-inventory reference."
else
    echo "FAIL: sensor binding differs; preserve $result_dir/binding-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/statistics-fixtures/inputs.txt" > "$result_dir/statistics-actual.txt"
if cmp -s "$kit_dir/statistics-fixtures/expected.txt" "$result_dir/statistics-actual.txt"; then
    echo "PASS: AWB measurements match the original translator reference."
else
    echo "FAIL: statistics decoding differs; preserve $result_dir/statistics-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/ae-grid-fixtures/inputs.txt" > "$result_dir/ae-grid-actual.txt"
if cmp -s "$kit_dir/ae-grid-fixtures/expected.txt" "$result_dir/ae-grid-actual.txt"; then
    echo "PASS: corrected AE0 grids/means match the original helper reference."
else
    echo "FAIL: AE0 correction differs; preserve $result_dir/ae-grid-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/ae-histogram-fixtures/inputs.txt" > "$result_dir/ae-histogram-actual.txt"
if cmp -s "$kit_dir/ae-histogram-fixtures/expected.txt" "$result_dir/ae-histogram-actual.txt"; then
    echo "PASS: AE histogram correction matches the original helper reference."
else
    echo "FAIL: histogram correction differs; preserve $result_dir/ae-histogram-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/ae-big-grid-fixtures/inputs.txt" > "$result_dir/ae-big-grid-actual.txt"
if cmp -s "$kit_dir/ae-big-grid-fixtures/expected.txt" "$result_dir/ae-big-grid-actual.txt"; then
    echo "PASS: big-AE correction and sums match the original helper reference."
else
    echo "FAIL: big-AE correction differs; preserve $result_dir/ae-big-grid-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/sensor-linear-fixtures/inputs.txt" > "$result_dir/sensor-linear-actual.txt"
if cmp -s "$kit_dir/sensor-linear-fixtures/expected.txt" "$result_dir/sensor-linear-actual.txt"; then
    echo "PASS: sensor-write sequences match the original method reference; no device writes were made."
else
    echo "FAIL: sensor-write sequence differs; preserve $result_dir/sensor-linear-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/exposure-fixtures/inputs.txt" > "$result_dir/exposure-actual.txt"
if cmp -s "$kit_dir/exposure-fixtures/expected.txt" "$result_dir/exposure-actual.txt"; then
    echo "PASS: gain/time codes match the original RKAIQ plus uClibc reference."
else
    echo "FAIL: exposure conversion differs; preserve $result_dir/exposure-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/sensor-descriptor-fixtures/inputs.txt" > "$result_dir/sensor-descriptor-actual.txt"
if cmp -s "$kit_dir/sensor-descriptor-fixtures/expected.txt" "$result_dir/sensor-descriptor-actual.txt"; then
    echo "PASS: sensor descriptors match the original method reference."
else
    echo "FAIL: sensor descriptor differs; preserve $result_dir/sensor-descriptor-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/iq-calibration-fixtures/inputs.txt" > "$result_dir/iq-calibration-actual.txt"
if cmp -s "$kit_dir/iq-calibration-fixtures/expected.txt" "$result_dir/iq-calibration-actual.txt"; then
    echo "PASS: IQ loading and conversion match the SDK-calibrated native reference."
else
    echo "FAIL: IQ calibration conversion differs; preserve $result_dir/iq-calibration-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/ae-decision-fixtures/inputs.txt" > "$result_dir/ae-decision-actual.txt"
if cmp -s "$kit_dir/ae-decision-fixtures/expected.txt" "$result_dir/ae-decision-actual.txt"; then
    echo "PASS: histogram AE proposals match the original solver reference."
else
    echo "FAIL: histogram AE solver differs; preserve $result_dir/ae-decision-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/ae-damping-fixtures/inputs.txt" > "$result_dir/ae-damping-actual.txt"
if cmp -s "$kit_dir/ae-damping-fixtures/expected.txt" "$result_dir/ae-damping-actual.txt"; then
    echo "PASS: dynamic AE damping matches the original reference."
else
    echo "FAIL: dynamic AE damping differs; preserve $result_dir/ae-damping-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/isp-pipeline-fixtures/inputs.txt" > "$result_dir/isp-pipeline-actual.txt"
if cmp -s "$kit_dir/isp-pipeline-fixtures/expected.txt" "$result_dir/isp-pipeline-actual.txt"; then
    echo "PASS: ISP pad setup matches the original call/record reference; no device configured."
else
    echo "FAIL: ISP pad setup differs; preserve $result_dir/isp-pipeline-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/isp-black-level-fixtures/inputs.txt" > "$result_dir/isp-black-level-actual.txt"
if cmp -s "$kit_dir/isp-black-level-fixtures/expected.txt" "$result_dir/isp-black-level-actual.txt"; then
    echo "PASS: ISP black-level parameters/cache match the original reference."
else
    echo "FAIL: ISP black-level conversion differs; preserve $result_dir/isp-black-level-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/isp-demosaic-fixtures/inputs.txt" > "$result_dir/isp-demosaic-actual.txt"
if cmp -s "$kit_dir/isp-demosaic-fixtures/expected.txt" "$result_dir/isp-demosaic-actual.txt"; then
    echo "PASS: demosaic hardware quantization and ISP32 parameters match the original reference."
else
    echo "FAIL: demosaic conversion differs; preserve $result_dir/isp-demosaic-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/demosaic-selection-fixtures/inputs.txt" > "$result_dir/demosaic-selection-actual.txt"
if cmp -s "$kit_dir/demosaic-selection-fixtures/expected.txt" "$result_dir/demosaic-selection-actual.txt"; then
    echo "PASS: demosaic IQ/ISO tuning through hardware conversion matches the original reference."
else
    echo "FAIL: demosaic ISO selection differs; preserve $result_dir/demosaic-selection-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/parameter-queue-fixtures/inputs.txt" > "$result_dir/parameter-queue-actual.txt"
if cmp -s "$kit_dir/parameter-queue-fixtures/expected.txt" "$result_dir/parameter-queue-actual.txt"; then
    echo "PASS: metadata parameter queue states and ioctl records match the original reference."
else
    echo "FAIL: metadata queue state differs; preserve $result_dir/parameter-queue-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/ae-measurement-fixtures/inputs.txt" > "$result_dir/ae-measurement-actual.txt"
if cmp -s "$kit_dir/ae-measurement-fixtures/expected.txt" "$result_dir/ae-measurement-actual.txt"; then
    echo "PASS: AE/histogram measurement configuration and caches match the original reference."
else
    echo "FAIL: measurement configuration differs; preserve $result_dir/ae-measurement-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/awb-measurement-fixtures/inputs.txt" > "$result_dir/awb-measurement-actual.txt"
if cmp -s "$kit_dir/awb-measurement-fixtures/expected.txt" "$result_dir/awb-measurement-actual.txt"; then
    echo "PASS: AWB measurement configuration matches the original reference."
else
    echo "FAIL: AWB measurement configuration differs; preserve $result_dir/awb-measurement-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/awb-gain-fixtures/inputs.txt" > "$result_dir/awb-gain-actual.txt"
if cmp -s "$kit_dir/awb-gain-fixtures/expected.txt" "$result_dir/awb-gain-actual.txt"; then
    echo "PASS: AWB gain and temporal values match the original reference."
else
    echo "FAIL: AWB gain values differ; preserve $result_dir/awb-gain-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/awb-probability-fixtures/inputs.txt" > "$result_dir/awb-probability-actual.txt"
if cmp -s "$kit_dir/awb-probability-fixtures/expected.txt" "$result_dir/awb-probability-actual.txt"; then
    echo "PASS: AWB illumination probabilities and weighted gains match the original reference."
else
    echo "FAIL: AWB illumination weighting differs; preserve $result_dir/awb-probability-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/numeric-fixture" < "$kit_dir/awb-preparation-fixtures/inputs.txt" > "$result_dir/awb-preparation-actual.txt"
if cmp -s "$kit_dir/awb-preparation-fixtures/expected.txt" "$result_dir/awb-preparation-actual.txt"; then
    echo "PASS: AWB measurement preparation and time-share caches match the original reference."
else
    echo "FAIL: AWB preparation differs; preserve $result_dir/awb-preparation-actual.txt" >&2
    exit 1
fi
"$kit_dir/bin/camera-probe" list > "$result_dir/camera-nodes.json"
echo "Camera node inventory: $result_dir/camera-nodes.json"
echo "Numerical PASS does not mean camera capture or complete RKAIQ reconstruction passed."
'''
(kit/'run-numeric-test.sh').write_text(script);(kit/'run-numeric-test.sh').chmod(0o755);items.append('run-numeric-test.sh')
metadata=json.loads(subprocess.check_output(['mise','exec','rust@1.93.1','--','cargo','metadata','--locked','--format-version','1','--manifest-path',str(source/'Cargo.toml')],cwd=ROOT,text=True))
licenses=[]
for package in metadata['packages']:
 if package['name']=='shieldsigner-rkaiq':continue
 folder=Path(package['manifest_path']).parent;license_files=[]
 for path in sorted(folder.iterdir()):
  if path.is_file() and path.name.upper().startswith(('LICENSE','LICENCE','COPYING','COPYRIGHT')):
   name='licenses/'+package['name']+'-'+package['version']+'/'+path.name;copy(path,name);license_files.append(name)
 licenses.append({'crate':package['name'],'version':package['version'],'declaredLicense':package['license'],'files':license_files})
# Include runtime notices for Rust's standard library and the statically linked musl.
sysroot=Path(subprocess.check_output(['mise','exec','rust@1.93.1','--','rustc','--print','sysroot'],cwd=ROOT,text=True).strip())
for name in ['LICENSE-APACHE','LICENSE-MIT','COPYRIGHT.html']:
 path=sysroot/'share/doc/rust'/name
 if path.exists():copy(path,'licenses/rust-runtime/'+name)
zigroot=Path(subprocess.check_output(['mise','where','zig@0.15.2'],cwd=ROOT,text=True).strip())
for path in [zigroot/'lib/libc/musl/COPYRIGHT',zigroot/'lib/libc/musl/COPYRIGHT.txt']:
 if path.exists():copy(path,'licenses/musl/'+path.name)
# The QR worker statically links ZXing-C++, libc++/libc++abi and compiler runtime.
zxing=ROOT/'.tools/zxing-cpp-3.1.1'
zxing_revision=subprocess.check_output(['git','-C',str(zxing),'rev-parse','HEAD'],text=True).strip()
assert zxing_revision=='287c85df6f961c8efbfb5ffd736cd9457b8b890e','Unexpected ZXing source revision'
copy(zxing/'LICENSE','licenses/zxing-cpp/LICENSE')
for path in sorted((zxing/'core/src/libzueci').iterdir()):
 if path.is_file():copy(path,'licenses/zxing-cpp/libzueci/'+path.name)
for component in ['libcxx','libcxxabi']:
 copy(zigroot/'lib'/component/'LICENSE.TXT','licenses/'+component+'/LICENSE.TXT')
copy(zigroot/'LICENSE','licenses/zig-runtime/LICENSE')
qr_dependencies={'name':'ZXing-C++','version':'3.1.1','sourceRevision':zxing_revision,
 'sourceUrl':'https://github.com/zxing-cpp/zxing-cpp/tree/'+zxing_revision,
 'buildScriptSnapshot':'source/qr-reader/build-qr-native-bench.py','rebuildTask':'mise run camera:qr:native-build (from full source checkout)',
 'compiler':'mise Zig0.15.2 C++20 Cortex-A7/musl',
 'binarySha256':hashlib.sha256(qr_source.read_bytes()).hexdigest(),
 'notes':['No QR payload is converted to text by the worker.','libzueci notice/source headers are retained alongside its parent Apache2.0 license.','The complete upstream source is available at the pinned source URL; no vendor camera code is bundled.']}
(kit/'licenses/qr-reader-dependencies.json').write_text(json.dumps(qr_dependencies,indent=2)+'\n');items.append('licenses/qr-reader-dependencies.json')
subprocess.run([sys.executable,str(ROOT/'reverse-engineering/rkaiq/scripts/collect-runtime-notices.py'),
 '--output',str(kit/'licenses')],cwd=ROOT,check=True)
for path in sorted((kit/'licenses').rglob('*')):
 if path.is_file():
  relative=str(path.relative_to(kit))
  if relative not in items:items.append(relative)
(kit/'licenses/dependencies.json').write_text(json.dumps(licenses,indent=2)+'\n');items.append('licenses/dependencies.json')
manifest={'sourceRevision':revision,'sourceWorktreeDirty':False,'version':version,'target':'armv7-unknown-linux-musleabihf',
 'status':'Experimental SC3336 Rust camera controls with native QR integration; physical qualification remains scoped by bundled evidence',
 'numericCases':proof['totalCases'],'fullIspReplacement':False,'linksVendorRkaiq':False,
 'fullRkaiqAbiReplacement':False,
 'fixedProfileVerification':'research/isp-'+version.removesuffix('-dev')+'-fresh-hardware-validation.json',
 'fixedFirstFrameCommand':'first-frame-sc3336','automaticExposureCommand':'auto-frame-sc3336',
 'liveAutomaticCommand':'auto-awb-frame-sc3336','continuousCommand':'stream-sc3336',
 'automaticExposureHardwareVerified':True,'automaticWhiteBalanceHardwareVerified':True,
 'whiteBalancePolicy':'FAST-to-normal seven-light AWB with exact registered configuration snapshots',
 'automatic3A':False,'controlledCleanRebootEvidenceBundled':True,'opticalScanQualified':qr_proof.get('opticalScanQualified',False),
 'nativeQrWorkerBundled':True,'nativeQrWorkerSha256':hashlib.sha256(qr_source.read_bytes()).hexdigest(),
 'fullUiQualified':False,'fullIqBundled':False,'publicQrFixturePayload':'1BoatSLRHtKNngkdXEeobR76b53LETtpyT','files':[]}
for name in sorted(items):
 path=kit/name;manifest['files'].append({'name':name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mode':format(path.stat().st_mode&0o777,'04o')})
(kit/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
archive=base/(kit.name+'.zip')
if archive.exists():
 with zipfile.ZipFile(archive) as old:previous=json.loads(old.read(kit.name+'/manifest.json'))
 if previous!=manifest:raise SystemExit('Refusing to replace an existing kit version; bump Cargo package version first')
 print('Identical version already packaged:',archive);raise SystemExit(0)
staged_archive=Path(staging.name)/(kit.name+'.zip')
with zipfile.ZipFile(staged_archive,'w',zipfile.ZIP_DEFLATED) as out:
 for name in [*sorted(items),'manifest.json']:out.write(kit/name,kit.name+'/'+name)
# Publish without overwriting an existing immutable archive, then expose its tree.
os.link(staged_archive,archive)
published=base/kit.name
if published.exists():shutil.rmtree(published)
shutil.move(str(kit),str(published))
staging.cleanup()
print(archive,archive.stat().st_size,'bytes; sha256',hashlib.sha256(archive.read_bytes()).hexdigest())
