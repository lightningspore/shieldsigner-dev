"""Public LCD review and original AES-ECB crypto round trip; no optical scan."""
import json
import sys
import tempfile
import time
import threading
from pathlib import Path
from types import SimpleNamespace
sys.path[:0]=[str(Path(__file__).resolve().parent),'/usr/lib/shieldsigner-camera/python','/opt/src']
from runtime import Runtime,install_view_dispatch
from seedsigner.models.seed import Seed
from seedsigner.models.seed_storage import SeedStorage
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.views.view import View
class Buttons:
    def load(self,keys):self.keys=keys;self.start=None;self.capture_qr=False
    def capture(self,expected):
        self.expected=expected;self.start=None;self.capture_qr=True;self.decoded=None;self.last=0

    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        if self.capture_qr:
            elapsed=now-self.start
            if self.decoded is not None:return {'KEY_PRESS'}
            if elapsed>20:raise TimeoutError('Encrypted QR pixels did not decode')
            if elapsed<1.5 or now-self.last<.2:return set()
            self.last=now
            with frame_lock:luma=bytes(frame[0::2])
            value=reader.decode_luma(luma,240,240)
            if value is not None:
                assert value==self.expected
                self.decoded=value
            return set()
        t=now-self.start-.15
        if t<0:return set()
        i=int(t/.2)
        if i>=len(self.keys):
            if t>len(self.keys)*.2+5:raise TimeoutError('Passphrase navigation did not finish')
            return set()
        return {self.keys[i]} if t%.2<.1 else set()
buttons=Buttons();rectangles=0;hardware=None
frame=bytearray(115200);frame_lock=threading.Lock()
from shieldsigner_lcd import QrWorker
reader=QrWorker('/usr/lib/shieldsigner-camera/shieldsigner-qr-reader',5)
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
restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
from seedsigner.gui.screens.scan_screens import ScanTypeEncryptionKeyScreen,ScanReviewEncryptionKeyScreen
from seedsigner.gui.screens.seed_screens import SeedEncryptedQRMnemonicIDScreen,SeedEncryptedQRReviewMnemonicIDScreen
from seedsigner.views.seed_views import SeedEncryptedQRTypeEncryptionKeyView,SeedEncryptedQRTypeEncryptionKeyExitDialogView,SeedEncryptedQRReviewEncryptionKeyView,SeedEncryptedQRMnemonicIDEntryView,SeedEncryptedQRMnemonicIDEntryExitDialogView,SeedEncryptedQRReviewMnemonicIDView
from seedsigner.views.view import BackStackView
from seedsigner.controller import Controller
from seedsigner.models.encryptedqr import EncryptedQRStorage
from seedsigner.views.seed_views import SeedEncryptedQRMnemonicIDPromptView,SeedEncryptedQRTranscribeModePromptView,SeedFinalizeView,SeedEncryptedQRFullScreenModeView,SeedOptionsView,SeedEncryptedQRTranscribeModeView,SeedTranscribeEncryptedQRZoomedInView
from seedsigner.views.scan_views import ScanDecryptEncryptedQRView
original_initialize=View._initialize
original_controller=Controller._instance
seed=Seed(['abandon']*11+['about'])
with tempfile.TemporaryDirectory(prefix='lvgl-encrypted-review-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__ENCRYPTION_MODE,C.ENCRYPTION_MODE_ECB,save=False)
    controller=SimpleNamespace(storage=SeedStorage(),storage2=EncryptedQRStorage(),resume_main_flow=None)
    Controller._instance=controller
    def initialize(view):
        view.controller=controller;view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    try:
        checks=[]
        for cls,field,count in ((ScanReviewEncryptionKeyScreen,'encryptionkey',3),(SeedEncryptedQRReviewMnemonicIDScreen,'mnemonic_id',2)):
            for text in ('',' public  value ','public'*32):
                print(json.dumps(dict(stage='review',screen=cls.__name__,length=len(text))),flush=True)
                buttons.load(['KEY_DOWN']*20+['KEY_UP']*(count-1)+['KEY_PRESS'])
                screen=cls(**{field:text},button_data=['Proceed','Edit','Scan'][:count])
                assert screen.display()==0
                assert getattr(screen,field)==text
            buttons.load(['KEY_UP']*20+['KEY_PRESS'])
            from seedsigner.gui.screens.screen import RET_CODE__BACK_BUTTON
            assert cls(**{field:'public'},button_data=['Proceed','Edit']).display()==RET_CODE__BACK_BUTTON
            checks.append(dict(screen=cls.__name__,fullTextPreserved=True,proceedAndBack=True))
        key=' public café  '
        buttons.load(['KEY_DOWN']*20+['KEY_UP']*2+['KEY_PRESS'])
        destination=SeedEncryptedQRReviewEncryptionKeyView(encryption_key=key,seed=seed).run()
        assert destination.View_cls is SeedEncryptedQRMnemonicIDPromptView
        buttons.load(['KEY_DOWN']*20+['KEY_UP']+['KEY_PRESS'])
        destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is SeedEncryptedQRReviewMnemonicIDView
        buttons.load(['KEY_DOWN']*20+['KEY_UP']+['KEY_PRESS'])
        destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is SeedEncryptedQRTranscribeModePromptView
        payload=destination.view_args['data']
        assert payload
        # QR scanners return bytes even when the export encoder accepts text.
        if isinstance(payload,str):payload=payload.encode('utf-8')
        print(json.dumps(dict(stage='original-encryption-complete')),flush=True)
        buttons.load(['KEY_DOWN']*12+['KEY_PRESS'])
        destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is SeedEncryptedQRFullScreenModeView
        buttons.capture(payload)
        destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is SeedOptionsView and destination.clear_history
        assert buttons.decoded==payload and not any(frame)
        payload=buttons.decoded
        print(json.dumps(dict(stage='rendered-qr-decoded-exact')),flush=True)
        from seedsigner.helpers.qr import QR
        modules=QR().qrsize(payload)
        assert modules<=33
        buttons.load(['KEY_DOWN']*12+['KEY_UP']+['KEY_PRESS'])
        destination=SeedEncryptedQRTranscribeModePromptView(data=payload,seed=seed).run()
        assert destination.View_cls is SeedEncryptedQRTranscribeModeView
        buttons.capture(payload)
        destination=destination.View_cls(**destination.view_args).run()
        assert buttons.decoded==payload and destination.View_cls is SeedTranscribeEncryptedQRZoomedInView
        buttons.load(['KEY_RIGHT']*8+['KEY_DOWN']*8+['KEY_LEFT']*8+['KEY_UP']*8+['KEY_PRESS'])
        destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is SeedOptionsView and destination.clear_history
        print(json.dumps(dict(stage='encrypted-transcription-complete',modules=modules)),flush=True)
        buttons.load(['KEY_DOWN']*12+['KEY_PRESS'])
        destination=ScanDecryptEncryptedQRView(encryption_key='wrong public key',encrypted_data=payload).run()
        assert destination.View_cls is BackStackView
        assert controller.storage.get_pending_seed() is None
        controller.storage2.clear_encryptedqr()
        destination=ScanDecryptEncryptedQRView(encryption_key=key,encrypted_data=payload).run()
        assert destination.View_cls is SeedFinalizeView
        assert controller.storage.get_pending_seed().mnemonic_list==seed.mnemonic_list
        assert controller.storage2.encryptedqr is None
        print(json.dumps(dict(passed=True,checks=checks,originalCryptoRoundTrip=True,wrongKeyRejected=True,mode=C.ENCRYPTION_MODE_ECB,physicalDisplay=hardware is not None,physicalButtons=False,dependencyInitializationInjected=True,opticalQualified=False,qrExportQualified=True,pixelsDecodedByNativeZXing=True,encryptedTranscriptionViews=True,transcriptionModules=modules)),flush=True)
    finally:
        pending=controller.storage.get_pending_seed()
        if pending is not None:pending.wipe()
        controller.storage2.clear_encryptedqr();seed.wipe()
        Controller._instance=original_controller;View._initialize=original_initialize;restore();runtime.close();reader.close()
        if hardware is not None:hardware.close()
