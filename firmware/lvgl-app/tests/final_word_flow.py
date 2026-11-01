"""Public exact-text encrypted entry contracts and original discard routes."""
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
    storage=SeedStorage();controller=SimpleNamespace(storage=storage,settings=settings)
    def initialize(view):
        view.controller=controller;view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    def choose(index,count):buttons.load(['KEY_DOWN']*12+['KEY_UP']*(count-1-index)+['KEY_PRESS'])
    try:
        for length in (12,24):
            for mode in ('zeros','coins','word'):
                print(json.dumps(dict(stage='final-word',length=length,mode=mode)),flush=True)
                storage.init_pending_mnemonic(num_words=length)
                for i in range(length):storage.update_pending_mnemonic('abandon',i)
                bits=7 if length==12 else 3
                if mode=='zeros':
                    choose(2,3);destination=ToolsCalcFinalWordFinalizePromptView().run()
                    assert destination.View_cls is ToolsCalcFinalWordShowFinalWordView
                    view=destination.View_cls(**destination.view_args);last_byte=0
                elif mode=='coins':
                    flips='1010101' if length==12 else '101'
                    view=ToolsCalcFinalWordShowFinalWordView(coin_flips=flips);last_byte=int(flips,2)
                else:
                    storage.update_pending_mnemonic('zoo',-1)
                    view=ToolsCalcFinalWordShowFinalWordView();last_byte=(1<<bits)-1
                entropy=bytes((16 if length==12 else 32)-1)+bytes([last_byte])
                expected=bip39.mnemonic_from_bytes(entropy).split()
                assert storage.pending_mnemonic==expected
                assert view.actual_final_word==expected[-1]
                choose(0,1);destination=view.run()
                assert destination.View_cls is ToolsCalcFinalWordDoneView
                if mode=='word':
                    buttons.load(['KEY_UP']*12+['KEY_PRESS']);destination=ToolsCalcFinalWordDoneView().run()
                    assert destination.View_cls is BackStackView and storage.pending_mnemonic==expected and storage.get_pending_seed() is None
                choose(1 if mode=='word' else 0,2);destination=ToolsCalcFinalWordDoneView().run()
                assert destination.View_cls is (SeedDiscardView if mode=='word' else SeedFinalizeView)
                assert storage.get_pending_seed().mnemonic_list==expected
                assert bip39.mnemonic_to_bytes(storage.get_pending_seed().mnemonic_str)==entropy
                assert not storage.pending_mnemonic
                checks.append(dict(length=length,mode=mode,originalChecksumMatchesIndependentBip39=True,originalPendingSeed=True,doneRoute=destination.View_cls.__name__))
                storage.clear_pending_seed()
        print(json.dumps(dict(passed=True,checks=checks,doneBackPreservesPendingMnemonic=True,physicalDisplay=hardware is not None,physicalButtons=False,dependencyInitializationInjected=True,coinKeyboardQualified=False,finalizationAndDiscardExecutionQualified=False)),flush=True)
    finally:
        storage.clear_pending_seed();storage.discard_pending_mnemonic();View._initialize=original_initialize;restore();runtime.close()
        if hardware is not None:hardware.close()
