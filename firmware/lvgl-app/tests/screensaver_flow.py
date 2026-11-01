"""Original Views/Controller + native screensaver, accelerated idle test."""
import hashlib,json,sys,tempfile,threading,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src','/usr/lib/shieldsigner-camera/python']
from runtime import Runtime,install_view_dispatch
from renderer_bridge import install as install_renderer
from screensaver_bridge import install as install_saver
from startup_policy import install as install_startup
from luckfox import LuckfoxHardware
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.gui.renderer import Renderer
from seedsigner.gui.screens.screen import ButtonListScreen,ButtonOption
from seedsigner.views.view import View
frame=bytearray(115200);lock=threading.Lock()
with tempfile.TemporaryDirectory(prefix='lvgl-saver-test-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json')
    settings=Settings.get_instance();settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__DISABLED,save=False)
    install_startup('/opt/src','/usr/lib/shieldsigner-camera/python')
    hardware=LuckfoxHardware()
    def pixels(area,data):
        x1,y1,x2,y2=area;stride=(x2-x1+1)*2
        with lock:
            for row,y in enumerate(range(y1,y2+1)):frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
        hardware.pixels(area,data)
    def digest():
        with lock:return hashlib.sha256(frame).digest()
    class Buttons:
        def load(self,mode):self.mode=mode;self.start=None;self.phase='idle';self.entered=False;self.baseline=None;self.restored=False;self.trace=[];self.last_trace=None
        def __call__(self):
            now=time.monotonic()
            if self.start is None:
                controller.screensaver.stop();controller.reset_screensaver_timeout()
                runtime.host.send('overlay_state')
                event=runtime.host.next_event()
                assert event['event']=='overlay_state' and not event['screensaver']
                self.start=time.monotonic()
                return set()
            elapsed=now-self.start
            marker=(self.phase,runtime.host.screensaver_active)
            if marker!=self.last_trace:self.trace.append((round(elapsed,3),*marker));self.last_trace=marker
            if elapsed>8:raise TimeoutError('Screensaver handoff stalled: '+self.phase)
            if self.mode=='disabled':
                assert not runtime.host.screensaver_active
                if elapsed>1.2:self.phase='select';return {'KEY_PRESS'}
                return set()
            if self.phase=='idle':
                if elapsed>.15 and self.baseline is None and not runtime.host.screensaver_active:
                    with lock:self.before=bytes(frame)
                    self.baseline=hashlib.sha256(self.before).digest()
                if self.mode=='explicit' and elapsed>.2 and not self.entered:
                    controller.start_screensaver();self.entered=True
                if runtime.host.screensaver_active and self.baseline is not None:
                    assert controller.is_screensaver_running
                    self.entered=True;self.phase='wake';self.wake=now
                return set()
            if self.phase=='wake':
                if now-self.wake<.4:return {'KEY_PRESS'}
                if runtime.host.screensaver_active:return set()
                self.phase='released';self.released=now
                return set()
            if self.phase=='released':
                if now-self.released<.2:return set()
                self.restored=(digest()==self.baseline)
                if not self.restored:
                    with lock:after=bytes(frame)
                    Path('/tmp/lvgl-saver-public-before.rgb565').write_bytes(self.before)
                    Path('/tmp/lvgl-saver-public-after.rgb565').write_bytes(after)
                    changed=sum(a!=b for a,b in zip(self.before,after))
                    raise AssertionError(f'Saved menu pixels differ: mode={self.mode}, changedBytes={changed}')
                self.phase='select'
            return {'KEY_PRESS'}
    buttons=Buttons();runtime=Runtime(sys.argv[1],pixels,buttons,activity_sink=hardware.buttons.update_last_input_time)
    restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
    restore_renderer=install_renderer(runtime,hardware,Renderer)
    from seedsigner.controller import Controller
    controller=Controller.get_instance();controller.screensaver_activation_ms=600
    restore_saver=install_saver(runtime,controller)
    class PublicView(View):
        def run(self):return self.run_screen(ButtonListScreen,title='Public saver test',button_data=[ButtonOption('Continue')])
    checks=[]
    try:
        for mode in ('automatic','explicit','disabled'):
            buttons.load(mode);view=PublicView();view.is_screensaver_allowed=(mode!='disabled')
            assert view.run()==0
            assert buttons.phase=='select',('Wake key activated underlying button',mode,buttons.phase,buttons.entered,buttons.restored,buttons.trace)
            if mode!='disabled':assert buttons.entered and buttons.restored
            checks.append(dict(mode=mode,wakeConsumed=(mode!='disabled'),savedPixelsRestored=buttons.restored))
        print(json.dumps(dict(passed=True,checks=checks,originalViewInitialization=True,originalControllerFacade=True,idleTimeoutMs=600,physicalDisplay=True,physicalButtons=False,customLogoQualified=False)))
    finally:
        restore_saver()
        for thread in (controller.wipe_timer_thread,controller.rng_monitor_thread):thread.stop();thread.join(3)
        restore_renderer();restore();runtime.close();hardware.close()
