"""Record passphrase-stage evidence without rewriting previous checkpoints."""
from pathlib import Path
import hashlib
import json
import subprocess
HERE=Path(__file__).resolve().parent
from artifact_paths import DIST
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read_receipt(name):
    data=[json.loads(line) for line in (DIST/name).read_text().splitlines() if line.startswith('{')]
    if len(data)!=1 or data[0].get('passed') is not True:raise ValueError('Receipt failed: '+name)
    return data[0]
binary=DIST/'build/shieldsigner-lvgl'
board_digest=subprocess.check_output(['adb','shell','sha256sum /tmp/shieldsigner-lvgl-host'],text=True).split()[0]
if board_digest!=sha(binary):raise ValueError('Board binary differs from tested host')
report=dict(checkpoint='2026-10-30-passphrase',scope='Public fixtures, original Views/models with injected dependency initialization, actual LCD and scripted keys; full app integration still incomplete',sources=json.loads((HERE/'sources.lock.json').read_text()),binarySha256=board_digest,binaryBytes=binary.stat().st_size,passphraseFlow=read_receipt('passphrase-flow-display-arm.log'),nativeCorpus=read_receipt('native-smoke-passphrase-arm.json'),hostUnitTests=30,installedAppChanged=False,osImageBuilt=False,flashed=False,limits=['Physical-button operation not qualified','Controller lifecycle and inactivity wipe not integrated','Embedded NUL in passphrase editing explicitly rejected','Camera/QR and signing integration still pending'],codeSha256={str(path.relative_to(HERE)):sha(path) for pattern in ['native/*','python/*.py','tests/*.py','patches/*.patch','*.py','*lock.json','source-guards.json'] for path in HERE.glob(pattern) if path.is_file()})
(HERE/'validation/passphrase-arm.json').write_text(json.dumps(report,indent=2)+'\n')
print(board_digest)
