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
from seedsigner.views.tools_views import ToolsTextQRTextEntryView,ToolsTextQRReviewTextView,ToolsTextQRTextEntryExitDialogView,ToolsTextQRTranscribeModePromptView,ToolsTextQRTranscribeModeView,ToolsTranscribeTextQRZoomedInView,ToolsTranscribeTextQRConfirmQRPromptView
from seedsigner.views.tools_views import ToolsTextQRView
from seedsigner.gui.screens.tools_screens import ToolsTextQRTextEntryScreen
from seedsigner.views.view import BackStackView
original_initialize=View._initialize;checks=[]
with tempfile.TemporaryDirectory(prefix='lvgl-textqr-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    def initialize(view):
        view.controller=SimpleNamespace();view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    def choose(index,count):buttons.load(['KEY_DOWN']*16+['KEY_UP']*(count-1-index)+['KEY_PRESS'])
    try:
        fixtures=['','  public  ','café e\u0301','line\r\nnext']
        for text in fixtures:
            buttons.load(['KEY3']);answer=ToolsTextQRTextEntryScreen(textToEncode=text).display()
            assert answer=={'textToEncode':text}
        text='  public café  ';buttons.load(['KEY_UP']*6+['KEY_PRESS'])
        answer=ToolsTextQRTextEntryScreen(textToEncode=text).display()
        assert answer=={'textToEncode':text,'is_back_button':True}
        buttons.load(['KEY_UP']*6+['KEY_PRESS']);destination=ToolsTextQRTextEntryView(textToEncode=text).run()
        assert destination.View_cls is ToolsTextQRTextEntryExitDialogView
        choose(1,2);destination=destination.View_cls(**destination.view_args).run();assert destination.View_cls is BackStackView
        raw='Public '+chr(92)+'u0041';text='Public A'
        buttons.load(['KEY3']);destination=ToolsTextQRTextEntryView(textToEncode=raw).run()
        assert destination.View_cls is ToolsTextQRReviewTextView and destination.view_args['text']==text
        choose(0,2);destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is ToolsTextQRTranscribeModePromptView
        choose(0,2);destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is ToolsTextQRTranscribeModeView
        choose(0,1);destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is ToolsTranscribeTextQRZoomedInView
        buttons.load(['KEY_RIGHT','KEY_DOWN','KEY_PRESS']);destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is ToolsTranscribeTextQRConfirmQRPromptView
        choose(1,2);destination=destination.View_cls(**destination.view_args).run()
        assert destination.View_cls is ToolsTextQRView and destination.clear_history
        print(json.dumps(dict(passed=True,exactSaveFixtures=len(fixtures),backTextExact=True,originalEscapeParsing=True,originalViews=True,transcriptionRouteReturnedToTextQR=True,dependencyInitializationInjected=True,physicalDisplay=hardware is not None,physicalButtons=False,opticalConfirmationQualified=False,fullscreenQualified=False)),flush=True)
    finally:
        View._initialize=original_initialize;restore();runtime.close()
        if hardware is not None:hardware.close()
