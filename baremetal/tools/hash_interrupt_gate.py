# SPDX-License-Identifier: MIT
"""Verify Ctrl-C aborts long native PBKDF2 without a second pending exception."""
import datetime,json,time
from pathlib import Path
import serial
from serial.tools import list_ports
root=Path(__file__).resolve().parents[1]
ports=[p for p in list_ports.comports() if (p.vid,p.pid)==(0x1209,0x0003) and p.serial_number=='rv1103-dev-001']
assert len(ports)==1,ports
folder=root/'logs/phase-12'/('hash-interrupt-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));folder.mkdir(parents=True)
script=b'''import hashlib
import camera
baseline=camera.settings()['rust_heap_bytes']
print('@@HASH_INTERRUPT_READY')
try:
    result=hashlib.pbkdf2_hmac('sha512',b'public password',b'public salt',1000000,64)
    raise AssertionError('PBKDF2 unexpectedly completed')
except KeyboardInterrupt:
    print('@@HASH_INTERRUPT_CAUGHT')
for i in range(500):
    value=i*i
assert hashlib.sha256(b'abc').hexdigest()=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS hash-interruption-recovery')
'''
out=b'';report={'serial':'rv1103-dev-001','scope':'One-million-round PBKDF2-SHA512 interrupted over USB; public values only','passed':False}
try:
 with serial.Serial(ports[0].device,115200,timeout=.1,write_timeout=3,exclusive=True) as console:
    console.write(b'\x03\x02\r');time.sleep(.2);console.reset_input_buffer();console.write(b'\x05');time.sleep(.2);console.read_all()
    for offset in range(0,len(script),128):console.write(script[offset:offset+128]);console.read_all();time.sleep(.01)
    console.write(b'\x04');deadline=time.monotonic()+5
    while b'@@HASH_INTERRUPT_READY\r\n' not in out and time.monotonic()<deadline:out+=console.read(4096)
    assert b'@@HASH_INTERRUPT_READY\r\n' in out,'No derivation ready marker'
    time.sleep(.1);started=time.monotonic();console.write(b'\x03');deadline=started+3
    while b'@@PASS hash-interruption-recovery\r\n' not in out and time.monotonic()<deadline:out+=console.read(4096)
    report['responseSecondsHostBound']=time.monotonic()-started
    assert b'@@HASH_INTERRUPT_CAUGHT\r\n' in out,'No caught KeyboardInterrupt'
    assert b'@@PASS hash-interruption-recovery\r\n' in out,'No recovered interpreter/hash/heap marker'
    report['passed']=True
except Exception as error:report['error']=str(error)
finally:
 (folder/'script.py').write_bytes(script);(folder/'serial.bin').write_bytes(out);(folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 print(out.decode(errors='replace'));print(json.dumps(report,indent=2));print('Evidence:',folder)
raise SystemExit(0 if report['passed'] else 1)
