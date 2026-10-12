#!/usr/bin/env python3
# /// script
# dependencies = ["shapely>=2,<3"]
# ///
"""Extract a pinned KiCad PCB into editable tscircuit component and routing data."""
import hashlib
import collections
import json
import math
from pathlib import Path
import re
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from shapely.affinity import rotate

ROOT = Path(__file__).resolve().parent.parent

def parse(text):
    stack = []
    root = None
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        if token == '(':
            node = []
            if stack:
                stack[-1].append(node)
            stack.append(node)
        elif token == ')':
            root = stack.pop()
        else:
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    return root

def children(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]

def one(node, key, default=None):
    return next(iter(children(node, key)), default or [])

def point(node, key):
    return [float(x) for x in one(node, key)[1:3]]

def arc_points(node, steps=36):
    a, b, c = [point(node, k) for k in ('start', 'mid', 'end')]
    ax, ay = a; bx, by = b; cx, cy = c
    d = 2 * (ax * (by-cy) + bx * (cy-ay) + cx * (ay-by))
    if abs(d) < 1e-10:
        raise ValueError('Degenerate board arc')
    ux = ((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
    uy = ((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
    start, mid, end = [math.atan2(y-uy, x-ux) for x,y in (a,b,c)]
    span = (end-start) % (2*math.pi)
    if (mid-start) % (2*math.pi) > span:
        span -= 2*math.pi
    radius = math.hypot(ax-ux, ay-uy)
    return [[ux+radius*math.cos(start+span*i/steps), uy+radius*math.sin(start+span*i/steps)] for i in range(steps+1)]

def main():
    source = ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
    source_bytes = source.read_bytes()
    pcb = parse(source_bytes.decode())
    edges, circles = [], []
    for node in pcb:
        if not isinstance(node, list) or one(node,'layer') != ['layer','Edge.Cuts']:
            continue
        if node[0] == 'gr_line': edges.append([point(node,'start'),point(node,'end')])
        elif node[0] == 'gr_arc': edges.append(arc_points(node))
        elif node[0] == 'gr_circle': circles.append({'center':point(node,'center'),'diameter':2*math.dist(point(node,'center'),point(node,'end'))})
        else: raise ValueError(f'Unhandled board outline primitive: {node[0]}')
    loops = []
    while edges:
        loop = edges.pop(0)
        while math.dist(loop[0],loop[-1]) > .02:
            for i, edge in enumerate(edges):
                if math.dist(loop[-1],edge[0]) < .02: break
                if math.dist(loop[-1],edge[-1]) < .02:
                    edge = list(reversed(edge)); break
            else: raise ValueError('Board outline is disconnected')
            loop += edge[1:]; edges.pop(i)
        loops.append(loop)
    loops.sort(key=lambda loop:(max(p[0] for p in loop)-min(p[0] for p in loop))*(max(p[1] for p in loop)-min(p[1] for p in loop)),reverse=True)
    outline = loops[0]
    xs, ys = zip(*outline)
    ox, oy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
    def xy(p): return {'x':round(p[0]-ox,6),'y':round(oy-p[1],6)}
    components, nets = [], collections.defaultdict(list)
    for f in children(pcb,'footprint'):
        props = {x[1]:x[2] for x in children(f,'property')}
        at = one(f,'at'); fx,fy = map(float,at[1:3]); theta = math.radians(float(at[3]) if len(at)>3 else 0)
        ref = props['Reference']; pads = []; pins = {}
        for i,p in enumerate(children(f,'pad')):
            layers = one(p,'layers')[1:]
            if not any(l in ('F.Cu','B.Cu','*.Cu') for l in layers): continue
            net = one(p,'net'); net = net[-1] if net else None
            pin = str(p[1])
            # KiCad repeats pad numbers for exposed-pad vias and module lands.
            # Each land gets a unique tscircuit port; the original net ties them.
            port = f'pin{i+1}'
            if net:
                nets[net].append(f'.{ref} .{port}')
            pa = one(p,'at'); px,py = map(float,pa[1:3])
            gx = fx+px*math.cos(theta)+py*math.sin(theta)
            gy = fy-px*math.sin(theta)+py*math.cos(theta)
            size = point(p,'size'); drill = one(p,'drill')
            holes = [float(v) for v in drill[1:] if isinstance(v,str) and re.fullmatch(r'[\d.]+',v)]
            if p[2] == 'np_thru_hole':
                circles.append({'center':[gx,gy],'diameter':holes[0]})
                continue
            label = one(p,'pinfunction')
            pins[port] = [f'pad_{pin}_{i+1}', label[1] if label else f'pad_{pin}']
            radius = min(size)*float(one(p,'roundrect_rratio',['_', '0'])[1])
            geometry = box(-size[0]/2,-size[1]/2,size[0]/2,size[1]/2)
            if p[3] == 'roundrect' and radius:
                geometry = box(-size[0]/2+radius,-size[1]/2+radius,size[0]/2-radius,size[1]/2-radius).buffer(radius,quad_segs=8)
            elif p[3] == 'custom':
                primitives = []
                for primitive in one(p,'primitives')[1:]:
                    if primitive[0] == 'gr_circle':
                        center = point(primitive,'center')
                        primitives.append(Point(center[0],-center[1]).buffer(math.dist(center,point(primitive,'end')),quad_segs=12))
                    elif primitive[0] == 'gr_poly':
                        primitives.append(Polygon([(float(pt[1]),-float(pt[2])) for pt in children(one(primitive,'pts'),'xy')]))
                    else: raise ValueError(f'Unsupported custom pad primitive: {primitive[0]}')
                if primitives: geometry = unary_union([geometry,*primitives])
            geometry = rotate(geometry,float(pa[3]) if len(pa)>3 else 0,origin=(0,0))
            pads.append({'port':port,'number':pin,'type':p[2],'shape':p[3],
                         'x':round(gx-fx,6),'y':round(fy-gy,6), 'absolute':xy([gx,gy]),
                         'width':size[0],'height':size[1],
                         'rotation':float(pa[3]) if len(pa)>3 else 0,
                         'layer':'bottom' if 'B.Cu' in layers else 'top',
                         'drill':holes,'net':net,
                         'radius':radius,'polygon':[{'x':round(x,6),'y':round(y,6)} for x,y in list(geometry.exterior.coords)[:-1]],
                         'primitives':one(p,'primitives')[1:]})
        components.append({'name':ref,'value':props.get('Value',''),'footprint':f[1],
                           'layer':'bottom' if one(f,'layer')[1]=='B.Cu' else 'top',
                           'dnp':'dnp' in one(f,'attr'),
                           'excludeFromBom':'exclude_from_bom' in one(f,'attr'),
                           'lcsc':props.get('LCSC'), 'datasheet':props.get('Datasheet'),
                           'description':props.get('Description',''),
                           **xy([fx,fy]),'pins':pins,'pads':pads})
    components.sort(key=lambda c:c['name'])
    net_names = {n:f'N{i+1}' for i,n in enumerate(sorted(nets))}
    segments = [{'net':one(s,'net')[-1],'start':xy(point(s,'start')),'end':xy(point(s,'end')),
                 'width':float(one(s,'width')[1]),'layer':'top' if one(s,'layer')[1]=='F.Cu' else 'bottom'} for s in children(pcb,'segment')]
    vias = [{'net':one(v,'net')[-1], **xy(point(v,'at')), 'outerDiameter':float(one(v,'size')[1]),
             'holeDiameter':float(one(v,'drill')[1])} for v in children(pcb,'via')]
    fills = []
    for zone in children(pcb,'zone'):
        for polygon in children(zone,'filled_polygon'):
            fills.append({'net':one(zone,'net')[-1], 'layer':'top' if one(polygon,'layer')[1]=='F.Cu' else 'bottom',
                          'points':[xy(list(map(float,p[1:]))) for p in children(one(polygon,'pts'),'xy')]})
    data = {'source': {'path': str(source.relative_to(ROOT)), 'sha256': hashlib.sha256(source_bytes).hexdigest()}, 'origin':{'x':ox,'y':oy},'width':max(xs)-min(xs),'height':max(ys)-min(ys),
            'outline':[xy(p) for p in outline[:-1]],
            'holes':[dict(xy(c['center']),diameter=c['diameter']) for c in circles],
            'cutouts':[[xy(p) for p in loop[:-1]] for loop in loops[1:]],'components':components,
            'nets':[{'name':net_names[n],'label':n,'ports':nets[n]} for n in sorted(nets)],
            'segments':segments,'vias':vias,'fills':fills}
    (ROOT/'src/generated').mkdir(parents=True,exist_ok=True)
    (ROOT/'src/generated/reference-board.json').write_text(json.dumps(data,indent=2)+'\n')
    print(f'Extracted {len(components)} components, {len(nets)} nets, {len(segments)} tracks, {len(vias)} vias, {len(fills)} filled polygons.')

if __name__ == '__main__': main()
