"""Reserved routing corridor, not a fabrication model of a particular FPC."""
import numpy as np
import trimesh

def envelopes():
    nodes=np.array([[-33.82,-9.95,-16],[-33.82,-14,-16],
                    [7,-14,-16],[7,-3,-9.2],[7,23,-9.2],[7,26,-10.4]])
    parts={}
    for i,(a,b) in enumerate(zip(nodes[:-1],nodes[1:])):
        tangent=(b-a)/np.linalg.norm(b-a)
        width=np.cross([0,0,1],tangent);width/=np.linalg.norm(width)
        normal=np.cross(tangent,width)
        transform=np.eye(4);transform[:3,:3]=np.column_stack([width,normal,tangent]);transform[:3,3]=(a+b)/2
        mesh=trimesh.creation.box([12,.4,np.linalg.norm(b-a)],transform=transform)
        mesh.visual.vertex_colors=[215,120,195,120]
        parts[f'Ribbon routing clearance {i+1}']=mesh
    return parts
