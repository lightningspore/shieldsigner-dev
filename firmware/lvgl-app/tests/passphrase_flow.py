"""Exact public passphrase responses and unchanged wallet-model review flow."""
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
        t=now-self.start-.15
        if t<0:return set()
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
restore=install_view_dispatch(runtime,sys.argv[2],Path(__file__).parent/'source-guards.json')
checks=[];storage=SeedStorage();original_initialize=View._initialize
with tempfile.TemporaryDirectory(prefix='lvgl-passphrase-test-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json')
    settings=Settings.get_instance();settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False);settings.set_value(C.SETTING__NETWORK,C.MAINNET,save=False)
    def initialize(view):
        view.controller=SimpleNamespace(storage=storage,resume_main_flow=None);view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None
    View._initialize=initialize
    try:
        fixtures=['','  spaced  ','café e\u0301','line\nbreak\rtest','a\0b','\0','nul\0 literal\\0 é',''.join(chr(n) for n in range(32,127))]
        for i,text in enumerate(fixtures):
            print('public-fixture-index',i,flush=True)
            buttons.load(['KEY3'])
            response=SeedAddPassphraseScreen(title='Public test',passphrase=text).display()
            assert response=={'passphrase':text},('save-exact',i)
        checks.append('save-empty-spaces-unicode-newlines-printable-ascii-exact')
        text='  café\0 e\u0301  '
        buttons.load(['KEY_UP']*6+['KEY_PRESS'])
        response=SeedAddPassphraseScreen(title='Public test',passphrase=text).display()
        assert response==dict(passphrase=text,is_back_button=True)
        checks.append('back-returns-current-text-and-back-flag')
        buttons.load(['KEY_UP']*6+['KEY3'])
        response=SeedAddPassphraseScreen(title='Public test',passphrase=' top-nav ').display()
        assert response=={'passphrase':' top-nav '}
        checks.append('save-from-top-nav-preserves-spaces')
        from seedsigner.views.seed_views import SeedAddPassphraseView,SeedReviewPassphraseView,SeedOptionsView,SeedAddPassphraseExitDialogView,SeedFinalizeView
        words=['abandon']*11+['about']
        seed=Seed(words);seed.set_passphrase('TREZOR\0public\\0');storage.set_pending_seed(seed)
        reference=Seed(words);reference.set_passphrase('TREZOR\0public\\0');expected=reference.get_fingerprint(C.MAINNET);reference.wipe()
        buttons.load(['KEY3']);destination=SeedAddPassphraseView().run()
        assert destination.View_cls is SeedReviewPassphraseView
        assert seed.passphrase=='TREZOR\0public\\0' and seed.get_fingerprint(C.MAINNET)==expected
        buttons.load(['KEY_PRESS']);destination=destination.View_cls().run()
        assert destination.View_cls is SeedOptionsView and storage.num_seeds()==1
        assert destination.view_args['seed'] is seed
        checks.append('original-add-review-finalize-model-fingerprint-unchanged')
        pending=Seed(words);pending.set_passphrase('public');storage.set_pending_seed(pending)
        buttons.load(['KEY_UP']*6+['KEY_PRESS']);destination=SeedAddPassphraseView().run()
        assert destination.View_cls is SeedAddPassphraseExitDialogView
        assert pending.passphrase=='public'
        buttons.load(['KEY_DOWN','KEY_PRESS']);destination=destination.View_cls().run()
        assert destination.View_cls is SeedFinalizeView and pending.passphrase==''
        checks.append('back-exit-dialog-discard-clears-passphrase')
        assert not Path(Settings.SETTINGS_FILENAME).exists()
        print(json.dumps(dict(passed=True,checks=checks,rectangles=rectangles,originalViewsModelsCrypto=True,dependencyInitializationInjected=True,physicalDisplay=hardware is not None,physicalButtons=False,persistentSettingsWritten=False)))
    finally:
        for seed in storage.seeds:seed.wipe()
        storage.seeds=[];storage.clear_pending_seed()
        View._initialize=original_initialize;restore();runtime.close()
        if hardware is not None:hardware.close()
