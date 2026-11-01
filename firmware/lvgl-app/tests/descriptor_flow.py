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
        t=now-self.start-.15
        if t<0:return set()
        if self.keys is None:
            if t>15:raise TimeoutError('Descriptor scan stalled')
            return set()
        i=int(t/.2)
        if i>=len(self.keys):
            if t>len(self.keys)*.2+5:raise TimeoutError('Passphrase navigation did not finish')
            return set()
        return {self.keys[i]} if t%.2<.1 else set()
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
from seedsigner.controller import Controller
from seedsigner.views.seed_views import LoadMultisigWalletDescriptorView,MultisigWalletDescriptorView,SeedAddressVerificationView
from seedsigner.views.scan_views import ScanWalletDescriptorView
from seedsigner.views.psbt_views import PSBTOverviewView,PSBTChangeDetailsView
from seedsigner.views.view import BackStackView,MainMenuView
from synthetic_frames import Source
from unittest.mock import patch
from embit import bip39
from embit.descriptor import Descriptor
original_initialize=View._initialize;original_controller=Controller._instance
seeds=[];checks=[]
with tempfile.TemporaryDirectory(prefix='lvgl-descriptor-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__SMARTCARD_SUPPORT,C.OPTION__DISABLED,save=False)
    controller=SimpleNamespace(multisig_wallet_descriptor=None,resume_main_flow=None,psbt_parser=None,unverified_address=None,reset_screensaver_timeout=lambda:None)
    Controller._instance=controller
    def initialize(view):
        view.controller=controller;view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    try:
        keys=[];fingerprints=[]
        for i in range(3):
            seed=Seed(bip39.mnemonic_from_bytes(bytes([i])*16).split());seeds.append(seed)
            fingerprint=seed.get_fingerprint();fingerprints.append(fingerprint)
            xpub=seed.get_xpub(wallet_path="m/48h/0h/0h/2h",network=C.MAINNET).to_base58()
            keys.append('['+fingerprint+'/48h/0h/0h/2h]'+xpub+'/0/*')
        payload=('wsh(sortedmulti(2,'+','.join(keys)+'))').encode()
        buttons.load(['KEY_DOWN']*20+['KEY_UP']+['KEY_PRESS'])
        destination=LoadMultisigWalletDescriptorView().run()
        assert destination.View_cls is ScanWalletDescriptorView
        source=Source([payload]);buttons.load(None)
        with patch('shieldsigner_native_stream.NativeVideoStream',lambda **kwargs:source):destination=destination.View_cls(**(destination.view_args or {})).run()
        assert destination.View_cls is MultisigWalletDescriptorView
        descriptor=controller.multisig_wallet_descriptor
        assert descriptor.is_basic_multisig
        assert [key.fingerprint.hex() for key in descriptor.keys]==fingerprints
        assert source.is_stopped and runtime.camera_stats['cameraStopped']
        assert runtime.camera_stats['qr']['lastExitCode']==0
        # Original scan normalization must provide both receive and change branches.
        assert descriptor.derive(0,branch_index=0).address()!=descriptor.derive(0,branch_index=1).address()
        buttons.load(['KEY_DOWN']*25+['KEY_PRESS']);destination=MultisigWalletDescriptorView().run()
        assert destination.View_cls is MainMenuView and controller.multisig_wallet_descriptor is descriptor
        checks.append(dict(case='scan-review-ok',policy='2 of 3',keys=3,nativeFrames=runtime.camera_stats['frames'],nativeQrExitCode=0,bothBranches=True))
        for flow,parser,expected in [(Controller.FLOW__PSBT,SimpleNamespace(unidentified_change_outputs=True),PSBTOverviewView),(Controller.FLOW__PSBT,SimpleNamespace(unidentified_change_outputs=False),PSBTChangeDetailsView),(Controller.FLOW__VERIFY_MULTISIG_ADDR,None,SeedAddressVerificationView)]:
            controller.resume_main_flow=flow;controller.psbt_parser=parser;controller.unverified_address={'address':'bc1public'}
            buttons.load(['KEY_DOWN']*25+['KEY_PRESS']);destination=MultisigWalletDescriptorView().run()
            assert destination.View_cls is expected and controller.resume_main_flow is None
            if expected is PSBTOverviewView:assert controller.psbt_parser is None and destination.skip_current_view
            checks.append(dict(case='resume',destination=expected.__name__,originalRouting=True))
        buttons.load(['KEY_UP']*15+['KEY_PRESS']);destination=MultisigWalletDescriptorView().run()
        assert destination.View_cls is BackStackView and controller.multisig_wallet_descriptor is None
        for flow,expected in [(None,MainMenuView),(Controller.FLOW__PSBT,BackStackView)]:
            controller.resume_main_flow=flow;buttons.load(['KEY_DOWN']*25+['KEY_PRESS']);destination=LoadMultisigWalletDescriptorView().run()
            assert destination.View_cls is expected
        print(json.dumps(dict(passed=True,checks=checks,reviewBackClearsDescriptor=True,loadCancelRoutes=True,physicalDisplay=hardware is not None,physicalButtons=False,physicalCamera=False,opticalQualified=False,nativeReceiverPreviewZXing=True,dependencyInitializationInjected=True,smartcardQualified=False,multisigSigningQualified=False)),flush=True)
    finally:
        controller.multisig_wallet_descriptor=None
        for seed in seeds:seed.wipe()
        Controller._instance=original_controller;View._initialize=original_initialize;restore();runtime.close()
        if hardware is not None:hardware.close()
