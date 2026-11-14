# SPDX-License-Identifier: MIT
"""Compare selected fixed ISP module readbacks with successful REF writes.

Does not qualify image quality, all register bits or unobserved write sites.
"""
import argparse
import json
from pathlib import Path
import re

# Ordinary config fields only. RAWAE_BIG declares bits0–2 and4–7; CCM_CTRL
# declares bits0–3. CCM signed coefficient writes use16-bit sign extension,
# while both REF and DUT read back11-bit coefficient payloads. These masks
# preserve all offset bits; they do not turn mismatches into accepted writes.
SEMANTIC_MASKS={0x4600:0xf7,0x700:0xf,
    0x704:0x07ff07ff,0x70c:0x07ff07ff,0x714:0x07ff07ff,
    0x708:0xffff07ff,0x710:0xffff07ff,0x718:0xffff07ff}

def compare(serial: Path, trace: Path):
    lines=trace.read_text().splitlines()
    if not lines[0].startswith('# applied=0 count=16374 dropped=0 errors=0;'):
        raise ValueError('Unexpected REF trace provenance')
    reference={}
    for line in lines[1:]:
        seq,stamp,kind,site,address,value,width=line.split()
        address,value=int(address,16),int(value,16)
        if 0xffa00000<=address<0xffa07f00:
            if kind!='0' or width!='4':raise ValueError('Unexpected ISP write type')
            reference[address-0xffa00000]=value
        if address==0xffa01c00 and value==0x20820401:break
    else:raise ValueError('Missing first trigger')
    rows=[]
    unobserved=[]
    for offset,value,mask in re.findall(r'@@ISP_FIXED_REG (0x[0-9a-f]+) (0x[0-9a-f]+) mask=(0x[0-9a-f]+)',serial.read_text(errors='replace')):
        offset,value,mask=map(lambda s:int(s,16),(offset,value,mask))
        mask &= SEMANTIC_MASKS.get(offset,0xffffffff)
        if offset not in reference:
            unobserved.append(hex(offset))
            continue
        expected=reference[offset]
        rows.append({'offset':hex(offset),'expected':hex(expected),'actual':hex(value),'mask':hex(mask),'matches':(expected&mask)==(value&mask)})
    if not rows or len({r['offset'] for r in rows})!=len(rows):raise ValueError('Missing/duplicate audit records')
    return {'selectedRegisters':len(rows),'matching':sum(r['matches'] for r in rows),'rows':rows,'unobservedOffsetsNotCompared':unobserved,
            'scope':'Selected fixed configuration bits versus observed REF writes; not full-register/phase qualification'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('serial',type=Path);parser.add_argument('trace',type=Path);args=parser.parse_args()
    result=compare(args.serial,args.trace);print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['selectedRegisters']==result['matching'] else 1)
