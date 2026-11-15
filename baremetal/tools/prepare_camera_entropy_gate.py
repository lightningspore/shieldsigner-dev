# SPDX-License-Identifier: MIT
"""Independent PUBLIC Pillow/CPython embit oracle for native camera/dice helpers."""
import hashlib,json,importlib.metadata
from pathlib import Path
from PIL import Image
from embit import bip39
root=Path(__file__).resolve().parents[1]
def frame(phase):
    y=bytes((i+phase)%256 for i in range(256))*1200
    return y+bytes([128])*153600
def reference_sample(data):
    image=Image.frombytes('L',(640,480),data[:307200])
    # Exact rational centers avoid Pillow resize's floating-point tie rounding.
    return bytes(image.getpixel((int((x+0.5)*640/96),int((y+0.5)*480/96))) for y in range(96) for x in range(96))
samples=[reference_sample(frame(phase)) for phase in range(1,6)]
chain=b''
for data in samples:chain=hashlib.sha256(chain+data).digest()
digest=hashlib.sha256(chain+frame(8)).digest()
lengths={12:16,15:20,18:24,21:28,24:32}
camera=[(words,bip39.mnemonic_from_bytes(digest[:size]).split()) for words,size in lengths.items()]
dice=[]
for words,rolls in ((12,50),(15,62),(18,75),(21,87),(24,99)):
    value=('123456'*20)[:rolls]
    dice.append((words,value,bip39.mnemonic_from_bytes(hashlib.sha256(value.encode()).digest()[:lengths[words]]).split()))
code='''# SPDX-License-Identifier: MIT
# PUBLIC synthetic camera bytes/dice only; no sensor access or private logs.
from seedsigner_port.camera_entropy import CameraPool,CameraFrame,derive_camera_entropy_bytes,clear_images
from seedsigner_port.camera_entropy_mnemonic import generate_mnemonic_from_bytes,generate_mnemonic_from_dice,ENTROPY_BYTES_REQUIRED,dice_entropy_is_sufficient
import machine,gc
expected='''+repr(digest)+'''
camera_cases='''+repr(camera)+'''
dice_cases='''+repr(dice)+'''
def frame(phase):return bytes((i+phase)%256 for i in range(256))*1200+bytes([128])*153600
pool=CameraPool()
for phase in range(1,6):assert pool.add(frame(phase))
assert pool.ready and not pool.add(frame(1))
samples=pool.transfer();final=CameraFrame(frame(8))
digest=derive_camera_entropy_bytes(samples,final)
assert digest==expected
for count,words in camera_cases:
    actual=generate_mnemonic_from_bytes(digest[:ENTROPY_BYTES_REQUIRED[count]])
    assert actual==words
    print('@@PASS public-camera-mnemonic-helper',count)
for count,rolls,words in dice_cases:
    assert dice_entropy_is_sufficient(rolls)
    assert generate_mnemonic_from_dice(rolls)==words
    assert not dice_entropy_is_sufficient('1'*len(rolls))
    print('@@PASS public-manual-dice-mnemonic-helper',count)
clear_images(samples,final)
assert final.closed and not any(final.data)
assert all(sample.closed and not any(sample.data) for sample in samples)
assert machine.last_reset() is None
print('@@PASS public-camera-entropy-owned-input-clear')
gc.collect()
'''
p=root/'micropython/camera_entropy_core_gate.py';p.write_text(code)
(root/'app/camera-entropy-public-oracle.json').write_text(json.dumps({'provider':'CPython hashlib + embit0.8.0 + Pillow grayscale pixels at exact rational centers','pillowVersion':importlib.metadata.version('pillow'),'gateSha256':hashlib.sha256(code.encode()).hexdigest(),'cameraCases':len(camera),'diceCases':len(dice),'scope':'Deterministic public synthetic NV12/ASCII rolls; no physical entropy/security qualification.'},indent=2)+'\n')
print('Prepared5camera and5manual-dice public mnemonic cases')
