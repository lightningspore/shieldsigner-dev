# SPDX-License-Identifier: MIT
import camera
import display
import time
import gc
from seedsigner_port.native_ui import ScreenSession
s=ScreenSession()
s.show('main_menu_screen',{'top_nav':{'title':'Home'},'button_list':['Scan','Seeds','Tools','Settings']})
camera.init()
baseline=camera.settings()['rust_heap_bytes']
started=time.ticks_ms()
frames=0
hashes=[]
try:
    camera.start_preview()
    for op in (camera.init,camera.capture,camera.start_preview):
        try:op()
        except OSError:pass
        else:raise AssertionError('conflicting camera operation accepted')
    try:camera.settings(ae_target=48)
    except ValueError:pass
    else:raise AssertionError('midstream settings accepted')
    print('@@LCD_PREVIEW_START_MS',(time.ticks_ms()-started)&0xffffffff)
    started=time.ticks_ms()
    for i in range(90):
        before=time.ticks_ms()
        frame=camera.next_preview()
        acquired=time.ticks_ms()
        display.blit_nv12(frame)
        h=0
        for j in range(0,len(frame),997):h=(h*33+frame[j])&0x3fffffff
        hashes.append(h)
        frames+=1
        if i%10==0:print('@@LCD_PREVIEW_FRAME',i,(acquired-before)&0xffffffff,(time.ticks_ms()-acquired)&0xffffffff,h)
    elapsed=(time.ticks_ms()-started)&0xffffffff
    assert len(set(hashes))>1
    print('@@LCD_PREVIEW_RATE',frames,elapsed,frames*1000/elapsed)
finally:
    camera.stop_preview()
    gc.collect()
    s.show('main_menu_screen',{'top_nav':{'title':'Home'},'button_list':['Scan','Seeds','Tools','Settings']})
assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS lcd-continuous-preview')
