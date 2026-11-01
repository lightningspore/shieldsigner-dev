"""Pinned I/O screen chrome and original camera-profile retry loop."""
from source_text import getsource as adapter_source
import ast,copy,queue,textwrap,time
from gettext import gettext as _
class CaptureInterrupted(BaseException):
    def __init__(self,error):self.error=error

def compile_capture(source,namespace):
    tree=ast.parse(textwrap.dedent(source))
    candidates=[node for node in ast.walk(tree) if isinstance(node,ast.Try) and node.body and isinstance(node.body[0],ast.Assign) and ast.unparse(node.body[0].targets[0])=='capture_profiles']
    if len(candidates)!=1:raise ValueError('Unexpected I/O camera-profile structure')
    body=candidates[0].body
    assigns=[node for node in body if isinstance(node,ast.Assign) and ast.unparse(node.targets[0])=='background_frame']
    loops=[node for node in body if isinstance(node,ast.For) and ast.unparse(node.target)=='profile' and ast.unparse(node.iter)=='capture_profiles']
    if len(assigns)!=1 or len(loops)!=1 or not isinstance(assigns[0].value,ast.Constant) or assigns[0].value.value is not None:raise ValueError('Unexpected I/O capture loop')
    stub=ast.parse('def capture(camera): pass')
    stub.body[0].body=copy.deepcopy([body[0],assigns[0],loops[0]])+[ast.Return(value=ast.Name(id='background_frame',ctx=ast.Load()))]
    local={};exec(compile(ast.fix_missing_locations(stub),'<original I/O capture profiles>','exec'),namespace,local)
    return local['capture']

def check(runtime):
    if runtime.lifecycle_check is None:return
    from lifecycle import WipeInterrupted
    try:runtime.lifecycle_check()
    except WipeInterrupted as error:raise CaptureInterrupted(error)

def wait(runtime,event):
    while True:
        check(runtime);value=runtime.host.next_event()
        if value.get('event')=='error':raise RuntimeError('Native I/O request rejected')
        if value.get('event')==event:return

def state(runtime,value):
    runtime.host.send('io_state',state=value);wait(runtime,'io_state_ready')

def rgb565(frame):
    from PIL import Image,ImageOps
    image=ImageOps.fit(ImageOps.autocontrast(frame,cutoff=2).convert('RGB'),(240,240),method=Image.Resampling.BICUBIC)
    rgb=image.tobytes();result=bytearray(240*240*2)
    for offset in range(240*240):
        index=offset*3;word=((rgb[index]>>3)<<11)|((rgb[index+1]>>2)<<5)|(rgb[index+2]>>3)
        result[offset*2]=word&255;result[offset*2+1]=word>>8
    return bytes(result)

def run(runtime,screen_class,arguments):
    from seedsigner.gui.screens import settings_screens
    from entropy_camera import create,start
    capture=compile_capture(adapter_source(screen_class._run),vars(settings_screens));camera=None;have_still=False
    runtime.io_stats=dict(captures=0,clears=0,profiles=0,failures=0,exited=False)
    class Camera:
        def start_video_stream_mode(self,**kwargs):check(runtime);runtime.io_stats['profiles']+=1;return start(camera,**kwargs)
        def read_video_stream(self,**kwargs):check(runtime);return camera.read_video_stream(**kwargs)
        def stop_video_stream_mode(self):return camera.stop_video_stream_mode()
    runtime.request+=1;runtime.host.send('key',key=runtime.last_key,pressed=False)
    runtime.host.send('screen',name='io_test_screen',request=runtime.request,config=dict(top_nav=dict(title=_('I/O Test'),show_back_button=False,show_power_button=False),capturing_text=_('Capturing image...'),clear_label=_('Clear'),exit_label=_('Exit'),allow_screensaver=runtime.view_allows_screensaver))
    try:
        wait(runtime,'screen_ready');runtime.reset_input()
        while True:
            runtime.poll_input()
            try:event=runtime.host.events.get_nowait()
            except queue.Empty:time.sleep(.01);continue
            if event.get('event')=='error':raise RuntimeError('Native I/O screen failed')
            if event.get('event')!='aux_key':continue
            key=event['key'];runtime.host.send('key',key=runtime.last_key,pressed=False)
            if key=='KEY3':runtime.io_stats['exited']=True;return None
            if key=='KEY2':state(runtime,0);have_still=False;runtime.io_stats['clears']+=1;continue
            if key!='KEY1':continue
            state(runtime,1)
            if camera is None:camera=create()
            frame=None
            try:frame=capture(Camera())
            except Exception as error:settings_screens.logger.warning("I/O test camera capture failed: %s",error)
            if frame is None:
                runtime.io_stats['failures']+=1
                state(runtime,2 if have_still else 0);continue
            try:pixels=rgb565(frame)
            except Exception as error:
                settings_screens.logger.warning("I/O test camera capture failed: %s",error)
                runtime.io_stats['failures']+=1;state(runtime,2 if have_still else 0);continue
            finally:frame=None
            runtime.host.send('io_frame',hex=pixels.hex());pixels=None;wait(runtime,'io_frame_ready')
            have_still=True;runtime.io_stats['captures']+=1
    except CaptureInterrupted as error:raise error.error
    finally:
        try:
            if camera is not None and getattr(camera,'_video_stream',None) is not None:camera.stop_video_stream_mode()
        finally:runtime.clear()
