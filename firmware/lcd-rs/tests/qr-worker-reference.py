"""Exercise compiled PyO3 QR protocol/lifecycle using a disposable fake worker."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
from shieldsigner_lcd import QrWorker

with tempfile.TemporaryDirectory() as directory:
    worker=Path(directory)/'worker'
    worker.write_text('#!'+sys.executable+'\n'+'''import os,struct,sys,time
os.write(1,b'SSQR001\\n')
while True:
 h=sys.stdin.buffer.read(12)
 if len(h)!=12:break
 magic,w,hgt=struct.unpack('<4sII',h)
 data=sys.stdin.buffer.read(w*hgt)
 if len(data)!=w*hgt:break
 if data[0]==0:answer=b'QRO1'+struct.pack('<I',0xffffffff)
 elif data[0]==1:answer=b'QRO1'+struct.pack('<I',6)+b'\\x00\\xff\\n\\r\\x00\\x80'
 elif data[0]==2:answer=b'QRO1'+struct.pack('<I',0)
 elif data[0]==3:answer=b'QRO1'+struct.pack('<I',8193)
 else:
  time.sleep(.2)
  answer=b'QRO1'+struct.pack('<I',1)+b'X'
 for b in answer:os.write(1,bytes([b]))
''')
    worker.chmod(0o700)
    client=QrWorker(str(worker),1)
    assert client.worker_pid is None
    assert client.decode_luma(bytes([1,0,0,0]),2,2)==b'\x00\xff\n\r\x00\x80'
    pid=client.worker_pid
    assert client.decode_luma(bytes(4),2,2) is None
    assert client.decode_luma(bytes([2,0,0,0]),2,2)==b''
    assert client.worker_pid==pid
    try:client.decode_luma(bytes([3,0,0,0]),2,2)
    except OSError:pass
    else:raise AssertionError('Oversized response accepted')
    assert client.worker_pid is None
    assert client.decode_luma(bytes([1,0,0,0]),2,2)==b'\x00\xff\n\r\x00\x80'
    # A native I/O wait must allow the Python observer to run.
    progressed=[]
    done=threading.Event()
    def observe():
        while not done.wait(.01):progressed.append(1)
    observer=threading.Thread(target=observe);observer.start()
    try:assert client.decode_luma(bytes([4,0,0,0]),2,2)==b'X'
    finally:done.set();observer.join()
    assert len(progressed)>=5,progressed
    stats=client.statistics()
    assert stats[:4]==(2,5,4,1),stats
    current=client.worker_pid
    client.close();client.close()
    assert client.worker_pid is None
    try:os.kill(current,0)
    except ProcessLookupError:pass
    else:raise AssertionError('Worker not reaped')
    for data,w,h in [(b'',0,1),(b'x',2,2)]:
        try:client.decode_luma(data,w,h)
        except ValueError:pass
        else:raise AssertionError('Invalid input accepted')
    assert client.worker_pid is None
print(json.dumps({'binaryPayloadExact':True,'emptyDistinctFromNoSymbol':True,'workerReused':True,'oversizedReplyRejected':True,'freshWorkerRecovery':True,'closeReapedOwnedPid':True,'pythonObserverIterationsDuringNativeIo':len(progressed),'statistics':stats,'hardwareTouched':False},indent=2))
