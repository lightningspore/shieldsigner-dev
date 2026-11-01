"""Native presentation around the pinned original entropy acquisition loop."""
from source_text import getsource as adapter_source
from gettext import gettext as _
import textwrap,time
from pathlib import Path
from types import SimpleNamespace
from entropy_source import acquisition_method
NAMES={'ToolsImageEntropyLivePreviewScreen','ToolsImageEntropyFinalImageScreen'}

def wait(runtime,event):
    while True:
        answer=runtime.host.next_event()
        if answer.get('event')=='error':raise RuntimeError('Native entropy display failed')
        if answer.get('event')==event:return

def begin(runtime,instructions):
    runtime.host.send('key',key=runtime.last_key,pressed=False)
    runtime.request+=1;runtime.host.send('scan',instructions=instructions,request=runtime.request)
    wait(runtime,'screen_ready')

def display_image(runtime,image,percent=0):
    from PIL import Image
    # Display copy only. Original frames/pool/final pixels never pass through
    # this resampling path before the original entropy mixer receives them.
    copy=image.convert('RGB');copy.thumbnail((240,180),Image.Resampling.NEAREST)
    canvas=Image.new('RGB',(240,180));canvas.paste(copy,((240-copy.width)//2,(180-copy.height)//2))
    runtime.host.send_preview(240,180,canvas.tobytes(),percent=percent,status=0)
    wait(runtime,'preview_ready')

def run_live(runtime,screen_class):
    from seedsigner.gui.screens import tools_screens as module
    from seedsigner.hardware.buttons import HardwareButtonsConstants as C
    from entropy_camera import create,start
    camera=create();names={getattr(C,name):name for name in ('KEY_LEFT','KEY_RIGHT','KEY_PRESS','KEY1','KEY2','KEY3')}
    def low(keys):
        if runtime.lifecycle_check is not None:runtime.lifecycle_check()
        active=runtime.read_buttons();keys=keys if isinstance(keys,(list,tuple)) else [keys]
        return any(names.get(key) in active for key in keys)
    def activity():
        if runtime.activity_sink is not None:runtime.activity_sink()
    runtime.entropy_stats=dict(previewFrames=0,poolFrames=0)
    state=SimpleNamespace(last=0)
    def preview(frame,entropy,count):
        runtime.entropy_stats.update(previewFrames=runtime.entropy_stats["previewFrames"]+1,poolFrames=count)
        if time.time()-state.last>=1:
            from PIL import Image
            sample=entropy.convert('L').resize((96,96),Image.Resampling.BILINEAR)
            value=module.mnemonic_generation._shannon_entropy(sample.tobytes());state.last=time.time()
            level=0 if value<3.5 else 1 if value<4.5 else 2
            label=_('LOW ENTROPY') if level==0 else _('GOOD ENTROPY') if level==2 else ''
            runtime.host.send('entropy_caption',text=f'{value:.2f} {label}',level=level);wait(runtime,'caption_ready')
        display_image(runtime,frame,int(count*100/screen_class.PREVIEW_POOL_SIZE))
    screen=SimpleNamespace(camera=camera,hw_inputs=SimpleNamespace(check_for_low=low,update_last_input_time=activity),PREVIEW_POOL_SIZE=screen_class.PREVIEW_POOL_SIZE,_lvgl_preview=preview)
    source=textwrap.dedent(adapter_source(screen_class._run));loop=acquisition_method(source,vars(module))
    try:
        begin(runtime,'< '+_('back')+' | '+_('click a button'))
        start(camera)
        return loop(screen)
    finally:
        try:camera.stop_video_stream_mode()
        finally:runtime.clear()

def run_review(runtime,arguments):
    from seedsigner.gui.screens.screen import RET_CODE__BACK_BUTTON
    from seedsigner.hardware.buttons import HardwareButtonsConstants as C
    allowed={'KEY_LEFT','KEY_RIGHT','KEY_PRESS','KEY1','KEY2','KEY3'}
    try:
        begin(runtime,'< '+_('reshoot')+' | '+_('accept')+' >')
        display_image(runtime,arguments['final_image'])
        # Retain the original release-before-review gate and exact accepted keys.
        while True:
            if runtime.lifecycle_check is not None:runtime.lifecycle_check()
            if not(runtime.read_buttons()&allowed):break
            time.sleep(.01)
        while True:
            if runtime.lifecycle_check is not None:runtime.lifecycle_check()
            active=runtime.read_buttons()&allowed
            if active:
                if runtime.activity_sink is not None:runtime.activity_sink()
                return RET_CODE__BACK_BUTTON if 'KEY_LEFT' in active else None
            time.sleep(.01)
    finally:runtime.clear()
