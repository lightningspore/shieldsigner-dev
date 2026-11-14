# SPDX-License-Identifier: MIT
"""Foreground preview. Frame views expire at the next camera fetch or stop."""
import time

def run(duration_ms=60000):
    import camera
    import display
    from seedsigner_port.buttons import ButtonInput
    from seedsigner_port.native_ui import ScreenSession
    screen=ScreenSession()
    buttons=ButtonInput()
    camera.init()
    frames=0
    started=time.ticks_ms()
    try:
        camera.start_preview()
        ready=time.ticks_ms()
        while ((time.ticks_ms()-ready)&0xffffffff)<duration_ms:
            frame=camera.next_preview()
            display.blit_nv12(frame)
            frames+=1
            # Poll during a short service interval so ordinary presses debounce.
            for _ in range(3):
                if buttons.poll(('KEY_PRESS','KEY3')) is not None:
                    return frames,((time.ticks_ms()-ready)&0xffffffff)
                time.sleep_ms(5)
        return frames,((time.ticks_ms()-ready)&0xffffffff)
    finally:
        camera.stop_preview()
        screen.show('main_menu_screen',{'top_nav':{'title':'Home'},'button_list':['Scan','Seeds','Tools','Settings']})
