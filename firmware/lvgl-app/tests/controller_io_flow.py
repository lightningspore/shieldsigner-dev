"""Real Controller I/O buttons -> physical capture/clear/reopen/exit -> Settings."""
import json,os,sys,tempfile,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
from runtime import Runtime,install_view_dispatch
from renderer_bridge import install as install_renderer
from luckfox import LuckfoxHardware
from seedsigner.gui.renderer import Renderer
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.views.view import View,Destination
from diagnostic_scope import attribute
import entropy_camera
with tempfile.TemporaryDirectory(prefix='lvgl-io-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__DISABLED,save=False)
    hardware=LuckfoxHardware();state={'start':None,'phase':None,'since':0};streams=[];requests=[];seen=[]
    def keys():
        now=time.monotonic()
        if state['start'] is None:state['start']=now
        elapsed=now-state['start']-.3
        if elapsed<0:return set()
        if elapsed>60:raise TimeoutError('I/O flow stalled')
        if elapsed<1.5:
            index=int(elapsed/.3);return {['KEY_UP','KEY_DOWN','KEY_LEFT','KEY_RIGHT','KEY_PRESS'][index]} if elapsed%.3<.15 else set()
        stats=runtime.io_stats
        if stats['failures']:raise RuntimeError('I/O physical capture failed')
        phase=(stats['captures'],stats['clears'])
        if phase!=state['phase']:state.update(phase=phase,since=now);return set()
        if now-state['since']<.2:return set()
        if phase==(0,0):return {'KEY1'}
        if phase==(1,0):return {'KEY2'}
        if phase==(1,1):return {'KEY1'}
        if phase==(2,1):return {'KEY3'}
        raise AssertionError('Unexpected I/O state '+str(phase))
    runtime=Runtime(sys.argv[1],hardware.pixels,keys,activity_sink=hardware.buttons.update_last_input_time)
    restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
    restore_renderer=install_renderer(runtime,hardware,Renderer)
    from startup_policy import install as install_startup
    install_startup('/opt/src','/usr/lib/shieldsigner-camera/python')
    from seedsigner.controller import Controller,StopFlowBasedTest,FlowBasedTestException
    from seedsigner.views.settings_views import IOTestView
    original_initialize=View._initialize;original_start=entropy_camera.start;original_run=runtime.run
    controller=None
    def start(camera,**kwargs):
        value=original_start(camera,**kwargs);streams.append(camera._video_stream);requests.append(kwargs);return value
    def run(screen,args):
        seen.append(screen.__name__)
        if screen.__name__=='ButtonListScreen':raise StopFlowBasedTest()
        if screen.__name__!='IOTestScreen':raise FlowBasedTestException('Unexpected I/O destination')
        return original_run(screen,args)
    runtime.run=run
    try:
        controller=Controller.get_instance();controller.boot_failover_cleared=True
        with attribute(entropy_camera,'start',start):controller.start(initial_destination=Destination(IOTestView),skip_startup_interstitials=True)
        assert seen==['IOTestScreen','ButtonListScreen'],seen
        assert View._initialize is original_initialize
        assert runtime.io_stats==dict(captures=2,clears=1,profiles=2,failures=0,exited=True),runtime.io_stats
        assert len(streams)==2 and all(stream.is_stopped and stream.owner_exit_code==0 and stream.frames_received>0 for stream in streams)
        dma=Path('/sys/kernel/debug/dma_buf/bufinfo').read_text().splitlines()[-1];assert dma=='Total 0 objects, 0 bytes',dma
        for thread in (controller.wipe_timer_thread,controller.rng_monitor_thread):thread.join(3);assert not thread.is_alive()
        print(json.dumps(dict(passed=True,originalController=True,originalViewInitialization=True,screenSequence=seen,ioStats=runtime.io_stats,requestedProfiles=requests,cameraFramesReceived=[stream.frames_received for stream in streams],ownerExitCodes=[stream.owner_exit_code for stream in streams],dma=dma,physicalCamera=True,physicalDisplay=True,physicalButtons=False,pixelsSaved=False)),flush=True)
    finally:
        if controller is not None:
            for thread in (controller.wipe_timer_thread,controller.rng_monitor_thread):thread.stop();thread.join(3)
        restore_renderer();restore();runtime.close();hardware.close()
