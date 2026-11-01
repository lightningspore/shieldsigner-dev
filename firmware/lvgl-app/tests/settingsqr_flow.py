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
from seedsigner.views.settings_views import SettingsIngestSettingsQRView
from seedsigner.views.view import MainMenuView
original_initialize=View._initialize;original_run=runtime.run;checks=[];seen=[]
with tempfile.TemporaryDirectory(prefix='lvgl-settingsqr-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    controller=SimpleNamespace(settings=settings)
    def initialize(view):
        view.controller=controller;view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    try:
        for apply in (False,True):
            settings.set_value(C.SETTING__BTC_DENOMINATION,C.BTC_DENOMINATION__BTC,save=False)
            before=settings._data.copy();seen=[]
            view=SettingsIngestSettingsQRView('settings::v1 name=Public_Café denom=sats')
            assert settings._data==before
            def run(screen,args):
                seen.append(screen.__name__)
                if screen.__name__=='SettingsQRReviewScreen':
                    assert settings._data==before
                    buttons.load(['KEY_PRESS'] if apply else ['KEY_DOWN','KEY_PRESS'])
                elif screen.__name__=='SettingsQRConfirmationScreen':
                    assert apply and settings.get_value(C.SETTING__BTC_DENOMINATION)==C.BTC_DENOMINATION__SATS
                    buttons.load(['KEY_PRESS'])
                else:raise AssertionError('Unexpected SettingsQR screen '+screen.__name__)
                return original_run(screen,args)
            runtime.run=run
            destination=view.run();assert destination.View_cls is MainMenuView
            assert seen==(['SettingsQRReviewScreen','SettingsQRConfirmationScreen'] if apply else ['SettingsQRReviewScreen'])
            if not apply:assert settings._data==before
            else:assert settings.get_value(C.SETTING__BTC_DENOMINATION)==C.BTC_DENOMINATION__SATS
            assert not Path(Settings.SETTINGS_FILENAME).exists()
            checks.append(dict(apply=apply,screenSequence=seen,unchangedUntilApply=True,returnedHome=True,persistentFileWritten=False))
        print(json.dumps(dict(passed=True,checks=checks,originalParserAndApply=True,dependencyInitializationInjected=True,physicalDisplay=hardware is not None,physicalButtons=False,opticalScanQualified=False)),flush=True)
    finally:
        runtime.run=original_run;View._initialize=original_initialize;restore();runtime.close()
        if hardware is not None:hardware.close()
