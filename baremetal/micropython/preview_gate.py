# SPDX-License-Identifier: MIT
import camera
import time
import gc
camera.init()
gc.collect()
baseline=camera.settings()['rust_heap_bytes']
start=time.ticks_ms()
frame=None

try:
    camera.start_preview()
    print('@@PREVIEW_START_MS',((time.ticks_ms()-start)&0xffffffff))
    hashes=[]
    for i in range(12):
        start=time.ticks_ms()
        frame=camera.next_preview()
        h=0
        for j in range(0,len(frame),997):h=(h*33+frame[j])&0x3fffffff
        hashes.append(h)
        print('@@PREVIEW_FRAME',i,((time.ticks_ms()-start)&0xffffffff),h,camera.settings())
    assert len(set(hashes))>1
    assert camera.preview_status()==(True,12)
finally:
    camera.stop_preview()
    del frame
    gc.collect()
assert camera.preview_status()==(False,0)
assert camera.settings()['rust_heap_bytes']==baseline
# Legacy bounded capture remains usable after the streaming session.
frame=camera.capture()
assert len(frame)==460800
assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS persistent-camera-preview')
