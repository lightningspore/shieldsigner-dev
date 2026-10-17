"""Package reviewed portable print artifacts and pin website/release checksums."""
from pathlib import Path
import hashlib
import json
import shutil
from zipfile import ZipFile,ZIP_DEFLATED

root=Path(__file__).resolve().parents[1];out=root/'dist/enclosure'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
reports=['mesh-check.json','printed-assembly-check.json','hardware-fit.json',
         'access-check.json','fastener-check.json','button-motion-check.json','exploded-check.json','slice-check.json']
for name in reports:
    report=json.loads((out/name).read_text())
    if isinstance(report,dict) and 'findings' in report:assert not report['findings'],name
slice_report=json.loads((out/'slice-check.json').read_text())
assert slice_report['bed_mm']==[256,256] and sum(p['objects'] for p in slice_report['plates'])==15
assert all(not p['support'] for p in slice_report['plates'])
assert 'button-fit-coupon' in json.loads((out/'mesh-check.json').read_text())
with ZipFile(out/'shieldsigner-enclosure-print.zip','w',ZIP_DEFLATED) as archive:
    for path in sorted(out.glob('*.stl')):archive.write(path,'print/'+path.name)
    archive.write(out/'print-plate.3mf','print/print-plate.3mf')
    for name in ['case.scad','print-profile.json']:archive.write(root/'enclosure'/name,'enclosure/'+name)
    archive.write(root/'docs/ENCLOSURE.md','docs/ENCLOSURE.md')
    archive.write(root/'LICENSE','LICENSE')
    for name in reports:archive.write(out/name,'checks/'+name)
    archive.writestr('README.txt','ShieldSigner modular enclosure prototype. Units: mm.\nMeasure soldered switch heights and generate matching button plungers; default button may not actuate shorter switches. Print other STL parts once. The button-fit-coupon is optional.\nPortable 3MF contains 15 independent print objects. See docs/ENCLOSURE.md first.\nCamera dimensions are adjustable assumptions; verify the purchased low-profile module.\nSource: https://github.com/lightningspore/shieldsigner-dev/tree/main/enclosure\n')
for name,source in [('shieldsigner-enclosure-assembled.glb','assembled.glb'),
                    ('shieldsigner-enclosure-exploded.glb','exploded.glb'),
                    ('shieldsigner-enclosure-plate.3mf','print-plate.3mf')]:shutil.copyfile(out/source,out/name)
names=['shieldsigner-enclosure-print.zip','shieldsigner-enclosure-assembled.glb',
       'shieldsigner-enclosure-exploded.glb','shieldsigner-enclosure-plate.3mf']
manifest={'version':'0.0.2-dev','status':'Digital prototype; physical first fit pending',
          'boardSha256':sha(root/'variants/lcd-module-2.8/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'),
          'scadSha256':sha(root/'enclosure/case.scad'),'assets':[]}
for name in names:
    path=out/name
    manifest['assets'].append({'name':name,'size':path.stat().st_size,'sha256':sha(path),
        'url':f'https://github.com/lightningspore/shieldsigner-dev/releases/download/enclosure-preview-0.0.2-dev/{name}'})
(root/'assets/enclosure-downloads.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Packaged portable enclosure kit and pinned four download checksums')
