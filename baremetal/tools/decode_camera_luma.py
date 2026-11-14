# SPDX-License-Identifier: MIT
"""Decode validated diagnostic luma rows; combine only exports of one snapshot."""
import argparse,re
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('output',type=Path)
p.add_argument('serial',type=Path,nargs='+')
a=p.parse_args()
rows={}
for path in a.serial:
    for row,encoded in re.findall(rb'^@@LUMA (\d+) ([0-9a-f]{1280})\r?$',path.read_bytes(),re.M):
        y=int(row);data=bytes.fromhex(encoded.decode())
        if y not in range(480):raise ValueError('Luma row outside snapshot')
        if y in rows and rows[y]!=data:raise ValueError('Conflicting snapshots or corrupted row')
        rows[y]=data
if set(rows)!=set(range(480)):raise ValueError('Incomplete snapshot; missing rows '+repr(sorted(set(range(480))-set(rows))))
a.output.parent.mkdir(parents=True,exist_ok=True)
Image.frombytes('L',(640,480),b''.join(rows[y] for y in range(480))).save(a.output)
print('Decoded640x480 luma snapshot:',a.output)
