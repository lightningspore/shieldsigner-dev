#!/usr/bin/env python3
# /// script
# dependencies = ["shapely>=2,<3"]
# ///
"""Independent comparison only: native data never participates in source builds."""
import hashlib,json,csv,re,math
from pathlib import Path
from shapely.geometry import Polygon,Point,LineString,box
from shapely.affinity import rotate,translate
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'src/generated/pill-board.json').read_text())
details=json.loads((ROOT/'src/generated/pill-details.json').read_text())
j=json.loads((ROOT/'dist/pill-native/board.circuit.json').read_text())
assert hashlib.sha256((ROOT/ref['source']['path']).read_bytes()).hexdigest()==ref['source']['sha256'],'Refresh reference after native edits'
def pts(x):return [(p['x'],p['y']) for p in x]
def brep(s):return Polygon(pts(s['outer_ring']['vertices']),[pts(r['vertices']) for r in s['inner_rings']])
native={p['uuid']:unary_union([brep(s) for s in p['copper']]) for p in details['pads']}
def geometry(p):
 s=p['shape']
 if s=='polygon':return Polygon(pts(p['points']))
 if s=='circle':a=Point(0,0).buffer(p.get('outer_diameter',p.get('radius',0)*2)/2,quad_segs=64)
 elif s=='pill':
  w,h=p['outer_width'],p['outer_height'];dx,dy=max(0,(w-h)/2),max(0,(h-w)/2)
  a=LineString([(-dx,-dy),(dx,dy)]).buffer(min(w,h)/2,quad_segs=64)
 elif s in ('rect','rotated_rect','circular_hole_with_rect_pad'):
  w,h=(p['width'],p['height']) if s in ('rect','rotated_rect') else (p['rect_pad_width'],p['rect_pad_height'])
  r=p.get('corner_radius',0)
  a=box(-w/2+r,-h/2+r,w/2-r,h/2-r).buffer(r,quad_segs=64) if r else box(-w/2,-h/2,w/2,h/2)
 else:raise AssertionError(s)
 return translate(rotate(a,p.get('ccw_rotation',0),origin=(0,0)),p['x'],p['y'])
class DSU:
 def __init__(self):self.p={}
 def root(self,x):
  self.p.setdefault(x,x)
  if self.p[x]!=x:self.p[x]=self.root(self.p[x])
  return self.p[x]
 def join(self,ids):
  if not ids:return
  root=self.root(ids[0])
  for x in ids[1:]:self.p[self.root(x)]=root
actual=DSU();expected=DSU()
for e in j:
 if e['type']=='source_trace':actual.join(e.get('connected_source_port_ids',[])+e.get('connected_source_net_ids',[]))
 if e['type']=='source_component_internal_connection':actual.join(e['source_port_ids'])
for b in ref['bridges']:expected.join(b['nets'])
# Values and supplier identities are a second, independent electrical/BOM oracle.
source_parts={e['name']:e for e in j if e['type']=='source_component'}
for part in ref['components']:
 actual_part=source_parts[part['name']]
 if part.get('lcsc'):assert actual_part.get('supplier_part_numbers',{}).get('jlcpcb')==[part['lcsc']],part['name']
 field={'R':'resistance','C':'capacitance'}.get(part['name'][0])
 if field:
  value=re.sub(r'^(\d+)([KMkR])(\d+)$',r'\1.\3\2',part['value'])
  m=re.fullmatch(r'([0-9.]+)([pnuUmMkKRG]?)(?:[fFΩ])?',value);assert m,part['value']
  factor={'p':1e-12,'n':1e-9,'u':1e-6,'U':1e-6,'m':1e-3,'k':1e3,'K':1e3,'M':1e6,'G':1e9,'R':1,'':1}[m[2]]
  assert math.isclose(actual_part[field],float(m[1])*factor,rel_tol=1e-9),part['name']
for row in csv.DictReader((ROOT/'variants/lcd-module-2.8/manufacturing/bom-jlcpcb.csv').open()):
 for name in row['Designator'].split(','):
  part=source_parts[name.strip()]
  assert part['manufacturer_part_number']==row['Comment'].split('; ',1)[1],name
  assert part['supplier_part_numbers']['jlcpcb']==[row['LCSC Part #']],name
ports={p['pcb_port_id']:p for p in j if p['type']=='pcb_port'}
matches=[];worst=0
for part in ref['components']:
 source=next(e for e in j if e['type']=='source_component' and e['name']==part['name'])
 if not part['pads']:continue
 comp=next(e for e in j if e['type']=='pcb_component' and e['source_component_id']==source['source_component_id'])
 lands=[e for e in j if e['type'] in ('pcb_smtpad','pcb_plated_hole') and e['pcb_component_id']==comp['pcb_component_id']]
 assert len(lands)==len(part['pads']),(part['name'],len(lands),len(part['pads']))
 for pad in part['pads']:
  target=native[pad['uuid']]
  bridge=next((b for b in ref['bridges'] if b['reference']==part['name']),None)
  if bridge and pad['port']=='pin1':target=target.union(Polygon(pts(bridge['points'])))
  land=min(lands,key=lambda x:geometry(x).hausdorff_distance(target));lands.remove(land)
  error=geometry(land).hausdorff_distance(target)
  assert error<=.005,f"{part['name']}.{pad['number']}: geometry differs by {error:.6f} mm"
  if pad['type']=='smd':assert land['layer']==pad['layer'],part['name']
  if pad['drill']:assert abs(land.get('hole_diameter',land.get('hole_width',0))-pad['drill'][0])<.001,part['name']
  worst=max(worst,error)
  port=ports[land['pcb_port_id']]['source_port_id']
  key=pad['net'] or f"NC_{part['name']}_{pad['number']}"
  matches.append((part['name'],pad['number'],actual.root(port),expected.root(key)))
# Both directions: catches missing connections and unintended net merges.
a_to_e={};e_to_a={}
for name,pin,a,e in matches:
 assert a_to_e.setdefault(a,e)==e,f'Unexpected short at {name}.{pin}'
 assert e_to_a.setdefault(e,a)==a,f'Missing connection at {name}.{pin}'
report={'physicalLands':len(matches),'maximumHausdorffDistanceMm':worst,'toleranceMm':.005,'electricalPartitions':len(e_to_a),'nativeSource':ref['source']}
(ROOT/'dist/pill-native/native-parity.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
