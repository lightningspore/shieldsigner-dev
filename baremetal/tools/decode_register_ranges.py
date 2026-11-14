# SPDX-License-Identifier: MIT
"""Validate complete framed REF snapshots and emit binary/text register dumps."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct
import zlib
from ref_range_snapshot import RESOURCES

def decode(path):
    records=[json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if len(records)<3 or records[0].get('kind')!='begin' or records[-1].get('kind')!='end':raise ValueError('Incomplete snapshot')
    begin,end=records[0],records[-1];base,length=RESOURCES[begin['block']]
    if (begin['base'],begin['length'])!=(base,length):raise ValueError('Resource mismatch')
    data=bytearray()
    for record in records[1:-1]:
        if record.get('kind')!='data' or record['offset']!=len(data):raise ValueError('Noncontiguous snapshot')
        chunk=base64.b64decode(record['data'],validate=True)
        if len(chunk)!=min(4096,length-len(data)):raise ValueError('Wrong chunk length')
        data.extend(chunk)
    if len(data)!=length or end['bytes']!=length or zlib.crc32(data)!=end['crc32']:raise ValueError('Length/checksum mismatch')
    return begin,bytes(data)

def save(paths,output):
    output.mkdir(parents=True,exist_ok=True);combined=[];manifest=[]
    for path in paths:
        begin,data=decode(path);name=begin['block'];base=begin['base']
        text='\n'.join(f'0x{base+offset:08x} 0x{value:08x}' for offset,(value,) in
                       zip(range(0,len(data),4),struct.iter_unpack('<I',data)))+'\n'
        (output/(name+'.bin')).write_bytes(data);(output/(name+'.txt')).write_text(text)
        gap=begin.get('coverageGap')
        combined.append(f'# {name} base=0x{base:08x} bytes={len(data)} coverageGap={gap}\n'+text)
        manifest.append({'block':name,'base':base,'bytes':len(data),'coverageGap':gap,'sha256':hashlib.sha256(data).hexdigest()})
    (output/'registers.txt').write_text(''.join(combined))
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('frames',nargs='+',type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();print(json.dumps(save(args.frames,args.output),indent=2))
