"""Nominal Keystone 5015 envelope; dimensions from manufacturer's 5015 drawing."""
from pathlib import Path
import hashlib,json,cadquery as cq
ROOT=Path(__file__).resolve().parents[1];K=ROOT/'variants/lcd-module-2.8/kicad'
p=K/'3dmodels/vendor/Keystone-5015-envelope.step'
# Nominal occupied envelope, intentionally not a detailed formed-metal model.
outer=cq.Workplane('XY').box(2.67,1.02,1.52,centered=(True,True,False))
# 0.25 mm stock shown in the manufacturer catalog; nominal rectangular loop.
opening=cq.Workplane('XY').box(2.17,1.10,1.27,centered=(True,True,False))
shape=outer.cut(opening)
cq.exporters.export(shape,str(p))
record=K/'3dmodels/provenance.json';data=json.loads(record.read_text());data['models']['vendor/'+p.name]={'provider':'Drawing-derived nominal envelope','source':'https://www.keyelco.com/product-pdf.cfm?p=1353','license':'Project-authored dimensional envelope; manufacturer drawing remains Keystone property','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'dimensionsMm':[2.67,1.02,1.52],'limitations':'Nominal rectangular loop with 0.25 mm walls, not detailed formed-metal CAD; confirm purchased part and clip clearance'};record.write_text(json.dumps(data,indent=2)+'\n')
