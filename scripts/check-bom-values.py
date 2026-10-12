#!/usr/bin/env python3
"""Catch value/catalog mismatches before exporting or publishing a purchase list."""
import json
import re
import runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
values=runpy.run_path(str(ROOT/'scripts/part-values.py'))
parse=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'))
board=parse['parse']((ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb').read_text())
catalog={p['code']:p for p in json.loads((ROOT/'docs/jlc-catalog.json').read_text())['parts']}

def normalized(value):
    return re.sub(r'\s+','',value.replace('µ','u').replace('μ','u')).casefold()

count=0
for part in parse['children'](board,'footprint'):
    props={p[1]:p[2] for p in parse['children'](part,'property')}
    ref=props['Reference']
    if 'dnp' in parse['one'](part,'attr') or ref[0] not in {'C','R','L'}: continue
    key={'C':'Capacitance','R':'Resistance','L':'Inductance'}[ref[0]]
    attributes={a['attribute_name_en']:a['attribute_value_name'] for a in catalog[props['LCSC']]['attributes']}
    expected=values['nominal'](props['Value'],[ref])
    assert normalized(expected)==normalized(attributes[key]),f'{ref}: {expected} but {props["LCSC"]} is {attributes[key]}'
    count+=1
for raw,refs,expected in [('1u',['C1'],'1 µF'),('5K1',['R1'],'5.1 kΩ'),('1m',['L1'],'1 mH'),('0R',['R1'],'0 Ω')]:
    assert values['nominal'](raw,refs)==expected
print(f'Checked {count} fitted passive values against catalog electrical attributes; F/Ω/H formatting verified.')
