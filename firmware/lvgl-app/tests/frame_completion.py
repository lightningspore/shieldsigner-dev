"""Native completed-frame callbacks are ordered after pixels and outside ACK queue."""
import json,sys,threading
from transport import NativeHost
class Sink:
 def __init__(self):self.pending=0;self.frames=0;self.event=threading.Event();self.rectangles=0
 def pixels(self,area,data):
  self.pending+=1;self.rectangles+=1
 def frame_complete(self):
  assert self.pending>0
  self.pending=0;self.frames+=1;self.event.set()
sink=Sink();host=NativeHost(sys.argv[1],sink.pixels)
try:
 before=sink.frames
 host.send('screen',name='main_menu_screen',request=1,config=dict(top_nav=dict(title='Home',show_power_button=True),button_list=['Scan','Seeds','Tools','Settings']))
 assert host.next_event()==dict(event='screen_ready',request=1)
 assert sink.frames>before and sink.pending==0
 before=sink.frames;sink.event.clear()
 host.send('key',key=19,pressed=True);host.send('key',key=19,pressed=False)
 assert sink.event.wait(3) and sink.frames>before and sink.pending==0
 assert host.events.empty()
 print(json.dumps(dict(passed=True,frames=sink.frames,rectangles=sink.rectangles,pixelsBeforeCompletion=True,incrementalUpdateCompleted=True,commandAckUndisplaced=True,completionNotQueued=True,physicalDisplay=False)),flush=True)
finally:host.close()
