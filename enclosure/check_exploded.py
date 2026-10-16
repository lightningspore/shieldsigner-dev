"""Check exploded printed parts against one another and native group bounds."""
from pathlib import Path
import runpy
import json
import numpy as np
import trimesh

root=Path(__file__).resolve().parents[1]
state=runpy.run_path(str(root/'enclosure/preview_assembly.py'))
exploded=state['exploded'];hardware_names=state['hardware_names']
printed_names=['base','bezel','left retainer','right retainer','camera tray','camera clamp','service cover',*[f'button {i}' for i in range(1,9)]]
findings=[]
for name in printed_names:
    a=exploded[name]
    for other,b in exploded.items():
        if name==other:continue
        if np.any(a.bounds[1]<=b.bounds[0]) or np.any(b.bounds[1]<=a.bounds[0]):continue
        if other in hardware_names:
            box=trimesh.creation.box(b.extents);box.apply_translation(b.bounds.mean(axis=0));b=box
        intersection=trimesh.boolean.intersection([a,b],engine='manifold')
        volume=abs(intersection.volume) if len(intersection.faces) else 0
        if volume>.005:findings.append([name,other,volume])
report={'printed_parts':len(printed_names),'native_groups':len(hardware_names),
        'method':'Exact printed/fastener meshes; conservative native group bounding boxes','findings':findings}
(root/'dist/enclosure/exploded-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert not findings
