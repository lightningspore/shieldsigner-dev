# SPDX-License-Identifier: MIT
# Exact DUT1 development USB identity; RAM-only interruption test.
import serial,time
from serial.tools import list_ports
ports=[p.device for p in list_ports.comports() if (p.vid,p.pid)==(0x1209,0x0003) and p.serial_number=="rv1103-dut1"]
assert len(ports)==1,ports
script=b'''import camera
camera.init()
baseline=camera.settings()['rust_heap_bytes']
try:
    camera.start_preview()
    print('@@PREVIEW_INTERRUPT_READY')
    while True:
        frame=camera.next_preview()
finally:
    camera.stop_preview()
    for i in range(500):
        x=i*i
    print('@@PREVIEW_INTERRUPT_CLEAN',camera.preview_status(),camera.settings()['rust_heap_bytes']==baseline)
'''
with serial.Serial(ports[0],115200,timeout=.1) as s:
 s.write(b'\x03\x02\r');time.sleep(.2);s.reset_input_buffer();s.write(b'\x05');time.sleep(.2);s.read_all()
 for i in range(0,len(script),128):s.write(script[i:i+128]);s.read_all();time.sleep(.01)
 s.write(b'\x04');out=b'';deadline=time.monotonic()+8
 while b'@@PREVIEW_INTERRUPT_READY\r\n' not in out and time.monotonic()<deadline:out+=s.read(4096)
 assert b'@@PREVIEW_INTERRUPT_READY\r\n' in out,out
 time.sleep(.12);s.write(b'\x03');deadline=time.monotonic()+3
 while b'>>> ' not in out and time.monotonic()<deadline:out+=s.read(4096)
 print(out.decode(errors='replace'))
 assert b'@@PREVIEW_INTERRUPT_CLEAN (False, 0) True' in out,out
 assert b'KeyboardInterrupt' in out,out
