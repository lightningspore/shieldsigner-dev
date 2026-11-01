"""Original Controller startup/menu/back-stack with native Renderer, temporary deployment.

Startup interstitials are explicitly skipped; no claim of full startup parity.
Only rendering and scripted input are substituted. No View initialization or
Controller methods/models/health-worker methods are replaced.
"""
import json,sys,tempfile,time,os
from contextlib import ExitStack
from types import SimpleNamespace
from diagnostic_scope import attribute
from resources import process_snapshot
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.gui.renderer import Renderer
from seedsigner.views.view import View
from runtime import Runtime,install_view_dispatch
from renderer_bridge import install as install_renderer
from luckfox import LuckfoxHardware
class Buttons:
    def load(self,keys):self.keys=keys;self.start=None
    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        t=now-self.start-.3
        if t<0:return set()
        i=int(t/.4)
        if i>=len(self.keys):
            if t>len(self.keys)*.4+10:raise TimeoutError('Controller navigation stalled')
            return set()
        return {self.keys[i]} if t%.4<.22 else set()
with tempfile.TemporaryDirectory(prefix='lvgl-controller-test-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json')
    settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__DISABLED,save=False)
    hardware=LuckfoxHardware();buttons=Buttons();public_frame=bytearray(115200)
    def pixels(area,data):
        x1,y1,x2,y2=area;stride=(x2-x1+1)*2
        for row,y in enumerate(range(y1,y2+1)):public_frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
        hardware.pixels(area,data)
    runtime=Runtime(sys.argv[1],pixels,buttons,activity_sink=hardware.buttons.update_last_input_time)
    restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
    restore_renderer=install_renderer(runtime,hardware,Renderer)
    original_initialize=View._initialize
    controller=None;seen=[];home_count=0;snapshots=[]
    original_clear=runtime.clear
    def clear():
        if '--startup' in sys.argv and seen and seen[-1]=='OpeningSplashScreen':
            Path('/tmp/lvgl-public-startup.rgb565').write_bytes(public_frame)
        return original_clear()
    runtime.clear=clear
    fixture_scope=ExitStack();battery_fixture='--home-battery-fixture' in sys.argv
    fixture_samples=[0];captures=[]
    if battery_fixture:
        from seedsigner.hardware.battery_hat import BatteryHat
        def percent():
            fixture_samples[0]+=1
            return (12.8,80.9,None)[min(fixture_samples[0]-1,2)]
        hat=SimpleNamespace(initialize=lambda:False,is_alive=lambda:False,is_enabled=lambda:True,detected=True,get_percent=percent,get_current=lambda:1 if fixture_samples[0]==2 else 0)
        fixture_scope.enter_context(attribute(BatteryHat,'get_instance',classmethod(lambda cls:hat)))
    original_run=runtime.run
    def run(screen,args):
        global home_count
        name=screen.__name__;seen.append(name)
        snapshots.append(dict(screen=name,python=process_snapshot(os.getpid()),native=process_snapshot(runtime.host.child.pid)))
        if name=='OpeningSplashScreen':buttons.load([])
        elif name=='WarningScreen':buttons.load(['KEY_DOWN']*16+['KEY_PRESS'])
        elif name=='MainMenuScreen':
            home_count+=1
            if home_count==2:raise StopFlowBasedTest()
            buttons.load(['KEY_DOWN']*3+['KEY_PRESS'])
            if battery_fixture:
                started=[None]
                def fixture_buttons():
                    if started[0] is None:started[0]=time.monotonic()
                    elapsed=time.monotonic()-started[0]
                    for index,threshold in enumerate((.5,1.5,2.5)):
                        if elapsed>=threshold and index>=len(captures):
                            path='/tmp/lvgl-public-home-battery-'+str(index)+'.rgb565'
                            Path(path).write_bytes(public_frame);captures.append(path)
                    return buttons() if elapsed>3.2 else set()
                runtime.read_buttons=fixture_buttons
        elif name=='ButtonListScreen':
            runtime.read_buttons=buttons;buttons.load(['KEY_UP']*10+['KEY_PRESS'])
        else:raise FlowBasedTestException('Unexpected Controller screen '+name)
        return original_run(screen,args)
    runtime.run=run
    try:
        from seedsigner.controller import Controller,StopFlowBasedTest,FlowBasedTestException
        if '--small-ram' in sys.argv:
            from startup_policy import install as install_startup
            install_startup('/opt/src','/usr/lib/shieldsigner-camera/python')
        controller=Controller.get_instance()
        controller.boot_failover_cleared=True # Test must not touch boot-counter MMIO.
        assert controller.wipe_timer_thread.is_alive() and controller.rng_monitor_thread.is_alive()
        assert Renderer.get_instance().canvas is None and Renderer.get_instance().draw is None
        activity_before=hardware.buttons.last_input_time
        controller.start(skip_startup_interstitials=('--startup' not in sys.argv))
        if '--startup' in sys.argv:assert seen[0]=='OpeningSplashScreen' and 'WarningScreen' in seen
        assert View._initialize is original_initialize
        assert home_count==2
        if battery_fixture:
            assert fixture_samples[0]>=3 and len(captures)==3
            assert runtime.home_battery_stats['updates']>=3

        assert hardware.buttons.last_input_time>activity_before
        assert controller.storage.num_seeds()==0
        assert controller.storage2 is not None
        for thread in (controller.wipe_timer_thread,controller.rng_monitor_thread):
            thread.join(3);assert not thread.is_alive()
        assert not Path(Settings.SETTINGS_FILENAME).exists()
        print(json.dumps(dict(passed=True,batterySensorInjected=battery_fixture,homeBatteryStats=getattr(runtime,'home_battery_stats',None),publicBatteryCaptures=captures,originalController=True,originalViewInitialization=True,screenSequence=seen,nativeRendererNoPILCanvas=True,activityTimerUpdated=True,resourceSnapshots=snapshots,resourceComparison=False,mandatoryStoragesInitialized=True,wipeAndRngWorkersStartedAndStopped=True,startupInterstitialsSkipped=('--startup' not in sys.argv),smallRamPolicyEnabled=('--small-ram' in sys.argv),physicalDisplay=True,physicalButtons=False,persistentSettingsWritten=False)))
    finally:
        if controller is not None:
            for thread in (controller.wipe_timer_thread,controller.rng_monitor_thread):
                if thread is not None:thread.stop();thread.join(3)
        fixture_scope.close();restore_renderer();restore();runtime.close();hardware.close()
