"""Public corpus transaction: original approval View, cancellation and real signing."""
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
import threading
sys.path.insert(0,"/usr/lib/shieldsigner-camera/python")
from shieldsigner_lcd import QrWorker
from seedsigner.models.decode_qr import DecodeQR
from seedsigner.views.view import View
class Buttons:
    def load(self,keys):self.keys=keys;self.start=None
    def capture(self):
        self.decoder=DecodeQR();self.capture_start=time.monotonic();self.capture_last=0;self.captured=0
    def __call__(self):
        now=time.monotonic()
        if hasattr(self,'decoder'):
            if self.decoder.is_complete:return {'KEY_PRESS'}
            if now-self.capture_start>30:raise TimeoutError('Signed QR export did not decode')
            if now-self.capture_last<.12:return set()
            self.capture_last=now
            with frame_lock:luma=bytes(frame[0::2])
            data=reader.decode_luma(luma,240,240)
            if data is not None:self.decoder.add_data(data);self.captured+=1
            return set()
        if self.start is None:self.start=now
        elapsed=now-self.start-.15
        if elapsed<0:return set()
        i=int(elapsed/.2)
        if i>=len(self.keys):
            if elapsed>len(self.keys)*.2+5:raise TimeoutError('Transaction navigation did not finish')
            return set()
        return {self.keys[i]} if elapsed%.2<.1 else set()
buttons=Buttons();rectangles=0
frame=bytearray(115200);frame_lock=threading.Lock()
reader=QrWorker("/usr/lib/shieldsigner-camera/shieldsigner-qr-reader",5)
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
from base64 import b64decode
from embit.psbt import PSBT
from embit.finalizer import finalize_psbt
from seedsigner.models.seed import Seed
from seedsigner.models.psbt_parser import PSBTParser
from seedsigner.views.psbt_views import PSBTFinalizeView,PSBTSignedQRDisplayView,PSBTMathView,PSBTAddressDetailsView,PSBTChangeDetailsView
from seedsigner.views.view import MainMenuView
from seedsigner.views.view import BackStackView
seed=Seed(['abandon']*11+['about'])
raw=Path(sys.argv[3]).read_bytes()
psbt=PSBT.parse(raw if raw.startswith(b'psbt\xff') else b64decode(raw))
with tempfile.TemporaryDirectory(prefix='lvgl-sign-test-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json')
    settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__NETWORK,C.MAINNET,save=False)
    parser=PSBTParser(psbt,seed,network=C.MAINNET)
    controller=SimpleNamespace(psbt=psbt,psbt_parser=parser,psbt_seed=seed,psbt_sign_with_satochip=False)
    def initialize(view):
        view.controller=controller;view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None
    View._initialize=initialize
    try:
        before=psbt.serialize()
        assert PSBTParser.sig_count(psbt)==0
        buttons.load(['KEY_UP']*6+['KEY_PRESS'])
        destination=PSBTFinalizeView().run()
        assert destination.View_cls is BackStackView
        assert psbt.serialize()==before,'Back changed transaction or signatures'
        destination=None
        reviewed=[]
        for expected in (PSBTMathView,PSBTAddressDetailsView,PSBTChangeDetailsView):
            buttons.load(['KEY_PRESS'])
            view=expected() if destination is None else destination.View_cls(**destination.view_args)
            assert type(view) is expected
            destination=view.run();reviewed.append(expected.__name__)
        assert destination.View_cls is PSBTFinalizeView
        buttons.load(['KEY_DOWN']*4+['KEY_PRESS'])
        destination=PSBTFinalizeView().run()
        assert destination.View_cls is PSBTSignedQRDisplayView
        count=PSBTParser.sig_count(controller.psbt)
        assert count>0
        # Original View deliberately trims UTXO metadata for QR export.
        # Finalize the signed pre-trim model, not that metadata-free export.
        assert PSBTParser.sig_count(psbt)==count
        assert [i.partial_sigs for i in controller.psbt.inputs]==[i.partial_sigs for i in psbt.inputs]
        tx=finalize_psbt(psbt)
        assert tx is not None,'Signed transaction did not finalize'
        assert [o.serialize() for o in tx.vout]==[o.serialize() for o in psbt.tx.vout],'Signing changed outputs'
        exported=controller.psbt.serialize()
        buttons.capture()
        destination=PSBTSignedQRDisplayView().run()
        assert destination.View_cls is MainMenuView and destination.clear_history
        assert buttons.decoder.get_data_psbt()==exported,'Rendered signed QR export changed bytes'
        assert not Path(Settings.SETTINGS_FILENAME).exists()
        print(json.dumps(dict(passed=True,fixture='NORMAL-1_p2wpkh',backPreservedExactBytes=True,signatures=count,finalizable=True,originalFinalizeView=True,originalParserAndCrypto=True,nativeLoading=True,reviewedViews=reviewed,signedQRBytesExact=True,capturedQRFrames=buttons.captured,opticalQualified=False,physicalDisplay=hardware is not None,physicalButtons=False,persistentSettingsWritten=False)))
    finally:
        seed.wipe();View._initialize=original_initialize;restore();runtime.close();reader.close()
        if hardware is not None:hardware.close()
