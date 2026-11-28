"""Round-trip production Gerbers/Excellon with an independent parser."""
import collections,hashlib,json,math,warnings
from pathlib import Path
from gerbonara.layers import LayerStack
from gerbonara.utils import MM
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'variants/full-size-pico';M=V/'manufacturing';FAB=ROOT/'dist/full-size-pico/prototype/gerbers';PCB=V/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
manifest=json.loads((M/'manifest.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(PCB)==manifest['boardSha256']
with warnings.catch_warnings(record=True) as ws:
 warnings.simplefilter('always');stack=LayerStack.open(FAB)
 assert len(stack.graphic_layers)==11
 assert set(stack.graphic_layers)=={('top','copper'),('bottom','copper'),('inner_1','copper'),('inner_2','copper'),('top','mask'),('bottom','mask'),('top','paste'),('bottom','paste'),('top','silk'),('bottom','silk'),('mechanical','outline')}
 (x0,y0),(x1,y1)=stack.outline.bounding_box(MM)
 assert abs(x1-x0-160.05)<.00001 and abs(y1-y0-70.05)<.00001,'Gerber perimeter/datum changed'
 expected=json.loads((ROOT/'dist/full-size-pico/native-drills.json').read_text());assert expected['boardSha256']==manifest['boardSha256']
 used=[]
 for file in stack.drill_layers:
  text=Path(file.original_path).read_text();plated='TF.FileFunction,Plated,' in text
  assert plated or 'TF.FileFunction,NonPlated,' in text
  exp=[p for p in expected['drills'] if p['plated']==plated];assert len(file.objects)==len(exp)
  for obj in file.objects:
   diameter=obj.tool.diameter
   a,z=([obj.x,obj.y],[obj.x,obj.y]) if hasattr(obj,'x') else ([obj.x1,obj.y1],[obj.x2,obj.y2])
   center=[(a[0]+z[0])/2,(a[1]+z[1])/2]
   candidates=[p for p in exp if p['owner'] not in used and abs(p['diameterMm']-diameter)<.00001 and math.dist(center,p['centerMm'])<.0015 and min(max(math.dist(a,p['endsMm'][0]),math.dist(z,p['endsMm'][1])),max(math.dist(a,p['endsMm'][1]),math.dist(z,p['endsMm'][0])))<.0015]
   assert len(candidates)==1,('Drill/slot geometry mismatch',a,z,diameter,candidates)
   used.append(candidates[0]['owner'])
 assert len(used)==len(expected['drills'])
 # Copper/paste/mask flashes retain native X2 component attributes. Factory BOM
 # expands this aggregate U202 into the two strips J203/J204 without changing metal.
 apertures={}
 for layer in ['copper','paste','mask']:
  pads=[o for o in stack.graphic_layers[('bottom',layer)].objects if isinstance(o.attrs,dict) and (o.attrs.get('.C')==('U202',) or o.attrs.get('.P',('',''))[0]=='U202') and hasattr(o,'x')]
  assert len(pads)==40,(layer,len(pads))
  sizes=[]
  for pad in pads:
   (ax,ay),(zx,zy)=pad.bounding_box(MM);sizes.append([zx-ax,zy-ay])
   index=round((130-pad.y-57.319)/2.54);row=min([85.3475,103.1275],key=lambda x:abs((pad.x+50)-x));xx=row+(1.8 if index%2==0 else -1.8)
   assert 0<=index<=19 and abs(pad.x+50-xx)<.00001 and abs(130-pad.y-(57.319+2.54*index))<.00001
   if layer in ['copper','paste']:assert abs(zx-ax-2.2)<.00001 and abs(zy-ay-1.27)<.00001,(layer,zx-ax,zy-ay)
   else:assert zx-ax>2.2 and zy-ay>1.27
  apertures[layer]={'count':len(pads),'sizeMm':sizes[0]}
 for side in ['top','bottom']:(M/f'gerber-{side}.svg').write_text(str(stack.to_pretty_svg(side=side)))
report=dict(boardSha256=manifest['boardSha256'],parser='gerbonara 1.6.3',graphicLayers=11,perimeterStrokeWidthMm=.05,boardOutlineMm=[160,70],allNativeDrillObjectsMatched=len(used),platedObjects=sum(p['plated'] for p in expected['drills']),nonplatedObjects=sum(not p['plated'] for p in expected['drills']),headerApertures=apertures,drillCoordinateToleranceMm=.0015,parserWarnings=sorted({str(w.message).split(': ',1)[-1] for w in ws}),scope='Independent export/datum/land/drill checks and render; factory DFM, stock reservation and placement preview approval remain separate.')
(M/'gerber-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('Independent Gerber pass: 11 layers, 160 x 70 mm perimeter, all',len(used),'native drills/slots and 40 header copper/paste/mask lands match.')
