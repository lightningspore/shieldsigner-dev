"""Original QR encoder -> upstream LVGL QR screen, without Pillow rendering."""
from gettext import gettext as _
import queue
import time

def part_bytes(part):
    if isinstance(part,str):return part.encode('utf-8')
    if isinstance(part,(bytes,bytearray)):return bytes(part)
    raise TypeError('QR encoder must return text or bytes')

def run_qr_output(runtime,arguments):
    from seedsigner.models.settings import Settings,SettingsConstants as C
    encoder=arguments.get('qr_encoder')
    if encoder is None:raise ValueError('QRDisplayScreen needs its original encoder')
    settings=Settings.get_instance()
    brightness=settings.get_value(C.SETTING__QR_BRIGHTNESS)
    first=encoder.next_part()
    binary=isinstance(first,(bytes,bytearray))
    cfg=dict(qr_data=bytes(first).hex() if binary else first,qr_mode='byte' if binary else 'auto',data_encoding='hex' if binary else 'utf8',border=2,initial_brightness=brightness,show_brightness_tips=settings.get_value(C.SETTING__QR_BRIGHTNESS_TIPS)==C.OPTION__ENABLED,brighter_text=_('Brighter'),darker_text=_('Darker'),density_control=False,allow_screensaver=False)
    animated=encoder.seq_len()>1
    runtime.request+=1
    runtime.host.send('key',key=runtime.last_key,pressed=False)
    runtime.host.send('screen',name='qr_display_screen',config=cfg,request=runtime.request)
    while True:
        event=runtime.host.next_event()
        if event.get('event')=='error':raise RuntimeError('Native QR configuration failed')
        if event.get('event')=='screen_ready' and event['request']==runtime.request:break
    runtime.reset_input()
    frames=1;tip_was_active=False;exit_event=None
    def read_event(event):
        nonlocal brightness,exit_event
        if event.get('event')=='error':raise RuntimeError('Native QR display failed')
        if event.get('event')=='qr_brightness':brightness=event['value']
        if event.get('event')=='button_selected':exit_event=event
    def until(kind,cleanup=False):
        deadline=time.monotonic()+runtime.host.timeout
        while time.monotonic()<deadline:
            if not cleanup:runtime.poll_input()
            try:event=runtime.host.events.get(timeout=.01)
            except queue.Empty:
                if runtime.host.error:raise RuntimeError('LVGL QR host failed') from runtime.host.error
                continue
            read_event(event)
            if event.get('event')==kind:return event
        raise TimeoutError('LVGL QR acknowledgement expired')
    try:
        next_frame=time.monotonic()+1/6
        while exit_event is None:
            runtime.poll_input()
            while True:
                try:read_event(runtime.host.events.get_nowait())
                except queue.Empty:break
            if exit_event is not None:break
            now=time.monotonic()
            if animated and now>=next_frame:
                next_frame=now+1/6
                runtime.host.send('qr_state');state=until('qr_state')
                if exit_event is not None:break
                tip_active=state['tip_active']
                if tip_was_active and not tip_active:encoder.restart()
                if not tip_active:
                    data=part_bytes(encoder.next_part())
                    runtime.host.send('qr_frame',hex=data.hex());until('qr_frame_ready');frames+=1
                tip_was_active=tip_active
            time.sleep(.01)
        # Preserve original persistence timing: save brightness once when exiting.
        settings.set_value(C.SETTING__QR_BRIGHTNESS,brightness)
        return 1000 if arguments.get('cancel_on_back',False) and exit_event.get('exit_key')==20 else None
    finally:
        runtime.qr_output_stats=dict(frames=frames,animated=animated,brightness=brightness,exited=exit_event is not None)
        runtime.host.send('clear');until('screen_cleared',cleanup=True)
