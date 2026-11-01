"""Tap/hold arbitration for original large-button grids; no system actions."""
from contracts import arguments

class Hold:
    def __init__(self,key,milliseconds,result):
        if type(milliseconds) is not int or milliseconds<=0 or type(result) is not int:
            raise ValueError('Invalid grid hold contract')
        self.key=key;self.seconds=milliseconds/1000;self.result=result;self.since=None;self.waking=False
    def poll(self,key,tap,now,wake=False):
        if key==self.key and wake and self.since is None:self.waking=True
        if self.waking:
            if key!=self.key:self.waking=False
            return key,tap,None,False
        if key==self.key:
            if self.since is None:self.since=now
            if now-self.since>=self.seconds:return None,None,self.result,True
            return None,None,None,True
        if self.since is not None:
            self.since=None
            # Original _is_long_press blocks other input until hold release.
            return None,self.key,None,False
        return key,tap,None,False

def prepare(screen_class,passed,keys):
    if screen_class.__name__ not in ('LargeButtonScreen','MainMenuScreen'):return None
    a=arguments(screen_class,passed)
    if screen_class.__name__=='MainMenuScreen':
        from seedsigner.models.settings import Settings
        from seedsigner.views.view import PowerOptionsView
        if Settings.RUNTIME_PROFILE in PowerOptionsView.LUCKFOX_PROFILES:
            from seedsigner.gui.screens.screen import RET_CODE__REBOOT_TO_LOADER
            from seedsigner.hardware.buttons import HardwareButtonsConstants
            a.update(long_press_key=HardwareButtonsConstants.KEY3,long_press_ret_code=RET_CODE__REBOOT_TO_LOADER,long_press_ms=screen_class.VERY_LONG_PRESS_MS)
    key=a.get('long_press_key')
    if key is None:return None
    if key not in keys:raise ValueError('Unknown grid hold key')
    return Hold(keys[key],a.get('long_press_ms',5000),a.get('long_press_ret_code'))
