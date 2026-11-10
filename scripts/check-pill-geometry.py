#!/usr/bin/env python3
# /// script
# dependencies = ["shapely>=2,<3"]
# ///
"""Compare every rendered land to an independent native KiCad polygonization."""
import json,math
from pathlib import Path
from shapely.geometry import Polygon,Point,LineString,box
from shapely.affinity import rotate,translate
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'src/generated/pill-board.json').read_text())
details=json.loads((ROOT/'src/generated/pill-details.json').read_text())
circuit=json.loads((ROOT/'dist/pill-tscircuit/shieldsigner-plus.circuit.json').read_text())
def points(vertices):return [(p['x'],p['y']) for p in vertices]
def brep(s):return Polygon(points(s['outer_ring']['vertices']),[points(r['vertices']) for r in s['inner_rings']])
native={p['uuid']:unary_union([brep(s) for s in p['copper']]) for p in details['pads']}
worst=0;checked=0
for part in ref['components']:
    source=next(c for c in circuit if c['type']=='source_component' and c['name']==part['name'])
    for pad in part['pads']:
        port=next(c for c in circuit if c['type']=='source_port' and c['source_component_id']==source['source_component_id'] and pad['port'] in c.get('port_hints',[]))
        pcbport=next(c for c in circuit if c['type']=='pcb_port' and c['source_port_id']==port['source_port_id'])
        land=next(c for c in circuit if c['type'] in ['pcb_smtpad','pcb_plated_hole'] and c.get('pcb_port_id')==pcbport['pcb_port_id'])
        if land['shape']=='polygon': actual=Polygon(points(land['points']))
        else:
            if land['shape']=='circle': actual=Point(0,0).buffer(land.get('outer_diameter',land.get('radius',0)*2)/2,quad_segs=64)
            elif land['shape']=='pill':
                w,h=land['outer_width'],land['outer_height'];radius=min(w,h)/2
                dx,dy=max(0,(w-h)/2),max(0,(h-w)/2)
                actual=LineString([(-dx,-dy),(dx,dy)]).buffer(radius,quad_segs=64)
            elif land['shape']=='circular_hole_with_rect_pad':
                w,h=land['rect_pad_width'],land['rect_pad_height'];actual=box(-w/2,-h/2,w/2,h/2)
            else:raise AssertionError(land['shape'])
            actual=translate(rotate(actual,land.get('ccw_rotation',0),origin=(0,0)),land['x'],land['y'])
        expected=native[pad['uuid']]
        error=actual.hausdorff_distance(expected)
        assert error<=.005, f"{part['name']}.{pad['port']} differs from native geometry by {error:.6f} mm"
        worst=max(worst,error);checked+=1
report={'source':ref['source'],'physicalLands':checked,'maximumHausdorffDistanceMm':worst,'toleranceMm':.005}
(ROOT/'dist/pill-tscircuit/native-land-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
