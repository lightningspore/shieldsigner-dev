"""Generate a DigiKey sourcing overlay; never mutate native or JLC manufacturing files."""
import argparse
import csv
import hashlib
import json
import runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
V=ROOT/'variants/lcd-module-2.8'
DEST=V/'self-assembly'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
data=json.loads((DEST/'selection.json').read_text())
nominal=runpy.run_path(str(ROOT/'scripts/part-values.py'))['nominal']
source=list(csv.DictReader((V/'manufacturing/population.csv').open()))
population={r['ref']:r for r in source if r['role']=='JLCPCB SMT assembly'}
assert len(population)==35
assigned={};rows=[];lines=['# DigiKey self-assembly BOM','','Optional sourcing for the revised **0.0.5-dev eight-pin pill carrier**. JLCPCB remains the primary assembled-board ordering path. This overlay never replaces the JLC BOM/CPL or native part fields.','','**35 SMT pieces / 17 DigiKey lines are selected, including every capacitor, resistor, LED and TVS (23 pieces / 12 lines).** The revised switches and USB-C use exact shared JLCPCB/DigiKey manufacturer parts. LCD, camera and Luckfox are excluded; customer headers and mechanical hardware remain separate.','','[Download DigiKey CSV](bom-digikey.csv) · [Remaining original-parts CSV](remaining-parts.csv)','','Stock is a dated observation, not reserved inventory. Counts marked “not recorded” require a checkout-time check. Quantities are exact installed counts without spares or soldering losses. Cut-tape order codes avoid full-reel minimums.','','| References | Value / requirements | Qty: 1 / 5 boards | Selected MPN | DigiKey cut-tape/tray code | Stock snapshot |','|---|---|---:|---|---|---:|']
for part in data['parts']:
 refs=part['refs'];qty=len(refs)
 assert part['url'].startswith('https://www.digikey.com/en/products/detail/')
 for ref in refs:
  assert ref in population and ref not in assigned,ref
  assigned[ref]=part
  fp=population[ref]['footprint']
  if ref[0] in 'RC':
   assert '0805' in fp and '0805' in part['spec'],ref
   assert nominal(population[ref]['value'],[ref])==part['value'],f'Nominal value mismatch: {ref}'
   if ref[0]=='R': assert '±1%' in part['spec'] and '125 mW' in part['spec']
  if ref=='D301': assert fp.endswith('D_SOD-123F') and part['mpn']=='SMF5.0CA'
  if ref=='D302': assert 'LED_0805' in fp
 assert len({population[ref]['mpn'] for ref in refs})==1
 row={'References':','.join(refs),'Value':part['value'],'Specification':part['spec'],'Quantity per board':qty,'Quantity for 5 boards':5*qty,'Manufacturer':part['manufacturer'],'Manufacturer Part Number':part['mpn'],'DigiKey Part Number':part['digikey'],'URL':part['url'],'Original JLC MPN':population[refs[0]]['mpn'],'Original LCSC':population[refs[0]]['lcsc'],'Selection':part['selection'],'Checked UTC date':part['checkedAt'],'Stock snapshot':part['stockSnapshot'] if part['stockSnapshot'] is not None else 'not recorded','Rationale':part['rationale']}
 rows.append(row)
 lines.append(f"| {', '.join(refs)} | {part['value']}; {part['spec']} | {qty} / {5*qty} | {part['mpn']} | [{part['digikey']}]({part['url']}) | {row['Stock snapshot']} |")
commodity={ref for ref in population if ref[0] in 'RCD'}
assert len(commodity)==23 and commodity<=assigned.keys()
assert len({p["digikey"] for p in data["parts"]})==len(data["parts"])
for part in data["parts"]:
 if set(part["refs"])<=commodity:
  assert part["stockSnapshot"] is not None and part["stockSnapshot"]>=len(part["refs"])*5,part["mpn"]
assert len(assigned)==35 and len(rows)==17
remaining=[]
for part in data['unresolved']:
 for ref in part['refs']:
  assert ref not in assigned and population[ref]['mpn']==part['mpn']
  assigned[ref]=part
 remaining.append({'References':','.join(part['refs']),'Quantity per board':len(part['refs']),'Original MPN':part['mpn'],'Original LCSC':population[part['refs'][0]]['lcsc'],'Status':part['reason']})
assert assigned.keys()==population.keys()
lines+=['','## Unresolved fitted parts (none in this revision)','',*['- **'+', '.join(p['refs'])+' / '+p['mpn']+'**: '+p['reason'] for p in data['unresolved']],'','## Assembly notes','','- All resistors remain 0805, ±1%, 125 mW with the same resistance. Capacitors retain nominal capacitance, voltage class, tolerance and dielectric. No pad or net changes are required by this sourcing overlay.','- The green LED uses the existing 560 Ω resistor. Its typical 2.65 V forward voltage gives an illustrative `(5 − 2.65) / 560 ≈ 4.2 mA`; actual current and brightness vary. Follow native K/cathode polarity.','- The TVS remains bidirectional 5 V stand-off / 200 W pulse class. A 9.2 V clamp rating is not an overvoltage shutdown or a guarantee that every downstream supply pin stays within its absolute maximum.','- Self-assembly of the entire board still includes the exposed-pad QFN smartcard bridge. Use a controlled paste/reflow process and inspection; the large passive lands do not make the QFN an ordinary header-soldering task.','- Use the revision-specific C&K switch and GCT USB4125 lands. Old-board footprints and enclosure plungers are not interchangeable by assumption.','- Physical bring-up and supply/camera/display qualification remain pending; use the staged assembly guide.','','## Selection notes','']
lines += [f"- **{', '.join(p['refs'])}**: {p['rationale']}" for p in data['parts']]
lines += ['','## Retained reference','', '[Kingbright LED drawing and ratings](../../../reference/pdfs/Kingbright-APT2012LZGCK.pdf). The [Littelfuse SMF manufacturer data sheet](https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_smf_datasheet.pdf.pdf) is the online TVS reference. The original JLC TVS drawing is retained separately.']
lines += ['','## Board identity','',f"Board SHA-256: `{hashlib.sha256((V/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb').read_bytes()).hexdigest()}`.",f"Supplier pages checked {data['checkedAt']}. Rebuild using `mise run bom:self-assembly`; verify generated data with `mise run bom:self-assembly -- --check`."]
import io
def csv_text(items):
 out=io.StringIO();w=csv.DictWriter(out,fieldnames=list(items[0]) if items else ['References','Quantity per board','Original MPN','Original LCSC','Status'],lineterminator='\n');w.writeheader();w.writerows(items);return out.getvalue()
outputs={'bom-digikey.csv':csv_text(rows),'remaining-parts.csv':csv_text(remaining),'BOM-DIGIKEY.md':'\n'.join(lines)+'\n'}
for name,text in outputs.items():
 path=DEST/name
 if args.check: assert path.is_file() and path.read_text()==text,f'Stale self-assembly output: {name}'
 else: path.write_text(text)
print('Self-assembly sourcing verified: 35 native SMT references accounted for; 35 DigiKey selections, no unresolved fitted parts; all 23 commodity pieces covered.')
