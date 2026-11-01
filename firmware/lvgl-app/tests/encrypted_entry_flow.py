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
restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
from seedsigner.gui.screens.scan_screens import ScanTypeEncryptionKeyScreen
from seedsigner.gui.screens.seed_screens import SeedEncryptedQRMnemonicIDScreen
from seedsigner.views.seed_views import SeedEncryptedQRTypeEncryptionKeyView,SeedEncryptedQRTypeEncryptionKeyExitDialogView,SeedEncryptedQRReviewEncryptionKeyView,SeedEncryptedQRMnemonicIDEntryView,SeedEncryptedQRMnemonicIDEntryExitDialogView,SeedEncryptedQRReviewMnemonicIDView
from seedsigner.views.view import BackStackView
checks=[];original_initialize=View._initialize
seed=Seed(['abandon']*11+['about'])
with tempfile.TemporaryDirectory(prefix='lvgl-encrypted-entry-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    def initialize(view):
        view.controller=SimpleNamespace();view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    try:
        fixtures=['','  public  ','café e\u0301','line\r\nnext',''.join(chr(n) for n in range(32,127))]
        for cls,field in ((ScanTypeEncryptionKeyScreen,'encryptionkey'),(SeedEncryptedQRMnemonicIDScreen,'mnemonic_id')):
            for index,text in enumerate(fixtures):
                print(json.dumps(dict(stage='entry',screen=cls.__name__,fixture=index)),flush=True)
                buttons.load(['KEY3']);value=cls(**{field:text}).display()
                assert value=={field:text}
            text='  public café  '
            buttons.load(['KEY_UP']*6+['KEY_PRESS']);value=cls(**{field:text}).display()
            assert value=={field:text,'is_back_button':True}
            checks.append(dict(screen=cls.__name__,saveFixturesExact=5,backTextExact=True))
        text='  public key  '
        buttons.load(['KEY3']);destination=SeedEncryptedQRTypeEncryptionKeyView(seed,encryption_key=text).run()
        assert destination.View_cls is SeedEncryptedQRReviewEncryptionKeyView and destination.view_args['encryption_key']==text
        buttons.load(['KEY_UP']*6+['KEY_PRESS']);destination=SeedEncryptedQRTypeEncryptionKeyView(seed,encryption_key=text).run()
        assert destination.View_cls is SeedEncryptedQRTypeEncryptionKeyExitDialogView
        buttons.load(['KEY_DOWN']*12+['KEY_PRESS']);destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is BackStackView
        buttons.load(['KEY3']);destination=SeedEncryptedQRMnemonicIDEntryView(encryption_key=text,i_vector=None,seed=seed,custom_id='  public id  ').run()
        assert destination.View_cls is SeedEncryptedQRReviewMnemonicIDView and destination.view_args['mnemonic_id']=='  public id  '
        buttons.load(['KEY_UP']*6+['KEY_PRESS']);destination=SeedEncryptedQRMnemonicIDEntryView(encryption_key=text,i_vector=None,seed=seed,custom_id='public').run()
        assert destination.View_cls is SeedEncryptedQRMnemonicIDEntryExitDialogView
        buttons.load(['KEY_DOWN']*12+['KEY_PRESS']);destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is BackStackView
        assert seed.mnemonic_list==['abandon']*11+['about']
        print(json.dumps(dict(passed=True,checks=checks,originalEntryViewsAndDiscard=True,seedUnchanged=True,physicalDisplay=hardware is not None,physicalButtons=False,dependencyInitializationInjected=True,cryptoExecuted=False,reviewScreensQualified=False)))
    finally:
        seed.wipe();View._initialize=original_initialize;restore();runtime.close()
        if hardware is not None:hardware.close()
