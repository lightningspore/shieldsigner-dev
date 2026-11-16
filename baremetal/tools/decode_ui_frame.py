# SPDX-License-Identifier: MIT
"""Decode the exact native UI framebuffer evidence, not a recreated screen."""

import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('serial', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
data = a.serial.read_bytes()
start = b'\r\n@@UI_RGB565_BEGIN 240 240\r\n'
end = b'\r\n@@UI_RGB565_END\r\n'
if data.count(start) != 1 or data.count(end) != 1:
    raise SystemExit('Need one complete native UI frame')
body = data.split(start, 1)[1].split(end, 1)[0]
rows = body.splitlines()
if len(rows) != 240 or any(not row.startswith(b'@@UI_ROW ') or len(row) != 969 for row in rows):
    raise SystemExit('Invalid framebuffer row count/length')
raw = b''.join(bytes.fromhex(row[9:].decode('ascii')) for row in rows)
if len(raw) != 115200:
    raise SystemExit('Invalid RGB565 byte count')
rgb = bytearray()
for offset in range(0, len(raw), 2):
    value = int.from_bytes(raw[offset : offset + 2], 'big')
    r = (value >> 11) & 31
    g = (value >> 5) & 63
    b = value & 31
    rgb.extend(((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)))
a.output.parent.mkdir(parents=True, exist_ok=True)
Image.frombytes('RGB', (240, 240), bytes(rgb)).save(a.output)
print(
    json.dumps(
        {
            'output': str(a.output),
            'frameSha256': hashlib.sha256(raw).hexdigest(),
            'rgbSha256': hashlib.sha256(rgb).hexdigest(),
            'sourceSha256': hashlib.sha256(data).hexdigest(),
        },
        indent=2,
    )
)
