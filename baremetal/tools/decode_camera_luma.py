# SPDX-License-Identifier: MIT
"""Validate complete luma exports; hashed chunks must identify one exact snapshot."""
import argparse
import hashlib
from pathlib import Path
import re

HEADER=re.compile(rb'^@@LUMA_BEGIN 640 480(?: SHA256 ([0-9a-f]{64}))?\r?$',re.M)
ROWS=re.compile(rb'^@@LUMA (\d+) ([0-9a-f]{1280})\r?$',re.M)

def decode_snapshot(paths,require_digest=False):
    rows={};identities=set();unverified=False
    for path in paths:
        content=Path(path).read_bytes()
        headers=HEADER.findall(content)
        if re.search(rb'^@@LUMA_BEGIN ',content,re.M) and not headers:
            raise ValueError('Malformed snapshot header')
        file_rows=ROWS.findall(content)
        if file_rows and not headers:unverified=True
        for identity in headers:
            if identity:identities.add(identity.decode())
            else:unverified=True
        for row,encoded in file_rows:
            y=int(row);data=bytes.fromhex(encoded.decode('ascii'))
            if y not in range(480):raise ValueError('Luma row outside snapshot')
            if y in rows and rows[y]!=data:raise ValueError('Conflicting snapshots or corrupted row')
            rows[y]=data
    if len(identities)>1:raise ValueError('Chunks belong to different snapshots')
    if identities and unverified:raise ValueError('Cannot mix hashed and unverified chunks')
    if require_digest and (not identities or unverified):raise ValueError('Snapshot checksum required')
    if set(rows)!=set(range(480)):
        raise ValueError('Incomplete snapshot; missing rows '+repr(sorted(set(range(480))-set(rows))))
    pixels=b''.join(rows[y] for y in range(480))
    identity=next(iter(identities),None)
    if identity and hashlib.sha256(pixels).hexdigest()!=identity:raise ValueError('Snapshot checksum mismatch')
    return pixels,identity

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('serial',type=Path,nargs='+')
    parser.add_argument('--require-digest',action='store_true')
    args=parser.parse_args()
    pixels,identity=decode_snapshot(args.serial,args.require_digest)
    from PIL import Image
    args.output.parent.mkdir(parents=True,exist_ok=True)
    Image.frombytes('L',(640,480),pixels).save(args.output)
    print('Decoded640x480 luma snapshot:',args.output,'checksum verified' if identity else 'legacy export without checksum')
if __name__=='__main__':main()
