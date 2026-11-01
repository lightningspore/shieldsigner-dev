"""Native preview framing, RGB order, both orientations, Back and cleanup."""
import json
import sys
import time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
from transport import NativeHost
from resources import process_snapshot
hardware=None
if '--display' in sys.argv:
    from luckfox import LuckfoxHardware
    hardware=LuckfoxHardware()
frame=bytearray(240*240*2)
def pixels(area,data):
    x1,y1,x2,y2=area;stride=(x2-x1+1)*2
    for row,y in enumerate(range(y1,y2+1)):frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
    if hardware is not None:hardware.pixels(area,data)
host=NativeHost(sys.argv[1],pixels)
snapshots=[]
def sample(stage):
    native=process_snapshot(host.child.pid) if Path('/proc/self/status').is_file() else None
    snapshots.append(dict(stage=stage,native=native))
sample("ready")
def until(name):
    while True:
        event=host.next_event()
        if event.get('event')=='error':raise AssertionError(event)
        if event.get('event')==name:return event
try:
    center=(120*240+120)*2
    host.send('scan',instructions='< back | Public preview test',request=1);until('screen_ready')
    assert not any(frame[center:center+2]),'First preview must start black'
    sample('preview-before-pixels')
    for width,height in [(240,180),(180,240)]:
        host.send_preview(width,height,bytes([80,160,240])*(240*180));until('preview_ready')
        center=(120*240+120)*2
        assert int.from_bytes(frame[center:center+2],'big')==((80>>3)<<11)|((160>>2)<<5)|(240>>3)
    pattern=(bytes(range(256))*507)[:240*180*3]
    host.send_preview(240,180,pattern);until('preview_ready')
    offset=(90*240+120)*3
    r,g,b=pattern[offset:offset+3]
    expected=((r>>3)<<11)|((g>>2)<<5)|(b>>3)
    assert int.from_bytes(frame[center:center+2],'big')==expected
    sample('preview-after-pixels')
    host.send('key',key=20,pressed=True);time.sleep(.1);host.send('key',key=20,pressed=False)
    event=until('button_selected');assert event['index']==1000
    host.send('scan_stop');until('scan_stopped');assert not any(frame)
    sample('stopped')
    for restart in range(3):
        host.send('scan',instructions='Public restart',request=restart+2);until('screen_ready')
        assert not any(frame[center:center+2]),'A previous frame survived preview restart'
        host.send_preview(240,180,bytes([240,80,160])*(240*180));until('preview_ready')
        assert any(frame[center:center+2])
        host.send('clear');until('screen_cleared');assert not any(frame)
    # One write queues a new scan behind clear; capacity release must retain it.
    packet=b'{"op":"clear"}\n{"op":"scan","instructions":"Public queued restart","request":101}\n'
    with host._write_lock:assert host.child.stdin.write(packet)==len(packet)
    until('screen_cleared');until('screen_ready')
    assert not any(frame[center:center+2])
    host.send('clear');until('screen_cleared')
    sample('final-stopped')
    print(json.dumps(dict(passed=True,queuedCommandPreserved=True,resourceSnapshots=snapshots,blackBeforeFirstFrame=True,blackAcrossRestarts=3,orientations=2,rgbOrder=True,binaryNewlinesPreserved=True,backSentinel=True,blackOnStop=True,physicalDisplay=hardware is not None)))
finally:
    host.close()
    if hardware is not None:hardware.close()
