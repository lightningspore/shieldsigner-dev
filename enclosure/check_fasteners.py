"""Allow explicit threaded engagement volumes, then reject all other collisions."""
from pathlib import Path
import json
import runpy
import numpy as np
import trimesh

root=Path(__file__).resolve().parents[1]
context=runpy.run_path(str(root/'enclosure/check_hardware.py'))
parts=context['parts'];hardware=context['hardware']
fasteners=runpy.run_path(str(root/'enclosure/fasteners.py'))
screws=fasteners['assembly']();cylinder=fasteners['cylinder']
findings=[];engagements=[]
for name,screw in screws.items():
    x,y=screw.bounds.mean(axis=0)[:2]
    if name.startswith('Closure'):z0,z1,d=-9,.4,2.5
    elif name.startswith('Retainer'):z0,z1,d=16.85,20.2,2
    elif name.startswith('Camera'):z0,z1,d=-19.8,-13.8,2
    elif name.startswith('Service'):z0,z1,d=-23.4,-19.4,2
    elif name.startswith('LCD top'):z0,z1,d=9.6,12,2.5
    elif name.startswith('Carrier underside'):z0,z1,d=0,2.4,2.5
    elif name.startswith('Base'):z0,z1,d=0,6.6,2.5
    else:raise AssertionError(name)
    # Only the shaft's intentional thread engagement is exempted. Heads and
    # all geometry outside this small cylinder remain in the collision test.
    free=trimesh.boolean.difference([screw,cylinder(d+.002,z0-.001,z1+.001,x,y)],engine='manifold')
    engagements.append({'screw':name,'nominal_thread_zone_mm':[z0,z1]})
    for other,b in [*parts.items(),*[(f'hardware {i}',m) for i,m in enumerate(hardware)]]:
        if np.any(free.bounds[1]<=b.bounds[0]) or np.any(b.bounds[1]<=free.bounds[0]):continue
        common=trimesh.boolean.intersection([free,b],engine='manifold')
        volume=abs(common.volume) if len(common.faces) else 0
        if volume>.005:findings.append([name,other,volume])
report={'screws':len(screws),'thread_engagements':engagements,'findings':findings}
(root/'dist/enclosure/fastener-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert not findings,'Fastener interference'
