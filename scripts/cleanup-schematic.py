#!/usr/bin/env python3
"""Normalize cached power symbols and explicit ERC metadata without changing wires."""
import importlib.util,re,shutil,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('sexpr',ROOT/'scripts/kicad-sexpr.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
backup=ROOT/'.tools/schematic-edits'/str(time.time_ns());backup.mkdir(parents=True)
def spans(text,prefix):return [(a,b,v) for a,b,v in s.expressions(text) if v.startswith(prefix)]
def pins(text):
 node=s.parse(text)
 return sorted((s.one(p,'number')[1],s.one(p,'at')) for sym in s.children(node,'symbol') for p in s.children(sym,'pin'))
paths=[ROOT/'kicad/rpi_interface.kicad_sch',ROOT/'kicad/smartcard_reader.kicad_sch',ROOT/'kicad/symbols/Library.kicad_sym',ROOT/'kicad/symbols/SeedSigner.kicad_sym']
original={p:p.read_text() for p in paths}
try:
 for p,text in original.items():
  shutil.copy2(p,backup/p.name);updated=text
  if p.name=='rpi_interface.kicad_sch':
   lib=(ROOT/'kicad/symbols/power.kicad_sym').read_text()
   for name in ['GND','+3.3V']:
    replacement=spans(lib,f'(symbol "{name}"')[0][2].replace(f'(symbol "{name}"',f'(symbol "power:{name}"',1)
    for a,b,v in reversed(spans(updated,f'(symbol "power:{name}"')):
     assert pins(v)==pins(replacement),'Power symbol pin coordinates must remain identical'
     updated=updated[:a]+replacement+updated[b:]
    if not spans(updated,f'(symbol "power:{name}"'):
     updated=updated.replace('(lib_symbols','(lib_symbols\n'+replacement,1)
   # Instance lib_name overrides otherwise select stale embedded variants.
   for a,b,v in sorted(list(s.expressions(updated)),reverse=True):
    if v.startswith('(symbol\n') and '(lib_name ' in v and any(x in v for x in ['(lib_id "power:','(lib_id "SeedSigner:WAVESHARE_LCD_BUTTON"']):
     updated=updated[:a]+re.sub(r'\s*\(lib_name "[^"\\]+"\)','',v,count=1)+updated[b:]
   for name in ['I2C-SCL','I2C-SDA']:
    for a,b,v in reversed(spans(updated,f'(label "{name}"')):
     updated=updated[:a]+v.replace('(label ', '(global_label ',1).replace(f'"{name}"',f'"{name}" (shape input)',1)+updated[b:]
   updated=updated.replace('"seedsigner-luckfox:WAVESHARE_LCD_BUTTON"','""')
  elif p.name=='SeedSigner.kicad_sym':
   updated=updated.replace('"seedsigner-luckfox:WAVESHARE_LCD_BUTTON"','""')
  else:
   for a,b,v in reversed(spans(updated,'(pin unspecified line')):
    if '(name "TEST"' in v and '(number "15"' in v:updated=updated[:a]+v.replace('(pin unspecified line','(pin input line',1)+updated[b:]
  if p.suffix=='.kicad_sch':
   old,new=s.parse(text),s.parse(updated)
   for key in ['wire','junction','no_connect']:assert s.children(old,key)==s.children(new,key),key
  s.parse(updated);p.write_text(updated)
 print('Schematic metadata updated; all wires, junctions and no-connect positions preserved. Backup:',backup)
except Exception:
 for p,text in original.items():p.write_text(text)
 raise
