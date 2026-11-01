"""Public status icon/color/visibility pixels and default action, host or ARM."""
import json,sys,time
from transport import NativeHost
from contracts import configuration
frame=bytearray(240*240*2)
def pixels(area,data):
    x1,y1,x2,y2=area;stride=(x2-x1+1)*2
    for row,y in enumerate(range(y1,y2+1)):
        frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
def colored():
    return sum(frame[(y*240+x)*2:(y*240+x)*2+2]==b'\xf8\x1f' for y in range(40,150) for x in range(20,220))
host=NativeHost(sys.argv[1],pixels);checks=[]
try:
    for name in ('LargeIconStatusScreen','WarningScreen'):
        cls=type(name,(),{})
        for size in (50,0):
            builder,cfg=configuration(cls,dict(title='Public status',text='Public body',status_icon_name='\ue913',status_color='#ff00ff',status_icon_size=size))
            cfg['initial_selected_index']=0
            host.send('screen',name=builder,config=cfg,request=len(checks)+1)
            event=host.next_event();assert event==dict(event='screen_ready',request=len(checks)+1),event
            count=colored()
            assert (count>5 if size else count==0),(name,size,count)
            host.send('key',key=10,pressed=True);time.sleep(.1);host.send('key',key=10,pressed=False)
            event=host.next_event();assert event['event']=='button_selected' and event['index']==0,event
            checks.append(dict(screen=name,iconVisible=bool(size),customColorPixels=count,defaultAction=event['index']))
    print(json.dumps(dict(passed=True,cases=checks,publicPixelsOnly=True,physicalDisplay=False)),flush=True)
finally:host.close()
