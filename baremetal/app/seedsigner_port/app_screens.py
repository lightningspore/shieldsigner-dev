# SPDX-License-Identifier: MIT
"""Only reviewed screen facades; actual C++ screens own presentation and events."""
from seedsigner_port.button_options import ButtonOption,ButtonOptionWithoutTranslation
from seedsigner_port.screen_contracts import BASIC,APP_SCREENS
from seedsigner_port.decode_platform import FeatureUnavailable
RET_CODE__BACK_BUTTON=1000
RET_CODE__POWER_BUTTON=1001
RET_CODE__DISPLAY_TOGGLE=1002
RET_CODE__REBOOT_TO_LOADER=1003
class _Scroll:
    scroll_y=0
class NativeScreen:
    def __init__(self,**kwargs):
        self.args=kwargs
        # Original Views read screen.buttons[0].scroll_y (lvgl-app screen_bridge
        # parity). The native bridge restores focus by index; scroll offset is 0.
        self.buttons=[_Scroll()]
    def display(self):
        from seedsigner_port.renderer import Renderer
        return Renderer.get_instance().run_screen(type(self),self.args)
class SeedAddPassphraseScreen(NativeScreen):pass
from seedsigner_port.app_screen_defaults import KEYBOARD_LABELS
for _name,_label in KEYBOARD_LABELS.items():setattr(SeedAddPassphraseScreen,_name,_label)
class SeedReviewPassphraseScreen(NativeScreen):
    def display(self):
        from seedsigner_port.renderer import Renderer
        from seedsigner_port.review_text import short_visible,pages,page_config,LEGEND
        from seedsigner_port.screen_contracts import result
        renderer=Renderer.get_instance()
        value=self.args['passphrase']
        if short_visible(value):return renderer.run_screen(type(self),self.args)
        content=pages(value)
        # The legend and each page are presentation steps. Only an original
        # action index or Back out of the first step is returned to the View.
        page=-1
        while True:
            if page<0:
                config={'top_nav':{'title':'Exact Characters','show_back_button':True},
                        'text':LEGEND,'read_first':True,'is_bottom_list':True,
                        'button_list':['Review'],'allow_screensaver':True}
            elif page<len(content):config=page_config(value,content[page],page,len(content))
            else:
                summary=self.args.copy();summary['passphrase']='%d chars read'%len(value)
                selected=renderer.run_screen(type(self),summary)
                if selected==RET_CODE__BACK_BUTTON:
                    page=len(content)-1
                    continue
                return selected
            renderer.service()
            event=renderer.session.run('button_list_screen',config)
            selected=result(event,1)
            if selected==RET_CODE__BACK_BUTTON:
                if page<0:return RET_CODE__BACK_BUTTON
                page-=1
            elif selected==0:page+=1
            else:raise ValueError('Unexpected review page action')
class ScanScreen(NativeScreen):
    def display(self):
        from seedsigner_port.controller import Controller
        from seedsigner_port.renderer import Renderer
        from seedsigner_port.scan_screen import NativeScanScreen,CooperativePreview
        import ui
        controller=Controller.get_instance();renderer=Renderer.get_instance()
        class Preview(CooperativePreview):
            def show(self,frame):
                renderer.service()
                super().show(frame)
        ui.overlays(0,0)
        try:
            return NativeScanScreen(camera=controller.camera,preview=Preview(),buttons=renderer.buttons,**self.args).run()
        finally:
            ui.overlays(0,controller.screensaver_activation_ms)
            controller.reset_screensaver_timeout()
class OpeningSplashScreen(NativeScreen):
    def display(self):
        from seedsigner_port.renderer import Renderer
        from seedsigner_port.controller import Controller
        from seedsigner_port.settings_store import Settings,SettingsConstants as C
        renderer=Renderer.get_instance()
        partner=Settings.get_instance().get_value(C.SETTING__PARTNER_LOGOS)==C.OPTION__ENABLED
        if self.args.get('force_partner_logos') is not None:partner=self.args['force_partner_logos']
        renderer.session.show('opening_splash_screen',{'version':Controller.VERSION,'show_partner_logos':partner,'sponsor_text':'With support from'})
        while True:
            event=renderer.session.poll()
            if event is not None:
                if event==(1,1101,''):return None
                raise ValueError('Unexpected native splash result')
            renderer.session.sleep(1)
_CACHE={}
def __getattr__(name):
    if name.startswith('__'):raise AttributeError(name)
    if name in ('seed_screens','screen'):return __import__('seedsigner_port.app_screens',None,None,('*',))
    if name not in BASIC and name not in APP_SCREENS:raise FeatureUnavailable('Native screen not reviewed: '+name)
    if name not in _CACHE:_CACHE[name]=type(name,(NativeScreen,),{})
    return _CACHE[name]

from seedsigner_port.qr_display import QRDisplayScreen
class LoadingScreenThread:
    """Original call boundary, rendered cooperatively; no background thread."""
    def __init__(self,text=''):self.text=text;self.active=False
    def start(self):
        from seedsigner_port.renderer import Renderer
        if self.active:raise RuntimeError('Loading screen already active')
        Renderer.get_instance().session.show('loading_spinner_screen',{'text':self.text})
        self.active=True
    def stop(self):
        if self.active:
            from seedsigner_port.renderer import Renderer
            Renderer.get_instance().display_blank_screen();self.active=False

from seedsigner_port.address_search import SeedAddressVerificationScreen

class SeedBIP85SelectChildIndexScreen(NativeScreen):
    """Original 0-9 keyboard (5 cols, save, no cursor keys) via native keyboard.
    Same contract as firmware/lvgl-app/python/contracts.py KEYBOARDS."""
    def display(self):
        from seedsigner_port.renderer import Renderer
        from seedsigner_port.localization import gettext as _
        a=self.args
        cfg={'top_nav':{'title':_(a.get('title') or 'BIP-85 Index'),'show_back_button':True,'show_power_button':False},
             'keys':list('0123456789'),'cols':5,'show_save_button':True,'show_cursor_keys':False,
             'initial_value':a.get('initial_value') or '','allow_screensaver':True}
        renderer=Renderer.get_instance();renderer.service();renderer.session.show('keyboard_screen',cfg)
        event=renderer.session.wait()
        if event==1000 or (isinstance(event,tuple) and len(event)==3 and event[0]==1 and event[1]==1000):return RET_CODE__BACK_BUTTON
        if not isinstance(event,tuple) or len(event)!=3 or event[0]!=2 or event[1]!=0 or type(event[2]) is not str:raise ValueError('Unexpected native numeric keyboard result')
        if any(c not in '0123456789' for c in event[2]):raise ValueError('Invalid numeric entry')
        return event[2]
