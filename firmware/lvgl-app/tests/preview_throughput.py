"""Eight public preview transport round trips; optional physical LCD sink."""
import json,statistics,sys,time
from transport import NativeHost
hardware=None;rectangles=0
if '--display' in sys.argv:
    sys.path.insert(0,'/opt/src')
    from luckfox import LuckfoxHardware
    hardware=LuckfoxHardware()
def pixels(area,data):
    global rectangles
    rectangles+=1
    if hardware is not None:hardware.pixels(area,data)
host=NativeHost(sys.argv[1],pixels);samples=[]
try:
    host.send('scan',instructions='Public transport timing',request=1)
    assert host.next_event()==dict(event='screen_ready',request=1)
    for index in range(8):
        frame=bytes((20+index,80,120))*(240*180)
        started=time.perf_counter();host.send_preview(240,180,frame)
        assert host.next_event()==dict(event='preview_ready')
        samples.append(time.perf_counter()-started)
    host.send('scan_stop');assert host.next_event()==dict(event='scan_stopped')
    print(json.dumps(dict(passed=True,samplesSeconds=samples,medianSeconds=statistics.median(samples),rectangles=rectangles,physicalDisplay=hardware is not None,cameraStarted=False,scope='Sequential preview IPC+render/flush acknowledgements, public RGB frames; not camera FPS or end-to-end QR latency.')),flush=True)
finally:
    host.close()
    if hardware is not None:hardware.close()
