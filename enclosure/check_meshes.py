"""Check exported print orientations; this does not certify component fit.

mise exec uv -- uv run --with trimesh --with networkx enclosure/check_meshes.py
"""
import json
from pathlib import Path
import trimesh
import numpy as np

root = Path(__file__).resolve().parents[1]
results = {}
for name in ("base", "bezel", "button", "retainer-left", "retainer-right", "camera-tray", "camera-clamp", "service-cover", "button-fit-coupon"):
    mesh = trimesh.load(root / "dist/enclosure" / f"{name}.stl", force="mesh")
    assert mesh.is_watertight, f"{name}: open mesh"
    assert mesh.is_winding_consistent, f"{name}: inconsistent winding"
    assert len(mesh.split()) == 1, f"{name}: disconnected solids"
    assert abs(mesh.bounds[0, 2]) < 0.001, f"{name}: bottom is not Z=0"
    assert all(mesh.extents[:2] < 248), f"{name}: exceeds 256 mm bed with margins"
    assert mesh.volume > 0
    steep = (mesh.face_normals[:,2] < -np.sin(np.deg2rad(45.2))) & (mesh.triangles_center[:,2] > .21)
    unsupported_area = float(mesh.area_faces[steep].sum())
    assert unsupported_area < .01, f"{name}: downward faces steeper than 45 degrees above first layer"
    results[name] = {"bounds": mesh.bounds.tolist(), "volume_mm3": mesh.volume,
                     "watertight": True, "connected_bodies": 1,
                     "steep_downward_area_above_first_layer_mm2":unsupported_area}
target = root / "dist/enclosure/mesh-check.json"
target.write_text(json.dumps(results, indent=2) + "\n")
print(target.read_text())
