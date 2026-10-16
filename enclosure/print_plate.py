"""Create a vendor-neutral 3MF with fifteen independently placed print objects."""
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
import trimesh
import numpy as np

root=Path(__file__).resolve().parents[1];out=root/'dist/enclosure'
placements=[('base',128,62),('bezel',128,152),('camera-tray',30,222),
            ('camera-clamp',70,222),('service-cover',110,222),
            ('retainer-left',155,222),('retainer-right',190,222)]
placements += [('button',211+13*(i%3),207+13*(i//3)) for i in range(8)]
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',ns)
def e(parent,tag,**attrs):return ET.SubElement(parent,f'{{{ns}}}{tag}',attrs)
model=ET.Element(f'{{{ns}}}model',{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
resources=e(model,'resources');build=e(model,'build')
bounds=[]
for index,(name,x,y) in enumerate(placements,1):
    mesh=trimesh.load(out/f'{name}.stl',force='mesh')
    b=mesh.bounds+np.array([x,y,0]);assert np.all(b[0]>=0) and np.all(b[1]<[252,252,250]);assert abs(b[0,2])<.001
    assert b[0,0]>18 or b[0,1]>28,'P1S exclusion overlap'
    for other in bounds:
        assert b[0,0]>other[1,0]+2 or other[0,0]>b[1,0]+2 or b[0,1]>other[1,1]+2 or other[0,1]>b[1,1]+2,'Print objects too close'
    bounds.append(b)
    obj=e(resources,'object',id=str(index),type='model',name=f'{name}-{index}')
    geometry=e(obj,'mesh');vertices=e(geometry,'vertices');triangles=e(geometry,'triangles')
    for vx,vy,vz in mesh.vertices:e(vertices,'vertex',x=f'{vx:.6f}',y=f'{vy:.6f}',z=f'{vz:.6f}')
    for a,b,c in mesh.faces:e(triangles,'triangle',v1=str(a),v2=str(b),v3=str(c))
    e(build,'item',objectid=str(index),transform=f'1 0 0 0 1 0 0 0 1 {x} {y} 0')
with zipfile.ZipFile(out/'print-plate.3mf','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
    z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
print('Validated fifteen independent objects; P1S exclusion clear; 2 mm minimum bounding-box spacing')
