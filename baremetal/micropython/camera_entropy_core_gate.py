# SPDX-License-Identifier: MIT
# PUBLIC synthetic camera bytes/dice only; no sensor access or private logs.
from seedsigner_port.camera_entropy import CameraPool,CameraFrame,derive_camera_entropy_bytes,clear_images
from seedsigner_port.camera_entropy_mnemonic import generate_mnemonic_from_bytes,generate_mnemonic_from_dice,ENTROPY_BYTES_REQUIRED,dice_entropy_is_sufficient
import machine,gc
expected=b'\x13>\x05\xaa\xa1\xcf.\xbc\xf98\xceP\x15\x89\x06!\x12\xe7\x10\xbf\xadZ\x95\x97\xdc\xa4\x8eR\x0fl\xe6\x89'
camera_cases=[(12, ['basket', 'usual', 'height', 'drum', 'very', 'fury', 'top', 'border', 'exotic', 'proof', 'dose', 'dry']), (15, ['basket', 'usual', 'height', 'drum', 'very', 'fury', 'top', 'border', 'exotic', 'proof', 'dose', 'drama', 'common', 'marriage', 'worth']), (18, ['basket', 'usual', 'height', 'drum', 'very', 'fury', 'top', 'border', 'exotic', 'proof', 'dose', 'drama', 'common', 'marriage', 'wrong', 'prize', 'night', 'royal']), (21, ['basket', 'usual', 'height', 'drum', 'very', 'fury', 'top', 'border', 'exotic', 'proof', 'dose', 'drama', 'common', 'marriage', 'wrong', 'prize', 'night', 'same', 'circle', 'bronze', 'census']), (24, ['basket', 'usual', 'height', 'drum', 'very', 'fury', 'top', 'border', 'exotic', 'proof', 'dose', 'drama', 'common', 'marriage', 'wrong', 'prize', 'night', 'same', 'circle', 'bronze', 'can', 'reopen', 'olive', 'derive'])]
dice_cases=[(12, '12345612345612345612345612345612345612345612345612', ['unveil', 'nice', 'picture', 'region', 'tragic', 'fault', 'cream', 'strike', 'tourist', 'control', 'recipe', 'tourist']), (15, '12345612345612345612345612345612345612345612345612345612345612', ['end', 'spider', 'topple', 'cliff', 'tomorrow', 'process', 'dismiss', 'produce', 'athlete', 'film', 'monster', 'team', 'vacant', 'ill', 'silk']), (18, '123456123456123456123456123456123456123456123456123456123456123456123456123', ['melt', 'churn', 'alley', 'retreat', 'flip', 'once', 'enough', 'gather', 'project', 'prosper', 'cannon', 'nasty', 'furnace', 'isolate', 'cost', 'laundry', 'lottery', 'slice']), (21, '123456123456123456123456123456123456123456123456123456123456123456123456123456123456123', ['start', 'insane', 'amazing', 'fall', 'kite', 'punch', 'owner', 'refuse', 'bone', 'trigger', 'spirit', 'luggage', 'slide', 'sound', 'reopen', 'broom', 'remember', 'nose', 'limb', 'swallow', 'kitten']), (24, '123456123456123456123456123456123456123456123456123456123456123456123456123456123456123456123456123', ['few', 'educate', 'sugar', 'bless', 'boring', 'random', 'strategy', 'waste', 'mutual', 'cargo', 'type', 'hawk', 'prefer', 'denial', 'scan', 'abstract', 'filter', 'extend', 'dignity', 'balcony', 'dust', 'unusual', 'correct', 'bubble'])]
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
