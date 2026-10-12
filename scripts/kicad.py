#!/usr/bin/env python3
"""mise entry point for the native KiCad project and review exports."""
import argparse,collections,hashlib,json,os,subprocess,sys,urllib.request
from zipfile import ZipFile,ZIP_DEFLATED
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
VERSION='10.0.7'
TOOLS=ROOT/'.tools';MOUNT=TOOLS/'kicad-10'
APP=MOUNT/'KiCad/KiCad.app'
PROJECT=ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pro'
PCB=PROJECT.with_suffix('.kicad_pcb');SCH=PROJECT.with_suffix('.kicad_sch')
OUT=ROOT/'dist/kicad'

def run(args,**kwargs):
    return subprocess.run([str(x) for x in args],check=True,**kwargs)

def cli(setup=False):
    override=os.environ.get('KICAD_CLI')
    if override:
        path=Path(override)
    else:
        path=APP/'Contents/MacOS/kicad-cli'
        if not path.exists():
            dmg=TOOLS/f'kicad-{VERSION}.dmg'
            if not dmg.exists():
                if not setup:raise RuntimeError('Run mise run kicad:setup first, or set KICAD_CLI to KiCad 10.')
                TOOLS.mkdir(exist_ok=True)
                url=f'https://downloads.kicad.org/kicad/macos/explore/stable/download/kicad-unified-universal-{VERSION}.dmg'
                print(f'Downloading KiCad {VERSION} (~1.34 GB) into .tools/',flush=True)
                tmp=dmg.with_suffix('.partial');urllib.request.urlretrieve(url,tmp);tmp.rename(dmg)
            run(['hdiutil','attach','-nobrowse','-readonly','-mountpoint',MOUNT,dmg])
    actual=subprocess.check_output([str(path),'version'],text=True).strip()
    if not actual.startswith('10.'):raise RuntimeError(f'KiCad 10 required; found {actual}')
    print('Using KiCad',actual,flush=True)
    return path

def report_summary():
    summary={}
    for kind in ['erc','drc']:
        j=json.loads((OUT/f'{kind}.json').read_text())
        all_items=j.get('violations',[])+[e for s in j.get('sheets',[]) for e in s['violations']]
        es=[e for e in all_items if not e.get('excluded',False)]
        summary[kind]={'bySeverity':dict(collections.Counter(e['severity'] for e in es)),
          'excluded':sum(bool(e.get('excluded')) for e in all_items),
          'byType':dict(collections.Counter(e['type'] for e in es)),
          'unconnectedItems':len(j.get('unconnected_items',[])),
          'schematicParityIssues':len(j.get('schematic_parity',[]))}
    (OUT/'checks-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    return summary

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['setup','open','check','export','fabricate']);args=parser.parse_args()
    os.chdir(ROOT);command=cli(setup=args.action=='setup');OUT.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();support=command.parent.parent/'SharedSupport'
    for version in ['9','10']:env[f'KICAD{version}_3DMODEL_DIR']=str(support/'3dmodels')
    if args.action=='setup':return
    if args.action=='open':
        run(['open','-a',command.parent.parent.parent,PROJECT]);return
    if args.action=='check':
        # Exceptions are valid only for the explicitly checked assembly variant.
        import importlib.util
        spec=importlib.util.spec_from_file_location('sexpr',ROOT/'scripts/kicad-sexpr.py');sx=importlib.util.module_from_spec(spec);spec.loader.exec_module(sx)
        tree=sx.parse(PCB.read_text());fps={next(x[2] for x in sx.children(f,'property') if x[1]=='Reference'):f for f in sx.children(tree,'footprint')}
        exceptions=json.loads((ROOT/'docs/drc-assembly-exceptions.json').read_text())
        for exception in exceptions:
            assert 'dnp' in sx.one(fps[exception['dnp']],'attr'),f"Invalid DNP exception: {exception['dnp']}"
            assert 'dnp' not in sx.one(fps[exception['fitted']],'attr'),f"Expected fitted strap: {exception['fitted']}"
        run([command,'sch','erc','--format','json','--severity-all','--output',OUT/'erc.json',SCH],env=env)
        run([command,'pcb','drc','--format','json','--schematic-parity','--severity-all','--refill-zones','--output',OUT/'drc.json',PCB],env=env)
        allowed={(e['type'],frozenset(e['refs'])) for e in exceptions}
        for issue in json.loads((OUT/'drc.json').read_text())['violations']:
            if issue.get('excluded'):
                refs=frozenset(i['description'].split()[-1] for i in issue['items'])
                assert (issue['type'],refs) in allowed,'Undocumented DRC exclusion'
        summary=report_summary()
        if any(v['bySeverity'].get('error',0) or v['unconnectedItems'] or v['schematicParityIssues'] for v in summary.values()):
            print('Native review found unresolved errors. Reports are preserved; do not order yet.',file=sys.stderr)
            return 1
    if args.action=='export':
        run([command,'sch','export','pdf','--output',OUT/'schematic.pdf',SCH],env=env)
        run([command,'sch','export','netlist','--format','kicadxml','--output',OUT/'netlist.xml',SCH],env=env)
        for side,layers in [('top','F.Cu,F.SilkS,Edge.Cuts'),('bottom','B.Cu,B.SilkS,Edge.Cuts')]:
            run([command,'pcb','export','svg','--layers',layers,'--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--output',OUT/f'pcb-{side}.svg',PCB],env=env)
        run([command,'pcb','export','pos','--format','csv','--units','mm','--exclude-dnp','--output',OUT/'positions.csv',PCB],env=env)
        print('Native review files:',OUT)
    if args.action=='fabricate':
        run([sys.executable,__file__,'check'])
        folder=OUT/'fabrication';folder.mkdir(exist_ok=True)
        layers='F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts'
        run([command,'pcb','export','gerbers','--layers',layers,'--check-zones','--output',str(folder)+'/',PCB],env=env)
        run([command,'pcb','export','drill','--format','excellon','--excellon-units','mm','--excellon-separate-th','--output',str(folder)+'/',PCB],env=env)
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()}
        manifest={'pcbSha256':hashlib.sha256(PCB.read_bytes()).hexdigest(),'activeDrcErrors':0,'documentedDnpExceptions':2,'qualification':'Fabrication geometry exported; assembly rotations, paste/reflow, LCD fit and bench operation require qualification','files':files}
        (OUT/'fabrication-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        with ZipFile(OUT/'shieldsigner-carrier-gerbers.zip','w',ZIP_DEFLATED) as archive:
            for path in sorted(folder.iterdir()):
                if path.is_file():archive.write(path,path.name)
        print('Gerbers and separate plated/nonplated drills:',OUT/'shieldsigner-carrier-gerbers.zip')
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except (RuntimeError,subprocess.CalledProcessError) as error:print(error,file=sys.stderr);sys.exit(1)
