"""Original Settings Views/model + real native LVGL/input, without GPIO.

Only View dependency initialization is substituted. Settings persistence is
redirected to a fresh temporary path. No View.run decisions or model mutations
are stubbed. Key plans travel through the actual Runtime debounce/native keypad.
"""
import json
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
from runtime import Runtime,install_view_dispatch
from seedsigner.views.view import View
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.views.settings_views import SettingsMenuView,SettingsEntryUpdateSelectionView

class Buttons:
    def load(self,keys):self.keys=keys;self.start=None
    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        elapsed=now-self.start-.15
        if elapsed<0:return set()
        index=int(elapsed/.20)
        if index>=len(self.keys):
            if elapsed>len(self.keys)*.20+5:raise TimeoutError('Scripted navigation did not finish')
            return set()
        return {self.keys[index]} if elapsed%(.20)<.10 else set()

buttons=Buttons();rectangles=0
def sink(*args):
    global rectangles
    rectangles+=1
root=Path(sys.argv[2]).resolve()
# Importing definitions does not initialize Settings; replace its path first.
with tempfile.TemporaryDirectory(prefix='lvgl-settings-test-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json')
    settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__NETWORK,C.MAINNET,save=False)
    before=settings.get_value(C.SETTING__NETWORK)
    original_initialize=View._initialize
    def initialize(view):
        view.controller=SimpleNamespace()
        view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240
        view.screen=None
        view._redirect=None
    View._initialize=initialize
    hardware=None
    if '--display' in sys.argv:
        from luckfox import LuckfoxHardware
        hardware=LuckfoxHardware()
    def output(area,data):
        sink(area,data)
        if hardware is not None:hardware.pixels(area,data)
    runtime=Runtime(sys.argv[1],output,buttons)
    uninstall=install_view_dispatch(runtime,root,Path(__file__).parent/'source-guards.json')
    steps=[]
    try:
        entries=__import__('seedsigner.models.settings_definition',fromlist=['SettingsDefinition']).SettingsDefinition.get_settings_entries(visibility=C.VISIBILITY__ADVANCED)
        index=next(i for i,e in enumerate(entries) if e.attr_name==C.SETTING__NETWORK)
        buttons.load(['KEY_DOWN']*index+['KEY_PRESS'])
        destination=SettingsMenuView(visibility=C.VISIBILITY__ADVANCED).run()
        assert destination.View_cls is SettingsEntryUpdateSelectionView
        assert destination.view_args['attr_name']==C.SETTING__NETWORK
        assert destination.view_args['parent_initial_scroll']>=0
        steps.append('advanced-menu-select-network')
        buttons.load(['KEY_DOWN','KEY_PRESS'])
        destination=destination.View_cls(**destination.view_args).run()
        assert settings.get_value(C.SETTING__NETWORK)==C.TESTNET
        steps.append('network-change-model-to-testnet')
        buttons.load(['KEY_LEFT','KEY_PRESS'])
        destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is SettingsMenuView
        assert destination.view_args['selected_attr']==C.SETTING__NETWORK
        steps.append('selection-back-restores-parent')
        buttons.load(['KEY_LEFT','KEY_PRESS'])
        destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is SettingsMenuView
        steps.append('advanced-back-to-general')
        # A selected row below the original 32-item bound must remain reachable
        # and return its actual scroll offset through view.screen.buttons[0].
        target=next(e for e in reversed(entries) if e.selection_options and e.type!=C.TYPE__FREE_ENTRY)
        buttons.load(['KEY_PRESS'])
        destination=SettingsMenuView(visibility=C.VISIBILITY__ADVANCED,selected_attr=target.attr_name).run()
        assert destination.View_cls is SettingsEntryUpdateSelectionView
        saved_scroll=destination.view_args['parent_initial_scroll']
        assert saved_scroll>0, saved_scroll
        steps.append('deep-row-selection-preserves-scroll')
        buttons.load(['KEY_LEFT','KEY_PRESS'])
        destination=destination.View_cls(**destination.view_args).run()
        assert destination.view_args['initial_scroll']==saved_scroll
        assert destination.view_args['selected_attr']==target.attr_name
        steps.append('deep-row-back-restores-offset-and-selection')
        assert not Path(Settings.SETTINGS_FILENAME).exists()
        print(json.dumps(dict(passed=True,steps=steps,rectangles=rectangles,originalViewsAndModel=True,nativeKeypad=True,physicalDisplay=hardware is not None,physicalButtons=False,persistentSettingsWritten=False,initialNetwork=before)))
    finally:
        uninstall();runtime.close();View._initialize=original_initialize
        if hardware is not None:hardware.close()
