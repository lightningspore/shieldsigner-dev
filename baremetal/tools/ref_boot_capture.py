# SPDX-License-Identifier: MIT
"""REF-only bounded UART/GPIO observer. Never drives GPIO or touches storage.

An optional reset byte is sent through the already proven UART recovery path.
GPIO is polled, not electrically timestamped: observed sample gaps are reported.
"""
import base64
import json
import mmap
import os
import struct
import sys
import termios
import time

port, duration = sys.argv[1], float(sys.argv[2])
reset = '--reset' in sys.argv[3:]
if not 0 < duration <= 60:
    raise SystemExit('capture duration must be 0..60s')
memory = os.open('/dev/mem', os.O_RDONLY | os.O_SYNC)
gpio = mmap.mmap(memory, 4096, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ, offset=0xff530000)
os.close(memory)
direction = struct.unpack_from('<I', gpio, 0x0c)[0]
if direction & 0x30:
    raise SystemExit('REF C4/C5 must both be inputs before capture')
fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
saved = termios.tcgetattr(fd)
settings = termios.tcgetattr(fd)
settings[0] = settings[1] = settings[3] = 0
settings[2] = termios.CS8 | termios.CLOCAL | termios.CREAD
settings[4] = settings[5] = termios.B115200
settings[6][termios.VMIN] = settings[6][termios.VTIME] = 0
termios.tcsetattr(fd, termios.TCSANOW, settings)
termios.tcflush(fd, termios.TCIFLUSH)
serial = bytearray()
edges = []
start = previous = time.monotonic_ns()
end = start + int(duration * 1e9)
last = (struct.unpack_from('<I', gpio, 0x70)[0] >> 20) & 1
initial = last
max_gap = 0
active_gap = None
pulse_gaps = []
count = 0
reset_sent_ns = None
uart_markers = {}
def received(data):
    serial.extend(data)
    observed = time.monotonic_ns() - start
    for name, marker in [('reset', b'@@RESET'), ('ddr', b'DDR '),
                         ('hello', b'@@PASS hello'), ('repl', b'@@REPL_READY')]:
        if name not in uart_markers and marker in serial:
            uart_markers[name] = observed
print('@@BOOT_CAPTURE_READY', flush=True)
try:
    if reset:
        reset_sent_ns = time.monotonic_ns() - start
        os.write(fd, b'\x1d')
        termios.tcdrain(fd)
    while True:
        now = time.monotonic_ns()
        if now >= end:
            break
        level = (struct.unpack_from('<I', gpio, 0x70)[0] >> 20) & 1
        gap = now - previous
        max_gap = max(max_gap, gap)
        if active_gap is not None:
            active_gap = max(active_gap, gap)
        if level != last:
            edges.append({'timeNs': now - start, 'level': level, 'previousSampleGapNs': gap})
            if level:
                active_gap = gap
            elif active_gap is not None:
                pulse_gaps.append(active_gap)
                active_gap = None
            last = level
        previous = now
        count += 1
        if count % 128 == 0:
            try:
                data = os.read(fd, 65536)
                if data:
                    received(data)
            except BlockingIOError:
                pass
    try:
        received(os.read(fd, 65536))
    except BlockingIOError:
        pass
finally:
    termios.tcsetattr(fd, termios.TCSANOW, saved)
    os.close(fd)
    gpio.close()
print('@@DATA ' + base64.b64encode(serial).decode('ascii'))
print('@@BOOT_GPIO ' + json.dumps({'initialLevel': initial, 'edges': edges,
    'sampleCount': count, 'maxSampleGapNs': max_gap,
    'highPulseMaxSampleGapsNs': pulse_gaps, 'refDirectionHigh': hex(direction),
    'resetRequestNs': reset_sent_ns, 'uartMarkerObservedNs': uart_markers,
    'scope': 'Polled REF GPIO1_C4; payload entry only, excludes ROM/DDR and power application'}))
