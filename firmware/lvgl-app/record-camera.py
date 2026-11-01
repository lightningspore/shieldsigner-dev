"""Record scoped scan/preview/native-QR evidence; never include sensor data."""
import hashlib
import json
from pathlib import Path
import subprocess
HERE=Path(__file__).resolve().parent
from artifact_paths import DIST
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def receipt(name):
    data=[json.loads(line) for line in (DIST/name).read_text().splitlines() if line.startswith('{')]
    if len(data)!=1 or data[0].get('passed') is not True:raise ValueError('Failed receipt: '+name)
    return data[0]
binary=DIST/'build/shieldsigner-lvgl'
board_sha=subprocess.check_output(['adb','shell','sha256sum /tmp/shieldsigner-lvgl-host'],text=True).split()[0]
if sha(binary)!=board_sha:raise ValueError('Board binary differs')
backend_paths=['/usr/lib/shieldsigner-camera/python/shieldsigner_lcd.abi3.so','/usr/lib/shieldsigner-camera/camera-probe','/usr/lib/shieldsigner-camera/shieldsigner-qr-reader']
backends={}
for path in backend_paths:backends[path]=subprocess.check_output(['adb','shell','sha256sum '+path],text=True).split()[0]
report=dict(checkpoint='2026-10-30-camera-native-qr',scope='ScanScreen and native transport; complete ScanView routing and known optical decoding not qualified',sources=json.loads((HERE/'sources.lock.json').read_text()),sourceGuards=json.loads((HERE/'source-guards.json').read_text()),binarySha256=board_sha,binaryBytes=binary.stat().st_size,installedBackendsSha256=backends,realCamera=receipt('camera-flow-display-arm.log'),syntheticQr=receipt('qr-scan-fixtures-display-arm.log'),previewProtocol=receipt('preview-protocol-display-arm.log'),previewFaults=receipt('preview-faults-arm.log'),nativeCorpus=receipt('native-smoke-camera-arm.json'),nativeRebuild=receipt('camera-native-rebuild.json'),hostUnitTests=36,installedAppChanged=False,osImageBuilt=False,flashed=False,limits=['No known-code optical qualification','Original complete ScanView destination routing/availability pending','Full Controller, entropy, QR output and signing integration pending','No matched memory/CPU/FPS comparison yet','Only 240x240 full-screen display target supported'],codeSha256={str(path.relative_to(HERE)):sha(path) for pattern in ['native/*','python/*.py','tests/*.py','patches/*.patch','*.py','*lock.json','source-guards.json'] for path in HERE.glob(pattern) if path.is_file()})
(HERE/'validation/camera-native-qr-arm.json').write_text(json.dumps(report,indent=2)+'\n')
print(board_sha)
