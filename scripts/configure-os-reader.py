#!/usr/bin/env python3
"""Apply only the reviewed SEC1210 reader variant to a pinned OS checkout."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

FILES = ['opt/luckfox/files/sec1210']
PIN = 'e7589465aff172f4f510ad46d18776ccc8d2c203'

def configure(checkout, variant):
    if variant not in {'UR2', 'URT'}: raise ValueError('Reader must be UR2 or URT')
    revision = subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()
    if revision != PIN: raise ValueError('OS revision differs from the reviewed pin')
    dirty = subprocess.check_output(['git','-C',str(checkout),'status','--porcelain','--untracked-files=all'],text=True)
    if any(line[3:] not in FILES for line in dirty.splitlines()): raise ValueError('OS has unrelated changes; preserve/review them first')
    prepared = []
    candidates = []
    for name in FILES:
        original = subprocess.check_output(['git','-C',str(checkout),'show',f'{PIN}:{name}'])
        needle = b'/dev/ttyS2:SEC1210URT'
        if original.count(needle) != 1: raise ValueError('Reader configuration shape changed')
        ur2 = original.replace(needle,b'/dev/ttyS2:SEC1210UR2')
        current = (checkout/name).read_bytes()
        if current not in {original,ur2}: raise ValueError('Reader file has unreviewed edits: '+name)
        desired = ur2 if variant=='UR2' else original
        candidates.append((checkout/name,desired))
        prepared.append({'file':name,'sha256':hashlib.sha256(desired).hexdigest()})
    for path,desired in candidates: path.write_bytes(desired)
    return {'osCommit':PIN,'readerVariant':variant,'files':prepared,'scope':'Reader configuration only; this carrier image still requires compilation and bench testing.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('checkout',type=Path);parser.add_argument('--variant',choices=['UR2','URT'],default='UR2');parser.add_argument('--manifest',type=Path)
    args=parser.parse_args();result=configure(args.checkout,args.variant)
    text=json.dumps(result,indent=2)+'\n'
    if args.manifest: args.manifest.parent.mkdir(parents=True,exist_ok=True);args.manifest.write_text(text)
    print(text,end='')
