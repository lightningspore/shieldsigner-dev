"""Record scoped public-fixture receipts and exact migration/build inputs."""
from pathlib import Path
import hashlib
import json
HERE=Path(__file__).resolve().parent
from artifact_paths import DIST
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def receipt(name):
    lines=(DIST/name).read_text().splitlines()
    records=[json.loads(line) for line in lines if line.startswith('{')]
    if len(records)!=1 or records[0].get('passed') is not True:raise ValueError('Missing successful receipt: '+name)
    return records[0]
report={
 'checkpoint':'2026-10-30-settings-keyboards-seed-recovery',
 'scope':'Isolated original-View/model flows and native UI contracts; full Controller and image integration incomplete',
 'sources':json.loads((HERE/'sources.lock.json').read_text()),
 'guards':json.loads((HERE/'source-guards.json').read_text()),
 'binarySha256':sha(DIST/'build/shieldsigner-lvgl'),
 'binaryBytes':(DIST/'build/shieldsigner-lvgl').stat().st_size,
 'nativeCorpus':receipt('native-smoke-settings-arm.json'),
 'settingsFlow':receipt('settings-flow-display-arm.log'),
 'directKeyboardFlow':receipt('keyboard-flow-arm.log'),
 'seedRecoveryFlow':receipt('seed-recovery-display-arm.log'),
 'nativeRebuild':json.loads((DIST/'native-reproducibility.json').read_text()),
 'hostUnitTests':25,
 'installedAppChanged':False,'osImageBuilt':False,'flashed':False,
 'limits':['View dependency initialization injected; full Controller lifecycle untested','Scripted keys; physical button operation unqualified','Seed recovery reviews prefilled public words; not typing all letters','No passphrase, camera/QR, signing or full-app memory qualification'],
 'codeSha256':{str(p.relative_to(HERE)):sha(p) for pattern in ['native/*','python/*.py','tests/*.py','patches/*.patch','*.py','*lock.json','source-guards.json'] for p in HERE.glob(pattern) if p.is_file()},
}
(HERE/'validation/settings-keyboards-seed-recovery-arm.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['binarySha256'])
