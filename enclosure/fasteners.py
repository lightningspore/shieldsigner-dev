"""Nominal screw envelopes and engagement arithmetic (threads are not modeled)."""
import trimesh
import numpy as np

def cylinder(d,z0,z1,x,y):
    mesh=trimesh.creation.cylinder(radius=d/2,height=z1-z0,sections=48)
    mesh.apply_translation([x,y,(z0+z1)/2]);return mesh

def screw(name,x,y,seat,length,diameter,direction,countersunk=False):
    tip=seat+direction*length
    if countersunk:
        head_height=diameter/2
        inner=seat+direction*head_height
        head=trimesh.creation.revolve([[0,0],[diameter,0],[diameter/2,head_height],[0,head_height]],sections=48)
        if direction<0:head.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[1,0,0]))
        head.apply_translation([x,y,seat])
        shaft=cylinder(diameter,min(inner,tip),max(inner,tip),x,y)
    else:
        outer=seat-direction*1.5
        head=cylinder(diameter*1.9,min(seat,outer),max(seat,outer),x,y)
        shaft=cylinder(diameter,min(seat,tip),max(seat,tip),x,y)
    mesh=trimesh.util.concatenate([head,shaft]);mesh.visual.vertex_colors=[100,105,110,255]
    return name,mesh

def assembly():
    parts={}
    for i,(x,y) in enumerate([(-35.25,23.9),(47.25,23.9),(-35.25,-23.9),(47.25,-23.9)]):
        parts.update([screw(f'LCD top M2.5x4 {i+1}',x,y,13.6,4,2.5,-1)])
        if i==0:parts.update([screw('Carrier underside M2.5x4',x,y,-1.6,4,2.5,1)])
        else:parts.update([screw(f'Base M2.5x30 {i}',x,y,-23.4,30,2.5,1,True)])
    for x in [-84.5,84.5]:parts.update([screw(f'Closure M2.5x30 {x}',x,0,21,30,2.5,-1,True)])
    for i,(x,y) in enumerate([(-67.2,7.7),(-67.2,-7.7),(-51.8,7.7),(66.5,7),(66.5,-7)]):
        parts.update([screw(f'Retainer M2x5 {i+1}',x,y,15.2,5,2,1)])
    for x in [-14.5,14.5]:
        for y in [-14.5,14.5]:parts.update([screw(f'Camera M2x10 {x},{y}',7+x,17+y,-9.8,10,2,-1)])
    for x in [-14,14]:
        for y in [-14,14]:parts.update([screw(f'Service M2x6 {x},{y}',-34+x,22+y,-25.4,6,2,1,True)])
    # 12 mm spacers: lower/upper screw engagement leaves 3 mm between tips.
    assert abs((12-(6.6+2.4))-3)<1e-6
    assert 21-30>-11.6 # Closure tip remains inside pilot depth.
    assert 15.2+5<21 # Retainer screws do not puncture front face.
    assert -9.8-10>-21 # Camera screws do not puncture rear floor.
    return parts
