"""Drawing-derived nominal envelopes for the dual-source switch and USB connector.
Use mise exec -- uv run --python 3.11 --with cadquery==2.8.0 python scripts/model-shared-parts.py.
Not manufacturer CAD: omits internal details, contacts and tolerances.
"""
from pathlib import Path
import hashlib,json
import cadquery as cq
R=Path(__file__).resolve().parents[1];K=R/'variants/lcd-module-2.8/kicad';D=K/'3dmodels/local';D.mkdir(exist_ok=True)
def box(w,d,h,x=0,y=0,z=0):return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).translate((x,y,z)).val()
switch=cq.Compound.makeCompound([box(6.1,3.7,1.9),box(2.7,1.3,.6,z=1.9),box(.7,.6,.15,x=-3.65),box(.7,.6,.15,x=3.65)])
# KiCad STEP +Y is opposite footprint Y. Shell slots remain y=-2.7,+1.1.
# Face is at footprint y=3.7. Shell is 6.8 deep and 3.16 high.
shell=box(8.94,6.8,3.16,y=-.3).cut(box(8.34,6.9,2.56,y=-.4,z=.3))
usb=cq.Compound.makeCompound([shell,*[box(.4,.8,1,x=x,y=y,z=-1) for x in [-4.32,4.32] for y in [-1.1,2.7]]])
f=K/'3dmodels/provenance.json';d=json.loads(f.read_text())
for name,shape,source in [('CK-PTS636-SK25-envelope.step',switch,'reference/pdfs/CK-PTS636.pdf, pages 3–4, 2.5 mm G leads'),('GCT-USB4125-envelope.step',usb,'reference/pdfs/GCT-USB4125.pdf, rev A6, default 1.0 mm stakes')]:
 p=D/name;cq.exporters.export(shape,str(p));b=p.read_bytes();d['models']['local/'+name]={'provider':'ShieldSigner drawing-derived nominal envelope','source':source,'license':'Repository license; original drawing retained separately','sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'limitations':'Envelope only; no manufacturer CAD or physical fit qualification; no detailed contacts'}
f.write_text(json.dumps(d,indent=2)+'\n')
