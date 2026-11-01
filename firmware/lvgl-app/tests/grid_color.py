"""Public grid style pixels + unchanged keypad results; host or physical LCD."""
import json,sys,time,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from contracts import configuration
from transport import NativeHost
hardware=None;classes={};option=lambda value:value
if '--display' in sys.argv:
 sys.path.insert(0,'/opt/src')
 from luckfox import LuckfoxHardware
 from seedsigner.gui.screens.screen import LargeButtonScreen,MainMenuScreen,ButtonOption
 classes=dict(LargeButtonScreen=LargeButtonScreen,MainMenuScreen=MainMenuScreen);option=ButtonOption
 hardware=LuckfoxHardware()
frame=bytearray(240*240*2);lock=threading.Lock()
def pixels(area,data):
 x1,y1,x2,y2=area;stride=(x2-x1+1)*2
 with lock:
  for row,y in enumerate(range(y1,y2+1)):frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
 if hardware is not None:hardware.pixels(area,data)
def counts(rgb):
 value=int(rgb[1:],16);r=value>>16;g=(value>>8)&255;b=value&255
 pattern=(((r>>3)<<11)|((g>>2)<<5)|(b>>3)).to_bytes(2,'big')
 with lock:
  return [sum(frame[(y*240+x)*2:(y*240+x)*2+2]==pattern for y in range(240) for x in range(start,start+120)) for start in (0,120)]
def wait_selected(rgb,index):
 deadline=time.monotonic()+3
 while time.monotonic()<deadline:
  values=counts(rgb)
  if values[index]>3000 and values[1-index]<3000:return
  time.sleep(.01)
 with lock:
  from collections import Counter
  dominant=Counter(bytes(frame[i:i+2]).hex() for i in range(0,len(frame),2)).most_common(6)
 raise AssertionError('Grid focus color pixels mismatch: '+repr(dict(rgb=rgb,index=index,counts=values,dominant=dominant,checks=checks)))
host=NativeHost(sys.argv[1],pixels);checks=[]
try:
 for name,count in [('LargeButtonScreen',2),('LargeButtonScreen',4),('MainMenuScreen',4)]:
  for color in (None,'#00ffff','#8a2be2'):
   args=dict(title='Public grid',button_data=[option(label) for label in ['One','Two','Three','Four'][:count]],selected_button=0)
   if color is not None:args['button_selected_color']=color
   builder,cfg=configuration(classes.get(name,type(name,(),{})),args)
   host.send('screen',name=builder,config=cfg,request=1);assert host.next_event()==dict(event='screen_ready',request=1)
   expected=color or '#ff9f0a';wait_selected(expected,0)
   host.send('key',key=19,pressed=True);host.send('key',key=19,pressed=False);wait_selected(expected,1)
   host.send('key',key=10,pressed=True);host.send('key',key=10,pressed=False)
   assert host.next_event()['index']==1
   checks.append(dict(screen=name,buttons=count,color=expected,rightThenSelectIndex=1))
 host.send('screen',name='power_options_screen',config=dict(top_nav=dict(title='Invalid fixture'),button_list=['One','Two'],button_selected_color='invalid'),request=2)
 assert host.next_event()==dict(event='error',kind='invalid_request')
 host.send('clear');assert host.next_event()==dict(event='screen_cleared')
 print(json.dumps(dict(passed=True,checks=checks,stylePixelCases=len(checks),originalScreenClasses=bool(classes),invalidColorRejected=True,physicalDisplay=hardware is not None,scriptedNativeKeypad=True,systemActionsExecuted=False)),flush=True)
finally:
 host.close()
 if hardware is not None:hardware.close()
