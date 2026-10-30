"""Native adapter pixel/rotation contracts using the compiled extension."""
import os
import socket
import struct
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from shieldsigner_lcd import FrameReceiver
from shieldsigner_camera_compat import VideoStream
from shieldsigner_native_camera import NativeCameraStream
from shieldsigner_native_stream import NativeVideoStream
from shieldsigner_integration import install_native_preview, IMAGE_CAMERA_SOURCE_SHA256
from shieldsigner_qr_decoder import RustTransportQrReader


def native_frame(pixels, mode='nv12'):
    left,right=socket.socketpair()
    receiver=FrameReceiver(left.fileno(),640,480,mode,framerate=120)
    packet=struct.pack('<8sIIII',b'SSNV12F1' if mode=='nv12' else b'SSRGB001',640,480,1,len(pixels))+pixels
    sender=threading.Thread(target=right.sendall,args=(packet,));sender.start()
    try:
        frame=receiver.read(0,1);sender.join();assert frame is not None
        return frame
    finally:
        receiver.close();left.close();right.close()


class NativeCameraTests(unittest.TestCase):
    def test_preview_rotations_and_entropy_shape(self):
        y=bytes(range(256))*1200
        frame=native_frame(y+bytes(640*480//2))
        with patch.dict(os.environ,{'SHIELDSIGNER_FRONTEND_BACKEND':'rust','SHIELDSIGNER_SMALL_RAM':'1'}):
            stream=VideoStream(framerate=6)
        self.assertIsInstance(stream,NativeCameraStream)
        original=Image.frombytes('L',(640,480),y)
        with patch.object(NativeVideoStream,'read',return_value=frame):
            self.assertIs(stream.read(),frame)
            entropy=stream.read(display=True)
            self.assertEqual((entropy.mode,entropy.size),('RGB',(640,480)))
            self.assertEqual(entropy.convert('L').tobytes(),y)
            for rotation in (0,90,180,270):
                expected=original.resize((240,180),Image.Resampling.NEAREST).convert('RGB').rotate(rotation,expand=True)
                actual=stream.read_native_preview(rotation)
                self.assertEqual(actual.size,expected.size)
                self.assertEqual(actual.tobytes(),expected.tobytes())
            # Guarded Camera wrapper rotates once and bypasses the old PIL path.
            class Camera:
                _video_stream=stream
                _camera_rotation=180
                def read_video_stream(self,**kwargs):return 'legacy'
            module=types.SimpleNamespace(Camera=Camera,__shieldsigner_camera_patch__={'sourceSha256':IMAGE_CAMERA_SOURCE_SHA256})
            with patch.dict(os.environ,{'SHIELDSIGNER_FRONTEND_BACKEND':'rust'}):install_native_preview(module)
            camera=Camera()
            self.assertEqual(camera.read_video_stream(as_image=True,preview=True).tobytes(),stream.read_native_preview(270).tobytes())
            self.assertEqual(camera.read_video_stream(as_image=True),'legacy')

    def test_true_rgb_still_pixels_preserved(self):
        rgb=bytes((7,83,231))*(640*480)
        frame=native_frame(rgb,'rgb')
        with patch.dict(os.environ,{'SHIELDSIGNER_FRONTEND_BACKEND':'rust','SHIELDSIGNER_SMALL_RAM':'1'}):stream=VideoStream(for_still=True)
        self.assertEqual(stream.transport,'rgb')
        with patch.object(NativeVideoStream,'read',return_value=frame):
            actual=stream.read(display=True)
        self.assertEqual((actual.mode,actual.size),('RGB',(640,480)))
        self.assertEqual(actual.tobytes(),rgb)

    def test_direct_native_qr_adapter_binary_and_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            worker=Path(directory)/'worker'
            worker.write_text('#!'+sys.executable+'\n'+'''import struct,sys
sys.stdout.buffer.write(b'SSQR001\\n');sys.stdout.buffer.flush()
while True:
 h=sys.stdin.buffer.read(12)
 if len(h)!=12:break
 _,w,height=struct.unpack('<4sII',h)
 data=sys.stdin.buffer.read(w*height)
 if len(data)!=w*height:break
 answer=data[:17]
 sys.stdout.buffer.write(b'QRO1'+struct.pack('<I',len(answer))+answer);sys.stdout.buffer.flush()
''')
            worker.chmod(0o700)
            frame=native_frame(bytes(range(256))*1200+bytes(640*480//2))
            client=RustTransportQrReader(str(worker))
            try:
                self.assertEqual(client.decode(frame),bytes(range(17)))
                self.assertEqual(client.decode(frame),bytes(range(17)))
                self.assertEqual((client.stats['starts'],client.stats['calls']),(1,2))
            finally:client.close()
            self.assertEqual(client.stats['lastExitCode'],0)


if __name__=='__main__':unittest.main()
