"""Original message review/address/signature QR flow with public fixtures."""
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
            if elapsed>20:raise TimeoutError('Signed-message QR pixels did not decode')
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
            if t>len(self.keys)*.2+5:raise TimeoutError('Message navigation did not finish')
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
from seedsigner.controller import Controller
from seedsigner.views.view import BackStackView,MainMenuView
from seedsigner.views.seed_views import SeedSignMessageStartView,SeedSignMessageConfirmMessageView,SeedSignMessageConfirmAddressView,SeedSignMessageSignedMessageQRView
from seedsigner.helpers import embit_utils
from embit import ec,compact
from embit.util import secp256k1
import base64,hashlib
original_initialize=View._initialize;original_controller=Controller._instance
seed=Seed(['abandon']*11+['about'])
with tempfile.TemporaryDirectory(prefix='lvgl-message-signing-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__MESSAGE_SIGNING,C.OPTION__ENABLED,save=False)
    controller=SimpleNamespace(sign_message_data=None,resume_main_flow=None,sign_message_with_satochip=False)
    Controller._instance=controller
    def initialize(view):
        view.controller=controller;view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    checks=[]
    try:
        path="m/84h/0h/0h/0/0"
        messages=[' public café  \nnext ', 'Public fixture only. '*28]
        for index,message in enumerate(messages):
            print(json.dumps(dict(stage='message-flow',fixture=index,length=len(message))),flush=True)
            controller.sign_message_data={'seed':seed}
            start=SeedSignMessageStartView(derivation_path=path,message=message)
            assert start._redirect.View_cls is SeedSignMessageConfirmMessageView
            buttons.load(['KEY_DOWN']*25+['KEY_PRESS'])
            destination=SeedSignMessageConfirmMessageView().run()
            assert destination.View_cls is SeedSignMessageConfirmAddressView
            assert controller.sign_message_data['message']==message
            assert controller.sign_message_data['paged_message']==[message]
            address_view=destination.View_cls(**(destination.view_args or {}))
            expected_address=address_view.address
            buttons.load(['KEY_UP']*12+['KEY_PRESS'])
            destination=address_view.run()
            assert destination.View_cls is BackStackView
            assert controller.sign_message_data['message']==message
            buttons.load(['KEY_DOWN']*12+['KEY_PRESS'])
            destination=address_view.run()
            assert destination.View_cls is SeedSignMessageSignedMessageQRView
            signed=destination.View_cls(**(destination.view_args or {}))
            expected=signed.signed_message.encode()
            signature=base64.b64decode(expected,validate=True)
            assert len(signature)==65
            digest=hashlib.sha256(hashlib.sha256(b'\x18Bitcoin Signed Message:\n'+compact.to_bytes(len(message.encode()))+message.encode()).digest()).digest()
            parsed=ec.Signature(secp256k1.ecdsa_signature_parse_compact(signature[1:]))
            assert seed.get_root().derive(path).key.get_public_key().verify(parsed,digest)
            buttons.capture(expected);destination=signed.run()
            assert buttons.decoded==expected and not any(frame)
            assert destination.View_cls is MainMenuView
            assert controller.sign_message_data is None and controller.resume_main_flow is None and not controller.sign_message_with_satochip
            checks.append(dict(messageLength=len(message),nativeReviewAndAddress=True,addressBackPreservedMessage=True,originalSignatureVerified=True,renderedQRBytesExact=True,cleanup=True))
        controller.sign_message_data={'seed':seed,'message':'Public cancel fixture','derivation_path':path}
        buttons.load(['KEY_UP']*15+['KEY_PRESS'])
        destination=SeedSignMessageConfirmMessageView().run()
        assert destination.View_cls is BackStackView and controller.sign_message_data is None
        print(json.dumps(dict(passed=True,checks=checks,firstPageBackClearsState=True,physicalDisplay=hardware is not None,physicalButtons=False,opticalQualified=False,dependencyInitializationInjected=True,satochipQualified=False)),flush=True)
    finally:
        controller.sign_message_data=None;seed.wipe();Controller._instance=original_controller
        View._initialize=original_initialize;restore();runtime.close();reader.close()
        if hardware is not None:hardware.close()
