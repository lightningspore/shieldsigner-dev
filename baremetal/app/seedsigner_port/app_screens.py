# SPDX-License-Identifier: MIT
"""Only reviewed screen facades; actual C++ screens own presentation and events."""
from seedsigner_port.button_options import ButtonOption,ButtonOptionWithoutTranslation
from seedsigner_port.screen_contracts import BASIC,APP_SCREENS
from seedsigner_port.decode_platform import FeatureUnavailable
RET_CODE__BACK_BUTTON=1000
RET_CODE__POWER_BUTTON=1001
RET_CODE__DISPLAY_TOGGLE=1002
RET_CODE__REBOOT_TO_LOADER=1003
class NativeScreen:
    def __init__(self,**kwargs):self.args=kwargs
    def display(self):
        from seedsigner_port.renderer import Renderer
        return Renderer.get_instance().run_screen(type(self),self.args)
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
