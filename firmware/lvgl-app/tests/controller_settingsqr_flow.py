"""Original Controller SettingsQR review/apply and Home return, public fixture.

Startup interstitials are explicitly skipped; no claim of full startup parity.
Only rendering and scripted input are substituted. No View initialization or
Controller methods/models/health-worker methods are replaced.
"""
import json,sys,tempfile,time,os
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
    controller=None;seen=[];home_count=0;snapshots=[];source_scope=None;scan_source=None
    original_clear=runtime.clear
    def clear():
        if '--startup' in sys.argv and seen and seen[-1]=='OpeningSplashScreen':
            Path('/tmp/lvgl-public-startup.rgb565').write_bytes(public_frame)
        return original_clear()
    runtime.clear=clear
    original_run=runtime.run
    settings.set_value(C.SETTING__BTC_DENOMINATION,C.BTC_DENOMINATION__BTC,save=False)
    baseline=settings._data.copy();apply='--cancel' not in sys.argv
    def run(screen,args):
        name=screen.__name__;seen.append(name)
        snapshots.append(dict(screen=name,python=process_snapshot(os.getpid()),native=process_snapshot(runtime.host.child.pid)))
        if name=='ScanScreen':buttons.load([])
        elif name=='SettingsQRReviewScreen':
            assert settings._data==baseline
            buttons.load(['KEY_PRESS'] if apply else ['KEY_DOWN','KEY_PRESS'])
        elif name=='SettingsQRConfirmationScreen':
            assert apply and settings.get_value(C.SETTING__BTC_DENOMINATION)==C.BTC_DENOMINATION__SATS
            buttons.load(['KEY_PRESS'])
        elif name=='MainMenuScreen':raise StopFlowBasedTest()
        else:raise FlowBasedTestException('Unexpected SettingsQR Controller screen '+name)
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
        from seedsigner.views.settings_views import SettingsIngestSettingsQRView
        from seedsigner.views.view import Destination
        payload='settings::v1 name=Public_Café denom=sats'
        initial=Destination(SettingsIngestSettingsQRView,view_args=dict(data=payload))
        if '--scan' in sys.argv:
            from synthetic_frames import Source
            from diagnostic_scope import attribute
            import shieldsigner_native_stream
            from seedsigner.views.scan_views import ScanView
            scan_source=Source([payload.encode()])
            source_scope=attribute(shieldsigner_native_stream,'NativeVideoStream',lambda **kwargs:scan_source);source_scope.__enter__()
            initial=Destination(ScanView)
        controller.start(initial_destination=initial,skip_startup_interstitials=True)
        assert View._initialize is original_initialize
        expected=['SettingsQRReviewScreen','SettingsQRConfirmationScreen','MainMenuScreen'] if apply else ['SettingsQRReviewScreen','MainMenuScreen']
        if '--scan' in sys.argv:
            expected=['ScanScreen']+expected
            assert scan_source.is_stopped and runtime.camera_stats['cameraStopped']
            assert runtime.camera_stats['qr']['lastExitCode']==0
        assert seen==expected,seen
        if not apply:assert settings._data==baseline
        else:assert settings.get_value(C.SETTING__BTC_DENOMINATION)==C.BTC_DENOMINATION__SATS
        assert hardware.buttons.last_input_time>activity_before
        assert controller.storage.num_seeds()==0
        assert controller.storage2 is not None
        for thread in (controller.wipe_timer_thread,controller.rng_monitor_thread):
            thread.join(3);assert not thread.is_alive()
        assert not Path(Settings.SETTINGS_FILENAME).exists()
        print(json.dumps(dict(passed=True,apply=apply,unchangedBeforeApply=True,opticalScanQualified=False,syntheticNativeScan=('--scan' in sys.argv),cameraCleanup=getattr(runtime,'camera_stats',None),originalController=True,originalViewInitialization=True,screenSequence=seen,nativeRendererNoPILCanvas=True,activityTimerUpdated=True,resourceSnapshots=snapshots,resourceComparison=False,mandatoryStoragesInitialized=True,wipeAndRngWorkersStartedAndStopped=True,startupInterstitialsSkipped=('--startup' not in sys.argv),smallRamPolicyEnabled=('--small-ram' in sys.argv),physicalDisplay=True,physicalButtons=False,persistentSettingsWritten=False)))
    finally:
        if controller is not None:
            for thread in (controller.wipe_timer_thread,controller.rng_monitor_thread):
                if thread is not None:thread.stop();thread.join(3)
        if source_scope is not None:source_scope.__exit__(None,None,None)
        restore_renderer();restore();runtime.close();hardware.close()
