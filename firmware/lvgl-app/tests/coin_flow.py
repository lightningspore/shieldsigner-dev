"""Original coin keyboard through checksum calculation and finalize/discard."""
import json
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
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
from seedsigner.views.tools_views import ToolsCalcFinalWordFinalizePromptView,ToolsCalcFinalWordShowFinalWordView,ToolsCalcFinalWordDoneView
from seedsigner.views.seed_views import SeedFinalizeView,SeedDiscardView
from seedsigner.views.view import BackStackView
from embit import bip39
original_initialize=View._initialize;checks=[]
with tempfile.TemporaryDirectory(prefix='lvgl-final-word-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__PASSPHRASE,C.OPTION__DISABLED,save=False)
    storage=SeedStorage();controller=SimpleNamespace(storage=storage,settings=settings,resume_main_flow=None)
    def initialize(view):
        view.controller=controller;view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    def choose(index,count):buttons.load(['KEY_DOWN']*12+['KEY_UP']*(count-1-index)+['KEY_PRESS'])
    from seedsigner.views.tools_views import ToolsCalcFinalWordCoinFlipsView
    from seedsigner.views.seed_views import SeedOptionsView
    from seedsigner.views.view import MainMenuView
    try:
        for length in (12,24):
            print(json.dumps(dict(stage='coin-keyboard',length=length)),flush=True)
            storage.init_pending_mnemonic(num_words=length)
            for i in range(length):storage.update_pending_mnemonic('abandon',i)
            before=list(storage.pending_mnemonic)
            # One entered bit followed by top-nav Back must not alter entropy.
            buttons.load(['KEY_PRESS','KEY_UP','KEY_PRESS'])
            destination=ToolsCalcFinalWordCoinFlipsView().run()
            assert destination.View_cls is BackStackView and storage.pending_mnemonic==before
            choose(0,3);destination=ToolsCalcFinalWordFinalizePromptView().run()
            assert destination.View_cls is ToolsCalcFinalWordCoinFlipsView
            # Enter an intentionally wrong leading zero, navigate DOWN to the
            # native control row and delete it. UP returns to the right-hand
            # value key; LEFT selects 1, then type the alternating fixture.
            # Without deletion the result starts 0 and cannot match expected bits.
            plan=['KEY_RIGHT','KEY_PRESS','KEY_DOWN','KEY_PRESS','KEY_UP','KEY_LEFT','KEY_PRESS','KEY_RIGHT','KEY_PRESS','KEY_LEFT','KEY_PRESS']
            if length==12:plan+=['KEY_RIGHT','KEY_PRESS','KEY_LEFT','KEY_PRESS']*2
            buttons.load(plan);destination=destination.View_cls(**(destination.view_args or {})).run()
            bits='1010101' if length==12 else '101'
            assert destination.View_cls is ToolsCalcFinalWordShowFinalWordView and destination.view_args['coin_flips']==bits
            assert storage.pending_mnemonic==before
            view=destination.View_cls(**destination.view_args)
            entropy=bytes((16 if length==12 else 32)-1)+bytes([int(bits,2)])
            expected=bip39.mnemonic_from_bytes(entropy).split()
            assert storage.pending_mnemonic==expected
            choose(0,1);destination=view.run()
            assert destination.View_cls is ToolsCalcFinalWordDoneView
            choose(0 if length==12 else 1,2);destination=destination.View_cls(**(destination.view_args or {})).run()
            assert storage.get_pending_seed().mnemonic_list==expected
            if length==12:
                assert destination.View_cls is SeedFinalizeView
                choose(0,1);destination=destination.View_cls(**(destination.view_args or {})).run()
                assert destination.View_cls is SeedOptionsView and destination.clear_history
                assert len(storage.seeds)==1 and storage.seeds[0].mnemonic_list==expected and storage.get_pending_seed() is None
                storage.seeds[0].wipe();storage.seeds.clear()
            else:
                assert destination.View_cls is SeedDiscardView
                choose(1,2);destination=destination.View_cls(**(destination.view_args or {})).run()
                assert destination.View_cls is MainMenuView and destination.clear_history
                assert storage.get_pending_seed() is None and not storage.seeds
            checks.append(dict(length=length,nativeKeyboardBitsExact=True,backspaceAndCancel=True,originalChecksumExact=True,executedOriginalFinalize=length==12,executedOriginalDiscard=length==24))
        print(json.dumps(dict(passed=True,checks=checks,physicalDisplay=hardware is not None,physicalButtons=False,dependencyInitializationInjected=True,entropySourceIsPublicScript=True)),flush=True)
    finally:
        storage.clear_pending_seed();storage.discard_pending_mnemonic()
        for seed in storage.seeds:seed.wipe()
        storage.seeds.clear();View._initialize=original_initialize;restore();runtime.close()
        if hardware is not None:hardware.close()
