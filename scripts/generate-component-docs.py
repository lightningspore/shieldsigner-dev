#!/usr/bin/env python3
"""Generate a complete reference-design component guide, with actual pad/net maps."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
board = json.loads((ROOT/'src/generated/reference-board.json').read_text())
roles = json.loads((ROOT/'docs/component-rationale.json').read_text())
overrides = json.loads((ROOT/'docs/native-overrides.json').read_text())
refs = {p['name'] for p in board['components']}
assert refs == set(roles), f'Missing or stale explanations: {refs ^ set(roles)}'
lines = ['# Component guide', '',
'Every physical component in the pinned PCB is covered below. Population flags, footprints and pin/net mappings come from the pinned KiCad PCB. Values and supplier IDs include the documented native variant overrides and catalog identity corrections; the experimental tscircuit reference still uses upstream values. Functional explanations are engineering interpretations unless the hardware guide explicitly attributes them to an upstream note or datasheet. This describes the inherited circuit; it does not claim the original designer compared alternatives or optimized each value.', '',
'Use original KiCad pad numbers when wiring or probing. The tscircuit `pinN` names identify individual copper lands, not original package pin numbers. Repeated module pad numbers are intentional (castellated land plus through-hole).', '',
'**Default DNP: J302, R404, R408.** Their footprints remain on the board. Populate R403 and R409 for IM1=1 and IM0=0. Never fit both resistors in either strap pair. Solder-jumper pairs have their own open/closed settings; see [hardware guide](HARDWARE.md#configuration).', '',
'## Index', '', '| Ref | Value | Block / role | Assembly |', '|---|---|---|---|']
for p in board['components']:
 r=roles[p['name']]
 lines.append(f"| [{p['name']}](#{p['name'].lower()}) | {overrides.get(p['name'], {}).get('value',p['value'])} | {r['role']} | {'DNP' if p['dnp'] else 'Reference default'} |")
for p in board['components']:
 r=roles[p['name']]
 lines += ['',f"## {p['name']}",'',f"**{overrides.get(p['name'], {}).get('value',p['value'])} — {r['role']}.**",'',f"**How it works:** {r['works']}",'',f"**Why this choice:** {r['why']}",'',f"**How it is used:** {r['use']}",'',f"**Assembly:** {'Do not populate in the reference default.' if p['dnp'] else 'Present in the reference default; jumpers require the stated bridge setting.' if p['name'].startswith('JP') else 'Populate in the reference default.'} {'Excluded from the upstream BOM.' if p['excludeFromBom'] else ''}",'',f"**Footprint:** `{overrides.get(p['name'], {}).get('footprint',p['footprint'])}`; {p['layer']} side."]
 if p['name'] in overrides:lines += ['', '**Native variant change:** '+overrides[p['name']]['reason']]
 if p['lcsc']:lines += ['',f"**Source supplier identifier:** LCSC `{overrides.get(p['name'], {}).get('lcsc',p['lcsc'])}`. See BOM.md and BOM-TABLE.md for verified catalog identity, availability and remaining footprint qualification."]
 lines += ['', '| Original pad | tscircuit physical land | Connected net |', '|---|---|---|']
 for pad in p['pads']:
  lines.append(f"| {pad['number']} | `{pad['port']}` | `{pad['net'] or 'No assigned net'}` |")
(ROOT/'docs/COMPONENTS.md').write_text('\n'.join(lines)+'\n')
print(f'Documented all {len(refs)} components with population flags and physical pad/net maps.')
