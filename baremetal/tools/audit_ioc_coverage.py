# SPDX-License-Identifier: MIT
"""Check SDK-known pin-control fields against the actual captured IOC resources.

This does not turn an unreadable resource tail into captured data. It establishes
whether that tail contains any pin-control fields used by the pinned SDK.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

def audit(kernel,dumps):
    path=kernel/'drivers/pinctrl/pinctrl-rockchip.c';source=path.read_text()
    banks=source.split('static struct rockchip_pin_bank rv1106_pin_banks[] = {',1)[1].split('\n};',1)[0]
    counts={int(bank):int(count) for bank,count in re.findall(r'PIN_BANK_IOMUX_FLAGS(?:_OFFSET)?\((\d+),\s*(\d+),',banks)}
    if set(counts)!=set(range(5)):raise ValueError('Unexpected bank description')
    rows=[]
    for group in ['DRV','PULL','SMT']:
        per_reg=int(re.search(r'#define\s+RV1106_'+group+r'_PINS_PER_REG\s+(\d+)',source)[1])
        offsets={int(bank):int(offset,16) for bank,offset in re.findall(r'#define\s+RV1106_'+group+r'_GPIO(\d)_OFFSET\s+(0x[0-9a-fA-F]+)',source)}
        if set(offsets)!=set(counts):raise ValueError('Missing GPIO offsets')
        for bank,offset in offsets.items():
            last=offset+((counts[bank]-1)//per_reg)*4
            rows.append({'kind':group,'bank':bank,'resource':'pmuioc' if bank==0 else 'ioc-prefix',
                         'firstOffset':offset,'lastOffset':last,'lastByteExclusive':last+4})
    # Explicit IOMUX offsets plus a conservative32-byte bound for four8-pin,
    #4-bit-per-pin groups. GPIO0 uses the separate PMU IOC resource.
    largest=max(int(value,16) for value in re.findall(r'0x[0-9a-fA-F]+',banks))
    rows.extend([{'kind':'IOMUX-bound','bank':'1–4','resource':'ioc-prefix','lastByteExclusive':largest+32},
                 {'kind':'IOMUX-bound','bank':0,'resource':'pmuioc','lastByteExclusive':32}])
    states={}
    for state in ['idle','streaming']:
        root=dumps/(state+'-full');manifest=json.loads((root/'manifest.json').read_text())
        entries={entry['block']:entry for entry in manifest}
        for name in ['pmuioc','ioc-prefix']:
            data=(root/(name+'.bin')).read_bytes();entry=entries[name]
            if len(data)!=entry['bytes'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('Snapshot manifest mismatch')
        states[state]=[dict(row,covered=row['lastByteExclusive']<=entries[row['resource']]['bytes']) for row in rows]
    return {'scope':'SDK-known pin-control register fields only; not a full capture of unreadable DT padding',
            'sourceSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'pinCounts':counts,
            'iocGap':'0xff570000–0xff577fff not captured; first address raised userspace external abort',
            'allKnownFieldsCovered':all(row['covered'] for rows in states.values() for row in rows),'states':states}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kernel',required=True,type=Path);parser.add_argument('--dumps',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    result=audit(args.kernel,args.dumps);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('All SDK-known GPIO IO fields covered:',result['allKnownFieldsCovered'])
    if not result['allKnownFieldsCovered']:raise SystemExit(1)
