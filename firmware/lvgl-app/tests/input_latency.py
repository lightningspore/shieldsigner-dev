"""Public keypad dispatch to completed physical SPI frame; excludes GPIO polling."""
import json,statistics,sys,threading,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'python'),'/opt/src','/usr/lib/shieldsigner-camera/python']
from transport import NativeHost
from luckfox import LuckfoxHardware
hardware=LuckfoxHardware();condition=threading.Condition();armed=None;elapsed=None

def complete():
 global elapsed,armed
 hardware.frame_complete()
 with condition:
  if armed is not None:
   elapsed=time.monotonic_ns()-armed;armed=None;condition.notify_all()

def summary(values):
 ordered=sorted(values)
 return dict(samples=len(values),medianMs=statistics.median(values),p95Ms=ordered[(95*len(ordered)+99)//100-1],maxMs=max(values),minMs=min(values))
host=None
try:
 host=NativeHost(sys.argv[1],hardware.pixels,frame_sink=complete,frame_reset=hardware.frame_reset)
 results=[]
 for builder,keys in [('main_menu_screen',(19,20)),('button_list_screen',(18,17))]:
  host.send('screen',name=builder,request=1,config=dict(top_nav=dict(title='Public latency fixture'),button_list=['One','Two','Three','Four']))
  assert host.next_event()==dict(event='screen_ready',request=1)
  values=[]
  for index in range(24):
   # No sampling, screenshots, camera or app work runs alongside these trials.
   # Give the prior focus update time to settle before arming the next sample.
   time.sleep(.15)
   with condition:
    elapsed=None;armed=time.monotonic_ns()
    host.send('key',key=keys[index%2],pressed=True)
    host.send('key',key=keys[index%2],pressed=False)
    assert condition.wait_for(lambda:elapsed is not None,timeout=3),'Focus update did not complete'
    values.append(elapsed/1e6)
  assert host.events.empty()
  results.append(dict(screen=builder,**summary(values)))
 host.send('clear');assert host.next_event()==dict(event='screen_cleared')
 print(json.dumps(dict(passed=True,results=results,physicalDisplay=True,timing='Python IPC dispatch to first completed SPI frame',includes=['IPC','LVGL scheduling/rendering','rectangle transport','SPI writes'],excludes=['GPIO polling/debounce','panel optical response','wallet View/Controller work','camera load'],publicFixtures=True)),flush=True)
finally:
 if host is not None:host.close()
 hardware.close()
