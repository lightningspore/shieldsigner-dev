"""Tessellate native KiCad assembly for enclosure visualization/collision checks.

Requires cadquery==2.8.0 and trimesh. Native STEP coordinates are in mm.
The 1.595 mm component reference is calibrated against the native LCD model:
its 19.295 mm exported maximum minus the documented 17.7 mm front height.
SW503's exported 1.595 mm mounting plane independently agrees. Never align to
the board-only dielectric top (1.51 mm) without checking component placement.
"""
from pathlib import Path
import hashlib
import json
import cadquery as cq
import trimesh

root = Path(__file__).resolve().parents[1]
source = root / "dist/lcd-module-2.8/shieldsigner-modular-assembly.step"
target = root / ".tools/enclosure/hardware.stl"
target.parent.mkdir(parents=True, exist_ok=True)
print("Reading native assembly STEP", flush=True)
shape = cq.importers.importStep(str(source)).val().translate((-128,89.579,-1.595))
vertices, faces = shape.tessellate(.08)
mesh = trimesh.Trimesh(vertices=[v.toTuple() for v in vertices], faces=faces)
mesh.export(target)
board=root/'variants/lcd-module-2.8/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
target.with_suffix('.json').write_text(json.dumps({
    'step_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'board_sha256':hashlib.sha256(board.read_bytes()).hexdigest(),
    'mesh_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
    'translation_mm':[-128,89.579,-1.595]},indent=2)+'\n')
print({"bounds":mesh.bounds.tolist(), "watertight":mesh.is_watertight,
       "triangles":len(mesh.faces), "output":str(target)}, flush=True)
