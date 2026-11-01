"""Original SeedQR transcription Views, public BIP39 fixtures, rendered QR decode."""
import json,sys,tempfile,threading,time
from pathlib import Path
from types import SimpleNamespace
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src','/usr/lib/shieldsigner-camera/python']
from runtime import Runtime,install_view_dispatch
from luckfox import LuckfoxHardware
from shieldsigner_lcd import QrWorker
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.models.seed import Seed
from seedsigner.models.encode_qr import SeedQrEncoder,CompactSeedQrEncoder
from seedsigner.models.qr_type import QRType
from seedsigner.views.view import View,BackStackView
from seedsigner.views.seed_views import SeedTranscribeSeedQRFormatView,SeedTranscribeSeedQRWarningView,SeedTranscribeSeedQRWholeQRView,SeedTranscribeSeedQRZoomedInView,SeedTranscribeSeedQRConfirmQRPromptView,SeedOptionsView
frame=bytearray(115200);lock=threading.Lock();hardware=LuckfoxHardware()
def pixels(area,data):
    x1,y1,x2,y2=area;stride=(x2-x1+1)*2
    with lock:
        for row,y in enumerate(range(y1,y2+1)):frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
    hardware.pixels(area,data)
class Buttons:
    def load(self,keys,expected=None):self.keys=keys;self.start=None;self.expected=expected;self.decoded=False;self.last=0
    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        elapsed=now-self.start
        if elapsed>15:raise TimeoutError('Transcription navigation/decoding stalled')
        if self.expected is not None:
            if self.decoded:return {'KEY_PRESS'}
            if elapsed<.3 or now-self.last<.15:return set()
            self.last=now
            with lock:luma=bytes(frame[0::2])
            data=reader.decode_luma(luma,240,240)
            if data is not None:
                assert data==self.expected,'Whole QR rendered different payload bytes'
                self.decoded=True
            return set()
        t=elapsed-.2
        if t<0:return set()
        i=int(t/.3)
        if i>=len(self.keys):return set()
        return {self.keys[i]} if t%.3<.16 else set()
buttons=Buttons();reader=QrWorker('/usr/lib/shieldsigner-camera/shieldsigner-qr-reader',5)
runtime=Runtime(sys.argv[1],pixels,buttons)
restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json');original_initialize=View._initialize
seeds=[];checks=[]
with tempfile.TemporaryDirectory(prefix='lvgl-transcribe-test-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__COMPACT_SEEDQR,C.OPTION__ENABLED,save=False)
    settings.set_value(C.SETTING__ENCRYPTED_QR,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__DIRE_WARNINGS,C.OPTION__ENABLED,save=False)
    def initialize(view):
        view.controller=SimpleNamespace();view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    try:
        for word_count in (12,24):
            words=['abandon']*(word_count-1)+(['about'] if word_count==12 else ['art'])
            seed=Seed(words);seeds.append(seed)
            for compact in (False,True):
                buttons.load((['KEY_DOWN'] if compact else [])+['KEY_PRESS'])
                destination=SeedTranscribeSeedQRFormatView(seed).run()
                assert destination.View_cls is SeedTranscribeSeedQRWarningView
                qr_type=QRType.SEED__COMPACTSEEDQR if compact else QRType.SEED__SEEDQR
                assert destination.view_args['seedqr_format']==qr_type
                buttons.load(['KEY_DOWN']*12+['KEY_PRESS'])
                destination=destination.View_cls(**destination.view_args).run()
                assert destination.View_cls is SeedTranscribeSeedQRWholeQRView
                encoder=(CompactSeedQrEncoder if compact else SeedQrEncoder)(mnemonic=words)
                part=encoder.next_part();expected=part if isinstance(part,bytes) else part.encode()
                buttons.load([],expected)
                destination=destination.View_cls(**destination.view_args).run()
                assert buttons.decoded and destination.View_cls is SeedTranscribeSeedQRZoomedInView
                buttons.load(['KEY_RIGHT','KEY_DOWN','KEY_LEFT','KEY_UP','KEY_PRESS'])
                destination=destination.View_cls(**destination.view_args).run()
                assert destination.View_cls is SeedTranscribeSeedQRConfirmQRPromptView
                buttons.load(['KEY_DOWN','KEY_PRESS'])
                destination=destination.View_cls(**destination.view_args).run()
                assert destination.View_cls is SeedOptionsView and destination.clear_history
                assert seed.mnemonic_list==words
                checks.append(dict(words=word_count,compact=compact,wholeQRBytesExact=True,zoomExitNone=True,optionalConfirmationDone=True,seedUnchanged=True))
        from seedsigner.helpers.qr import QR
        buttons.load(['KEY_UP']*6+['KEY_PRESS'])
        destination=SeedTranscribeSeedQRWholeQRView(seeds[0],QRType.SEED__SEEDQR,QR().qrsize(SeedQrEncoder(mnemonic=seeds[0].mnemonic_list).next_part())).run()
        assert destination.View_cls is BackStackView
        print(json.dumps(dict(passed=True,checks=checks,wholeQRBack=True,originalViewsAndEncoders=True,dependencyInitializationInjected=True,physicalDisplay=True,physicalButtons=False,opticalQualified=False,scanConfirmationQualified=False)))
    finally:
        for seed in seeds:seed.wipe()
        View._initialize=original_initialize;restore();runtime.close();reader.close();hardware.close()
