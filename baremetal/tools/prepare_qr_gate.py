# SPDX-License-Identifier: MIT
"""Generate public QR fixtures for the real MicroPython/ZXing DUT gate."""

import pyformat  # noqa: F401  (formats generated Python on write)
from pathlib import Path
import qrcode

root = Path(__file__).resolve().parents[1]
cases = [
    b'shieldsigner baremetal public QR test',
    bytes(range(128)),
    b'\x00\xff\x80binary\x00payload',
]
code = '''# SPDX-License-Identifier: MIT
# Generated public fixtures; no wallet secrets. See tools/prepare_qr_gate.py.
import qr
import camera
import time
import gc
steady=None

def check(rows,payload,rotate=False,invert=False):
    global steady
    scale=4
    n=len(rows)
    width=n*scale
    image=bytearray(width*width)
    for y in range(width):
        for x in range(width):
            a,b=(n-1-x//scale,y//scale) if rotate else (y//scale,x//scale)
            image[y*width+x]=255 if (rows[a][b]=='0')!=invert else 0
    before=camera.settings()['rust_heap_bytes']
    start=time.ticks_ms()
    decoded=qr.decode(image,width,width)
    assert decoded==payload
    after=camera.settings()['rust_heap_bytes']
    print('@@QR_FIXTURE',len(payload),rotate,invert,(time.ticks_ms()-start)&0xffffffff,before,after)
    if steady is None:steady=after
    else:assert after==steady
'''
for i, data in enumerate(cases):
    q = qrcode.QRCode(border=4, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(data, optimize=0)
    q.make(fit=True)
    rows = tuple(''.join('1' if x else '0' for x in row) for row in q.get_matrix())
    code += 'rows=' + repr(rows) + '\npayload=' + repr(data) + '\n'
    code += 'check(rows,payload)\ncheck(rows,payload,True)\ncheck(rows,payload,False,True)\n'
code += '''baseline=camera.settings()['rust_heap_bytes']
for i in range(10):
    check(rows,payload)
    assert camera.settings()['rust_heap_bytes']==baseline
assert qr.decode(bytes([255])*4096,64,64) is None
for w,h,data in ((0,1,b''),(641,1,b''),(1,481,b''),(2,2,b'123')):
    try:qr.decode(data,w,h)
    except ValueError:pass
    else:raise AssertionError('invalid QR buffer accepted')
gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS native-zxing-qr')
'''
(root / 'micropython/qr_gate.py').write_text(code)
