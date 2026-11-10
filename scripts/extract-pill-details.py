#!/usr/bin/env python3
"""Read-only KiCad geometry extraction for the complete pill-carrier port.

Run through mise with uv; KiCad's bundled Python resolves its stroke font,
mirroring, arcs, pad apertures and footprint transforms. Never saves the board.
"""
import hashlib, json, os, runpy, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if '--worker' not in sys.argv:
    cli = runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']()
    python = cli.parent.parent/'Frameworks/Python.framework/Versions/3.9/bin/python3'
    sys.exit(subprocess.call([str(python), __file__, '--worker']))
import wx
wx.Log.SetLogLevel(wx.LOG_Error)
app = wx.App(False)
import pcbnew as p
source = ROOT/'variants/lcd-module-2.8/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
before = source.read_bytes()
b = p.LoadBoard(str(source))
reference = json.loads((ROOT/'src/generated/pill-board.json').read_text())
ox, oy = reference['origin']['x'], reference['origin']['y']
def point(v): return {'x':round(p.ToMM(v.x)-ox,6), 'y':round(oy-p.ToMM(v.y),6)}
def ring(chain, clockwise):
    points = [point(chain.CPoint(i)) for i in range(chain.PointCount())]
    # Circuit JSON BRep winding in +Y-up coordinates.
    area = sum(a['x']*z['y']-z['x']*a['y'] for a,z in zip(points,points[1:]+points[:1]))
    if (area < 0) != clockwise: points.reverse()
    return {'vertices':points}
def polygons(poly):
    return [{'outer_ring':ring(poly.Outline(i),True),
             'inner_rings':[ring(poly.Hole(i,h),False) for h in range(poly.HoleCount(i))]}
            for i in range(poly.OutlineCount())]
layers = {}
for name, layer in [('F.SilkS',p.F_SilkS),('B.SilkS',p.B_SilkS),('F.Fab',p.F_Fab),('B.Fab',p.B_Fab),
                    ('F.CrtYd',p.F_CrtYd),('B.CrtYd',p.B_CrtYd),('F.Mask',p.F_Mask),('B.Mask',p.B_Mask),
                    ('F.Paste',p.F_Paste),('B.Paste',p.B_Paste),('Dwgs.User',p.Dwgs_User),('Cmts.User',p.Cmts_User),
                    ('Eco1.User',p.Eco1_User),('Eco2.User',p.Eco2_User),('Margin',p.Margin),
                    ('F.Adhes',p.F_Adhes),('B.Adhes',p.B_Adhes)]:
    poly = p.SHAPE_POLY_SET()
    b.ConvertBrdLayerToPolygonalContours(layer, poly)
    layers[name] = polygons(poly)
texts, models, pads, inventory, courtyards = [], [], [], [], []
def record(item, ref=None):
    entry = {'uuid':item.m_Uuid.AsString(),'reference':ref,'type':type(item).__name__,
             'layer':b.GetLayerName(item.GetLayer())}
    if isinstance(item,p.PCB_TEXT):
        entry.update(text=item.GetShownText(False), visible=item.IsVisible(), mirrored=item.IsMirrored(),
                     position=point(item.GetPosition()), angle=item.GetTextAngleDegrees())
        texts.append(entry.copy())
    inventory.append(entry)
for item in b.GetDrawings(): record(item)
for f in b.GetFootprints():
    ref = f.GetReference()
    f.BuildCourtyardCaches()
    for name,layer in [('top',p.F_CrtYd),('bottom',p.B_CrtYd)]:
        for shape in polygons(f.GetCourtyard(layer)):
            courtyards.append({'reference':ref,'layer':name,'shape':shape})
    for item in f.GraphicalItems(): record(item,ref)
    for item in f.GetFields(): record(item,ref)
    for model in f.Models():
        filename = model.m_Filename.replace('${KIPRJMOD}',str(source.parent))
        path = Path(filename)
        assert path.is_file(), f'Missing retained model: {filename}'
        models.append({'reference':ref,'path':str(path.relative_to(ROOT)),
                       'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                       'show':model.m_Show,'offset':{k:getattr(model.m_Offset,k) for k in ['x','y','z']},
                       'rotation':{k:getattr(model.m_Rotation,k) for k in ['x','y','z']},
                       'scale':{k:getattr(model.m_Scale,k) for k in ['x','y','z']}})
    for pad in f.Pads():
        copper=[]
        for layer in [p.F_Cu,p.B_Cu]:
            if pad.IsOnLayer(layer):
                poly=p.SHAPE_POLY_SET()
                pad.TransformShapeToPolygon(poly,layer,0,p.FromMM(.002),p.ERROR_INSIDE)
                copper=polygons(poly);break
        pads.append({'reference':ref,'uuid':pad.m_Uuid.AsString(),'number':pad.GetNumber(),
                     'maskTop':pad.IsOnLayer(p.F_Mask),'maskBottom':pad.IsOnLayer(p.B_Mask),
                     'maskMarginTop':p.ToMM(pad.GetSolderMaskExpansion(p.F_Mask)),
                     'maskMarginBottom':p.ToMM(pad.GetSolderMaskExpansion(p.B_Mask)),
                     'pasteTop':pad.IsOnLayer(p.F_Paste),'pasteBottom':pad.IsOnLayer(p.B_Paste),'copper':copper})
result = {'source':reference['source'], 'engine':p.GetBuildVersion(),'origin':reference['origin'],
          'thickness':p.ToMM(b.GetDesignSettings().GetBoardThickness()),'layers':layers,
          'texts':texts,'models':models,'pads':pads,'inventory':inventory,'courtyards':courtyards}
assert source.read_bytes() == before, 'Read-only extraction changed the board'
(ROOT/'src/generated/pill-details.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
print('Native detail polygons:',{layer:len(shapes) for layer,shapes in layers.items()})
print(f'Retained {len(texts)} text items and {len(models)} model instances.')
