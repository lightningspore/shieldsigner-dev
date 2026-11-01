"""App-side LVGL runtime; original wallet Views supply screen arguments.

Display and input are injected. This file has no wallet model, image processing,
or cryptographic behavior. The default policy refuses unreviewed screens.
"""
import queue
import time
from contracts import configuration,result,SUPPORTED,UnmigratedScreen,KEYBOARDS
from transport import NativeHost

KEYS={'KEY_UP':17,'KEY_DOWN':18,'KEY_LEFT':20,'KEY_RIGHT':19,'KEY_PRESS':10,'KEY1':ord('1'),'KEY2':ord('2'),'KEY3':ord('3')}
class Runtime:
    def __init__(self,binary,pixel_sink,read_buttons,activity_sink=None,*,locale_root=None):
        self.locale_assets=None
        if locale_root is not None:
            from locale_assets import LocaleAssets
            self.locale_assets=LocaleAssets(locale_root)
        self.binary=binary;self.pixel_sink=pixel_sink;self.lifecycle_check=None
        self.width=240;self.height=240
        self.host=NativeHost(binary,pixel_sink)
        self.read_buttons=read_buttons
        self.screensaver_timeout_ms=0;self.view_allows_screensaver=True
        self.activity_sink=activity_sink
        self.last_activity=-float("inf")
        self.request=0
        self.current=None
        self.low_since={}
        self.last_key=10
        self.closed=False
        self.last_scroll_y=0

    def run(self,screen_class,kwargs):
        if self.locale_assets is not None:self.locale_assets.sync(self.host)
        from grid_hold import prepare
        self.input_hold=prepare(screen_class,kwargs,KEYS)
        self.hold_result=None
        try:return self._run_screen(screen_class,kwargs)
        finally:self.input_hold=None;self.hold_result=None

    def _run_screen(self,screen_class,kwargs):
        if self.lifecycle_check is not None:self.lifecycle_check()
        if screen_class.__name__=='IOTestScreen':
            from io_test import run
            return run(self,screen_class,kwargs)
        if screen_class.__name__=='ToolsBatteryCalibrationRunningScreen':
            from calibration import run
            return run(self,screen_class,kwargs)
        if screen_class.__name__=='OpeningSplashScreen':
            from startup_splash import run
            return run(self,kwargs)
        if screen_class.__name__=='QRDisplayScreen':
            from qr_output import run_qr_output
            return run_qr_output(self,kwargs)
        if screen_class.__name__=='ToolsImageEntropyLivePreviewScreen':
            from image_entropy import run_live
            return run_live(self,screen_class)
        if screen_class.__name__=='ToolsImageEntropyFinalImageScreen':
            from image_entropy import run_review
            return run_review(self,kwargs)
        if screen_class.__name__=='ScanScreen':
            from camera_scan import run_scan
            return run_scan(self,kwargs)
        builder,cfg=configuration(screen_class,kwargs)
        if self.locale_assets is not None:
            picker=self.locale_assets.picker(screen_class,kwargs,cfg)
            if picker is not None:builder,cfg=picker
        cfg["allow_screensaver"]=cfg.get("allow_screensaver",True) and self.view_allows_screensaver
        self.request+=1
        self.host.send('key',key=self.last_key,pressed=False)
        self.host.send('screen',name=builder,config=cfg,request=self.request)
        # Discard prior-screen events only until this screen's build acknowledgement.
        while True:
            event=self.host.next_event()
            if event.get('event')=='error':raise RuntimeError('Native screen configuration rejected')
            if event.get('event')=='screen_ready' and event['request']==self.request:break
        self.reset_input()
        address_progress=None
        if screen_class.__name__=='MainMenuScreen':
            from home_battery import monitor
            battery=monitor(self)
            from home_recovery import monitor as recovery_monitor
            from seedsigner.gui.renderer import Renderer
            recovery=recovery_monitor(self,screen_class,KEYS,Renderer._instance)
            def address_progress():
                battery()
                return recovery()
        if screen_class.__name__=='BatteryInfoScreen':
            from battery_info import monitor
            address_progress=monitor(self)
        if screen_class.__name__=='MemoryInfoScreen':
            from live_info import monitor
            address_progress=monitor(self,screen_class,cfg)
        if screen_class.__name__=='SeedAddressVerificationScreen':
            from address_search import monitor
            address_progress=monitor(self,screen_class,kwargs)
        while True:
            if address_progress is not None:
                completed=address_progress()
                if completed is not None:return completed
            if self.host.error:raise RuntimeError('LVGL output failed') from self.host.error
            self.poll_input()
            if self.hold_result is not None:return self.hold_result
            try:event=None if self.host.events.empty() else self.host.events.get_nowait()
            except queue.Empty:event=None
            if event:
                if event.get('event')=='error':raise RuntimeError('Native LVGL error')
                if event.get('event') in ('button_selected','text_entered','passphrase_result'):
                    self.last_scroll_y=int(event.get('scroll_y',0))
                    value=result(event,len(cfg.get('rows',cfg.get('button_list',[]))))
                    if event['event']=='text_entered' and screen_class.__name__ in KEYBOARDS and cfg.get('show_save_button'):
                        value=value.strip()  # Original generic keyboard Save behavior; not passphrases.
                    from encrypted_contracts import TEXT_FIELDS,typed_result
                    if screen_class.__name__ in TEXT_FIELDS:value=typed_result(screen_class.__name__,value)
                    if screen_class.__name__=='ToolsTextQRTextEntryScreen':
                        from textqr_contracts import typed_result as textqr_result
                        value=textqr_result(value)
                    if screen_class.__name__ in ('ToolsTranscribeTextQRZoomedInScreen','SeedTranscribeSeedQRZoomedInScreen','SeedTranscribeEncryptedQRZoomedInScreen') and value==1000:return None
                    return value
            time.sleep(.01)

    def reconfigure_display(self,width,height,configure):
        """Quiesce pixel delivery before changing hardware; fail closed on error."""
        if getattr(self,'closed',False):raise RuntimeError('LVGL runtime closed')
        if type(width) is not int or type(height) is not int or (width,height) not in ((240,240),(320,240)):
            raise ValueError('Unsupported LVGL geometry')
        self.host.close() # Joins its pixel reader before configure touches SPI.
        configure()
        self.width=width;self.height=height
        self.host=NativeHost(self.binary,self.pixel_sink,width=width,height=height)
        self.configure_screensaver(self.screensaver_timeout_ms)
        self.reset_input()

    def show_loading(self,text):
        self.request+=1
        token=self.request
        self.host.send('key',key=self.last_key,pressed=False)
        self.host.send('screen',name='loading_spinner_screen',config={'text':text or ''},request=token)
        while True:
            event=self.host.next_event()
            if event.get('event')=='error':raise RuntimeError('Native loading screen failed')
            if event.get('event')=='screen_ready' and event.get('request')==token:return token

    def configure_screensaver(self,timeout_ms):
        if type(timeout_ms) is not int or not 0<=timeout_ms<=0xffffffff:raise ValueError('Invalid screensaver timeout')
        self.screensaver_timeout_ms=timeout_ms
        self.host.send('overlays',timeout_ms=timeout_ms)

    def clear(self):
        self.host.send('clear')
        while True:
            event=self.host.next_event()
            if event.get('event')=='error':raise RuntimeError('Native display cleanup failed')
            if event.get('event')=='screen_cleared':return

    def hide_loading(self,token):
        # A late spinner stop must never erase a newer destination or indicator.
        if self.request!=token:return
        self.clear()

    def reset_input(self):
        consume=getattr(self,'consume_input_override',None)
        if consume is not None:consume()
        self.waiting_release=True
        self.current=None
        self.low_since.clear()

    def poll_input(self):
        if self.lifecycle_check is not None:self.lifecycle_check()
        active=self.read_buttons()
        now=time.monotonic()
        if self.waiting_release:
            self.waiting_release=bool(active)
            return
        # No key or pending debounce/release can change input state here.
        # Lifecycle and hardware reads above still run on every poll.
        if not active and self.current is None and not self.low_since:return
        key=None;tap=None
        for name in KEYS:
            if name in active:
                self.low_since.setdefault(name,now)
                if now-self.low_since[name]>=.025 and key is None:key=KEYS[name]
            else:
                low=self.low_since.pop(name,None)
                if low is not None and now-low>=.025 and self.current!=KEYS[name] and tap is None:tap=KEYS[name]
        hold=getattr(self,'input_hold',None)
        if hold is not None:
            key,tap,completed,held=hold.poll(key,tap,now,wake=getattr(self.host,'screensaver_active',False))
            if completed is not None:self.hold_result=completed
            if held and now-self.last_activity>=.25:
                if self.activity_sink is not None:self.activity_sink()
                self.host.send('activity');self.last_activity=now
        # Preserve a sampled short press released across a slow poll, as the
        # original GPIO check_for_low does. Screen handoff still waits for release.
        if key is None and self.current is None and tap is not None:
            if self.activity_sink is not None:self.activity_sink();self.last_activity=now
            self.host.send('key',key=tap,pressed=True)
            self.host.send('key',key=tap,pressed=False)
            self.last_key=tap
            return
        if key is not None and self.activity_sink is not None and (key!=self.current or now-self.last_activity>=.25):
            self.activity_sink();self.last_activity=now
        if key!=self.current:
            if self.current is not None:self.host.send('key',key=self.current,pressed=False)
            if key is not None:self.host.send('key',key=key,pressed=True);self.last_key=key
            self.current=key

    def close(self):
        if not self.closed:self.closed=True;self.host.close()


def install_view_dispatch(runtime,app_root,manifest):
    """Explicit process-local installation. Does not edit original app sources.

    Reviewed direct Screen(...).display() calls also route through LVGL.
    Unsupported View calls raise UnmigratedScreen.
    """
    from types import SimpleNamespace
    from guards import verify
    from pathlib import Path
    import inspect
    verify(app_root,manifest)
    from seedsigner.views.view import View
    if Path(inspect.getfile(View)).resolve() != Path(app_root).resolve()/'seedsigner/views/view.py':
        raise RuntimeError('Imported View is outside reviewed app root')
    if hasattr(View,'__shieldsigner_lvgl_dispatch__'):raise RuntimeError('LVGL dispatch already installed')
    import json
    from seedsigner.gui.screens import screen
    from screen_bridge import install_modules
    guards=json.loads(Path(manifest).read_text())
    module_specs={
        'seedsigner.gui.screens.'+name:(Path(app_root).resolve()/'seedsigner/gui/screens'/f'{name}.py',guards[f'gui/screens/{name}.py'])
        for name in ('screen','seed_screens','settings_screens','tools_screens','scan_screens','psbt_screens')
    }
    restore_screens=install_modules(runtime,SUPPORTED,module_specs)
    from loading import install as install_loading
    restore_loading=install_loading(runtime,screen.LoadingScreenThread)
    from seedsigner.views.screensaver import OpeningSplashScreen
    from startup_splash import install as install_splash
    restore_splash=install_splash(runtime,OpeningSplashScreen)
    from entropy_fallback import install as install_fallback
    restore_fallback=install_fallback(View,app_root,manifest)
    from word_pagination import install as install_pagination
    restore_pagination=install_pagination(View,app_root,manifest)
    from slip39_lifecycle import install as install_slip39_lifecycle
    restore_slip39=install_slip39_lifecycle(app_root,manifest)
    original=View.run_screen
    def run_screen(view,Screen_cls,**kwargs):
        if Screen_cls.__name__ not in SUPPORTED:raise UnmigratedScreen(Screen_cls.__name__)
        runtime.view_allows_screensaver=bool(getattr(view,"is_screensaver_allowed",True))
        view.screen=Screen_cls(**kwargs)
        return view.screen.display()
    View.run_screen=run_screen
    View.__shieldsigner_lvgl_dispatch__=original
    def uninstall():
        View.run_screen=original
        restore_screens()
        restore_loading()
        restore_splash()
        restore_slip39()
        restore_pagination()
        restore_fallback()
        del View.__shieldsigner_lvgl_dispatch__
    return uninstall
