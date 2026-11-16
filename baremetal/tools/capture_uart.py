"""REF-side bounded UART capture; base64-framed stdout survives the REF ADB PTY."""

import base64
import os
import select
import sys
import termios
import time

port, baud, duration = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
a = termios.tcgetattr(fd)
a[0], a[1], a[2], a[3] = 0, 0, termios.CS8 | termios.CLOCAL | termios.CREAD, 0
a[4] = a[5] = getattr(termios, 'B' + str(baud))
a[6][termios.VMIN] = a[6][termios.VTIME] = 0
termios.tcsetattr(fd, termios.TCSANOW, a)
actual = termios.tcgetattr(fd)
if actual[4:6] != a[4:6]:
    os.close(fd)
    raise RuntimeError('UART baud readback does not match requested baud')
termios.tcflush(fd, termios.TCIFLUSH)
print('@@CAPTURE_READY', flush=True)
end = time.monotonic() + duration
try:
    while time.monotonic() < end:
        if select.select([fd], [], [], min(0.1, max(0, end - time.monotonic())))[0]:
            data = os.read(fd, 4096)
            if data:
                print('@@DATA ' + base64.b64encode(data).decode('ascii'), flush=True)
finally:
    os.close(fd)
