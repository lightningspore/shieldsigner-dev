"""Boolean checks for printed parts in their assembly frame.

Run after build.py with trimesh and manifold3d available. Hardware collision
checks are separate: passing this script only proves printed-part clearances.
"""
from pathlib import Path
import json
import numpy as np
import trimesh

root = Path(__file__).resolve().parents[1]
out = root / "dist/enclosure"
parts = {}
def add(name, filename, offset, flip=False):
    mesh = trimesh.load(out / f"{filename}.stl", force="mesh")
    if flip:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1,0,0]))
    mesh.apply_translation(offset)
    parts[name] = mesh

add("base", "base", [0,0,-23.4])
add("bezel", "bezel", [0,0,21], True)
add("left retainer", "retainer-left", [-59.53,0,15.15])
add("right retainer", "retainer-right", [62,0,15.15])
add("service cover", "service-cover", [-34,22,-25.4])
add("camera tray", "camera-tray", [7,17,-13.8])
add("camera clamp", "camera-clamp", [7,17,-11.4])
buttons = [[-70.02,0],[-59.53,10.494],[-59.53,0],[-59.53,-10.426],
           [-49.08,0],[58.88,10.284],[58.88,.014],[58.88,-10.316]]
for i,(x,y) in enumerate(buttons):
    add(f"button {i+1}", "button", [x,y,22], True)
checks = []
for i,(name,a) in enumerate(parts.items()):
    for other,b in list(parts.items())[i+1:]:
        if np.any(a.bounds[1] <= b.bounds[0]) or np.any(b.bounds[1] <= a.bounds[0]):
            continue
        intersection = trimesh.boolean.intersection([a,b],engine="manifold")
        volume = abs(intersection.volume) if len(intersection.faces) else 0
        checks.append({"parts":[name,other],"intersection_mm3":volume})
        assert volume < .001, (name,other,volume)
scene = trimesh.Scene(parts)
scene.export(out / "case-assembly.glb")
(out / "printed-assembly-check.json").write_text(json.dumps(checks,indent=2)+"\n")
print(f"{len(parts)} assembled printed parts; {len(checks)} overlapping-bound pairs have no solid interference")
