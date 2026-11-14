"""Host PTY check: the real capture helper must preserve all 256 byte values."""
import base64
import os
from pathlib import Path
import pty
import subprocess
import sys
import unittest

HELPER = Path(__file__).resolve().parents[1]/'tools/capture_uart.py'

class CaptureTest(unittest.TestCase):
    def test_binary_bytes_survive_line_transport(self):
        master, slave = pty.openpty()
        proc = subprocess.Popen([sys.executable, str(HELPER), os.ttyname(slave), '115200', '0.5'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            self.assertEqual(proc.stdout.readline().strip(), b'@@CAPTURE_READY')
            payload = bytes(range(256))*4
            os.write(master, payload)
            stdout, stderr = proc.communicate(timeout=5)
            self.assertEqual(proc.returncode, 0, stderr)
            received = b''.join(base64.b64decode(line.split()[1], validate=True)
                                for line in stdout.splitlines() if line.startswith(b'@@DATA '))
            self.assertEqual(received, payload)
        finally:
            if proc.poll() is None:
                proc.kill(); proc.wait()
            os.close(master); os.close(slave)

if __name__ == '__main__':
    unittest.main()
