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
from seedsigner.gui.screens.screen import ResetScreen,RebootToLoaderScreen,LargeButtonScreen,ButtonOption,MainMenuScreen,RET_CODE__REBOOT_TO_LOADER
from seedsigner.views.view import PowerOffView,BackStackView
original_initialize=View._initialize;checks=[]
class PresentationDone(Exception):pass
with tempfile.TemporaryDirectory(prefix='lvgl-power-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    def initialize(view):
        view.controller=SimpleNamespace();view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    try:
        for cls in (ResetScreen,RebootToLoaderScreen):
            started=[None];before=rectangles
            def hold():
                if started[0] is None:started[0]=time.monotonic()
                if time.monotonic()-started[0]>.8:raise PresentationDone()
                return set()
            runtime.read_buttons=hold
            try:cls().display();raise AssertionError('Noninteractive screen returned')
            except PresentationDone:pass
            assert rectangles>before
            checks.append(dict(screen=cls.__name__,rendered=True,systemActionInvoked=False))
            runtime.clear()
        runtime.read_buttons=buttons
        for count,keys,expected in [(2,['KEY_RIGHT','KEY_PRESS'],1),(4,['KEY_DOWN','KEY_RIGHT','KEY_PRESS'],3),(4,['KEY_LEFT','KEY_PRESS'],1000)]:
            buttons.load(keys)
            value=LargeButtonScreen(title='Public grid',button_data=[ButtonOption('Tile '+str(i)) for i in range(count)],show_back_button=True).display()
            assert value==expected,(count,keys,value)
            checks.append(dict(screen='LargeButtonScreen',buttons=count,result=value,systemActionInvoked=False))
        for cls,count,duration,expected in [(LargeButtonScreen,2,.3,0),(LargeButtonScreen,2,5.3,RET_CODE__REBOOT_TO_LOADER),(MainMenuScreen,4,.3,0),(MainMenuScreen,4,5.3,RET_CODE__REBOOT_TO_LOADER)]:
            began=[None]
            def hold_key():
                if began[0] is None:began[0]=time.monotonic()
                elapsed=time.monotonic()-began[0]
                if elapsed>duration+4:raise TimeoutError('Hold did not finish')
                return {'KEY3'} if .5<=elapsed<.5+duration else set()
            runtime.read_buttons=hold_key
            kwargs=dict(title='Public hold',button_data=[ButtonOption('Tile '+str(i)) for i in range(count)])
            if cls is LargeButtonScreen:kwargs.update(long_press_key='KEY3',long_press_ms=5000,long_press_ret_code=RET_CODE__REBOOT_TO_LOADER)
            value=cls(**kwargs).display()
            assert value==expected,(cls.__name__,duration,value)
            checks.append(dict(screen=cls.__name__,holdSeconds=duration,result=value,systemActionInvoked=False))
        runtime.configure_screensaver(600)
        began=[None];shown=[False];woke=[False];hold_start=[None]
        def wake_hold():
            if began[0] is None:began[0]=time.monotonic()
            now=time.monotonic();elapsed=now-began[0]
            if runtime.host.screensaver_active and hold_start[0] is None:hold_start[0]=now
            if hold_start[0] is not None:
                held=now-hold_start[0]
                if held<5.3:return {'KEY3'}
                if not runtime.host.screensaver_active:woke[0]=True
                if 5.8<=held<6.1:return {'KEY_PRESS'}
            if elapsed>12:raise TimeoutError('Wake hold did not finish; saver observed='+str(hold_start[0] is not None))
            return set()
        runtime.read_buttons=wake_hold
        value=MainMenuScreen(title='Public wake',button_data=[ButtonOption('Tile '+str(i)) for i in range(4)]).display()
        assert value==0 and woke[0] and hold_start[0] is not None and time.monotonic()-hold_start[0]>=5.8,(value,woke[0],hold_start[0],time.monotonic()-began[0])
        checks.append(dict(screen='MainMenuScreen',wakeHoldConsumed=True,freshTapSelected=True,systemActionInvoked=False))
        runtime.configure_screensaver(0)
        runtime.read_buttons=buttons;buttons.load(['KEY_PRESS'])
        destination=PowerOffView().run()
        assert destination.View_cls is BackStackView
        assert not Path(Settings.SETTINGS_FILENAME).exists()
        print(json.dumps(dict(passed=True,checks=checks,originalPowerOffViewReturnedBack=True,dependencyInitializationInjected=True,restartExecuted=False,loaderRebootExecuted=False,physicalDisplay=hardware is not None,physicalButtons=False)),flush=True)
    finally:
        View._initialize=original_initialize;restore();runtime.close()
        if hardware is not None:hardware.close()
