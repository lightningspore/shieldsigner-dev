"""Original address-search workers/callbacks with public derived addresses."""
import json
from pathlib import Path
import sys
import time
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
from runtime import Runtime,install_view_dispatch
from seedsigner.gui.screens import seed_screens
from seedsigner.gui.screens.screen import ButtonOption
class Buttons:
    def load(self,keys):self.keys=keys;self.start=None
    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        t=now-self.start-.2
        if t<0:return set()
        i=int(t/.2)
        if i>=len(self.keys):
            if t>len(self.keys)*.2+5:raise TimeoutError('Address search navigation did not finish')
            return set()
        return {self.keys[i]} if t%.2<.1 else set()
buttons=Buttons();hardware=None;rectangles=0
if '--display' in sys.argv:
    from luckfox import LuckfoxHardware
    hardware=LuckfoxHardware()
def pixels(area,data):
    global rectangles
    rectangles+=1
    if hardware is not None:hardware.pixels(area,data)
runtime=Runtime(sys.argv[1],pixels,buttons);restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
from seedsigner.models.seed import Seed
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.models.threads import ThreadsafeCounter
from seedsigner.views.seed_views import SeedAddressVerificationView
from seedsigner.helpers import embit_utils
from seedsigner.views.view import View,MainMenuView
from seedsigner.views.seed_views import SeedAddressVerificationSuccessView
from types import SimpleNamespace
original_initialize=View._initialize
seed=Seed(['abandon']*11+['about']);checks=[]
import tempfile
with tempfile.TemporaryDirectory(prefix='lvgl-address-test-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json')
    settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__NETWORK,C.MAINNET,save=False)
    path="m/84'/0'/0'"
    xpub=seed.get_xpub(wallet_path=path,network=C.MAINNET)
    worker=None
    try:
        for change in (False,True):
            address=embit_utils.get_single_sig_address(xpub=xpub,script_type=C.NATIVE_SEGWIT,index=7,is_change=change,embit_network='main')
            counter=ThreadsafeCounter();verified=ThreadsafeCounter(None);branch=ThreadsafeCounter(None)
            worker=SeedAddressVerificationView.BruteForceAddressVerificationThread(address=address,seed=seed,descriptor=None,script_type=C.NATIVE_SEGWIT,embit_network='main',derivation_path=path,threadsafe_counter=counter,verified_index=verified,verified_index_is_change=branch)
            worker.start();buttons.load([])
            value=seed_screens.SeedAddressVerificationScreen(address=address,script_type='Native Segwit',sig_type='Single Sig',network='Mainnet',is_mainnet=True,threadsafe_counter=counter,verified_index=verified,button_data=[ButtonOption('Skip 10'),ButtonOption('Cancel')],max_iterations=100).display()
            worker.stop();worker.join(5)
            assert not worker.is_alive()
            assert value==1 and verified.cur_count==7 and branch.cur_count==int(change)
            checks.append(dict(change=change,verifiedIndex=7,workerJoined=True))
        # Original callback must end an exhausted batch without user input.
        counter=ThreadsafeCounter(20);verified=ThreadsafeCounter(None);buttons.load([])
        value=seed_screens.SeedAddressVerificationScreen(address=address,script_type='Native Segwit',sig_type='Single Sig',network='Mainnet',is_mainnet=True,threadsafe_counter=counter,verified_index=verified,button_data=[ButtonOption('Cancel')],max_iterations=20).display()
        assert value==1000
        for attempt in range(3):
            buttons.load(['KEY_PRESS'])
            counter.set_value(0)
            value=seed_screens.SeedAddressVerificationScreen(address=address,script_type='Native Segwit',sig_type='Single Sig',network='Mainnet',is_mainnet=True,threadsafe_counter=counter,verified_index=verified,button_data=[ButtonOption('Cancel')],max_iterations=20).display()
            assert value==0
        controller=SimpleNamespace(multisig_wallet_descriptor=None,unverified_address=dict(address=address,derivation_path=path,script_type=C.NATIVE_SEGWIT,sig_type=C.SINGLE_SIG,network=C.MAINNET))
        def initialize(view):
            view.controller=controller;view.settings=settings
            view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
            view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None
        View._initialize=initialize
        buttons.load([])
        view=SeedAddressVerificationView(seed=seed)
        destination=view.run()
        assert destination.View_cls is SeedAddressVerificationSuccessView
        assert not view.addr_verification_thread.is_alive()
        assert controller.unverified_address['verified_index']==7
        assert controller.unverified_address['verified_index_is_change'] is True
        buttons.load(['KEY_DOWN']*12+['KEY_PRESS'])
        destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is MainMenuView
        print(json.dumps(dict(passed=True,checks=checks,originalWorkerAndCallback=True,batchExhaustionReturnsBack=True,cancelButtonIndex=0,enterOnlyCancelRepeats=3,fullSingleSigViewAndSuccess=True,physicalDisplay=hardware is not None,physicalButtons=False)))
    finally:
        if worker is not None:worker.stop();worker.join(5)
        seed.wipe();View._initialize=original_initialize;restore();runtime.close()
        if hardware is not None:hardware.close()
