#!/usr/bin/env python3
"""Build the native front 'Orbital field guide' without altering any hardware.

Default: write a candidate and an SVG plate for review. --apply installs the
candidate only after exact protected-tree comparison and native DRC succeed.
The baseline and all existing labels are retained verbatim.
"""
import argparse
import hashlib
import html
import json
import math
import runpy
import subprocess
import uuid
from pathlib import Path

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from svgpathtools import parse_path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
BASE_COMMIT = '10ad10f'
BASE_SHA = '45f28bbfcf4099a6d512e9cc8dbf73b67a4cb39fba47443068fa4b424abf5109'
OUT = ROOT / '.tools/front-artwork'
PLATE = ROOT / 'assets/branding/front-orbital-field-guide.svg'
RECORD = ROOT / 'docs/pcb-front-artwork.json'
Y = 89.579
MIN_STROKE = .15
MASK_CLEARANCE = .35


def uid(value):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'shieldsigner-front-orbital:' + value))


def native_polygon(shape):
    def points(ring):
        return [(128 + p['x'], Y - p['y']) for p in ring['vertices']]
    return Polygon(points(shape['outer_ring']), [points(r) for r in shape['inner_rings']])


def geometry_parts(geometry, kind):
    if geometry.geom_type == kind:
        yield geometry
    elif hasattr(geometry, 'geoms'):
        for child in geometry.geoms:
            yield from geometry_parts(child, kind)


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    baseline = subprocess.check_output(['git', 'show', f'{BASE_COMMIT}:kicad/{BOARD.name}'], cwd=ROOT)
    assert hashlib.sha256(baseline).hexdigest() == BASE_SHA
    (OUT/'baseline.kicad_pcb').write_bytes(baseline)
    details = json.loads(subprocess.check_output(['git','show',f'{BASE_COMMIT}:src/generated/pill-details.json'],cwd=ROOT))
    assert details['source']['sha256'] == BASE_SHA, 'Generate from the artwork baseline before first application'
    # Exact KiCad mask apertures, existing printed geometry and front courtyards.
    masks = unary_union([native_polygon(s) for s in details['layers']['F.Mask']]).buffer(MASK_CLEARANCE)
    labels = unary_union([native_polygon(s) for s in details['layers']['F.SilkS']]).buffer(.4)
    bodies = unary_union([native_polygon(c['shape']) for c in details['courtyards'] if c['layer']=='top']).buffer(.35)
    mounts = unary_union([Point(x,y).buffer(3.8) for x,y in
                         [(78,65.679),(78,113.479),(187,65.679),(187,113.479),
                          (92.75,65.679),(92.75,113.479),(175.25,65.679),(175.25,113.479),
                          (176.7,68),(176.7,111)]])
    usable = LineString([(83,Y),(173,Y)]).buffer(33.2, quad_segs=96)
    obstacles = unary_union([masks, labels, bodies, mounts])
    texts, strokes, solids, icon_boxes = [], [], [], []

    def text(value,x,y,size=1,stroke=.17,angle=0):
        # Conservative reservation; native DRC independently checks actual glyphs.
        width=len(value)*size*.92
        bounds=affinity.rotate(box(x-width/2-.35,y-size*.8-.3,x+width/2+.35,y+size*.8+.3),angle,origin=(x,y))
        assert usable.covers(bounds), f'Text outside safe board: {value}'
        assert not bounds.intersects(obstacles), f'Text overlaps retained feature: {value}'
        texts.append(dict(text=value,x=x,y=y,size=size,stroke=stroke,angle=angle,bounds=bounds))

    def path(points,width=.2,icon=False):
        strokes.append((LineString(points),width,icon))

    def ellipse(cx,cy,rx,ry,start=0,end=360,rotation=0,width=.2,icon=False):
        a=math.radians(rotation)
        pts=[]
        for i in range(max(2,round(abs(end-start)*1.5))+1):
            t=math.radians(start+(end-start)*i/max(2,round(abs(end-start)*1.5)))
            x,y=rx*math.cos(t),ry*math.sin(t)
            pts.append((cx+x*math.cos(a)-y*math.sin(a),cy+x*math.sin(a)+y*math.cos(a)))
        path(pts,width,icon)

    def star(x,y,r=.65):
        path([(x-r,y),(x+r,y)],.15)
        path([(x,y-r),(x,y+r)],.15)

    # The large shield is the existing repository-authored mark, sampled from
    # its vector source, never raster-traced or substituted with a new identity.
    import xml.etree.ElementTree as ET
    mark=ET.parse(ROOT/'assets/branding/shieldsigner-mark.svg').getroot()
    for element in mark:
        if not element.tag.endswith('path'):
            continue
        for subpath in parse_path(element.attrib['d']).continuous_subpaths():
            points=[]
            for segment in subpath:
                count=max(1,math.ceil(segment.length()/1.2))
                for i in range(count):
                    z=segment.point(i/count)
                    points.append((134+(z.real-32)*.40,84+(z.imag-34)*.40))
            solids.append(Polygon(points))
    icon_boxes.append(box(121.8,71.6,146.2,97))

    def qr_finder(cx,cy):
        # An abstract QR finder symbol, deliberately not an encoded QR payload.
        for x,y in [(cx-3.4,cy-3.4),(cx+.8,cy-3.4),(cx-3.4,cy+.8)]:
            path([(x,y),(x+2.6,y),(x+2.6,y+2.6),(x,y+2.6),(x,y)],.25,True)
            solids.append(box(x+.85,y+.85,x+1.75,y+1.75))
        for dx,dy in [(1,1),(2.6,1),(1,2.6),(2.6,2.6)]:
            solids.append(box(cx+dx,cy+dy,cx+dx+.65,cy+dy+.65))
        icon_boxes.append(box(cx-4.3,cy-4.3,cx+4.3,cy+4.3))

    qr_finder(110,85)
    qr_finder(158,85)
    text('SHIELDSIGNER',134,64.9,2.4,.32)
    text('OFFLINE SIGNING INSTRUMENT',134,69,1,.16)
    text('01 / SCAN',110,93,1.15,.19)
    text('UNSIGNED TX',110,96, .85,.15)
    text('02 / REVIEW + SIGN',134,100.2,1.1,.18)
    text('EVERY OUTPUT. EVERY FEE.',134,103.4,.85,.15)
    text('03 / EXPORT',158,93,1.15,.19)
    text('SIGNED TX',158,96,.85,.15)
    text('ONE DISPLAY / J701 OR J702',134,110.6,.95,.16)
    text('JP701: 3V3 / JP702: 5V / NEVER BOTH',134,113.8,.85,.15)
    text('NAVIGATION',65,68.5,1.1,.18)
    text('CONTEXT',197,89.6,1,.17,90)
    text('OPEN HARDWARE',134,117.2,1,.17)

    # A pair of tilted orbital paths ties QR input, the shield and QR output.
    ellipse(134,85,34,18.7,rotation=-14,width=.25)
    ellipse(134,85,35.4,20.1,rotation=-14,width=.15)
    ellipse(134,85,29,15.7,22,158,rotation=14,width=.15)
    for x, direction in [(117,1),(150,1)]:
        path([(x-1.8,85),(x+1.8,85)],.25,True)
        path([(x+.1,83.9),(x+1.8,85),(x+.1,86.1)],.25,True)
    # Capsule border, navigation graduations and control constellations span
    # the full face. Clearances create deliberate interruptions at hardware.
    for inset,width in [(2.1,.28),(3.2,.15)]:
        border=LineString([(83,Y),(173,Y)]).buffer(35-inset,quad_segs=96).exterior
        path(list(border.coords),width)
    for cx,sign in [(83,-1),(173,1)]:
        for deg in range(-78,79,6):
            a=math.radians(deg)
            r=31.8
            length=1.5 if deg%18==0 else .65
            path([(cx+sign*r*math.cos(a),Y+r*math.sin(a)),
                  (cx+sign*(r-length)*math.cos(a),Y+(r-length)*math.sin(a))],.18)
    for radius,width in [(17.8,.23),(19,.15)]:
        ellipse(68.47,89.579,radius,radius,-160,150,width=width)
    for cx,cy in [(68.47,79.085),(57.98,89.579),(78.92,89.579),(68.47,100.005)]:
        ellipse(cx,cy,5.15,5.15,width=.2)
    path([(68.47,84.5),(68.47,94.6)],.2)
    path([(63.4,89.579),(73.5,89.579)],.2)
    ellipse(68.47,89.579,1.2,1.2,width=.25,icon=True)
    for cy in [79.295,89.565,99.895]:
        ellipse(186.88,cy,5.2,5.2,width=.23)
    path([(195,76),(195,103)],.2)
    for cy in [79.295,89.565,99.895]:
        path([(192.8,cy),(195,cy)],.2)
    for x,y,r in [(105,63,.7),(164,61.5,.65),(171,74,.7),(104,105,.55),
                  (164,107,.65),(158,117,.55),(94,60,.6),(62,109,.6)]:
        star(x,y,r)
    for x,y in [(104,74),(166,99),(118,106),(149,63)]:
        ellipse(x,y,.7,.7,width=.2)

    text_blocks=unary_union([t['bounds'] for t in texts])
    icons=unary_union(icon_boxes)
    graphics=[]
    svg=[]
    ink=[]
    index=0

    def number(v):
        return f'{v:.6f}'.rstrip('0').rstrip('.')

    for shape,width,is_icon in strokes:
        assert width>=MIN_STROKE
        exclusion=unary_union([obstacles.buffer(width/2),text_blocks,icons if not is_icon else Polygon()])
        clipped=shape.intersection(usable.buffer(-width/2)).difference(exclusion)
        for line in geometry_parts(clipped,'LineString'):
            if line.length<.7:
                continue
            # Emit editable polylines as native segments; deterministic UUIDs
            # retain one composition across regeneration and review cycles.
            points=list(line.simplify(.012).coords)
            svg.append(f'<polyline points="{" ".join(f"{x:.5f},{y:.5f}" for x,y in points)}" fill="none" stroke="currentColor" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>')
            for start,end in zip(points,points[1:]):
                if math.dist(start,end)<.025:
                    continue
                graphics.append(f'(gr_line (start {number(start[0])} {number(start[1])}) (end {number(end[0])} {number(end[1])}) (stroke (width {width}) (type solid)) (layer "F.SilkS") (uuid "{uid(str(index))}"))')
                index+=1
            ink.append(line.buffer(width/2))
    for solid in solids:
        clipped=solid.intersection(usable).difference(unary_union([obstacles,text_blocks]))
        for polygon in geometry_parts(clipped,'Polygon'):
            assert not polygon.interiors, 'Use explicit triangulation for a holed polygon'
            if polygon.area<.05:
                continue
            points=list(polygon.exterior.coords)[:-1]
            graphics.append(f'(gr_poly (pts {" ".join(f"(xy {number(x)} {number(y)})" for x,y in points)}) (stroke (width 0) (type solid)) (fill solid) (layer "F.SilkS") (uuid "{uid(str(index))}"))')
            index+=1
            svg.append(f'<polygon points="{" ".join(f"{x:.5f},{y:.5f}" for x,y in points)}" fill="currentColor"/>')
            ink.append(polygon)
    for t in texts:
        graphics.append(f'(gr_text {json.dumps(t["text"])} (at {t["x"]} {t["y"]} {-t["angle"]}) (layer "F.SilkS") (uuid "{uid(str(index))}") (effects (font (size {t["size"]} {t["size"]}) (thickness {t["stroke"]}))))')
        index+=1
        svg.append(f'<text x="{t["x"]}" y="{t["y"]}" fill="currentColor" font-family="monospace" font-size="{t["size"]*1.4}" text-anchor="middle" dominant-baseline="central" transform="rotate({t["angle"]} {t["x"]} {t["y"]})">{html.escape(t["text"])}</text>')
    group_name='Front / Orbital field guide'
    group=f'(group "{group_name}" (uuid "{uid("group")}") (members {" ".join(json.dumps(uid(str(i))) for i in range(index))}))'
    ungrouped=baseline.decode().rstrip()[:-1]+'\n'+'\n'.join(graphics)+'\n)\n'
    candidate=ungrouped.rstrip()[:-1]+'\n'+group+'\n)\n'
    path=OUT/'candidate.kicad_pcb';path.write_text(candidate)
    # Keep the exact project rules during the candidate's independent DRC.
    path.with_suffix('.kicad_pro').write_bytes(BOARD.with_suffix('.kicad_pro').read_bytes())
    (OUT/'fp-lib-table').write_text((BOARD.parent/'fp-lib-table').read_text().replace('${KIPRJMOD}',str(BOARD.parent)))
    PLATE.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="48 54.579 160 70" width="160mm" height="70mm" style="color:#f4efdb">\n'
                     '<title>ShieldSigner / Orbital field guide / native front silkscreen</title>\n'
                     '<path d="M83 54.579 H173 A35 35 0 0 1 173 124.579 H83 A35 35 0 0 1 83 54.579" fill="#172b25"/>\n'
                     +'\n'.join(svg)+'\n</svg>\n')
    (OUT/'ungrouped.kicad_pcb').write_text(ungrouped)
    audit=runpy.run_path(str(ROOT/'scripts/audit-pcb-artwork.py'))['compare'](OUT/'baseline.kicad_pcb',OUT/'ungrouped.kicad_pcb')
    assert audit['passed'] and not audit['protectedChangedTags']
    # No line or filled ink touches expanded mask apertures. Text is guarded
    # by its conservative bounds above and by KiCad DRC before installation.
    assert unary_union(ink).intersection(masks.buffer(-.001)).area<.000001
    record=dict(schema=1,name='Orbital field guide',baselineCommit=BASE_COMMIT,baselineBoardSha256=BASE_SHA,
                boardSha256=hashlib.sha256(path.read_bytes()).hexdigest(),layer='F.SilkS',
                graphics=index,minimumStrokeMm=MIN_STROKE,maskClearanceMm=MASK_CLEARANCE,
                groupUuid=uid('group'),groupName=group_name,
                boundsMm=[49.8,56.379,206.2,122.779],
                source='assets/branding/front-orbital-field-guide.svg',
                themes=['ShieldSigner shield/lightning mark','The Space / orbital navigation','QR air gap / verify before signing','open hardware / assembly field guide'],
                protectedTreeSha256=audit['candidate']['protectedSha256'],
                scope='Top-level front silkscreen additions only. All existing labels, rear artwork, footprints, copper, masks, holes, outlines, rules, fills and schematic remain unchanged.')
    (OUT/'record.json').write_text(json.dumps(record,indent=2)+'\n')
    (OUT/'artwork-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print('Built candidate:',path.relative_to(ROOT),'; native graphic items:',index,flush=True)
    return path,record


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply',action='store_true')
    args=ap.parse_args()
    candidate,record=build()
    if args.apply:
        assert hashlib.sha256(BOARD.read_bytes()).hexdigest() in {BASE_SHA,record['boardSha256']},'Board changed; refusing overwrite'
        cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']()
        subprocess.run([str(cli),'pcb','drc','--severity-all','--format','json','--refill-zones','--output',str(OUT/'drc.json'),str(candidate)],check=True)
        drc=json.loads((OUT/'drc.json').read_text())
        assert not drc['violations'] and not drc.get('unconnected_items'), 'Inspect candidate DRC before applying'
        BOARD.write_bytes(candidate.read_bytes())
        RECORD.write_text(json.dumps(record,indent=2)+'\n')
        print('Applied front artwork; exact baseline backup:',OUT/'baseline.kicad_pcb')


if __name__=='__main__':
    main()
