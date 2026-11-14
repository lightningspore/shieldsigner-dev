# SPDX-License-Identifier: MIT
# App argument/result contracts through the actual renderer, using test input fixtures.
from seedsigner_port.native_ui import ScreenSession
from seedsigner_port.buttons import ButtonInput
from seedsigner_port.screen_contracts import UnmigratedScreen
import machine
import ui
assert machine.console_status()['usb_only']==0
class Clock:
    now=0
    mask=0
f=Clock()
b=ButtonInput(lambda:f.mask,lambda:f.now)
s=ScreenSession(buttons=b,clock=lambda:f.now,sleep=lambda ms:None)
class ButtonOption:
    def __init__(self,label):
        self.button_label=label
        self.icon_name=None
        self.right_icon_name=None
        self.icon_color=None
        self.button_label_color=None
class ButtonOptionWithoutTranslation(ButtonOption):pass
class MainMenuScreen:pass
class ButtonListScreen:pass
class LargeButtonScreen:pass
def pulse(mask):
    f.mask=0;f.now+=20;s.poll();f.now+=10;s.poll()
    f.mask=mask;f.now+=20;assert s.poll() is None
    f.now+=10
    return s.poll()
s.show_screen(MainMenuScreen,{'title':'Home','button_data':['Scan','Seeds','Tools','Settings']})
assert pulse(8) is None
assert s.screen_result(pulse(16))==1
s.show_screen(ButtonListScreen,{'title':'Argument test','button_data':[ButtonOption('First'),ButtonOptionWithoutTranslation('Second')],'is_button_text_centered':False})
assert pulse(2) is None
assert s.screen_result(pulse(16))==1
s.show_screen(ButtonListScreen,{'title':'Argument test','button_data':['First','Second']})
assert pulse(1) is None
assert s.screen_result(pulse(16))==1000
s.show_screen(LargeButtonScreen,{'title':'Grid test','button_data':['First','Second']})
assert pulse(8) is None
assert s.screen_result(pulse(16))==1
for name,args in [('SeedFinalizeScreen',{}),('LargeButtonScreen',{'button_data':['A','B'],'long_press_key':'KEY3'})]:
    try:
        s.show_screen(name,args)
        assert False
    except UnmigratedScreen:
        pass
s.show_screen(MainMenuScreen,{'title':'Home','button_data':['Scan','Seeds','Tools','Settings']})
print('@@APP_SCREEN_CONTRACTS',ui.status())
print('@@PASS app-basic-screen-contracts')
