"""Reserve card/USB insertion space and the assumed low-profile camera envelope."""
from pathlib import Path
import json
import runpy
import numpy as np
import trimesh

root=Path(__file__).resolve().parents[1]
parts=runpy.run_path(str(root/'enclosure/check_assembly.py'))['parts']
parts.update(runpy.run_path(str(root/'enclosure/fasteners.py'))['assembly']())
def box(size,centre):
    m=trimesh.creation.box(size);m.apply_translation(centre);return m
spaces={
    'card insertion clearance':box([55,65.53,4],[11.42,-67.235,-3.5]),
    'USB-C plug housing clearance':box([14,22,7.5],[-31.49,-44.6,-3]),
    'Luckfox USB plug housing clearance':box([14,30,8],[-33.86,32.94,-15.35]),
    'Luckfox microSD insertion clearance':box([14,30,4.5],[-34.21,31.53,-11.25]),
    'assumed camera PCB':box([26,26,1.2],[7,17,-12]),
    'assumed camera rear connector':box([16,4,2],[7,28,-10.4])}
lens=trimesh.creation.cylinder(radius=7,height=10,sections=96)
lens.apply_translation([7,17,-17.6]);spaces['assumed camera lens']=lens
spaces.update(runpy.run_path(str(root/'enclosure/ribbon_clearance.py'))['envelopes']())
findings=[]
for label,a in spaces.items():
    for name,b in parts.items():
        if np.any(a.bounds[1]<=b.bounds[0]) or np.any(b.bounds[1]<=a.bounds[0]):continue
        intersection=trimesh.boolean.intersection([a,b],engine='manifold')
        volume=abs(intersection.volume) if len(intersection.faces) else 0
        if volume>.001:findings.append([label,name,volume])
report={'checked':list(spaces),'findings':findings,'camera_status':'Assumed maximum envelope: verify purchased camera dimensions before printing'}
(root/'dist/enclosure/access-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert not findings
