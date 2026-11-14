# SPDX-License-Identifier: MIT
"""Decode the bounded NV12 thumbnail sent as Y/Cb/Cr triples over UART.

REF's pinned output configuration is full-range YCbCr. This produces a visual
diagnostic, not a colour calibration or Phase8 qualification result.
"""
import argparse
from pathlib import Path
from PIL import Image

def decode(serial: Path, output: Path):
    lines = serial.read_text(errors='replace').splitlines()
    if lines.count('@@ISP_YUV_BEGIN 160 120') != 1 or lines.count('@@ISP_YUV_END') != 1:
        raise ValueError('Missing/duplicate preview framing')
    start = lines.index('@@ISP_YUV_BEGIN 160 120')
    end = lines.index('@@ISP_YUV_END')
    rows = [bytes.fromhex(line.removeprefix('@@ISP_YUV ')) for line in lines[start+1:end]]
    if len(rows) != 120 or any(len(row) != 160*3 for row in rows):
        raise ValueError('Incomplete thumbnail')
    image = Image.frombytes('YCbCr', (160,120), b''.join(rows)).convert('RGB')
    image.resize((640,480)).save(output)
    print(output)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('serial',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    decode(args.serial,args.output)
