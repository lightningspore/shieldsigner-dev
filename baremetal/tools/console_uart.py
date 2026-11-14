# SPDX-License-Identifier: MIT
"""REF-side single-owner UART paste-mode exchange; no camera/storage changes."""
import base64
import os
import select
import sys
import termios
import time

device,encoded,token,timeout=sys.argv[1:]
script=base64.b64decode(encoded,validate=True)
fd=os.open(device,os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
previous=termios.tcgetattr(fd)
try:
    attrs=termios.tcgetattr(fd)
    attrs[:4]=[0,0,termios.CS8|termios.CREAD|termios.CLOCAL,0]
    attrs[4]=attrs[5]=termios.B115200
    attrs[6][termios.VMIN]=0;attrs[6][termios.VTIME]=0
    termios.tcsetattr(fd,termios.TCSANOW,attrs)
    os.write(fd,b'\x03\r')
    time.sleep(.2)
    termios.tcflush(fd,termios.TCIFLUSH)
    os.write(fd,b'\x05')
    time.sleep(.1)
    payload=script+b"\nprint('@@CONSOLE_DONE "+token.encode()+b"')\n\x04"
    while payload:
        try:payload=payload[os.write(fd,payload):]
        except BlockingIOError:select.select([],[fd],[],.1)
    seen=b'';end=time.monotonic()+float(timeout)
    while time.monotonic()<end:
        if select.select([fd],[],[],.2)[0]:
            data=os.read(fd,4096)
            seen+=data
            sys.stdout.buffer.write(b'@@DATA '+base64.b64encode(data)+b'\n');sys.stdout.buffer.flush()
            marker=b'\n@@CONSOLE_DONE '+token.encode()
            if marker in seen and (marker+b'\r\n' in seen or marker+b'\n' in seen):break
    else:raise TimeoutError('No completed interpreter script')
finally:
    termios.tcsetattr(fd,termios.TCSANOW,previous)
    os.close(fd)
