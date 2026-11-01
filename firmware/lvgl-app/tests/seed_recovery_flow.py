"""Original seed recovery/finalization Views/models, driven through native LVGL.

Uses only the public BIP39 abandon/about vector. Each prefilled word is accepted
via LVGL KEY2; this tests the review/edit route, not typing every letter. Only
View dependency initialization is injected. No cryptographic methods are stubbed.
"""
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
from seedsigner.models.seed_storage import SeedStorage
from seedsigner.views.view import View
class Buttons:
    def load(self,keys):self.keys=keys;self.start=None
    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        elapsed=now-self.start-.15
        if elapsed<0:return set()
        i=int(elapsed/.2)
        if i>=len(self.keys):
            if elapsed>len(self.keys)*.2+5:raise TimeoutError('Seed recovery navigation did not finish')
            return set()
        return {self.keys[i]} if elapsed%.2<.1 else set()
buttons=Buttons();rectangles=0
hardware=None
if '--display' in sys.argv:
    from luckfox import LuckfoxHardware
    hardware=LuckfoxHardware()
def pixels(area,data):
    global rectangles
    rectangles+=1
    if hardware is not None:hardware.pixels(area,data)
runtime=Runtime(sys.argv[1],pixels,buttons)
restore=install_view_dispatch(runtime,sys.argv[2],Path(__file__).parent/'source-guards.json')
original_initialize=View._initialize
storage=SeedStorage()
controller=SimpleNamespace(storage=storage,resume_main_flow=None)
with tempfile.TemporaryDirectory(prefix='lvgl-seed-test-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json')
    settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__NETWORK,C.MAINNET,save=False)
    settings.set_value(C.SETTING__WORDLIST_LANGUAGE,C.WORDLIST_LANGUAGE__ENGLISH,save=False)
    def initialize(view):
        view.controller=controller;view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None
    View._initialize=initialize
    try:
        from seedsigner.views.seed_views import SeedMnemonicEntryView,SeedFinalizeView,SeedOptionsView
        public_words=['abandon']*11+['about']
        storage.init_pending_mnemonic(12)
        for i,word in enumerate(public_words):storage.update_pending_mnemonic(word,i)
        destination=None
        for i in range(12):
            buttons.load(['KEY2'])
            view=SeedMnemonicEntryView(cur_word_index=i)
            destination=view.run()
            if i<11:
                assert destination.View_cls is SeedMnemonicEntryView
                assert destination.view_args['cur_word_index']==i+1
                assert storage.get_pending_mnemonic_word(i)==public_words[i]
            else:assert destination.View_cls is SeedFinalizeView
        seed=storage.get_pending_seed()
        assert seed.mnemonic_list==public_words
        assert seed.get_fingerprint(network=C.MAINNET)=='73c5da0a'
        buttons.load(['KEY_PRESS'])
        destination=destination.View_cls().run()
        assert destination.View_cls is SeedOptionsView
        assert storage.num_seeds()==1 and storage.get_pending_seed() is None
        assert destination.view_args['seed'] is seed
        # Backing out of word one must clear the pending mnemonic, not the stored seed.
        storage.init_pending_mnemonic(12)
        storage.update_pending_mnemonic('abandon',0)
        buttons.load(['KEY_UP']*5+['KEY_PRESS'])
        destination=SeedMnemonicEntryView(cur_word_index=0).run()
        assert storage.pending_mnemonic_length==0
        assert storage.num_seeds()==1
        assert not Path(Settings.SETTINGS_FILENAME).exists()
        print(json.dumps(dict(passed=True,acceptedWords=12,publicVector='BIP39-abandon-about',fingerprint='73c5da0a',finalizedStoredSeed=True,cancelFirstWordClearedPending=True,originalViewsModelsCrypto=True,dependencyInitializationInjected=True,physicalDisplay=hardware is not None,physicalButtons=False,persistentSettingsWritten=False,rectangles=rectangles)))
    finally:
        for seed in storage.seeds:seed.wipe()
        storage.seeds=[];storage.clear_pending_seed();storage.discard_pending_mnemonic()
        View._initialize=original_initialize;restore();runtime.close()
        if hardware is not None:hardware.close()
