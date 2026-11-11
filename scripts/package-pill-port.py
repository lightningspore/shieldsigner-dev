#!/usr/bin/env python3
"""Rebuild portable native assets for the complete tscircuit pill-carrier port."""
import argparse, hashlib, json, runpy, shutil, subprocess
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--assets-only',action='store_true');args=parser.parse_args()
ref=json.loads((ROOT/'src/generated/pill-board.json').read_text())
board=ROOT/ref['source']['path'];out=ROOT/'dist/pill-tscircuit';out.mkdir(exist_ok=True,parents=True)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(board)==ref['source']['sha256'],'Stale geometry'
cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']()
def run(*cmd):subprocess.run([str(cli),*[str(v) for v in cmd]],check=True,cwd=ROOT)
# All retained model files and their authored transforms are cache inputs.
inputs=[Path(__file__),board,board.with_suffix('.kicad_pro'),ROOT/'src/generated/pill-details.json',*board.parent.rglob('*.step')]
key=hashlib.sha256(''.join(str(p.relative_to(ROOT))+sha(p) for p in sorted(inputs)).encode()).hexdigest()
cache=out/'native-assets-key.json'
if args.assets_only:
    if not cache.exists() or json.loads(cache.read_text()).get('sha256')!=key or not (out/'components-native.glb').exists():
        origin=ref['origin']
        run('pcb','export','glb','--force','--no-board-body','--user-origin',f"{origin['x']}x{origin['y']}mm",'--output',out/'components-native.glb',board)
    return_code=0
else:
    native=out/'native'
    if native.exists(): shutil.rmtree(native)  # generated snapshot only
    native.mkdir()
    # Copy only version-controlled native design and library snapshots; no OS/editor caches.
    if (ROOT/'.git').exists():
        tracked=subprocess.check_output(['git','ls-files','-z','--',str(board.parent.relative_to(ROOT))],cwd=ROOT).decode().split('\0')
    else:
        allowed={'.kicad_pcb','.kicad_pro','.kicad_sch','.kicad_mod','.kicad_sym','.kicad_dru','.step','.stp','.wrl','.json','.md','.txt'}
        tracked=[str(p.relative_to(ROOT)) for p in board.parent.rglob('*') if p.is_file() and
                 (p.suffix.lower() in allowed or p.name in {'fp-lib-table','sym-lib-table'}) and
                 not any(part.startswith('.') or part.endswith('-backups') for part in p.relative_to(board.parent).parts)]
    for entry in filter(None,tracked):
        path=ROOT/entry
        if not path.is_file():continue
        target=native/path.relative_to(board.parent);target.parent.mkdir(exist_ok=True,parents=True)
        shutil.copyfile(path,target)
    for path in [ROOT/'LICENSE',ROOT/'reference/provenance.json']:
        shutil.copyfile(path,native/path.name)
    source_manifest={str(p.relative_to(native)):sha(p) for p in sorted(native.rglob('*')) if p.is_file()}
    (out/'native-source-manifest.json').write_text(json.dumps({'source':ref['source'],'files':source_manifest},indent=2)+'\n')
    if not cache.exists() or json.loads(cache.read_text()).get('sha256')!=key or not (out/'native-gerbers').is_dir():
        origin=ref['origin']
        run('pcb','export','glb','--force','--include-silkscreen','--include-soldermask','--include-pads','--include-tracks','--include-zones',
            '--user-origin',f"{origin['x']}x{origin['y']}mm",'--output',out/'native-assembly.glb',board)
        layers='F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts'
        run('pcb','export','gerbers','--layers',layers,'--check-zones','--output',str(out/'native-gerbers')+'/',board)
        run('pcb','export','drill','--format','excellon','--excellon-units','mm','--excellon-separate-th','--output',str(out/'native-gerbers')+'/',board)
        for side,layer in [('top','F.SilkS'),('bottom','B.SilkS')]:
            run('pcb','export','svg','--layers',layer,'--mode-single','--page-size-mode','1','--drill-shape-opt','0','--exclude-drawing-sheet','--output',out/f'native-silk-{side}.svg',board)
        run('sch','export','svg','--output',str(out/'native-schematic')+'/',board.with_suffix('.kicad_sch'))
        run('pcb','export','pos','--format','csv','--units','mm','--exclude-dnp','--output',out/'native-positions.csv',board)
        cache.write_text(json.dumps({'sha256':key})+'\n')
    supplier=out/'supplier-reference';supplier.mkdir(exist_ok=True)
    for name in ['README.md','bom-jlcpcb.csv','cpl-jlcpcb.csv','population.csv']:
        shutil.copyfile(ROOT/'hardware/manufacturing'/name,supplier/name)
    for name in ['check-results.json','header-map.json','mechanical.json','branding.json','branding-audit.json']:
        shutil.copyfile(ROOT/'hardware'/name,out/f'native-{name}')
    for kind in ['erc','drc']:
        path=ROOT/'dist/lcd-module-2.8'/f'{kind}.json'
        if path.exists(): shutil.copyfile(path,out/f'native-{kind}.json')
    shutil.copyfile(ROOT/'src/generated/pill-details.json',out/'native-details.json')
    # Preserve every original setup/zone/stackup and custom attribute without inventing JSON fields.
    sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'))
    tree=sx['parse'](board.read_text())
    (out/'native-design.json').write_text(json.dumps({'source':ref['source'],'pcb':tree,'project':json.loads(board.with_suffix('.kicad_pro').read_text())},separators=(',',':'))+'\n')
    report={'source':ref['source'],'qualification':'Port and native manufacturing geometry; not hardware qualification',
            'nativeSourceFiles':len(source_manifest),'files':{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.suffix!='.zip' and p.name!='package-manifest.json'}}
    (out/'package-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    with ZipFile(out/'shieldsigner-pill-tscircuit.zip','w',ZIP_DEFLATED) as archive:
        for path in sorted(out.rglob('*')):
            if path.is_file() and path.suffix!='.zip':archive.write(path,path.relative_to(out))
        for path in ['src/PillCarrierReference.tsx','src/index.tsx','src/StandardFpcReference.tsx','src/ShieldSignerPlus.tsx','src/generated/pill-board.json','src/generated/pill-details.json','scripts/build.tsx','scripts/pill-details.ts','scripts/generate-reference.py','scripts/extract-pill-details.py','scripts/convert-pill-models.mjs','scripts/render-pill-previews.mjs','scripts/package-pill-port.py','scripts/check-pill.tsx','scripts/check-pill-artwork.mjs','scripts/check-pill-geometry.py','scripts/kicad.py','scripts/kicad-sexpr.py','scripts/dev.ts','package.json','bun.lock','mise.toml','tsconfig.json','docs/PORT-STATUS.md']:
            file=ROOT/path
            if file.exists():archive.write(file,'tscircuit-source/'+path)
        # Reproducible pill-only checkout layout, including local libraries/models.
        for path in sorted(native.rglob('*')):
            if path.is_file():
                rel=path.relative_to(native)
                if str(rel)=='LICENSE': target='tscircuit-source/LICENSE'
                elif str(rel)=='provenance.json': target='tscircuit-source/reference/provenance.json'
                else: target=f'tscircuit-source/kicad/{rel}'
                archive.write(path,target)
        for path in supplier.iterdir():
            archive.write(path,f'tscircuit-source/hardware/manufacturing/{path.name}')
        for name in ['check-results.json','header-map.json','mechanical.json','branding.json','branding-audit.json']:
            archive.write(ROOT/'hardware'/name,f'tscircuit-source/hardware/{name}')
        # Shared renderer still has a default import of the standard-board snapshot.
        archive.write(ROOT/'src/generated/reference-board.json','tscircuit-source/src/generated/reference-board.json')
    print(f'Packaged {len(source_manifest)} native source/library files, original rules, stackup, Gerbers, drills and complete tscircuit outputs.')
