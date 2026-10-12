#!/usr/bin/env python3
"""Apply reviewed, non-routing fixes to the native variant; preserve baseline."""
import json,re,runpy,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
DIR=ROOT/'kicad'
# Use the expression scanner, without executing the library-building script.
source=(ROOT/'scripts/prepare-kicad-project.py').read_text()
namespace={};exec(source[source.index('def expressions'):source.index('\nsymbols=')],namespace)
expressions=namespace['expressions']
def apply(path,callback):
 text=path.read_text();changes=[]
 for start,end,expr in expressions(text):
  replacement=callback(expr)
  if replacement!=expr:changes.append((start,end,replacement))
 # Callbacks target non-overlapping symbol/footprint nodes.
 for start,end,replacement in sorted(changes,reverse=True):text=text[:start]+replacement+text[end:]
 path.write_text(text)

# SEC1210 outputs were declared power inputs by the upstream custom symbol.
def fix_pins(expr):
 if re.match(r'\(pin\s+power_in\b',expr) and re.search(r'\(name\s+"(?:SC2_VCC|SC1_VCC|VDD33)"',expr):
  return expr.replace('(pin power_in','(pin power_out',1)
 return expr
apply(DIR/'smartcard_reader.kicad_sch',fix_pins)
apply(DIR/'symbols/Library.kicad_sym',fix_pins)

# Explicit unused-pin declarations based on baseline native ERC locations.
report=json.loads((ROOT/'dist/kicad/erc-baseline.json').read_text())
files={'/RPi Interface/':'rpi_interface.kicad_sch','/Screen/':'screen.kicad_sch','/Smartcard Interface/':'smartcard_reader.kicad_sch'}
for sheet in report['sheets']:
 if sheet['path'] not in files:continue
 path=DIR/files[sheet['path']];text=path.read_text();markers=[]
 for error in sheet['violations']:
  if error['type']!='pin_not_connected':continue
  for item in error['items']:
   x,y=item['pos']['x'],item['pos']['y']
   # Don't duplicate a marker on rerun.
   if re.search(r'\(no_connect\s+\(at\s+'+re.escape(str(x))+r'\s+'+re.escape(str(y))+r'\)',text):continue
   markers.append(f'(no_connect (at {x} {y}) (uuid "{uuid.uuid5(uuid.NAMESPACE_URL, "shieldsigner-nc:"+sheet["path"]+":"+str(x)+":"+str(y))}"))')
 text=text.rstrip();assert text.endswith(')');path.write_text(text[:-1]+'\n'+'\n'.join(markers)+'\n)\n')

# Explicitly identify alternate schematic-only interface and testpoint.
def schematic_only(expr):
 if not re.match(r'\(symbol\s*\(lib_id',expr):return expr
 if re.search(r'\(property "Reference" "(?:U201|TP201)"',expr):
  expr=expr.replace('(on_board yes)','(on_board no)').replace('(in_bom yes)','(in_bom no)')
 return expr
apply(DIR/'rpi_interface.kicad_sch',schematic_only)

# Datasheet DS00001561D table 6-4 / notes 6-2 and 6-3 require 1 uF.
def decoupling(expr):
 if not (re.match(r'\(symbol\s*\(lib_id',expr) or expr.startswith('(footprint ')):return expr
 if re.search(r'\(property "Reference" "(?:C603|C604)"',expr):
  expr=expr.replace('(property "Value" "100n"','(property "Value" "1u"').replace('(property "LCSC" "C49678"','(property "LCSC" "C28323"')
 return expr
apply(DIR/'smartcard_reader.kicad_sch',decoupling)
apply(DIR/'SeedSigner-Plus-smartcard-pico.kicad_pcb',decoupling)

# Upstream USB input/GND are passive pins. Annotate their known external supply.
path=DIR/'Power.kicad_sch';text=path.read_text()
standard=ROOT/'.tools/kicad-10/KiCad/KiCad.app/Contents/SharedSupport/symbols/power.kicad_sym'
flag=next(expr for a,b,expr in expressions(standard.read_text()) if re.match(r'\(symbol\s+"PWR_FLAG"',expr))
embedded=flag.replace('"PWR_FLAG"','"power:PWR_FLAG"',1)
if '(symbol "power:PWR_FLAG"' not in text:
 a,b,expr=next((a,b,e) for a,b,e in expressions(text) if e.startswith('(lib_symbols'))
 text=text[:b-1]+'\n'+embedded+'\n'+text[b-1:]
local=DIR/'symbols/power.kicad_sym';library=local.read_text()
if '(symbol "PWR_FLAG"' not in library:local.write_text(library.rstrip()[:-1]+'\n'+flag+'\n)\n')
for ref,x,y in [('#FLG0301',243.84,77.47),('#FLG0302',139.7,102.87)]:
 if f'"Reference" "{ref}"' in text:continue
 root_uuid=re.search(r'\(uuid "([^"]+)"', (DIR/'SeedSigner-Plus-smartcard-pico.kicad_sch').read_text())[1]
 sheet_uuid=re.search(r'\(uuid "([^"]+)"',text)[1]
 marker=f'''(symbol (lib_id "power:PWR_FLAG") (at {x} {y} 0) (unit 1)
 (exclude_from_sim no) (in_bom no) (on_board yes) (dnp no)
 (uuid "{uuid.uuid5(uuid.NAMESPACE_URL,'shieldsigner:'+ref)}")
 (property "Reference" "{ref}" (at {x} {y-4} 0) (effects (font (size 1.27 1.27)) (hide yes)))
 (property "Value" "PWR_FLAG" (at {x} {y-2} 0) (effects (font (size 1.27 1.27))))
 (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))
 (instances (project "SeedSigner-Plus-smartcard-pico" (path "/{root_uuid}/{sheet_uuid}" (reference "{ref}") (unit 1)))))'''
 text=text.rstrip()[:-1]+'\n'+marker+'\n)\n'
path.write_text(text)
print('Applied unused-pin declarations, power-pin corrections, schematic-only flags and 1 uF output decoupling.')
