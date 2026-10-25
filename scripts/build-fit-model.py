"""Export a case-aligned CAD fit kit; no manufacturing geometry is changed."""
from pathlib import Path
import hashlib
import json
import runpy
import zipfile
import cadquery as cq
import trimesh

root = Path(__file__).resolve().parents[1]
out = root/'dist/fit'; out.mkdir(parents=True, exist_ok=True)
runpy.run_path(str(root/'scripts/audit-assembly-stack.py'))
runpy.run_path(str(root/'enclosure/color_hardware.py'))
parts = runpy.run_path(str(root/'enclosure/check_assembly.py'))['parts']
hardware = trimesh.load(root/'.tools/enclosure/hardware-groups.glb')
names = {'Carrier and SMT parts':'carrier_and_smt', 'J701':'display_module',
 'J701_1':'lcd_female_socket','J701_2':'lcd_male_header','U202':'luckfox_module',
 'U202_1':'luckfox_female_a','U202_2':'luckfox_female_b',
 'U202_3':'luckfox_male_a','U202_4':'luckfox_male_b',
 **{f'H70{i}':f'display_spacer_{i}' for i in range(1,5)}}
assert set(hardware.geometry)==set(names)
meshes={names[n]:m.copy() for n,m in hardware.geometry.items()}
# GLB uses metres by specification. STEP and STL use millimetres.
def glb(items, filename):
    scaled={}
    for name,mesh in items.items():
        m=mesh.copy();m.apply_scale(.001);scaled[name]=m
    target=out/filename
    trimesh.Scene(scaled).export(target)
    restored=trimesh.load(target)
    assert set(restored.geometry)==set(scaled), 'GLB lost selectable groups'
    assert abs(restored.bounds[1,2]-max(m.bounds[1,2] for m in scaled.values()))<1e-6
    assert restored.extents.max()<.3, 'GLB must be metres, not millimetres'
glb(meshes,'shieldsigner-pcb-fit.glb')
case={}
for name,m in parts.items():
    mesh=m.copy();mesh.visual.vertex_colors=[160,170,180,255]
    key='case_'+name.replace(' ','_');case[key]=mesh
    folder=out/'case';folder.mkdir(exist_ok=True)
    mesh.export(folder/f'{key}.stl')
glb({**meshes,**case},'shieldsigner-case-fit.glb')
source=root/'dist/lcd-module-2.8/shieldsigner-modular-assembly.step'
native_manifest=json.loads((root/'assets/modular-downloads.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==next(a['sha256'] for a in native_manifest['assets'] if a['name']==source.name)
print('Importing complete native STEP for case-frame translation…',flush=True)
shape=cq.importers.importStep(str(source)).val().translate((-128,89.579,-1.595))
cq.exporters.export(shape,str(out/'shieldsigner-pcb-fit.step'))
# Round-trip units/extent check catches dropped geometry or translation errors.
bounds=shape.BoundingBox()
assert abs(bounds.zlen-35.52)<.05,(bounds.zmin,bounds.zmax)
readback=cq.importers.importStep(str(out/'shieldsigner-pcb-fit.step')).val().BoundingBox()
assert abs(readback.zlen-bounds.zlen)<.001
readme=root/'variants/lcd-module-2.8/FIT-MODEL.md'
with zipfile.ZipFile(out/'shieldsigner-fit-kit.zip','w',zipfile.ZIP_DEFLATED) as bundle:
    bundle.write(readme,'README.md')
    bundle.write(root/'variants/lcd-module-2.8/assembly-fit-check.json','assembly-fit-check.json')
    for path in sorted(out.glob('*.step')):bundle.write(path,path.name)
    for path in sorted(out.glob('*.glb')):bundle.write(path,path.name)
    for path in sorted((out/'case').glob('*.stl')):bundle.write(path,'case/'+path.name)
manifest={'version':'0.0.1-dev','boardSha256':json.loads((root/'assets/modular-downloads.json').read_text())['boardSha256'],
 'scadSha256':hashlib.sha256((root/'enclosure/case.scad').read_bytes()).hexdigest(),
 'sourceStepSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'assets':[]}
for path in sorted(out.iterdir()):
    if path.is_file():manifest['assets'].append({'name':path.name,'size':path.stat().st_size,
      'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
      'url':'https://github.com/lightningspore/shieldsigner-dev/releases/download/fit-preview-0.0.1-dev/'+path.name})
(root/'assets/fit-downloads.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Fit kit exported; STEP round-trip height:',readback.zlen,flush=True)
