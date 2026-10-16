"""Check nominal button motion with only the switch actuator contact exempted."""
from pathlib import Path
import json
import runpy
import numpy as np
import trimesh

root=Path(__file__).resolve().parents[1]
c=runpy.run_path(str(root/'enclosure/check_hardware.py'))
parts=c['parts'];hardware=c['hardware'];findings=[]
for name,rest in parts.items():
    if not name.startswith('button'):continue
    x,y=rest.bounds.mean(axis=0)[:2]
    actuator=trimesh.creation.cylinder(radius=1.001,height=.252,sections=48)
    actuator.apply_translation([x,y,2.375])
    for stroke in np.linspace(0,.35,8):
        button=rest.copy();button.apply_translation([0,0,-stroke])
        free=trimesh.boolean.difference([button,actuator],engine='manifold')
        for other,b in [*[(k,v) for k,v in parts.items() if k!=name],*[(f'hardware {i}',m) for i,m in enumerate(hardware)]]:
            if np.any(free.bounds[1]<=b.bounds[0]) or np.any(b.bounds[1]<=free.bounds[0]):continue
            common=trimesh.boolean.intersection([free,b],engine='manifold')
            volume=abs(common.volume) if len(common.faces) else 0
            if volume>.005:findings.append([name,float(stroke),other,volume])
report={'buttons':8,'sampled_strokes_mm':np.linspace(0,.35,8).tolist(),
        'nominal_switch_travel_mm':.25,'actuator_contact_exception':'2 mm diameter, Z=2.249..2.501 mm only','findings':findings}
(root/'dist/enclosure/button-motion-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert not findings
