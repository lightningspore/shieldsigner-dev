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
import os
os.environ['SHIELDSIGNER_SMALL_RAM']='1'
from seedsigner.views.tools_views import ToolsBatteryCalibrationView
from seedsigner.views.view import BackStackView
from seedsigner.hardware.battery_hat import BatteryHat
from seedsigner.hardware.microsd import MicroSD
from diagnostic_scope import attribute
import entropy_camera
original_initialize=View._initialize;original_run=runtime.run;streams=[];requests=[];steps=[];seen=[]
original_start=entropy_camera.start
with tempfile.TemporaryDirectory(prefix='lvgl-calibration-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    log_path=Path(temporary)/'public-discharge.csv';mode=['running']
    fixture=SimpleNamespace(is_enabled=lambda:True,process_discharge_log=lambda **kwargs:steps.append(kwargs),get_discharge_log_path=lambda:log_path,get_voltage=lambda:3.7,get_current=lambda:-100)
    def initialize(view):
        view.controller=SimpleNamespace();view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    def start(camera,**kwargs):
        result=original_start(camera,**kwargs);streams.append(camera._video_stream);requests.append(kwargs);return result
    def run(screen,args):
        name=screen.__name__;seen.append(name);runtime.read_buttons=buttons
        if name=='ToolsBatteryCalibrationIntroScreen':buttons.load(['KEY_UP']*6+['KEY_PRESS'] if mode[0]=='intro-back' else ['KEY_PRESS'])
        elif name=='ToolsBatteryCalibrationStartScreen':buttons.load(['KEY_UP']*6+['KEY_PRESS'] if mode[0]=='start-back' else ['KEY_PRESS'])
        elif name=='ToolsBatteryCalibrationRunningScreen':
            began=time.monotonic()
            def keys():
                if time.monotonic()-began>45:raise TimeoutError('Calibration did not update')
                return {'KEY_PRESS'} if getattr(runtime,'calibration_stats',{}).get('displayUpdates',0)>=2 and streams and streams[-1].frames_received>0 else set()
            runtime.read_buttons=keys
        else:raise AssertionError('Unexpected calibration screen '+name)
        return original_run(screen,args)
    runtime.run=run
    try:
        with attribute(BatteryHat,'get_instance',classmethod(lambda cls:fixture)),attribute(MicroSD,'get_instance',classmethod(lambda cls:SimpleNamespace(is_inserted=True,has_persistent_storage=False))),attribute(entropy_camera,'start',start):
            destination=ToolsBatteryCalibrationView().run()
            assert destination.View_cls is BackStackView
            assert len(streams)==1 and streams[0].is_stopped and streams[0].owner_exit_code==0
            assert requests==[dict(resolution=(320,240),framerate=30,format='rgb')]
            assert not log_path.exists() and steps==[dict(step=5)]
            dma=Path('/sys/kernel/debug/dma_buf/bufinfo').read_text().splitlines()[-1];assert dma=='Total 0 objects, 0 bytes',dma
            for value in ('intro-back','start-back'):
                mode[0]=value;destination=ToolsBatteryCalibrationView().run()
                assert destination.View_cls is BackStackView and len(streams)==1
        print(json.dumps(dict(passed=True,screenSequence=seen,displayUpdates=runtime.calibration_stats['displayUpdates'],originalCalibrationViewAndLoop=True,temporaryLogRemovedOnCancel=True,introAndStartBackWithoutCamera=True,requestedCameraArgumentsPreserved=True,physicalCamera=True,cameraOwnerExitCode=0,cameraFramesReceived=streams[0].frames_received,dma=dma,batteryAndCardMetadataInjected=True,dependencyInitializationInjected=True,physicalDisplay=hardware is not None,physicalButtons=False,dischargeCompletionQualified=False,chargingAbortHardwareQualified=False)),flush=True)
    finally:
        View._initialize=original_initialize;runtime.run=original_run;restore();runtime.close()
        if hardware is not None:hardware.close()
