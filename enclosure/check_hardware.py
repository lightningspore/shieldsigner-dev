"""Check printed parts against native closed solids and conservative open-face bounds.

The Luckfox source includes open/doubled surface details. Its entire bounding
box is reserved rather than discarding those details from the fit assessment.
"""
from pathlib import Path
import json
import hashlib
import runpy
import numpy as np
import trimesh

root=Path(__file__).resolve().parents[1]
metadata=json.loads((root/'.tools/enclosure/hardware.json').read_text())
for key,path in [('step_sha256','dist/lcd-module-2.8/shieldsigner-modular-assembly.step'),
                 ('board_sha256','variants/lcd-module-2.8/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'),
                 ('mesh_sha256','.tools/enclosure/hardware.stl')]:
    assert hashlib.sha256((root/path).read_bytes()).hexdigest()==metadata[key],'Stale hardware mesh; regenerate before fit checks'
parts=runpy.run_path(str(root/'enclosure/check_assembly.py'))['parts']
mesh=trimesh.load(root/'.tools/enclosure/hardware.stl',force='mesh')
mesh.update_faces(mesh.unique_faces())
mesh.remove_unreferenced_vertices()
components=mesh.split(only_watertight=False)
for m in components:
    if m.is_watertight:m.fix_normals(multibody=False)
closed=[m for m in components if m.is_volume]
open_parts=[m for m in components if not m.is_volume]
luckfox_bounds=np.array([[-44.4,-11.25,-17.85],[-23.3,18,1.45]])
surface_proxies=[]
for m in open_parts:
    if np.all(m.bounds[0]>=luckfox_bounds[0]) and np.all(m.bounds[1]<=luckfox_bounds[1]):continue
    # Other supplier surfaces are reserved independently, never silently dropped.
    box=trimesh.creation.box(extents=np.maximum(m.extents,.01))
    box.apply_translation(m.bounds.mean(axis=0))
    surface_proxies.append(box)
proxy=trimesh.creation.box(extents=luckfox_bounds[1]-luckfox_bounds[0])
proxy.apply_translation(luckfox_bounds.mean(axis=0))
hardware=[*closed,proxy,*surface_proxies]
findings=[]
for name,a in parts.items():
    for i,b in enumerate(hardware):
        if np.any(a.bounds[1]<=b.bounds[0]) or np.any(b.bounds[1]<=a.bounds[0]):continue
        intersection=trimesh.boolean.intersection([a,b],engine='manifold')
        volume=abs(intersection.volume) if len(intersection.faces) else 0
        if volume>.001:findings.append({'part':name,'hardware_index':i,'intersection_mm3':volume,'hardware_bounds':b.bounds.tolist()})
report={'closed_native_components':len(closed),'open_surface_components_reserved_by_envelope':len(open_parts),'individual_surface_proxies_outside_luckfox':len(surface_proxies),'findings':findings}
(root/'dist/enclosure/hardware-fit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert not findings,'Hardware interference requires geometry revision'
