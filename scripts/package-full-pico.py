"""Package only the already checked full-size prototype artifacts."""
import csv,hashlib,json
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'variants/full-size-pico';M=V/'manufacturing';OUT=ROOT/'dist/full-size-pico';P=OUT/'prototype';PCB=V/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
board_sha=sha(PCB);state=json.loads((V/'study-status.json').read_text());manifest=json.loads((M/'manifest.json').read_text())
assert board_sha==state['boardSha256']==manifest['boardSha256']
for name in ['gerber-audit.json','mating-audit.json','plus-mating-audit.json','header-placement-map.json','experimental-checks.json']:
 assert json.loads((M/name).read_text())['boardSha256']==board_sha, 'Stale review: '+name
for name,digest in manifest['files'].items():assert sha(P/'gerbers'/name)==digest
bom=list(csv.DictReader((M/'bom-jlcpcb.csv').open()));cpl=list(csv.DictReader((M/'cpl-jlcpcb.csv').open()));refs={n for row in bom for n in row['Designator'].split(',')}
assert len(cpl)==46 and refs=={row['Designator'] for row in cpl} and 'U202' not in refs
# Explicit order-kit allowlist: no private infrastructure, credentials or OS caches.
files={}
for file in M.iterdir():
 if file.is_file() and file.suffix in {'.md','.json','.csv','.pdf','.svg','.png','.txt'}:files[file.name]=file
files['shieldsigner-full-pico-gerbers.zip']=P/'shieldsigner-full-pico-gerbers.zip'
for name in ['bom-jlcpcb.csv','cpl-jlcpcb.csv','ORDER.md','procurement-for-ten.csv']:files[name]=M/name
for name in ['XKB-X6511WVS-series.pdf','Harwin-M20-782.pdf','Luckfox-Pico.pdf','Luckfox-Pico-Plus.pdf','pinout.jpg','plus-pinout.jpg']:files['manufacturer-reference/'+name]=V/'reference'/name
for name in ['BRINGUP.md','PCB-SOFTWARE-COMPATIBILITY.md']:files['bring-up/'+name]=ROOT/'docs'/name
for name in ['source.json','audit.json','study-status.json']:files['provenance/'+name]=V/name
files['provenance/native-checks.json']=OUT/'checks-summary.json';files['LICENSE']=ROOT/'LICENSE'
checksums={name:sha(file) for name,file in files.items()};archive=P/'shieldsigner-full-pico-prototype-10.zip'
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
 for name,file in sorted(files.items()):z.write(file,name)
 z.writestr('SHA256SUMS',''.join(f'{digest}  {name}\n' for name,digest in sorted(checksums.items())))
with ZipFile(archive) as z:
 assert z.testzip() is None
 for name,digest in checksums.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
(P/'prototype-download.json').write_text(json.dumps({'name':archive.name,'sha256':sha(archive),'boardSha256':board_sha,'quantity':10,'status':state['status'],'assemblyCheckoutReady':False},indent=2)+'\n')
print('Prepared',archive,'\nSHA256',sha(archive),'\nSupplier sourcing/placement/DFM approval remains required; no new order or reservation placed by this workflow.')
