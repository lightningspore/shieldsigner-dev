"""Native I/O button, camera plane color, clear and rejection checks; public pixels."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from transport import NativeHost
frame=bytearray(115200)
def pixels(area,data):
    x1,y1,x2,y2=area;stride=(x2-x1+1)*2
    for row,y in enumerate(range(y1,y2+1)):frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
host=NativeHost(sys.argv[1],pixels)
def wait(event):
    value=host.next_event();assert value.get('event')==event,value
    return value
try:
    host.send('screen',name='io_test_screen',request=1,config=dict(top_nav=dict(title='Public I/O'),capturing_text='Capturing image...',clear_label='Clear',exit_label='Exit'))
    wait('screen_ready')
    for key in (17,18,20,19,10):
        before=bytes(frame);host.send('key',key=key,pressed=True);host.send('io_state',state=0);wait('io_state_ready')
        assert bytes(frame)!=before,key
        host.send('key',key=key,pressed=False);time.sleep(.2)
        host.send('io_state',state=0);wait('io_state_ready')
    for key,name in ((49,'KEY1'),(50,'KEY2'),(51,'KEY3')):
        host.send('key',key=key,pressed=True);assert wait('aux_key')['key']==name
        host.send('key',key=key,pressed=False)
    host.send('io_frame',hex=(b'\0\xf8'*57600).hex());wait('io_frame_ready')
    red=sum(frame[i:i+2]==b'\xf8\0' for i in range(0,len(frame),2));assert red>1000,red
    host.send('io_state',state=0);wait('io_state_ready')
    assert not any(frame[i:i+2]==b'\xf8\0' for i in range(0,len(frame),2))
    for value in ('00','z'*230400):
        host.send('io_frame',hex=value);wait('error')
    host.send('io_state',state=3);wait('error')
    host.send('clear');wait('screen_cleared');host.send('io_state',state=0);wait('error')
    print(json.dumps(dict(passed=True,dpadAndClickFlashed=5,auxKeysForwarded=3,redPlanePixels=red,rgb565ByteOrderVerified=True,clearHidStill=True,malformedRequestsRejected=3,inactiveRejected=True,processAlive=host.child.poll() is None,physicalDisplay=False)),flush=True)
finally:host.close()
