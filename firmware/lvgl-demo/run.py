"""Temporary demo adapter: existing LCD initialization, native LVGL pixels.

Run only after stopping the regular app/supervisor. No installed files change.
KEY3 exits; reboot restores the normal app. /tmp/lvgl-demo-input accepts u/d/p.
"""
import os
import select
import signal
import struct
import subprocess
import sys
import time
import threading
import json
from pathlib import Path
sys.path.insert(0, '/opt/src')
from seedsigner.hardware.displays.ST7789 import ST7789
from seedsigner.hardware.buttons import HardwareButtons

sys.path.insert(0, '/usr/lib/shieldsigner-camera/python')
os.environ['SHIELDSIGNER_SMALL_RAM'] = '1'
stop = False
camera_stop = threading.Event()
def camera_worker():
    from shieldsigner_native_stream import NativeVideoStream
    from shieldsigner_lcd import PreviewRenderer
    stream = None
    try:
        stream = NativeVideoStream(owner_config=json.loads(Path('/usr/lib/shieldsigner-camera/owner.json').read_text()), transport='nv12', consumer_framerate=5).start()
        renderer = PreviewRenderer(160,240)
        while not camera_stop.is_set():
            image = stream.read()
            if image is None: continue
            width,height,pixels = renderer.render_frame(image,90)
            assert (width,height)==(240,160)
            Path('/tmp/lvgl-camera-next.rgb').write_bytes(pixels)
            os.replace('/tmp/lvgl-camera-next.rgb','/tmp/lvgl-camera.rgb')
    except Exception as exc:
        print('Camera demo error:', repr(exc), flush=True)
    finally:
        if stream is not None:
            try: stream.stop()
            except Exception as exc: print('Camera cleanup:', repr(exc), flush=True)
        Path('/tmp/lvgl-camera.rgb').unlink(missing_ok=True)
        print('Camera demo owner stopped',flush=True)
camera_thread = None

def shutdown(*_):
    global stop
    stop = True
signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)
lcd = None
child = None
buttons = None
fifo = Path('/tmp/lvgl-demo-input')
frame = bytearray(240*240*2)
try:
    Path('/tmp/lvgl-demo-page').unlink(missing_ok=True)
    Path('/tmp/lvgl-camera.rgb').unlink(missing_ok=True)
    lcd = ST7789(240,240)
    lcd._ensure_initialized()
    lcd.set_color_inversion(False)
    buttons = HardwareButtons.get_instance()
    child = subprocess.Popen(['/tmp/lvgl-demo'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,bufsize=0)
    fifo.unlink(missing_ok=True)
    os.mkfifo(fifo,0o600)
    control = os.open(fifo,os.O_RDWR|os.O_NONBLOCK)
    pending = bytearray()
    previous = set()
    low_since = {}
    last_capture = 0
    keys = {'KEY_UP':'u','KEY_DOWN':'d','KEY_PRESS':'p','KEY_LEFT':'b','KEY2':'b','KEY1':'p','KEY3':'q'}
    print('LVGL demo running; KEY3 exits. Up/Down/Press navigate.',flush=True)
    while not stop and child.poll() is None:
        ready,_,_ = select.select([child.stdout,control],[],[],0.01)
        if control in ready:
            for key in os.read(control,32):
                if chr(key) in 'udpbq': child.stdin.write(bytes([key]))
        if child.stdout in ready:
            data = os.read(child.stdout.fileno(),16384)
            if not data: break
            pending.extend(data)
        while len(pending)>=8:
            x1,y1,x2,y2=struct.unpack_from('<4H',pending)
            if not(0<=x1<=x2<240 and 0<=y1<=y2<240): raise ValueError('Invalid LVGL rectangle')
            size=(x2-x1+1)*(y2-y1+1)*2
            if len(pending)<size+8: break
            raw=bytes(pending[8:8+size]); del pending[:8+size]
            lcd.SetWindows(x1,y1,x2+1,y2+1)
            lcd._dc.write(True)
            lcd._chunked_transfer(raw)
            stride=(x2-x1+1)*2
            for row,y in enumerate(range(y1,y2+1)):
                frame[(y*240+x1)*2:(y*240+x2+1)*2]=raw[row*stride:(row+1)*stride]
        now=time.monotonic()
        try: page = Path('/tmp/lvgl-demo-page').read_text().strip()
        except FileNotFoundError: page = '0'
        if page == '1' and camera_thread is None:
            camera_stop.clear()
            camera_thread = threading.Thread(target=camera_worker,daemon=True)
            camera_thread.start()
        elif page != '1' and camera_thread is not None:
            camera_stop.set()
            camera_thread.join(timeout=10)
            if camera_thread.is_alive(): raise TimeoutError('Camera demo did not stop')
            camera_thread = None
        active=set()
        for name,key in keys.items():
            pin=buttons._gpio_pins.get(name)
            if pin is not None and not pin.read():
                low_since.setdefault(name,now)
                if now-low_since[name]>=0.025: active.add(name)
            else: low_since.pop(name,None)
        for name in active-previous: child.stdin.write(keys[name].encode())
        previous=active
        if now-last_capture>1:
            Path('/tmp/lvgl-demo.rgb565').write_bytes(frame)
            last_capture=now
finally:
    camera_stop.set()
    if camera_thread is not None: camera_thread.join(timeout=10)
    if child is not None:
        child.terminate()
        try: child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            child.kill(); child.wait()
    if buttons is not None:
        for pin in buttons._gpio_pins.values(): pin.close()
    if lcd is not None: lcd.close()
    fifo.unlink(missing_ok=True)
    print('LVGL demo stopped; reboot to restore SeedSigner.',flush=True)
