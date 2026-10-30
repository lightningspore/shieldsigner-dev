#!/usr/bin/env python3
"""Off-board packed-ARM frame-path allocations; no GPIO, entropy or GUI claim.

Uses the guarded Camera.read_video_stream method with an uninitialized Camera
shell and a real synthetic socket stream. Native Vec/Pillow allocations are
not fully visible to tracemalloc; compare ordinary PSS separately.
"""
import argparse
import json
import hashlib
import os
from pathlib import Path
import socket
import struct
import sys
import tempfile
import threading
import time
import tracemalloc

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('root',type=Path);p.add_argument('--runtime-python',type=Path,required=True)
p.add_argument('--native-extension-root',type=Path,required=True)
p.add_argument('--backend',choices=['python','rust'],required=True)
a=p.parse_args();root=a.root.resolve()
sys.path[:0]=[str(a.runtime_python.resolve()),str(a.native_extension_root.resolve()),str(root/'usr/lib/shieldsigner-camera/python'),str(root/'opt/src')]
os.environ.pop('SHIELDSIGNER_CAMERA_CONFIG',None)
os.environ['SHIELDSIGNER_FRONTEND_BACKEND']=a.backend
os.environ['SHIELDSIGNER_SMALL_RAM']='1'
os.environ['SHIELDSIGNER_QR_READER']=str(root/'usr/lib/shieldsigner-camera/shieldsigner-qr-reader')
import shieldsigner_lcd
native_sha=hashlib.sha256(Path(shieldsigner_lcd.__file__).read_bytes()).hexdigest()
from shieldsigner_integration import install_camera_backend
from shieldsigner_camera_compat import VideoStream
module=install_camera_backend(root/'opt/src')
# Explicit diagnostic shell: exercise the actual read/rotation methods without
# configuring GPIO, Settings, Controller instances or the physical camera.
camera=module.Camera.__new__(module.Camera)
camera._camera_rotation=0;camera._runtime_profile='luckfox_22'
y=bytes(range(256))*1200
payload=y+bytes([128])*(640*480//2)
packet=struct.pack('<8sIIII',b'SSNV12F1',640,480,1,len(payload))+payload
with tempfile.TemporaryDirectory() as directory:
    path=str(Path(directory)/'camera.sock')
    server=socket.socket(socket.AF_UNIX);server.bind(path);server.listen(1)
    done=threading.Event()
    def send():
        peer,_=server.accept()
        with peer:
            while not done.is_set():
                try:peer.sendall(packet)
                except OSError:break
                done.wait(.01)
    sender=threading.Thread(target=send);sender.start()
    stream=VideoStream(framerate=120);stream.socket_path=path;camera._video_stream=stream
    tracemalloc.start(1)
    try:
        stream.start()
        def prepare(n):
            images=0;deadline=time.monotonic()+15
            while images<n and time.monotonic()<deadline:
                image=camera.read_video_stream(as_image=True,preview=True)
                if image is not None:
                    assert image.size==(180,240)
                    images+=1
            assert images==n
        prepare(20)
        before,_=tracemalloc.get_traced_memory();tracemalloc.reset_peak()
        prepare(40)
        current,peak=tracemalloc.get_traced_memory()
        snapshot=tracemalloc.take_snapshot()
        blocks=sum(stat.count for stat in snapshot.statistics('filename'))
        del snapshot
        frames=stream.frames_received
    finally:
        tracemalloc.stop();done.set();stream.stop();sender.join();server.close();module.__shieldsigner_qr_client__.close()
print(json.dumps({'backend':a.backend,'nativeExtensionSha256':native_sha,'warmupPreviews':20,'measuredPreviews':40,
 'tracedBytesBeforeSteady':before,'tracedLiveBytesAfterSteady':current,'tracedPeakBytesDuringSteady':peak,
 'tracedPeakAboveSteadyStartBytes':peak-before,'liveTracedBlocksAfterSteady':blocks,'framesReceived':frames,
 'nativePoolPayloadBytesNotFullyTraced':3*640*480*3//2 if a.backend=='rust' else None,
 'nativeReusablePreviewBytesNotFullyTraced':240*180*3 if a.backend=='rust' else None,
 'scope':'Actual guarded Camera read/preview adapter and socket receiver under packed ARM Python/QEMU; no initialized Controller or GUI',
 'hardwareTouched':False,'targetPssMeasured':False},indent=2))
