"""Original xpub review and static export; public fixture, injected dependencies."""
import json
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
from runtime import Runtime,install_view_dispatch
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.models.seed import Seed
import threading
sys.path.insert(0,'/usr/lib/shieldsigner-camera/python')
from shieldsigner_lcd import QrWorker
from seedsigner.views.view import View
class Buttons:
    def load(self,keys):
        self.keys=keys;self.start=None
        if hasattr(self,'expected'):del self.expected
    def capture(self,expected):
        self.expected=expected;self.capture_start=time.monotonic();self.last=0;self.decoded=False
    def __call__(self):
        now=time.monotonic()
        if hasattr(self,'expected'):
            if self.decoded:return {'KEY_PRESS'}
            if now-self.capture_start>20:raise TimeoutError('Xpub QR did not decode')
            if now-self.last<.12:return set()
            self.last=now
            with frame_lock:luma=bytes(frame[0::2])
            data=reader.decode_luma(luma,240,240)
            if data is not None:
                assert data==self.expected,'Rendered xpub differs from original encoder'
                self.decoded=True
            return set()
        if self.start is None:self.start=now
        elapsed=now-self.start-.15
        if elapsed<0:return set()
        i=int(elapsed/.2)
        if i>=len(self.keys):
            if elapsed>len(self.keys)*.2+5:raise TimeoutError('Xpub navigation did not finish')
            return set()
        return {self.keys[i]} if elapsed%.2<.1 else set()
buttons=Buttons();rectangles=0
frame=bytearray(115200);frame_lock=threading.Lock()
reader=QrWorker('/usr/lib/shieldsigner-camera/shieldsigner-qr-reader',5)
hardware=None
if '--display' in sys.argv:
    from luckfox import LuckfoxHardware
    hardware=LuckfoxHardware()
def pixels(area,data):
    global rectangles
    rectangles+=1
    x1,y1,x2,y2=area;stride=(x2-x1+1)*2
    with frame_lock:
        for row,y in enumerate(range(y1,y2+1)):frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
    if hardware is not None:hardware.pixels(area,data)
runtime=Runtime(sys.argv[1],pixels,buttons)
restore=install_view_dispatch(runtime,sys.argv[2],Path(__file__).parent/'source-guards.json')
original_initialize=View._initialize
seed=Seed(['abandon']*11+['about'])
controller=SimpleNamespace()
with tempfile.TemporaryDirectory(prefix='lvgl-xpub-test-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json')
    settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__NETWORK,C.MAINNET,save=False)
    settings.set_value(C.SETTING__XPUB_DETAILS,C.OPTION__ENABLED,save=False)
    def initialize(view):
        view.controller=controller;view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None
    View._initialize=initialize
    try:
        from seedsigner.views.seed_views import SeedExportXpubDetailsView,SeedExportXpubQRDisplayView,SeedExportXpubVerifyAddressView
        from seedsigner.views.view import BackStackView
        cases=[]
        for account in (0,7):
            for cancel in (True,False):
                buttons.load(['KEY_UP']*6+['KEY_PRESS'] if cancel else ['KEY_PRESS'])
                view=SeedExportXpubDetailsView(seed=seed,sig_type=C.SINGLE_SIG,script_type=C.NATIVE_SEGWIT,xpub_qr_format=C.XPUB_QR_FORMAT__STATIC,custom_derivation=None,account=account)
                destination=view.run()
                if cancel:assert destination.View_cls is BackStackView
                else:
                    assert destination.View_cls is SeedExportXpubQRDisplayView
                    assert destination.view_args['derivation_path']==f"m/84'/0'/{account}'",destination.view_args
                    export=destination.View_cls(**destination.view_args)
                    expected=export.qr_encoder.next_part().encode('utf-8')
                    assert expected.startswith(f"[73c5da0a/84'/0'/{account}']".encode())
                    buttons.capture(expected)
                    destination=export.run()
                    assert destination.View_cls is SeedExportXpubVerifyAddressView
                    assert buttons.decoded
                cases.append(dict(account=account,cancel=cancel,staticQRBytesExact=not cancel))
        assert not Path(Settings.SETTINGS_FILENAME).exists()
        print(json.dumps(dict(passed=True,cases=cases,originalViewAndDerivation=True,physicalDisplay=hardware is not None,physicalButtons=False,persistentSettingsWritten=False)))
    finally:
        seed.wipe();View._initialize=original_initialize;restore();runtime.close();reader.close()
        if hardware is not None:hardware.close()
