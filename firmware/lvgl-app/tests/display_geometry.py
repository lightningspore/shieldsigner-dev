"""ARM native viewport/frame bounds and grid input; no physical display/GPIO."""
import json,sys
from transport import NativeHost
results=[]
for width,height in ((240,240),(320,240)):
 extents=[-1,-1];rectangles=[0]
 def pixels(area,data):
  x1,y1,x2,y2=area
  assert 0<=x1<=x2<width and 0<=y1<=y2<height
  assert len(data)==(x2-x1+1)*(y2-y1+1)*2
  extents[0]=max(extents[0],x2);extents[1]=max(extents[1],y2);rectangles[0]+=1
 host=NativeHost(sys.argv[1],pixels,width=width,height=height)
 try:
  host.send('screen',name='main_menu_screen',request=1,config=dict(top_nav=dict(title='Home',show_power_button=True),button_list=['Scan','Seeds','Tools','Settings']))
  assert host.next_event()==dict(event='screen_ready',request=1)
  assert extents==[width-1,height-1],extents
  for key in (18,19,10):
   host.send('key',key=key,pressed=True);host.send('key',key=key,pressed=False)
  event=host.next_event();assert event['event']=='button_selected' and event['index']==3,event
  host.send('clear');assert host.next_event()['event']=='screen_cleared'
  results.append(dict(width=width,height=height,fullViewportPainted=True,rectangles=rectangles[0],gridSelected=3))
 finally:host.close()
print(json.dumps(dict(passed=True,cases=results,physicalDisplay=False,physicalButtons=False,settingsSwitchingQualified=False)),flush=True)
