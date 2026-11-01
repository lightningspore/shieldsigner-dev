"""Actual native process handoff; geometry-only fixture, no SPI or GPIO."""
import json,sys
from runtime import Runtime
geometry=[240,240];extents=[-1,-1];checks=[]
def pixels(area,data):
 x1,y1,x2,y2=area
 assert 0<=x1<=x2<geometry[0] and 0<=y1<=y2<geometry[1]
 extents[0]=max(extents[0],x2);extents[1]=max(extents[1],y2)
app=Runtime(sys.argv[1],pixels,lambda:set())
try:
 app.configure_screensaver(45000)
 for width,height in ((320,240),(240,240)):
  old=app.host.child;called=[]
  def configure():
   assert old.poll() is not None
   geometry[:]=[width,height];extents[:]=[-1,-1];called.append(True)
  app.reconfigure_display(width,height,configure)
  assert called==[True] and app.host.child.pid!=old.pid
  assert app.waiting_release and app.current is None and app.screensaver_timeout_ms==45000
  app.host.send('screen',name='main_menu_screen',request=1,config=dict(top_nav=dict(title='Home',show_power_button=True),button_list=['Scan','Seeds','Tools','Settings']))
  assert app.host.next_event()==dict(event='screen_ready',request=1)
  assert extents==[width-1,height-1],extents
  checks.append(dict(width=width,height=height,previousProcessReapedBeforeConfigure=True,newProcess=True,fullViewport=True,inputReleaseGate=True))
 print(json.dumps(dict(passed=True,cases=checks,physicalDisplay=False,hardwareConfigureFixture=True,settingsSwitchingQualified=False)),flush=True)
finally:app.close()
