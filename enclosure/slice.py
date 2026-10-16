"""Slice with fully resolved official P1S profiles; reject CLI fallback settings."""
from pathlib import Path
import json
import subprocess
import zipfile
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1]
profiles=Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')
cache=root/'.tools/enclosure/slicer';cache.mkdir(parents=True,exist_ok=True)
def resolve(path,seen=()):
    data=json.loads(path.read_text());parent=data.get('inherits');base={}
    if parent:
        assert parent not in seen,'Profile inheritance cycle'
        matches=list(profiles.rglob(parent+'.json'));assert len(matches)==1,(parent,matches)
        base=resolve(matches[0],(*seen,parent))
    base.update(data);base.pop('inherits',None);base['instantiation']='true'
    return base
sources={'process':root/'enclosure/print-profile.json',
         'machine':profiles/'machine/Bambu Lab P1S 0.4 nozzle.json',
         'filament':profiles/'filament/Bambu PLA Basic @BBL P1S 0.4 nozzle.json'}
for name,path in sources.items():(cache/f'{name}.json').write_text(json.dumps(resolve(path),indent=2)+'\n')
target=root/'dist/enclosure/print-plate-P1S.3mf'
command=['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio',
         '--load-settings',f'{cache}/process.json;{cache}/machine.json',
         '--load-filaments',str(cache/'filament.json'),'--arrange','1','--orient','0',
         '--slice','0','--export-3mf',str(target),str(root/'dist/enclosure/print-plate.3mf')]
with (cache/'slice.log').open('w') as log:subprocess.run(command,cwd=cache,stdout=log,stderr=subprocess.STDOUT,check=True)
with zipfile.ZipFile(target) as archive:
    settings=json.loads(archive.read('Metadata/project_settings.config'))
    assert settings['printer_model']=='Bambu Lab P1S'
    assert settings['printable_area']==['0x0','256x0','256x256','0x256'],settings['printable_area']
    assert settings['nozzle_diameter']==['0.4']
    assert settings['enable_support']=='0'
    info=ET.fromstring(archive.read('Metadata/slice_info.config'))
    plates=[];count=0
    for plate in info.findall('plate'):
        metadata={m.get('key'):m.get('value') for m in plate.findall('metadata')}
        assert metadata['outside']=='false' and metadata['support_used']=='false'
        objects=plate.findall('object');assert all(o.get('skipped')=='false' for o in objects)
        count+=len(objects)
        gcode=archive.read(f"Metadata/plate_{metadata['index']}.gcode")
        assert len(gcode)>10000
        plates.append({'index':metadata['index'],'objects':len(objects),'estimated_seconds':metadata['prediction'],'support':False})
    assert count==15,count
report={'printer':'P1S 0.4','material':'PLA','bed_mm':[256,256], 'plates':plates,
        'log_messages':(cache/'slice.log').read_text().splitlines()}
(root/'dist/enclosure/slice-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
