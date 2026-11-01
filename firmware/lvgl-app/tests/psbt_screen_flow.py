"""Original transaction Screen classes via LVGL; public display fixtures only."""
import json
from pathlib import Path
import sys
import time
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
from runtime import Runtime,install_view_dispatch
from seedsigner.gui.screens import psbt_screens
from seedsigner.gui.screens.screen import ButtonOption
class Buttons:
    def load(self,keys):self.keys=keys;self.start=None
    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        t=now-self.start-.2
        if t<0:return set()
        i=int(t/.2)
        if i>=len(self.keys):
            if t>len(self.keys)*.2+5:raise TimeoutError('Transaction review navigation did not finish')
            return set()
        return {self.keys[i]} if t%.2<.1 else set()
buttons=Buttons();hardware=None;rectangles=0
if '--display' in sys.argv:
    from luckfox import LuckfoxHardware
    hardware=LuckfoxHardware()
def pixels(area,data):
    global rectangles
    rectangles+=1
    if hardware is not None:hardware.pixels(area,data)
runtime=Runtime(sys.argv[1],pixels,buttons);restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
checks=[]
address='bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu'
try:
    cases=[
      (psbt_screens.PSBTOverviewScreen,dict(spend_amount=9000000,change_amount=1000000,fee_amount=1,num_inputs=2,num_change_outputs=1,destination_addresses=[address],is_high_fee_tx=True)),
      (psbt_screens.PSBTMathScreen,dict(input_amount=10000001,spend_amount=9000000,change_amount=1000000,fee_amount=1,num_inputs=2,num_recipients=1,is_high_fee_tx=True)),
      (psbt_screens.PSBTAddressDetailsScreen,dict(title='Recipient 1',address=address,amount=1,button_data=[ButtonOption('Next')])),
      (psbt_screens.PSBTChangeDetailsScreen,dict(title='Your Change',address=address,amount=1000000,is_change_addr_verified=True,derivation_path_addr_index=7,button_data=[ButtonOption('Next')])),
      (psbt_screens.PSBTOpReturnScreen,dict(title='OP_RETURN',op_return_data=b'public text',button_data=[ButtonOption('Next')])),
      (psbt_screens.PSBTOpReturnScreen,dict(title='OP_RETURN',op_return_data=b'\x00\xffpublic',button_data=[ButtonOption('Next')])),
      (psbt_screens.PSBTOpReturnScreen,dict(title='OP_RETURN',op_return_data=b'',button_data=[ButtonOption('Next')])),
      (psbt_screens.PSBTFinalizeScreen,dict(is_rbf=True,locktime_text='Locked until block 900000',button_data=[ButtonOption('Approve transaction')])),
    ]
    for cls,args in cases:
        buttons.load((['KEY_DOWN']*4 if cls is psbt_screens.PSBTFinalizeScreen else [])+['KEY_PRESS'])
        value=cls(**args).display()
        assert value==0,(cls.__name__,value)
        checks.append(cls.__name__)
    print(json.dumps(dict(passed=True,screens=checks,rectangles=rectangles,originalScreenClasses=True,physicalDisplay=hardware is not None,physicalButtons=False,signingPerformed=False)))
finally:
    restore();runtime.close()
    if hardware is not None:hardware.close()
