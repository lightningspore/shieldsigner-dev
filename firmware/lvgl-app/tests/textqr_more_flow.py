"""Public exact-text encrypted entry contracts and original discard routes."""
import json
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
sys.path[:0]=[str(Path(__file__).resolve().parent),'/usr/lib/shieldsigner-camera/python','/opt/src']
from runtime import Runtime,install_view_dispatch
from seedsigner.gui.screens.seed_screens import SeedAddPassphraseScreen
from seedsigner.models.seed import Seed
from seedsigner.models.seed_storage import SeedStorage
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.views.view import View
class Buttons:
    def load(self,keys):self.keys=keys;self.start=None
    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        t=now-self.start-.5
        if t<0:return set()
        i=int(t/.35)
        if i>=len(self.keys):
            if t>len(self.keys)*.35+5:raise TimeoutError('Passphrase navigation did not finish')
            return set()
        return {self.keys[i]} if t%.35<.22 else set()
buttons=Buttons();rectangles=0;hardware=None
if '--display' in sys.argv:
    from luckfox import LuckfoxHardware
    hardware=LuckfoxHardware()
def pixels(area,data):
    global rectangles
    rectangles+=1
    if hardware is not None:hardware.pixels(area,data)
runtime=Runtime(sys.argv[1],pixels,buttons)
restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
import threading
from seedsigner.views.tools_views import ToolsTextQRFullScreenModeView,ToolsTranscribeTextQRConfirmScanView,ToolsTextQRView
from seedsigner.views.view import BackStackView
from synthetic_frames import Source,blank_source
from diagnostic_scope import attribute
import shieldsigner_native_stream
from shieldsigner_lcd import QrWorker
original_initialize=View._initialize;original_run=runtime.run;checks=[]
frame=bytearray(115200);lock=threading.Lock();original_pixels=runtime.host.pixel_sink
reader=QrWorker('/usr/lib/shieldsigner-camera/shieldsigner-qr-reader',5)
def observe(area,data):
    x1,y1,x2,y2=area;stride=(x2-x1+1)*2
    with lock:
        for row,y in enumerate(range(y1,y2+1)):frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
    original_pixels(area,data)
runtime.host.pixel_sink=observe
with tempfile.TemporaryDirectory(prefix='lvgl-textqr-more-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    def initialize(view):
        view.controller=SimpleNamespace(reset_screensaver_timeout=lambda:None);view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    try:
        for text in ('  public  ','café e\u0301\r\nnext','Public longer text '*30):
            state={'start':None,'decoded':False}
            def decode_pixels():
                if state['start'] is None:state['start']=time.monotonic()
                if state['decoded']:return {'KEY_PRESS'}
                if time.monotonic()-state['start']>20:raise TimeoutError('Text QR pixels did not decode')
                if time.monotonic()-state['start']<1:return set()
                with lock:luma=bytes(frame[0::2])
                value=reader.decode_luma(luma,240,240)
                if value is not None:
                    assert value==text.encode(), 'Rendered Text QR payload mismatch'
                    state['decoded']=True
                return set()
            runtime.read_buttons=decode_pixels
            destination=ToolsTextQRFullScreenModeView(text=text).run()
            assert state['decoded'] and destination.View_cls is ToolsTextQRView and destination.clear_history
            assert not any(frame)
        runtime.read_buttons=buttons
        for mode in ('match','mismatch','cancel'):
            text=' public café\r\n '
            source=blank_source() if mode=='cancel' else Source([(text if mode=='match' else 'different public text').encode()])
            seen=[]
            def run(screen,args):
                seen.append(screen.__name__)
                if screen.__name__=='ScanScreen':buttons.load(['KEY_LEFT'] if mode=='cancel' else [])
                else:buttons.load(['KEY_DOWN']*12+['KEY_PRESS'])
                return original_run(screen,args)
            runtime.run=run
            with attribute(shieldsigner_native_stream,'NativeVideoStream',lambda **kwargs:source):
                destination=ToolsTranscribeTextQRConfirmScanView(text=text).run()
            assert source.is_stopped and runtime.camera_stats['cameraStopped'] and runtime.camera_stats['qr']['lastExitCode']==0
            assert destination.View_cls is (ToolsTextQRView if mode=='match' else BackStackView)
            assert seen==['ScanScreen','LargeIconStatusScreen' if mode=='match' else 'DireWarningScreen'],seen
            checks.append(dict(mode=mode,originalComparison=True,sourceStopped=True,qrWorkerExitCode=0))
        print(json.dumps(dict(passed=True,fullscreenRenderedPayloadsExact=3,blackOnExit=True,confirmationChecks=checks,originalViewsAndDecoder=True,dependencyInitializationInjected=True,physicalDisplay=hardware is not None,physicalButtons=False,syntheticNV12=True,opticalQualified=False)),flush=True)
    finally:
        View._initialize=original_initialize;restore();runtime.close();reader.close()
        if hardware is not None:hardware.close()
