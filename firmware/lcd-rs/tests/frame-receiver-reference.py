"""Compiled PyO3 socket fixture; no camera, GPIO or private data."""
import json
import socket
import struct
import threading
import time
from shieldsigner_lcd import FrameReceiver

left,right=socket.socketpair()
receiver=FrameReceiver(left.fileno(),2,2,framerate=120)
right.sendall(struct.pack('<8sIIII',b'SSNV12F1',2,2,42,6)+bytes([0,255,128,1,9,8]))
a=receiver.read(0,1)
b=receiver.read(1,1)
assert a.sequence==b.sequence==42
assert a.size==(2,2) and a.format=='nv12'
assert a.luma_bytes()==bytes([0,255,128,1])
assert receiver.read(0,.01) is None
# Python can run while read waits; cancellation reaps only the native thread.
progress=[]
done=threading.Event()
def observe():
    while not done.wait(.01):progress.append(1)
t=threading.Thread(target=observe);t.start()
try:assert receiver.read(2,.15).sequence==42
finally:done.set();t.join()
# Consumer 2 had a fresh frame, so exercise a genuine wait separately.
t=threading.Thread(target=observe);done.clear();t.start()
try:assert receiver.read(2,.15) is None
finally:done.set();t.join()
assert len(progress)>=5
blocked=[]
def wait_for_next():
    blocked.append(receiver.read(0,1))
waiter=threading.Thread(target=wait_for_next);waiter.start()
time.sleep(.03)
start=time.monotonic();receiver.close();receiver.close()
waiter.join(.3)
assert not waiter.is_alive() and blocked==[None]
assert time.monotonic()-start<.3
assert receiver.statistics()==(1,0,True)
assert a.luma_bytes()==bytes([0,255,128,1]) # frame outlives receiver
# The original descriptor is still owned by Python and remains usable.
left.sendall(b'X');assert right.recv(1)==b'X'
left.close();right.close()
print(json.dumps({'passed':True,'independentConsumers':True,'immutableFrameOutlivesReceiver':True,
 'callerFdPreserved':True,'closeIdempotent':True,'pythonProgressDuringWait':len(progress),'hardwareTouched':False},indent=2))
