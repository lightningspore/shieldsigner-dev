"""Original Controller wipe interrupts an LVGL seed screen; public fixture only."""
import json,sys,tempfile,time,threading
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
from runtime import Runtime,install_view_dispatch
from renderer_bridge import install as install_renderer
from lifecycle import install as install_lifecycle
from toast_bridge import install as install_toasts
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.models.seed import Seed
from seedsigner.gui.renderer import Renderer
from seedsigner.gui import toast
from seedsigner.views.view import View,Destination,MainMenuView
from seedsigner.gui.screens.seed_screens import SeedWordsScreen
from seedsigner.gui.screens.screen import ButtonOption
from luckfox import LuckfoxHardware
with tempfile.TemporaryDirectory(prefix='lvgl-wipe-test-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json')
    settings=Settings.get_instance();settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__DISABLED,save=False)
    hardware=LuckfoxHardware();state={'home_since':None,'homes':0};errors=[];timer=None
    def buttons():
        if state.get('active_home') and state['home_since'] is None:state['home_since']=time.monotonic()
        if state['home_since'] is not None:
            elapsed=time.monotonic()-state['home_since']
            if '--home-first' in sys.argv and state['homes']==1:
                if .3<elapsed<.65:return {'KEY_PRESS'}
                if elapsed>10:raise FlowBasedTestException('Home did not enter Scan')
            elif elapsed>1:raise StopFlowBasedTest()
        if '--io' in sys.argv and state.get('active_io') and not state.get('active_home'):
            if state.get('io_since') is None:state['io_since']=time.monotonic();return set()
            elapsed=time.monotonic()-state['io_since']
            if timer is None and elapsed>10:raise FlowBasedTestException('I/O capture press did not start the camera')
            if .3<elapsed<.65:return {'KEY1'}
        return set()
    runtime=Runtime(sys.argv[1],hardware.pixels,buttons,activity_sink=hardware.buttons.update_last_input_time)
    restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
    restore_renderer=install_renderer(runtime,hardware,Renderer)
    restore_toasts=install_toasts(runtime,toast)
    from seedsigner.controller import Controller,StopFlowBasedTest,FlowBasedTestException
    startup_policy=None
    if '--small-ram' in sys.argv:
        from startup_policy import install as install_startup_policy
        startup_policy=install_startup_policy('/opt/src','/usr/lib/shieldsigner-camera/python')
    restore_lifecycle=install_lifecycle(runtime,Controller)
    controller=None;seed=Seed(['abandon']*11+['about']);seed_buffer=seed.seed_bytes;old_child=runtime.host.child
    seen=[];original_run=runtime.run
    def trigger():
        try:
            if '--real-timer' in sys.argv:
                settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__FIVE_MINUTES,save=False)
                hardware.buttons.last_input_time=int(time.time()*1000)-(5*60+1)*1000
            else:controller.handle_wipe_timeout()
        except BaseException as error:errors.append(type(error).__name__)
    def run(screen,args):
        global timer
        seen.append(screen.__name__)
        if screen.__name__ in ('ScanScreen','ToolsImageEntropyLivePreviewScreen','IOTestScreen'):
            state['home_since']=None;state['active_home']=False
            if screen.__name__=='IOTestScreen':state['active_io']=True;state['io_since']=None
        elif screen.__name__=='SeedWordsScreen':
            timer=threading.Timer(.5,trigger);timer.start()
        elif screen.__name__=='MainMenuScreen':
            state['home_since']=None;state['active_home']=True;state['homes']+=1
        else:raise FlowBasedTestException('Unexpected wipe destination '+screen.__name__)
        return original_run(screen,args)
    runtime.run=run
    original_preview=runtime.host.send_preview
    def preview(*args,**kwargs):
        global timer
        value=original_preview(*args,**kwargs)
        if timer is None and ('--entropy' not in sys.argv or getattr(runtime,'entropy_stats',{}).get('poolFrames',0)>=1):
            timer=threading.Timer(.5,trigger);timer.start()
        return value
    runtime.host.send_preview=preview
    import entropy_camera
    from diagnostic_scope import attribute
    streams=[];original_camera_start=entropy_camera.start
    def camera_start(camera,**kwargs):
        global timer
        value=original_camera_start(camera,**kwargs);streams.append(camera._video_stream)
        if '--io' in sys.argv and timer is None:timer=threading.Timer(.5,trigger);timer.start()
        assert streams[-1].transport=='nv12'
        return value
    camera_scope=attribute(entropy_camera,'start',camera_start);camera_scope.__enter__()
    class PublicSensitiveView(View):
        def run(self):
            if '--io' in sys.argv:
                from seedsigner.gui.screens.settings_screens import IOTestScreen
                self.run_screen(IOTestScreen)
            elif '--camera' in sys.argv:
                from seedsigner.gui.screens.scan_screens import ScanScreen
                from seedsigner.models.decode_qr import DecodeQR
                self.run_screen(ScanScreen,decoder=DecodeQR(),instructions_text='Public wipe cleanup test')
            else:self.run_screen(SeedWordsScreen,words=seed.mnemonic_list[:4],page_index=0,num_pages=3,button_data=[ButtonOption('Next')])
            raise AssertionError('Wiped seed screen resumed')
    try:
        controller=Controller.get_instance();controller.boot_failover_cleared=True
        controller.storage.seeds.append(seed)
        initial=Destination(PublicSensitiveView)
        if '--entropy' in sys.argv:
            from seedsigner.views.tools_views import ToolsImageEntropyLivePreviewView
            initial=Destination(ToolsImageEntropyLivePreviewView)
        controller.start(initial_destination=None if '--home-first' in sys.argv else initial,skip_startup_interstitials=True)
        if timer is not None:timer.join(3)
        assert not errors,errors
        assert not hardware.buttons.override_ind
        expected='IOTestScreen' if '--io' in sys.argv else ('ToolsImageEntropyLivePreviewScreen' if '--entropy' in sys.argv else ('ScanScreen' if '--camera' in sys.argv else 'SeedWordsScreen'))
        assert seen==(['MainMenuScreen'] if '--home-first' in sys.argv else [])+[expected,'MainMenuScreen'],seen
        if '--camera' in sys.argv:
            assert runtime.camera_stats['frames']>0
            assert runtime.camera_stats['cameraStopped'] and runtime.camera_stats['ownerExitCode']==0,runtime.camera_stats
        if '--io' in sys.argv:
            assert runtime.io_stats['profiles']==1 and runtime.io_stats['captures']==0,runtime.io_stats
            assert streams and all(stream.is_stopped and stream.owner_exit_code==0 for stream in streams)
            dma=Path('/sys/kernel/debug/dma_buf/bufinfo').read_text().splitlines()[-1];assert dma=='Total 0 objects, 0 bytes',dma
        if '--entropy' in sys.argv:
            assert runtime.entropy_stats['poolFrames']>=1
            assert streams and all(stream.is_stopped and stream.owner_exit_code==0 for stream in streams)
            assert controller.image_entropy_preview_frames is None and controller.image_entropy_final_image is None
            dma=Path('/sys/kernel/debug/dma_buf/bufinfo').read_text().splitlines()[-1]
            assert dma=='Total 0 objects, 0 bytes',dma
        assert controller.storage.num_seeds()==0 and seed.seed_bytes is None and not seed.mnemonic_list
        assert not any(seed_buffer)
        assert old_child.poll() is not None and runtime.host.child.pid!=old_child.pid
        for thread in (controller.wipe_timer_thread,controller.rng_monitor_thread):thread.join(3);assert not thread.is_alive()
        print(json.dumps(dict(passed=True,originalWipePolicy=True,hardwareOverrideConsumed=True,ioCaptureInterrupted=('--io' in sys.argv),ioStats=getattr(runtime,'io_stats',None),entropyInterrupted=('--entropy' in sys.argv),entropyStats=getattr(runtime,'entropy_stats',None),entropyOwnerExitCodes=[stream.owner_exit_code for stream in streams],publicSeedBufferZeroed=True,seedStorageCleared=True,oldNativeProcessReaped=True,newNativeProcess=True,seedViewDidNotResume=True,returnedThroughOriginalController=True,screenSequence=seen,originalWipeTimerTriggerSimulated=('--real-timer' not in sys.argv),originalWipeTimerPolled=('--real-timer' in sys.argv),expiredActivityTimestampInjected=('--real-timer' in sys.argv),smallRamPolicy=startup_policy,homeFirst=('--home-first' in sys.argv),cameraCleanup=getattr(runtime,'camera_stats',None),physicalDisplay=True,physicalButtons=False)))
    finally:
        if timer is not None:timer.cancel();timer.join(3)
        if controller is not None:
            for thread in (controller.wipe_timer_thread,controller.rng_monitor_thread,controller.toast_notification_thread):
                if thread is not None:thread.stop();thread.join(3)
        camera_scope.__exit__(None,None,None);seed.wipe();restore_lifecycle();restore_toasts();restore_renderer();restore();runtime.close();hardware.close()
