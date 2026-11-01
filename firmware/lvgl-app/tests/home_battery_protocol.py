"""Public battery metadata/native ownership protocol; no physical sensor claims."""
import json,sys,time
from transport import NativeHost
frame=bytearray(240*240*2)
def pixels(area,data):
 x1,y1,x2,y2=area;stride=(x2-x1+1)*2
 for row,y in enumerate(range(y1,y2+1)):frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
host=NativeHost(sys.argv[1],pixels)
def ack(name):
 while True:
  event=host.next_event()
  if event['event']=='overlay_changed':continue
  assert event['event']==name,event
  return event
def update(**state):
 host.send('home_battery',**state);ack('home_battery_updated')
def red():
 return sum(frame[(y*240+x)*2:(y*240+x)*2+2]==b'\xf8\xc1' for y in range(17) for x in range(70))
try:
 host.send('screen',name='main_menu_screen',request=1,config=dict(top_nav=dict(title='Home',show_power_button=True),button_list=['Scan','Seeds','Tools','Settings']))
 ack('screen_ready');baseline=bytes(frame)
 update(visible=False);assert bytes(frame)==baseline
 # First detection occurs while saver owns active display. The battery must
 # attach to the saved Home screen, survive dismissal and never touch saver.
 host.send('overlays',timeout_ms=600)
 deadline=time.monotonic()+4
 while not host.screensaver_active:
  assert time.monotonic()<deadline,'Saver activation timed out'
  time.sleep(.02)
 update(visible=True,percent=12,charging=False)
 assert host.screensaver_active
 host.send('screensaver_dismiss');host.send('overlays',timeout_ms=0)
 host.send('overlay_state');assert not ack('overlay_state')['screensaver']
 assert red()>0
 low=bytes(frame)
 update(visible=True,percent=80,charging=False);assert red()==0 and bytes(frame)!=low
 full=bytes(frame)
 update(visible=True,percent=80,charging=True);assert bytes(frame)!=full
 update(visible=True,percent=None,charging=False)
 update(visible=False);assert bytes(frame)==baseline
 host.send('home_battery',visible=True,percent='bad',charging=False);ack('error')
 update(visible=True,percent=50,charging=False)
 host.send('clear');ack('screen_cleared')
 host.send('home_battery',visible=False);ack('error')
 print(json.dumps(dict(passed=True,absentUnchanged=True,lowBatteryRed=True,chargeAndPercentDiffer=True,unknownHandled=True,hideRestoresBaseline=True,firstDetectionDuringSaverSurvives=True,malformedAndInactiveRejected=True,physicalDisplay=False,physicalBattery=False)),flush=True)
finally:host.close()
