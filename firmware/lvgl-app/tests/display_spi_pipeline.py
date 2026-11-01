"""Real native/transport/pixel adapter to fake SPI endpoint; no GPIO/LCD."""
import json,sys,threading
from pathlib import Path
from types import SimpleNamespace
from transport import NativeHost
from luckfox import LuckfoxHardware
from guards import verify
verify('/opt/src',Path(__file__).parent/'source-guards.json')
class Display:
 width=320;height=240
 def __init__(self):self.buffers={};self.windows=[];self._dc=SimpleNamespace(write=lambda value:None)
 def command(self,value):
  self.current=value
  if value in (0x2a,0x2b):self.buffers[value]=[]
  elif value==0x2c:assert all(len(self.buffers[key])==4 for key in (0x2a,0x2b))
  else:raise AssertionError('Unexpected SPI command')
 def data(self,value):
  assert 0<=value<=255
  self.buffers[self.current].append(value)
 def _chunked_transfer(self,data):
  if self.current in (0x2a,0x2b):
   assert len(data)==4
   for value in data:self.data(value)
   return
  x=self.buffers[0x2a];y=self.buffers[0x2b]
  x1,x2=x[0]*256+x[1],x[2]*256+x[3];y1,y2=y[0]*256+y[1],y[2]*256+y[3]
  assert 0<=x1<=x2<320 and 0<=y1<=y2<240
  assert len(data)==(x2-x1+1)*(y2-y1+1)*2
  self.windows.append((x1,y1,x2,y2))
hardware=LuckfoxHardware.__new__(LuckfoxHardware);hardware.lock=threading.Lock();hardware.lcd=Display();hardware.scaler=None
host=NativeHost(sys.argv[1],hardware.pixels,width=320,height=240)
try:
 host.send('screen',name='main_menu_screen',request=1,config=dict(top_nav=dict(title='Home',show_power_button=True),button_list=['Scan','Seeds','Tools','Settings']))
 assert host.next_event()==dict(event='screen_ready',request=1)
 assert max(window[2] for window in hardware.lcd.windows)==319
 assert max(window[3] for window in hardware.lcd.windows)==239
 assert any(window[0]<=255<window[2] for window in hardware.lcd.windows)
 print(json.dumps(dict(passed=True,realNativeAndTransport=True,realPixelAdapter=True,fakeSPI=True,full320ColumnsAddressed=True,windowCount=len(hardware.lcd.windows),physicalDisplay=False)),flush=True)
finally:host.close()
