"""Bake native KiCad GLB colors/transforms into one efficient preview mesh."""
from pathlib import Path
import numpy as np
import trimesh
import re
import json

root=Path(__file__).resolve().parents[1]
scene=trimesh.load(root/'dist/lcd-module-2.8/shieldsigner-modular-assembly.glb')
frame=np.array([[1000,0,0,-128],[0,0,-1000,89.579],[0,1000,0,-1.595],[0,0,0,1]])
meshes=[];groups={}
for node in scene.graph.nodes_geometry:
    transform,geometry=scene.graph[node]
    mesh=scene.geometry[geometry].copy()
    mesh.apply_transform(frame@transform)
    material=getattr(mesh.visual,'material',None)
    color=getattr(material,'baseColorFactor',None)
    if color is None:color=[110,120,130,255]
    mesh.visual=trimesh.visual.ColorVisuals(mesh=mesh,vertex_colors=np.tile(color,(len(mesh.vertices),1)))
    meshes.append(mesh)
    parent=node;group='Carrier and SMT parts'
    while parent is not None:
        if re.fullmatch(r'(?:J701|U202|H70[1-4])(?:_\d+)?',str(parent)):
            group=str(parent);break
        parent=scene.graph.transforms.parents.get(parent)
    groups.setdefault(group,[]).append(mesh)
combined=trimesh.util.concatenate(meshes)
combined.export(root/'.tools/enclosure/hardware-colored.glb')
grouped={name:trimesh.util.concatenate(items) for name,items in groups.items()}
trimesh.Scene(grouped).export(root/'.tools/enclosure/hardware-groups.glb')
metadata={name:mesh.bounds.tolist() for name,mesh in grouped.items()}
(root/'.tools/enclosure/hardware-groups.json').write_text(json.dumps(metadata,indent=2)+'\n')
print(json.dumps(metadata,indent=2))
print('Native colored hardware baked:',len(meshes),'source nodes;',len(combined.faces),'triangles;',combined.bounds)
