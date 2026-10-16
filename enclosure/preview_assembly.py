"""Export assembled/exploded GLB previews with explicit assumed camera envelope."""
from pathlib import Path
import runpy
import trimesh

root=Path(__file__).resolve().parents[1]
parts=runpy.run_path(str(root/'enclosure/check_assembly.py'))['parts']
hardware=trimesh.load(root/'.tools/enclosure/hardware-groups.glb')
names={'Carrier and SMT parts':'Carrier and SMT parts','J701':'LCD module',
       'J701_1':'Carrier LCD socket','J701_2':'LCD male header',
       'U202':'Luckfox Mini','U202_1':'Carrier Luckfox socket A',
       'U202_2':'Carrier Luckfox socket B','U202_3':'Luckfox male header A',
       'U202_4':'Luckfox male header B',**{f'H70{i}':f'Display spacer H70{i}' for i in range(1,5)}}
assert set(hardware.geometry)==set(names),'Native model group labels changed; review exploded placements'
hardware_names=set(names.values())
parts.update({names[name]:mesh for name,mesh in hardware.geometry.items()})
camera=trimesh.creation.box([26,26,1.2]);camera.apply_translation([7,17,-12])
lens=trimesh.creation.cylinder(radius=7,height=10,sections=64);lens.apply_translation([7,17,-17.6])
connector=trimesh.creation.box([16,4,2]);connector.apply_translation([7,28,-10.4])
parts['Camera envelope (assumed)']=trimesh.util.concatenate([camera,lens,connector])
parts.update(runpy.run_path(str(root/'enclosure/fasteners.py'))['assembly']())
parts.update(runpy.run_path(str(root/'enclosure/ribbon_clearance.py'))['envelopes']())
for name,mesh in parts.items():
    if name.startswith('button'):mesh.visual.vertex_colors=[245,150,30,255]
    elif name.startswith('camera') or name.startswith('Camera'):mesh.visual.vertex_colors=[140,90,160,255]
    elif name not in hardware_names and 'M2' not in name and not name.startswith('Ribbon'):mesh.visual.vertex_colors=[160,170,180,255]
trimesh.Scene(parts).export(root/'dist/enclosure/assembled.glb')
exploded={}
for name,mesh in parts.items():
    m=mesh.copy()
    if name.startswith('LCD top'):dz=35
    elif name in ['LCD module','LCD male header']:dz=20
    elif name in ['Luckfox Mini','Luckfox male header A','Luckfox male header B']:dz=-15
    elif name.startswith('Base M2') or name.startswith('Service M2'):dz=-95
    elif name.startswith('Closure M2'):dz=110
    elif name.startswith('Retainer M2'):dz=35
    elif name.startswith('Camera M2'):dz=-20
    elif name=='base':dz=-70
    elif name=='service cover':dz=-95
    elif name=='bezel':dz=90
    elif name.startswith('button'):dz=60
    elif 'retainer' in name:dz=35
    elif name=='camera tray':dz=-40
    elif name=='camera clamp':dz=-20
    elif name.startswith('Camera'):dz=-30
    else:dz=0
    m.apply_translation([0,0,dz]);exploded[name]=m
trimesh.Scene(exploded).export(root/'dist/enclosure/exploded.glb')
print('Exported assembled.glb and exploded.glb; camera is an assumed envelope, not manufacturer CAD')
