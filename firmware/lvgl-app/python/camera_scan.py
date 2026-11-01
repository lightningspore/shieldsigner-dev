"""LVGL ScanScreen adapter using installed managed Rust camera and native ZXing.

The decoder receives the same full-resolution binary QR result as add_image().
Preview uses the existing native luma resize/rotation; no wallet/entropy policy.
"""
from gettext import gettext as _
import json
import os
from pathlib import Path
import queue
import time

def run_scan(runtime,arguments):
    from shieldsigner_native_stream import NativeVideoStream
    from shieldsigner_lcd import PreviewRenderer
    from shieldsigner_qr_decoder import RustTransportQrReader
    from seedsigner.models.decode_qr import DecodeQRStatus
    from seedsigner.models.settings import Settings,SettingsConstants
    decoder=arguments.get('decoder')
    if decoder is None:raise ValueError('ScanScreen needs its original decoder')
    if arguments.get('render_rect') not in (None,(0,0,240,240)):raise NotImplementedError('Non-fullscreen Scan render rectangle')
    config=json.loads(Path(os.environ.get('SHIELDSIGNER_CAMERA_CONFIG','/usr/lib/shieldsigner-camera/owner.json')).read_text())
    runtime.request+=1
    runtime.host.send('key',key=runtime.last_key,pressed=False)
    runtime.host.send('scan',instructions='< '+_('back')+'  |  '+_(arguments.get('instructions_text') or ''),request=runtime.request)
    while True:
        event=runtime.host.next_event()
        if event.get('event')=='error':raise RuntimeError('LVGL scan initialization failed')
        if event.get('event')=='screen_ready' and event['request']==runtime.request:break
    runtime.reset_input()
    stream=None;reader=None
    frames=0;decoded=0
    timings={name:0.0 for name in ('frameRead','previewRender','qrDecode','previewSend','previewAck')}
    completed_frames=0;first_complete=None;last_complete=None
    def wait_for(kind,cleanup=False):
        cancelled=False;end=time.monotonic()+runtime.host.timeout
        while time.monotonic()<end:
            if not cleanup:runtime.poll_input()
            try:event=runtime.host.events.get(timeout=.01)
            except queue.Empty:
                if runtime.host.error:raise RuntimeError('LVGL preview failed') from runtime.host.error
                continue
            if event.get('event')=='error':raise RuntimeError('LVGL preview rejected')
            if event.get('event')=='button_selected' and event.get('index')==1000:cancelled=True
            if event.get('event')==kind:return cancelled
        raise TimeoutError('LVGL preview acknowledgement expired')
    def cancelled():
        runtime.poll_input()
        while True:
            try:event=runtime.host.events.get_nowait()
            except queue.Empty:return False
            if event.get('event')=='error':raise RuntimeError('LVGL scan failed')
            if event.get('event')=='button_selected' and event.get('index')==1000:return True
    try:
        reader=RustTransportQrReader(os.environ.get('SHIELDSIGNER_QR_READER','/usr/lib/shieldsigner-camera/shieldsigner-qr-reader'))
        stream=NativeVideoStream(owner_config=config,transport='nv12',consumer_framerate=arguments.get('framerate',6))
        stream.start()
        renderer=PreviewRenderer(240,180)
        rotation=(90+int(Settings.get_instance().get_value(SettingsConstants.SETTING__CAMERA_ROTATION)))%360
        while True:
            if cancelled():return False
            began=time.perf_counter();frame=stream.read();timings['frameRead']+=time.perf_counter()-began
            if frame is None:continue
            if cancelled():return False
            began=time.perf_counter();width,height,rgb=renderer.render_frame(frame,rotation);timings['previewRender']+=time.perf_counter()-began
            began=time.perf_counter();payload=reader.decode(frame);timings['qrDecode']+=time.perf_counter()-began
            status=DecodeQRStatus.FALSE if payload is None else decoder.add_data(payload)
            frames+=1;decoded+=int(payload is not None)
            progress=decoder.get_percent_complete(weight_mixed_frames=True)
            indicator=1 if status==DecodeQRStatus.PART_COMPLETE else 2 if status==DecodeQRStatus.PART_EXISTING else 3
            began=time.perf_counter();runtime.host.send_preview(width,height,rgb,percent=int(progress),status=indicator);timings['previewSend']+=time.perf_counter()-began
            began=time.perf_counter();back=wait_for('preview_ready');timings['previewAck']+=time.perf_counter()-began
            last_complete=time.perf_counter();completed_frames+=1
            if first_complete is None:first_complete=last_complete
            if status in (DecodeQRStatus.COMPLETE,DecodeQRStatus.INVALID):return None
            if back:return False
    finally:
        try:
            if reader is not None:reader.close()
        finally:
            try:
                if stream is not None:stream.stop()
            finally:
                runtime.camera_stats={'frames':frames,'decodedFrames':decoded,'cameraStopped':stream is None or stream.is_stopped,'ownerExitCode':None if stream is None else stream.owner_exit_code,'qr':{} if reader is None else dict(reader.stats)}
                interval=None if first_complete is None else last_complete-first_complete
                runtime.camera_stats.update(completedPreviewFrames=completed_frames,processedFrameIntervalSeconds=interval,processedFramesPerSecond=(completed_frames-1)/interval if interval and completed_frames>1 else None,stageSeconds=timings)
                runtime.host.send('scan_stop')
                wait_for('scan_stopped',cleanup=True)
