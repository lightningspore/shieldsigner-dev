"""Exercise native protocol bounds, byte preservation, failure and restart."""
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image
from shieldsigner_qr_decoder import NativeQrReader

FAKE = '''import os,struct,sys,time
r=sys.stdin.buffer;w=sys.stdout.buffer
def read(n):
 data=b""
 while len(data)<n:
  chunk=r.read(n-len(data))
  if not chunk:sys.exit(0)
  data+=chunk
 return data
w.write(b"SSQR001\\n");w.flush()
while True:
 magic,width,height=struct.unpack("<4sII",read(12));pixels=read(width*height)
 if pixels[0]==1:sys.exit(2)
 if pixels[0]==2:time.sleep(3)
 if pixels[0]==3:w.write(struct.pack("<4sI",b"BAD!",9000));w.flush();continue
 data=None if pixels[0]==255 else b"\\x00\\xff\\x80"
 w.write(struct.pack("<4sI",b"QRO1",0xffffffff if data is None else len(data)))
 if data is not None:w.write(data)
 w.flush()
'''


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        worker = Path(self.temp.name)/"worker"
        worker.write_text("#!"+sys.executable+"\n"+FAKE)
        worker.chmod(0o755)
        self.reader = NativeQrReader(worker, timeout=.4)

    def tearDown(self):
        self.reader.close()
        self.temp.cleanup()

    def test_binary_reuse_and_no_result(self):
        frame = Image.new("RGB", (40, 40), (40, 40, 40))
        self.assertEqual(self.reader.decode(frame), b"\x00\xff\x80")
        pid = self.reader._process.pid
        self.assertEqual(self.reader.decode(frame), b"\x00\xff\x80")
        self.assertIsNone(self.reader.decode(Image.new("L", (40,40), 255)))
        self.assertEqual(pid, self.reader._process.pid)
        self.assertEqual(self.reader.stats["starts"], 1)

    def test_failure_cleanup_and_restart(self):
        for value in [1, 2, 3]:
            with self.subTest(value=value):
                with self.assertRaises((OSError, RuntimeError)):
                    self.reader.decode(Image.new("L", (20,20), value))
                self.assertIsNone(self.reader._process)
                self.assertEqual(self.reader.decode(Image.new("L", (20,20), 40)), b"\x00\xff\x80")
                process = self.reader._process
                self.reader.close()
                self.assertIsNotNone(process.poll())

    def test_invalid_dimensions_do_not_start(self):
        with self.assertRaises(ValueError):
            self.reader.decode(Image.new("L", (1921,1)))
        self.assertIsNone(self.reader._process)


if __name__ == "__main__":
    unittest.main()
