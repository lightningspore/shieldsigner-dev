"""Real Controller/RNG workers and camera entropy acquisition; scripted public test."""
import json,sys,tempfile,time,os
from resources import process_snapshot,system_snapshot
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
    periodic=[];last_sample=[0]
    def sample(stage):
        periodic.append(dict(stage=stage,seconds=round(time.monotonic(),3),python=process_snapshot(os.getpid()),native=process_snapshot(runtime.host.child.pid),system=system_snapshot()))
    def pixels(area,data):
        x1,y1,x2,y2=area;stride=(x2-x1+1)*2
        for row,y in enumerate(range(y1,y2+1)):public_frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
        hardware.pixels(area,data)
        now=time.monotonic()
        if now-last_sample[0]>3 and len(periodic)<20:
            last_sample[0]=now;sample('pixels')
    runtime=Runtime(sys.argv[1],pixels,buttons,activity_sink=hardware.buttons.update_last_input_time)
    restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
    restore_renderer=install_renderer(runtime,hardware,Renderer)
    import entropy_camera,gc
    from diagnostic_scope import attribute
    original_camera_start=entropy_camera.start
    collections=[];camera_backends=[];streams=[]
    def camera_start(camera):
        sample('before-camera-start')
        if '--collect-before-camera' in sys.argv:
            began=time.monotonic();count=gc.collect()
            collections.append(dict(objects=count,seconds=round(time.monotonic()-began,3)))
            sample('after-collection')
        result=original_camera_start(camera)
        assert camera._video_stream.transport=='nv12',camera._video_stream.transport
        camera_backends.append(dict(transport=camera._video_stream.transport,backend=camera._video_stream.backend_info))
        streams.append(camera._video_stream)
        return result
    camera_scope=attribute(entropy_camera,'start',camera_start);camera_scope.__enter__()
    sample_scope=None
    if '--sample-luma' in sys.argv:
        import image_entropy
        from experimental_entropy_samples import sample as luma_sample
        original_acquisition=image_entropy.acquisition_method
        def acquisition(source,namespace):
            before='entropy_frame: Image = self.camera.read_video_stream(as_image=True)'
            if source.count(before)!=1:raise ValueError('Unexpected sample read boundary')
            source=source.replace(before,'entropy_frame: Image = _lvgl_luma_sample(self.camera)')
            return original_acquisition(source,dict(namespace,_lvgl_luma_sample=luma_sample))
        sample_scope=attribute(image_entropy,'acquisition_method',acquisition);sample_scope.__enter__()
    original_initialize=View._initialize
    controller=None;seen=[];home_count=0;snapshots=[]
    original_clear=runtime.clear
    def clear():
        if '--startup' in sys.argv and seen and seen[-1]=='OpeningSplashScreen':
            Path('/tmp/lvgl-public-startup.rgb565').write_bytes(public_frame)
        return original_clear()
    runtime.clear=clear
    original_run=runtime.run
    active={'screen':None,'ready':None,'began':time.monotonic()}
    def keys():
        if time.monotonic()-active['began']>90:raise TimeoutError('Controller entropy stalled')
        if active['screen']=='ToolsImageEntropyLivePreviewScreen':
            stats=getattr(runtime,'entropy_stats',{})
            if '--cancel' in sys.argv:return {'KEY_LEFT'} if stats.get('previewFrames',0)>=3 else set()
            if stats.get('poolFrames')==5:
                if active['ready'] is None:active['ready']=stats['previewFrames']
                if stats['previewFrames']>active['ready']:return {'KEY_PRESS'}
            return set()
        return buttons()
    runtime.read_buttons=keys
    def run(screen,args):
        name=screen.__name__;seen.append(name);active['screen']=name
        snapshots.append(dict(screen=name,python=process_snapshot(os.getpid()),native=process_snapshot(runtime.host.child.pid)))
        if name=='MainMenuScreen':raise StopFlowBasedTest()
        if name=='ToolsImageEntropyFinalImageScreen':buttons.load(['KEY_PRESS'])
        elif name=='ButtonListScreen':
            if '--generate' in sys.argv:buttons.load(['KEY_PRESS'])
            else:raise StopFlowBasedTest()
        elif '--generate' in sys.argv and name in ('DireWarningScreen','SeedWordsScreen'):raise StopFlowBasedTest()
        elif name!='ToolsImageEntropyLivePreviewScreen':raise FlowBasedTestException('Unexpected entropy screen '+name)
        return original_run(screen,args)
    runtime.run=run
    try:
        from seedsigner.controller import Controller,StopFlowBasedTest,FlowBasedTestException
        if '--small-ram' in sys.argv:
            from startup_policy import install as install_startup
            install_startup('/opt/src','/usr/lib/shieldsigner-camera/python')
        sample('before-controller')
        controller=Controller.get_instance()
        sample('after-controller')
        controller.boot_failover_cleared=True # Test must not touch boot-counter MMIO.
        assert controller.wipe_timer_thread.is_alive() and controller.rng_monitor_thread.is_alive()
        assert Renderer.get_instance().canvas is None and Renderer.get_instance().draw is None
        activity_before=hardware.buttons.last_input_time
        from seedsigner.views.tools_views import ToolsImageEntropyLivePreviewView
        from seedsigner.views.view import Destination
        assert controller.hardware_rng_is_healthy,controller.hardware_rng_failure_reason
        controller.start(initial_destination=Destination(ToolsImageEntropyLivePreviewView),skip_startup_interstitials=True)
        assert View._initialize is original_initialize
        expected=['ToolsImageEntropyLivePreviewScreen','MainMenuScreen'] if '--cancel' in sys.argv else ['ToolsImageEntropyLivePreviewScreen','ToolsImageEntropyFinalImageScreen','ButtonListScreen']
        if '--generate' in sys.argv:
            assert seen[:3]==expected and seen[3:] in (['DireWarningScreen'],['SeedWordsScreen']),seen
            pending=controller.storage.get_pending_seed();assert pending is not None
            assert len(pending.mnemonic_list)==12 and pending.seed_bytes and any(pending.seed_bytes)
            buffer=pending.seed_bytes
            assert controller.image_entropy_preview_frames is None and controller.image_entropy_final_image is None
            controller.storage.clear_pending_seed()
            assert not any(buffer) and pending.seed_bytes is None and not pending.mnemonic_list
            assert controller.storage.get_pending_seed() is None
        else:assert seen==expected,seen
        assert hardware.buttons.last_input_time>activity_before
        assert controller.storage.num_seeds()==0
        assert controller.storage2 is not None
        for thread in (controller.wipe_timer_thread,controller.rng_monitor_thread):
            thread.join(3);assert not thread.is_alive()
        assert not Path(Settings.SETTINGS_FILENAME).exists()
        dma=Path('/sys/kernel/debug/dma_buf/bufinfo').read_text().splitlines()[-1]
        assert dma=='Total 0 objects, 0 bytes',dma
        assert streams and all(stream.is_stopped and stream.owner_exit_code==0 for stream in streams)
        print(json.dumps(dict(passed=True,realRngHealthGate=True,rngHealthy=controller.hardware_rng_is_healthy,entropyStats=runtime.entropy_stats,dma=dma,fullMixerQualified=('--generate' in sys.argv),pendingSeedCreatedAndWiped=('--generate' in sys.argv),lumaSampleExperiment=('--sample-luma' in sys.argv),originalController=True,originalViewInitialization=True,screenSequence=seen,nativeRendererNoPILCanvas=True,activityTimerUpdated=True,resourceSnapshots=snapshots,resourceSamples=periodic,preCameraCollections=collections,cameraBackends=camera_backends,resourceComparison=False,mandatoryStoragesInitialized=True,wipeAndRngWorkersStartedAndStopped=True,startupInterstitialsSkipped=('--startup' not in sys.argv),smallRamPolicyEnabled=('--small-ram' in sys.argv),physicalDisplay=True,physicalButtons=False,persistentSettingsWritten=False)))
    except BaseException:
        print(json.dumps(dict(stage='controller-entropy-failure',screenSequence=seen,entropyStats=getattr(runtime,'entropy_stats',{}),resourceSamples=periodic,preCameraCollections=collections,cameraBackends=camera_backends)),flush=True)
        raise
    finally:
        if controller is not None:
            controller.storage.clear_pending_seed()
            for thread in (controller.wipe_timer_thread,controller.rng_monitor_thread):
                if thread is not None:thread.stop();thread.join(3)
        if sample_scope is not None:sample_scope.__exit__(None,None,None)
        camera_scope.__exit__(None,None,None);restore_renderer();restore();runtime.close();hardware.close()
