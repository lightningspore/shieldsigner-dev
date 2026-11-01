"""Direct original keyboard screen calls through native LVGL; public inputs only."""
import json
import sys
import time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
from runtime import Runtime,install_view_dispatch
from seedsigner.gui.screens import screen,seed_screens,settings_screens,tools_screens
class Buttons:
    def load(self,keys):self.keys=keys;self.start=None
    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        elapsed=now-self.start-.15
        if elapsed<0:return set()
        index=int(elapsed/.2)
        if index>=len(self.keys):
            if elapsed>len(self.keys)*.2+5:raise TimeoutError('Scripted keyboard navigation did not finish')
            return set()
        return {self.keys[index]} if elapsed%.2<.1 else set()
buttons=Buttons();rectangles=0
def pixels(*args):
    global rectangles
    rectangles+=1
runtime=Runtime(sys.argv[1],pixels,buttons)
restore=install_view_dispatch(runtime,sys.argv[2],Path(__file__).parent/'source-guards.json')
checks=[]
def check(cls,args,keys,expected,label):
    buttons.load(keys)
    instance=cls(**args)
    assert not hasattr(instance,'hw_inputs'), 'PIL screen constructor ran'
    actual=instance.display()
    assert actual==expected, (label,repr(actual))
    checks.append(label)
try:
    check(settings_screens.SettingPBFDK2IterationsScreen,dict(initial_value='125'),['KEY3'],'125','PBKDF2-direct-key3-save')
    check(seed_screens.SeedBIP85SelectChildIndexScreen,dict(initial_value='00042'),['KEY3'],'00042','BIP85-leading-zero-preserved')
    check(seed_screens.SeedExportXpubAccountNumberScreen,dict(initial_value='0'),['KEY3'],'0','account-zero-save')
    check(seed_screens.SeedExportXpubCustomDerivationScreen,dict(initial_value="m/84'/0'/0'"),['KEY3'],"m/84'/0'/0'",'derivation-path-exact')
    check(seed_screens.SeedBIP85SelectChildIndexScreen,dict(initial_value='7'),['KEY_UP','KEY3'],'7','key3-save-from-top-nav')
    check(seed_screens.SeedBIP85SelectChildIndexScreen,dict(initial_value=''),['KEY3','KEY_PRESS','KEY3'],'0','empty-save-ignored-then-type-zero')
    check(seed_screens.SeedBIP85SelectChildIndexScreen,dict(initial_value=''),['KEY_UP','KEY_PRESS'],1000,'keyboard-back-sentinel')
    check(screen.KeyboardScreen,dict(title='Public test',keys_charset='0123456789',initial_value=' 42 ',show_save_button=True),['KEY3'],'42','generic-save-original-trim')
    check(tools_screens.ToolsDiceEntropyEntryScreen,dict(return_after_n_chars=3),['KEY_PRESS']*3,'111','dice-exact-mapped-values-auto-complete')
    check(tools_screens.ToolsCoinFlipEntryScreen,dict(return_after_n_chars=3),['KEY_PRESS']*3,'111','coin-exact-values-auto-complete')
    print(json.dumps(dict(passed=True,checks=checks,rectangles=rectangles,originalScreenClasses=True,directConstruction=True,pilScreenConstructors=False,nativeKeypad=True,physicalButtons=False)))
finally:restore();runtime.close()
