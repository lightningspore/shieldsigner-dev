# SPDX-License-Identifier: MIT
"""Decode the bounded DUT RGB UART preview; reject partial frames."""
import argparse
from pathlib import Path
from PIL import Image

def decode(data):
    lines=data.splitlines();start=next(i for i,line in enumerate(lines) if line.startswith(b'@@RGB_BEGIN '))
    _,width,height=lines[start].split();width=int(width);height=int(height)
    if not 1<=width<=2304 or not 1<=height<=1296:raise ValueError('Invalid preview dimensions')
    rows=[]
    for line in lines[start+1:]:
        if line==b'@@RGB_END':break
        if not line.startswith(b'@@RGB '):raise ValueError('Unexpected preview data')
        row=bytes.fromhex(line[6:].decode('ascii'))
        if len(row)!=width*3:raise ValueError('Truncated preview row')
        rows.append(row)
    else:raise ValueError('Missing preview terminator')
    if len(rows)!=height:raise ValueError('Truncated preview')
    return Image.frombytes('RGB',(width,height),b''.join(rows))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('serial',type=Path);parser.add_argument('png',type=Path)
    args=parser.parse_args();image=decode(args.serial.read_bytes());image.save(args.png)
    print('Decoded',image.size,'RGB preview into',args.png)
