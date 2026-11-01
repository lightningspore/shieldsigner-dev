"""Original SeedQR scan-confirm Views with synthetic public camera frames.

Injects only physical camera source and View dependencies/input. Native NV12 RX,
preview, ZXing and original DecodeQR/seed comparison remain real.
"""
import json,sys,tempfile,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src','/usr/lib/shieldsigner-camera/python']
from runtime import Runtime,install_view_dispatch
from luckfox import LuckfoxHardware
from synthetic_frames import Source,blank_source
from seedsigner.models.seed import Seed
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.views.view import View,BackStackView
from seedsigner.views.seed_views import SeedTranscribeSeedQRConfirmScanView,SeedTranscribeSeedQRConfirmSuccessView,SeedTranscribeSeedQRConfirmWrongSeedView,SeedTranscribeSeedQRConfirmInvalidQRView,SeedOptionsView
class Buttons:
    def load(self,scan=False,cancel=False):self.start=None;self.scan=scan;self.cancel=cancel
    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        elapsed=now-self.start
        if elapsed>15:raise TimeoutError('SeedQR confirmation navigation stalled')
        if self.scan:return {'KEY_LEFT'} if self.cancel and elapsed>.5 else set()
        t=elapsed-.2
        if t<0:return set()
        i=int(t/.3);keys=['KEY_DOWN']*12+['KEY_PRESS']
        return {keys[i]} if i<len(keys) and t%.3<.16 else set()
buttons=Buttons();hardware=LuckfoxHardware();runtime=Runtime(sys.argv[1],hardware.pixels,buttons)
restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json');original_initialize=View._initialize
seed=Seed(['abandon']*11+['about']);checks=[]
with tempfile.TemporaryDirectory(prefix='lvgl-seedqr-confirm-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    def initialize(view):
        view.controller=SimpleNamespace();view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    try:
        for name,payload,expected in [('matching',bytes(16),SeedTranscribeSeedQRConfirmSuccessView),('different-seed',bytes(range(16)),SeedTranscribeSeedQRConfirmWrongSeedView),('not-seed',b'1BoatSLRHtKNngkdXEeobR76b53LETtpyT',SeedTranscribeSeedQRConfirmInvalidQRView),('cancel',None,BackStackView)]:
            source=Source([payload]) if payload is not None else blank_source()
            buttons.load(scan=True,cancel=(payload is None))
            view=SeedTranscribeSeedQRConfirmScanView(seed)
            with patch('shieldsigner_native_stream.NativeVideoStream',lambda **kwargs:source):destination=view.run()
            assert destination.View_cls is expected
            assert source.is_stopped and runtime.camera_stats['cameraStopped']
            qr=runtime.camera_stats['qr']
            assert qr['errors']==0 and qr['lastExitCode']==0,qr
            if expected is not BackStackView:
                buttons.load()
                result=destination.View_cls(**(destination.view_args or {})).run()
                if expected is SeedTranscribeSeedQRConfirmSuccessView:assert result.View_cls is SeedOptionsView and result.view_args['seed'] is seed
                else:assert result.View_cls is BackStackView and result.skip_current_view
            else:assert not destination.skip_current_view
            assert seed.mnemonic_list==['abandon']*11+['about']
            checks.append(dict(case=name,originalDestination=expected.__name__,nativeFrames=runtime.camera_stats['frames'],qrWorkerExitCode=qr['lastExitCode'],sourceStopped=True,seedUnchanged=True))
        assert not Path(Settings.SETTINGS_FILENAME).exists()
        print(json.dumps(dict(passed=True,checks=checks,originalScanViewAndSeedComparison=True,nativeReceiverPreviewZXing=True,physicalCamera=False,opticalQualified=False,physicalDisplay=True,physicalButtons=False,dependencyInitializationInjected=True)))
    finally:
        seed.wipe();View._initialize=original_initialize;restore();runtime.close();hardware.close()
