# SPDX-License-Identifier: MIT
# Original startup Views; actual native splash completion and warning selection.
from seedsigner_port.controller import Controller,StopFlowBasedTest
from seedsigner_port.renderer import Renderer
import ui,json,time
class StartupDriver:
    def __init__(self):self.screens=[];self.started=time.ticks_ms()
    def __getattr__(self,name):return getattr(ui,name)
    def render(self,builder,encoded):
        cfg=json.loads(encoded);ui.render(builder,encoded);self.screens.append(builder)
        if builder=='opening_splash_screen':
            assert cfg['version']==Controller.VERSION
        elif builder=='large_icon_status_screen':
            assert cfg['top_nav']['title']=='Unhardened Build'
            assert 'USB Python console' in cfg['text'] and 'unqualified entropy' in cfg['text']
            assert 'Do not use real seeds.' in cfg['text']
            # Focus may begin in overflowing text; END is a native key we do not
            # expose. Actual DOWN presses reach the original acknowledgment.
            for i in range(8):ui.key(18,True);ui.key(18,False)
            ui.key(10,True);ui.key(10,False)
        elif builder=='main_menu_screen':raise StopFlowBasedTest()
        else:raise StopFlowBasedTest()
Renderer._instance=None;driver=StartupDriver();Renderer.configure_instance(backend=driver)
Controller._instance=None;controller=Controller.get_instance()
controller.start()
assert driver.screens==['opening_splash_screen','large_icon_status_screen','main_menu_screen']
print('@@PASS original-startup-splash-development-warning-home',time.ticks_ms()-driver.started)
Renderer._instance=None;renderer=Renderer.get_instance();ui.overlays(0,0)
renderer.session.show_screen('MainMenuScreen',{'title':'Home','button_data':['Scan','Seeds','Tools','Settings']})
