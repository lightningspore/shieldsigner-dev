"""Make a watertight print-only assembly mockup from the case-aligned native mesh.

Retains carrier/module geometry, replaces upstream open Luckfox surfaces with a
conservative solid envelope, and adds thin vertical ties for floating details.
Not an electrically accurate model or a replacement manufacturing output.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import trimesh

root=Path(__file__).resolve().parents[1]
out=root/'dist/fit';out.mkdir(parents=True,exist_ok=True)
manifest=json.loads((root/'assets/modular-downloads.json').read_text())
source=root/'dist/lcd-module-2.8/shieldsigner-modular-assembly.glb'
assert hashlib.sha256(source.read_bytes()).hexdigest()==next(a['sha256'] for a in manifest['assets'] if a['name']==source.name)
# Refresh the colored group meshes directly from the checksum-verified assembly.
import runpy
runpy.run_path(str(root/'enclosure/color_hardware.py'))
scene=trimesh.load(root/'.tools/enclosure/hardware-groups.glb')
solids=[];carrier=[];ties=[]
for name,mesh in scene.geometry.items():
    if name=='U202':
        # All outside dimensions retained; small component spaces are filled in.
        proxy=trimesh.creation.box(extents=mesh.extents)
        proxy.apply_translation(mesh.bounds.mean(axis=0));solids.append(proxy)
        continue
    m=mesh.copy();m.merge_vertices()
    for part in m.split(only_watertight=False):
        assert part.is_watertight, f'Unexpected open mesh in {name}'
        part.fix_normals(multibody=False)
        assert part.is_volume
        solids.append(part)
        if name=='Carrier and SMT parts':carrier.append(part)
board=max(carrier,key=lambda p:p.volume)
assert board.extents[0]>150 and board.extents[1]>65 and board.extents[2]<2
board.export(out/'shieldsigner-bare-pcb-mm.stl')
assembly=trimesh.boolean.union(solids,engine='manifold')
# Fill enclosed connector cavities and join separate outer shells. Through holes
# in the carrier remain open; artificial ties can occupy a mating pin hole.
outer=[p for p in assembly.split(only_watertight=False) if p.volume>0]
for part in outer:part.fix_normals(multibody=False)
assembly=trimesh.boolean.union(outer,engine='manifold')
for attempt in range(3):
    islands=[p for p in assembly.split(only_watertight=False) if p.volume>0]
    if len(islands)==1:break
    main=max(islands,key=lambda p:p.extents[0])
    additions=[]
    for part in islands:
        if part is main:continue
        # Anchor in an actual upper surface, rather than a hollow bbox centre.
        index=int(np.argmax(part.triangles_center[:,2]))
        anchor=part.triangles_center[index]-part.face_normals[index]*.05
        target=float(board.bounds.mean(axis=0)[2])
        tie=trimesh.creation.box(extents=[2,2,abs(anchor[2]-target)+.08])
        tie.apply_translation([anchor[0],anchor[1],(anchor[2]+target)/2])
        additions.append(tie);ties.append(tie)
    assembly=trimesh.boolean.union([assembly,*additions],engine='manifold')
assert len([p for p in assembly.split(only_watertight=False) if p.volume>0])==1,'Mockup has disconnected outer bodies'
assert assembly.is_watertight and assembly.is_volume and assembly.is_winding_consistent
expected=scene.bounds
assert np.max(np.abs(assembly.bounds-expected))<.01,(assembly.bounds,expected)
path=out/'shieldsigner-printable-fit-mm.stl'
assembly.export(path)
readback=trimesh.load(path,force='mesh')
assert readback.is_watertight and readback.is_volume
assert len([p for p in readback.split() if p.volume>0])==1
report={'boardSha256':manifest['boardSha256'],'sourceGlbSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'units':'mm','coordinateFrame':'Same case-aligned frame as shieldsigner-pcb-fit.step; front +Z',
 'boundsMm':assembly.bounds.tolist(),'sizeMm':assembly.extents.tolist(),
 'watertight':bool(readback.is_watertight),'connectedBodies':1,'triangles':len(readback.faces),
 'verticalPrintTies':len(ties),'simplification':'Luckfox replaced by its full bounding box; 2 mm ties join floating bodies to carrier; enclosed socket cavities filled. Fit mockup only; filled spaces are not available for case features.',
 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
(out/'printable-fit-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
