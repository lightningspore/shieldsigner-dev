"""Pinned native splash; original startup View/checks remain authoritative."""
from gettext import gettext as _
import queue,time

def configuration(version,partner_setting,forced=None):
    if forced is not None and type(forced) is not bool:raise ValueError('Invalid splash partner override')
    return dict(version=str(version),show_partner_logos=partner_setting if forced is None else forced,sponsor_text=_('An unofficial fork of:'),dismissible=False,logo_already_shown=False,allow_screensaver=False)

def run(runtime,args):
    from seedsigner.models.settings import Settings
    from seedsigner.models.settings_definition import SettingsConstants as C
    from seedsigner.controller import Controller
    cfg=configuration(Controller.get_instance().VERSION,Settings.get_instance().get_value(C.SETTING__PARTNER_LOGOS)==C.OPTION__ENABLED,args.get('force_partner_logos'))
    runtime.request+=1;request=runtime.request
    runtime.host.send('key',key=runtime.last_key,pressed=False)
    runtime.host.send('screen',name='opening_splash_screen',config=cfg,request=request)
    try:
        while True:
            event=runtime.host.next_event()
            if event.get('event')=='error':raise RuntimeError('Native splash failed')
            if event.get('event')=='screen_ready' and event.get('request')==request:break
        runtime.reset_input();deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            runtime.poll_input()
            try:event=runtime.host.events.get(timeout=.01)
            except queue.Empty:
                if runtime.host.error:raise RuntimeError('Native splash output failed') from runtime.host.error
                continue
            if event.get('event')=='error':raise RuntimeError('Native splash animation failed')
            if event.get('event')=='button_selected' and event.get('index')==1101:return None
        raise TimeoutError('Native splash completion expired')
    finally:runtime.clear()

def install(runtime,cls):
    original_init=cls.__init__;own_display=cls.__dict__.get('display')
    def initialize(screen,force_partner_logos=None):screen.force_partner_logos=force_partner_logos
    def display(screen):return runtime.run(cls,{'force_partner_logos':screen.force_partner_logos})
    cls.__init__=initialize;cls.display=display
    def restore():
        cls.__init__=original_init
        if own_display is None:del cls.display
        else:cls.display=own_display
    return restore
