"""Native partial frames → scaler, compared to pinned original resize method."""
import ast,array,json,sys,threading
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
from guards import verify
from transport import NativeHost
from display_scaler import FrameScaler
verify('/opt/src',Path(__file__).parent/'source-guards.json')
source=Path('/opt/src/seedsigner/gui/renderer.py').read_text()
cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='Renderer')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_resize_for_display')
namespace={'Image':Image};exec(compile(ast.Module(body=[method],type_ignores=[]),'<original resize>','exec'),namespace)
resize=namespace['_resize_for_display'];original=SimpleNamespace(_needs_resize=True,_display_size=(128,128))
class Sink:
 def __init__(self):self.scaler=FrameScaler();self.reference=bytearray(240*240*2);self.frames=0;self.rectangles=0;self.event=threading.Event()
 def pixels(self,area,data):
  self.scaler.update(area,data);self.rectangles+=1
  x1,y1,x2,y2=area;stride=(x2-x1+1)*2
  for row,y in enumerate(range(y1,y2+1)):self.reference[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
 def frame_complete(self):
  actual=self.scaler.complete();assert actual is not None
  words=array.array('H',self.reference);words.byteswap()
  image=Image.frombytes('RGB',(240,240),words.tobytes(),'raw','BGR;16');expected=resize(original,image)
  try:
   assert actual.size==(128,128) and actual.tobytes()==expected.tobytes()
  finally:actual.close();expected.close();image.close()
  self.frames+=1;self.event.set()
sink=Sink();host=NativeHost(sys.argv[1],sink.pixels)
try:
 host.send('screen',name='main_menu_screen',request=1,config=dict(top_nav=dict(title='Home',show_power_button=True),button_list=['Scan','Seeds','Tools','Settings']))
 assert host.next_event()==dict(event='screen_ready',request=1) and sink.frames>0
 before=sink.frames;sink.event.clear();host.send('key',key=19,pressed=True);host.send('key',key=19,pressed=False)
 assert sink.event.wait(3) and sink.frames>before
finally:host.close()
sink.scaler.wipe();assert not any(sink.scaler.buffer) and sink.scaler.complete() is None
print(json.dumps(dict(passed=True,frames=sink.frames,rectangles=sink.rectangles,realNativeAndTransport=True,originalResizeMethodExact=True,fullAndIncrementalFrames=True,retainedScalerBufferZeroed=True,physicalDisplay=False,ST7735DriverConnected=False)),flush=True)
