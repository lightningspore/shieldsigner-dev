#!/usr/bin/env python3
"""Assemble a checksummed hardware-test kit, excluding vendor binaries/pseudocode."""
from pathlib import Path
import hashlib,json,platform,shutil,subprocess,zipfile,tomllib
from elftools.elf.elffile import ELFFile
ROOT=Path(__file__).resolve().parents[3]
version=tomllib.loads((ROOT/'firmware/rkaiq-rs/Cargo.toml').read_text())['package']['version']
base=ROOT/'dist/reverse-engineering';kit=base/('rkaiq-camera-test-'+version);kit.mkdir(parents=True,exist_ok=True)
arm=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
smoke=json.loads((ROOT/'reverse-engineering/rkaiq/arm-smoke.json').read_text())
proof=json.loads((ROOT/'reverse-engineering/rkaiq/numeric-equivalence.json').read_text());assert proof['mismatchCount']==0
items=[]
def copy(source,name):
 target=kit/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);items.append(name);return target
for name in ['camera-probe','numeric-fixture','frame-preview']:
 source=arm/name;assert hashlib.sha256(source.read_bytes()).hexdigest()==smoke['binaries'][name],'Smoke-test binary is stale'
 with source.open('rb') as f:
  elf=ELFFile(f);assert elf['e_machine']=='EM_ARM';assert not any(s['p_type']=='PT_INTERP' for s in elf.iter_segments())
  dynamic=elf.get_section_by_name('.dynamic');assert dynamic is None or not any(t.entry.d_tag=='DT_NEEDED' for t in dynamic.iter_tags()),'Unexpected dynamic dependency'
 copy(source,'bin/'+name).chmod(0o755)
for name in ['inputs.txt','expected.txt']:copy(base/'fixtures'/name,'fixtures/'+name)
for name in ['README.md','HARDWARE-TEST.md','FUNCTIONS.md','LIFECYCLE.md','DISCOVERY.md','STATISTICS.md','AE.md','AWB.md','ISP.md','PARAMETERS.md','SENSOR.md','CALIBRATION.md','iq-calibration-equivalence.json','iq-plan-validation.json','sensor-descriptor-equivalence.json','exposure-equivalence.json','sensor-linear-equivalence.json','ae-decision-equivalence.json','ae-damping-equivalence.json','isp-pipeline-equivalence.json','isp-black-level-equivalence.json','isp-demosaic-equivalence.json','demosaic-selection-equivalence.json','parameter-queue-equivalence.json','ae-measurement-equivalence.json','awb-measurement-equivalence.json','awb-gain-equivalence.json','awb-probability-equivalence.json','awb-preparation-equivalence.json','ae-big-grid-equivalence.json','ae-histogram-equivalence.json','ae-grid-equivalence.json','statistics-equivalence.json','binding-equivalence.json','lifecycle-equivalence.json','numeric-equivalence.json','arm-smoke.json','artifacts.json']:
 copy(ROOT/'reverse-engineering/rkaiq'/name,'HARDWARE-TEST.md' if name=='HARDWARE-TEST.md' else 'research/'+name)
for name in ['isp-color-equivalence.json','awb-translation-equivalence.json','raw-bridge-validation.json']:
 copy(ROOT/'reverse-engineering/rkaiq'/name,'research/'+name)
copy(ROOT/'reverse-engineering/rkaiq/examples/pipeline-linear.template.json','examples/pipeline-linear.template.json')
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
assert smoke['awbGainReferenceCases']==6000 and smoke['awbGainMatch']
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
for path in sorted(source.rglob('*')):
 if path.is_file() and 'target' not in path.relative_to(source).parts and path.name!='.gitignore':copy(path,'source/rkaiq-rs/'+str(path.relative_to(source)))
if platform.system()=='Darwin' and platform.machine()=='arm64':
 for name in ['frame-preview','camera-probe']:
  host=source/'target/release'/name
  if host.exists():copy(host,'host/'+name+'-macos-arm64').chmod(0o755)
readme='''Experimental RKAIQ Rust camera test kit 0.0.1

START WITH HARDWARE-TEST.md.

This is a partial numerical reconstruction plus diagnostic tools, not a complete
RKAIQ/ISP replacement. No firmware installation or boot-service changes are made.
Explicit startup commands change graph, sensor and ISP state. The kit does
not include or link the original vendor RKAIQ binaries. A real camera is required
to test frame capture; the completed numerical/ARM-emulation tests do not prove it.

All bin/ executables target ARMv7 Linux and are statically linked. On this Mac,
host/frame-preview-macos-arm64 can convert captured raw frames for inspection.
The PGM preview is uncalibrated; Bayer frames use 2x2 binning.

Run ./run-numeric-test.sh RESULTS_DIRECTORY on the Luckfox, then follow the guide.
This version includes first-frame-sc3336: explicit graph plan + full existing
SC3336 IQ JSON + parameter/image nodes + output basename. It connects fixed
startup exposure, ISP parameters, raw DMA-BUF bridging and image capture.
The full original IQ profile is NOT bundled: use the matching file already on
your device or retrieve the SHA-pinned source from research/artifacts.json.
Fill examples/pipeline-linear.template.json from actual inventory; placeholders
are not runnable. No successful vendor-free hardware frame is claimed.
Automatic exposure/white balance and full native startup fidelity are unfinished.
manifest.json records SHA-256 for each kit file. Source and dependency license
texts are included. Full investigation and reproducible mise tasks:
https://github.com/lightningspore/shieldsigner-dev/tree/main/reverse-engineering/rkaiq
'''
(kit/'README.txt').write_text(readme.replace('0.0.1',version));items.append('README.txt')
script='''#!/bin/sh
set -eu
kit_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
result_dir=${1:-/tmp/shieldsigner-rust-results}
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
(kit/'licenses/dependencies.json').write_text(json.dumps(licenses,indent=2)+'\n');items.append('licenses/dependencies.json')
manifest={'version':version,'target':'armv7-unknown-linux-musleabihf','status':'Partial reconstruction; hardware camera validation pending',
 'numericCases':proof['totalCases'],'fullIspReplacement':False,'linksVendorRkaiq':False,'fixedFirstFrameCommand':'first-frame-sc3336','automatic3A':False,'vendorFreeHardwareFrameVerified':False,'fullIqBundled':False,'files':[]}
for name in sorted(items):
 path=kit/name;manifest['files'].append({'name':name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(kit/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
archive=base/(kit.name+'.zip')
if archive.exists():
 with zipfile.ZipFile(archive) as old:previous=json.loads(old.read(kit.name+'/manifest.json'))
 if previous!=manifest:raise SystemExit('Refusing to replace an existing kit version; bump Cargo package version first')
 print('Identical version already packaged:',archive);raise SystemExit(0)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as out:
 for name in [*sorted(items),'manifest.json']:out.write(kit/name,kit.name+'/'+name)
print(archive,archive.stat().st_size,'bytes; sha256',hashlib.sha256(archive.read_bytes()).hexdigest())
