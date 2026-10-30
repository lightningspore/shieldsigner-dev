"""Real compiled receiver with synthetic sockets; no V4L2 or GPIO."""
import socket
import struct
import tempfile
import threading
import time
import unittest
from pathlib import Path
from shieldsigner_native_stream import NativeVideoStream


def packet(sequence=1):
    return struct.pack('<8sIIII', b'SSNV12F1', 2, 2, sequence, 6)+bytes([sequence]*6)


class NativeStreamTests(unittest.TestCase):
    def test_external_socket_frame_and_clean_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            path=str(Path(directory)/'camera.sock')
            server=socket.socket(socket.AF_UNIX);server.bind(path);server.listen(1)
            release=threading.Event()
            def serve():
                peer,_=server.accept()
                with peer:
                    peer.sendall(packet(3));release.wait(2)
            worker=threading.Thread(target=serve);worker.start()
            stream=NativeVideoStream(socket_path=path,width=2,height=2,transport='nv12',consumer_framerate=120).start()
            try:
                frame=None
                for _ in range(10):
                    frame=stream.read()
                    if frame is not None:break
                self.assertIsNotNone(frame);self.assertEqual(frame.sequence,3)
                start=time.monotonic();stream.stop();self.assertLess(time.monotonic()-start,.4)
                self.assertFalse(stream._thread.is_alive())
                self.assertEqual(frame.luma_bytes(),bytes([3]*4))
            finally:
                release.set();stream.stop();worker.join();server.close()

    def test_rejected_second_start_preserves_active_receiver_and_consumers(self):
        import types
        stream=NativeVideoStream(width=2,height=2,transport='nv12')
        stream._thread=types.SimpleNamespace(is_alive=lambda:True)
        receiver=object();stream._native_receiver=receiver
        stream._native_consumers={123:0}
        with self.assertRaises(RuntimeError):stream.start()
        self.assertIs(stream._native_receiver,receiver)
        self.assertEqual(stream._native_consumers,{123:0})

    def test_connect_timeout_after_disconnect_uses_remaining_retry_budget(self):
        class Owner:
            def poll(self):return None
        class ManagedFixture(NativeVideoStream):
            connect_calls=0
            def _connect(self,deadline):
                self._owner=Owner();self.connect_calls+=1
                if self.connect_calls==2:raise TimeoutError('Injected reconnect timeout')
                return super()._connect(deadline)
            def _finish_owner(self):self._owner=None
        with tempfile.TemporaryDirectory() as directory:
            path=str(Path(directory)/'camera.sock')
            server=socket.socket(socket.AF_UNIX);server.bind(path);server.listen(2);server.settimeout(2)
            release=threading.Event()
            def serve():
                peer,_=server.accept()
                with peer:peer.sendall(packet(1))
                peer,_=server.accept()
                with peer:peer.sendall(packet(2));release.wait(2)
            worker=threading.Thread(target=serve);worker.start()
            stream=ManagedFixture(socket_path=path,width=2,height=2,transport='nv12',frame_timeout=.5).start()
            try:
                deadline=time.monotonic()+2;frame=None
                while time.monotonic()<deadline:
                    frame=stream.read()
                    if frame is not None and frame.sequence==2:break
                self.assertIsNotNone(frame);self.assertEqual(frame.sequence,2)
                self.assertEqual(stream.connect_calls,3)
                self.assertEqual(stream.reconnects,2)
            finally:
                release.set();stream.stop();worker.join();server.close()

    def test_reconnect_timeouts_exhaust_the_consecutive_budget(self):
        class Owner:
            def poll(self):return None
        class ManagedFixture(NativeVideoStream):
            connect_calls=0
            def _connect(self,deadline):
                self._owner=Owner();self.connect_calls+=1
                if self.connect_calls>1:raise TimeoutError('Injected reconnect timeout')
                left,right=socket.socketpair();right.close()
                return left
            def _finish_owner(self):self._owner=None
        stream=ManagedFixture(width=2,height=2,transport='nv12',reconnect_attempts=2).start()
        try:
            stream._thread.join(2)
            self.assertFalse(stream._thread.is_alive())
            self.assertEqual(stream.connect_calls,3)
            self.assertEqual(stream.reconnects,2)
            self.assertIsInstance(stream.error,RuntimeError)
            self.assertIn('retry budget exhausted',str(stream.error))
        finally:stream.stop()

    def test_managed_transport_reconnect_and_protocol_failure_is_terminal(self):
        class Owner:
            def poll(self):return None
        class ManagedFixture(NativeVideoStream):
            def _connect(self,deadline):
                self._owner=Owner()
                return super()._connect(deadline)
            def _finish_owner(self):self.finished=True;self._owner=None
        for malformed in (False,True):
            with self.subTest(malformed=malformed),tempfile.TemporaryDirectory() as directory:
                path=str(Path(directory)/'camera.sock')
                server=socket.socket(socket.AF_UNIX);server.bind(path);server.listen(2);server.settimeout(2)
                release=threading.Event()
                def serve():
                    peer,_=server.accept()
                    with peer:
                        if malformed:
                            bad=bytearray(packet());bad[0]=0;peer.sendall(bad);release.wait(1)
                        else:peer.sendall(packet(1))
                    if not malformed:
                        peer,_=server.accept()
                        with peer:peer.sendall(packet(2));release.wait(2)
                worker=threading.Thread(target=serve);worker.start()
                stream=ManagedFixture(socket_path=path,width=2,height=2,transport='nv12',frame_timeout=.5).start()
                try:
                    deadline=time.monotonic()+2
                    if malformed:
                        while stream.error is None and time.monotonic()<deadline:time.sleep(.01)
                        self.assertIsInstance(stream.error,ValueError)
                        self.assertEqual(stream.reconnects,0)
                    else:
                        frame=None
                        while time.monotonic()<deadline:
                            frame=stream.read()
                            if frame is not None and frame.sequence==2:break
                        self.assertIsNotNone(frame);self.assertEqual(frame.sequence,2)
                        self.assertEqual(stream.reconnects,1)
                    stream.stop();self.assertTrue(stream.finished)
                finally:
                    release.set();stream.stop();worker.join();server.close()


if __name__=='__main__':unittest.main()
