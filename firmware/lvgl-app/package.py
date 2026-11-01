"""Stage/verify an inactive LVGL runtime payload; no OS build, install or flash."""
import argparse,importlib.util,json,os,shutil,stat,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
from artifact_paths import ROOT,DIST,LVGL_SOURCES
sys.path[:0]=[str(HERE/'python'),str(HERE)]
from app import verify_native_artifact
from build_manifest import inputs,sha256
PREFIX='payload/usr/lib/shieldsigner-lvgl'

def stage(output,locale_root=None):
    binary=DIST/'build/shieldsigner-lvgl';native_manifest=binary.parent/'build-manifest.json'
    native=verify_native_artifact(binary,native_manifest)
    if native['inputs']!=inputs(HERE):raise ValueError('Native inputs changed; rebuild first')
    spec=importlib.util.spec_from_file_location('camera_image_validation',ROOT/'scripts/prepare-camera-image.py')
    checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    checker.validate_static_arm(binary)
    files={PREFIX+'/shieldsigner-lvgl':binary,PREFIX+'/shieldsigner-lvgl.manifest.json':native_manifest,PREFIX+'/python/source-guards.json':HERE/'source-guards.json',PREFIX+'/source-pins.json':HERE/'sources.lock.json'}
    locale_index=None
    if locale_root is not None:
        from locale_assets import LocaleAssets
        assets=LocaleAssets(locale_root);locale_index=assets.index
        for relative in [*locale_index['files'],'runtime-index.json']:
            files[PREFIX+'/locales/'+relative]=assets.root/relative
    excluded={'bytecode_cache.py','diagnostic_scope.py','resources.py'}
    for path in sorted((HERE/'python').glob('*.py')):
        if path.name not in excluded:files[PREFIX+'/python/'+path.name]=path
    notices='payload/usr/share/licenses/shieldsigner-lvgl/'
    files[notices+'SeedSigner-MIT.txt']=ROOT/'LICENSE'
    for path in sorted((HERE/'licenses').glob('*')):
        if path.is_file():files[notices+'local/'+path.name]=path
    audit_path=HERE/'validation/notice-audit-host.json'
    audit=json.loads(audit_path.read_text())
    expected_notices={path.name:dict(sha256=sha256(path),bytes=path.stat().st_size) for path in (HERE/'licenses').iterdir() if path.is_file()}
    if audit['notices']!=expected_notices or audit['sourcePins']!=json.loads((HERE/'sources.lock.json').read_text()):raise ValueError('Notice inventory changed; rerun audit_licenses.py')
    files[notices+'notice-audit.json']=audit_path
    for name in ('LICENCE.txt','COPYRIGHTS.md'):
        files[notices+'lvgl/'+name]=LVGL_SOURCES/'lvgl'/name
    for path in sorted((LVGL_SOURCES/'lvgl/src').rglob('*')):
        if path.is_file() and path.name.upper().startswith(('LICENSE','LICENCE','COPYING','NOTICE')):
            files[notices+'lvgl/src/'+str(path.relative_to(LVGL_SOURCES/'lvgl/src'))]=path
    for path in files.values():
        if not path.is_file() or path.is_symlink():raise ValueError('Missing/unsafe runtime input: '+str(path))
    output.mkdir(parents=True,exist_ok=False);entries={}
    for relative,source in sorted(files.items()):
        destination=output/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,destination)
        mode=0o755 if source==binary else 0o644;destination.chmod(mode)
        entries[relative]=dict(sha256=sha256(destination),bytes=destination.stat().st_size,mode=mode)
    launcher='''#!/bin/sh
set -eu
exec python3 -B -X pycache_prefix=/usr/lib/shieldsigner-lvgl/bytecode /usr/lib/shieldsigner-lvgl/python/app.py \\
  --app-root /opt/src --camera-root /usr/lib/shieldsigner-camera/python \\
  --binary /usr/lib/shieldsigner-lvgl/shieldsigner-lvgl \\
  --settings /userdata/shieldsigner-lvgl-settings.json -- "$@"
'''
    if locale_index is not None:
        launcher=launcher.replace('  --settings ', '  --locale-root /usr/lib/shieldsigner-lvgl/locales \\\n  --settings ')
    relative=PREFIX+'/launch.sh';destination=output/relative
    destination.write_text(launcher);destination.chmod(0o755)
    entries[relative]=dict(sha256=sha256(destination),bytes=destination.stat().st_size,mode=0o755)
    # Keep runtime source-guard checks, but compile the import-only edits before
    # wallet startup so large temporary AST/compiler allocations stay out of it.
    cache=output/PREFIX/'python/import-cache'
    compiled=subprocess.run(['uv','run','--python','3.12','python',str(HERE/'python/import_cache.py'),str(LVGL_SOURCES/'application/src'),str(HERE/'source-guards.json'),str(cache),'--filename-root','/opt/src','--stream-source',str(ROOT/'firmware/rkaiq-rs/python/shieldsigner_video_stream.py')],env=dict(os.environ,PYTHONHASHSEED='0'),text=True,stdout=subprocess.PIPE,check=True)
    cache_result=json.loads(compiled.stdout)
    for path in sorted(cache.iterdir()):
        path.chmod(0o644);relative=str(path.relative_to(output))
        entries[relative]=dict(sha256=sha256(path),bytes=path.stat().st_size,mode=0o644)
    # The import policy handles transformed modules; cache unchanged sources
    # separately so a first boot does not rebuild their compiler working set.
    from dependency_policy import specifications
    from sources import fetch
    app_root=fetch('application')/'src';transformed={relative for relative,kind in specifications().values()}
    mapping=[dict(source=str(path),filename='/opt/src/'+str(path.relative_to(app_root))) for path in sorted(app_root.rglob('*.py')) if '__pycache__' not in path.parts and str(path.relative_to(app_root)) not in {'main.py',*('seedsigner/'+name for name in transformed)}]
    mapping += [dict(source=str(path),filename='/usr/lib/shieldsigner-lvgl/python/'+path.name) for path in sorted((output/PREFIX/'python').glob('*.py')) if path.name!='app.py']
    camera_root=ROOT/'firmware/rkaiq-rs/python'
    for name in ('shieldsigner_integration.py','shieldsigner_qr_decoder.py','shieldsigner_camera_compat.py','shieldsigner_process_log.py','shieldsigner_native_stream.py','shieldsigner_native_camera.py','shieldsigner_lcd_driver.py'):
        source=ROOT/'firmware/lcd-rs/python'/name if name=='shieldsigner_lcd_driver.py' else camera_root/name
        mapping.append(dict(source=str(source),filename='/usr/lib/shieldsigner-camera/python/'+name))
    source_cache=output/PREFIX/'bytecode'
    with tempfile.TemporaryDirectory(prefix='lvgl-source-map-') as temporary:
        plan=Path(temporary)/'map.json';plan.write_text(json.dumps(mapping))
        subprocess.run(['uv','run','--python','3.12','python',str(HERE/'python/bytecode_cache.py'),'--stage-map',str(plan),str(source_cache)],env=dict(os.environ,PYTHONHASHSEED='0'),stdout=subprocess.PIPE,text=True,check=True)
    for path in sorted(source_cache.rglob('*')):
        if not path.is_file():continue
        path.chmod(0o644);entries[str(path.relative_to(output))]=dict(sha256=sha256(path),bytes=path.stat().st_size,mode=0o644)
    manifest=dict(kind='shieldsigner-lvgl-inactive-runtime',schema=1,compiledSourceCache=True,compiledImportCache=True,releaseReady=False,licenseClosureVerified=False,noticeAuditIncluded=True,serviceInstalled=False,requiresExistingApplicationRoot='/opt/src',requiresCameraRuntime='/usr/lib/shieldsigner-camera',settings='/userdata/shieldsigner-lvgl-settings.json',localesIncluded=locale_index is not None,nativeBuild=native,sources=json.loads((HERE/'sources.lock.json').read_text()),files=entries)
    (output/'runtime-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    return verify(output)

def verify(directory):
    directory=directory.resolve();manifest=json.loads((directory/'runtime-manifest.json').read_text())
    if manifest.get('kind')!='shieldsigner-lvgl-inactive-runtime' or manifest.get('schema')!=1:raise ValueError('Unsupported runtime manifest')
    if manifest.get('releaseReady') is not False or manifest.get('serviceInstalled') is not False:raise ValueError('This stager does not qualify or activate releases')
    expected=set(manifest['files'])
    actual={str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file() or path.is_symlink()}
    if actual!=expected|{'runtime-manifest.json'}:raise ValueError('Unexpected/missing staged files')
    for relative,entry in manifest['files'].items():
        path=directory/relative
        if Path(relative).is_absolute() or '..' in Path(relative).parts or path.is_symlink() or directory not in path.resolve().parents:raise ValueError('Unsafe staged path')
        if sha256(path)!=entry['sha256'] or path.stat().st_size!=entry['bytes'] or stat.S_IMODE(path.stat().st_mode)!=entry['mode']:raise ValueError('Staged file mismatch: '+relative)
    native=verify_native_artifact(directory/PREFIX/'shieldsigner-lvgl',directory/PREFIX/'shieldsigner-lvgl.manifest.json')
    if native!=manifest['nativeBuild']:raise ValueError('Inconsistent native provenance')
    if manifest.get('noticeAuditIncluded'):
        root=directory/'payload/usr/share/licenses/shieldsigner-lvgl'
        audit=json.loads((root/'notice-audit.json').read_text())
        for name,entry in audit['notices'].items():
            if Path(name).name!=name:raise ValueError('Unsafe notice name')
            path=root/'local'/name
            if sha256(path)!=entry['sha256'] or path.stat().st_size!=entry['bytes']:raise ValueError('Inconsistent staged notice inventory')
        if audit['sourcePins']!=manifest['sources']:raise ValueError('Notice source pins mismatch')
    if manifest.get('compiledImportCache'):
        cache=directory/PREFIX/'python/import-cache';index=json.loads((cache/'index.json').read_text())
        from import_cache import policy_sha
        from stream_imports import NAME,SOURCE_SHA256
        if index['policySha256']!=policy_sha(directory/PREFIX/'python'):raise ValueError('Staged import-cache policy differs')
        guards=json.loads((directory/PREFIX/'python/source-guards.json').read_text())
        from dependency_policy import specifications
        if set(index['modules'])!=set(specifications())|{NAME}:raise ValueError('Incomplete staged import cache')
        for name,(relative,kind) in specifications().items():
            item=index['modules'][name]
            if item['sourceSha256']!=guards[relative] or Path(item['file']).name!=item['file'] or sha256(cache/item['file'])!=item['codeSha256']:raise ValueError('Staged import-cache artifact differs')
        item=index['modules'][NAME]
        if item['sourceSha256']!=SOURCE_SHA256 or Path(item['file']).name!=item['file'] or sha256(cache/item['file'])!=item['codeSha256']:raise ValueError('Staged stream import cache differs')

    if manifest.get('compiledSourceCache'):
        if 'exec python3 -B -X pycache_prefix=/usr/lib/shieldsigner-lvgl/bytecode ' not in (directory/PREFIX/'launch.sh').read_text():raise ValueError('Launcher does not select the staged source cache')
        root=directory/PREFIX/'bytecode';record=json.loads((root/'index.json').read_text())
        if record['magic']!=index['magic']:raise ValueError('Source/import cache ABI differs')
        source_expected={'index.json'}
        for item in record['entries']:
            relative=Path(item['file']);target=Path(item['filename'])
            if relative.is_absolute() or '..' in relative.parts or not target.is_absolute() or '..' in target.parts:raise ValueError('Unsafe source-cache path')
            data=(root/relative).read_bytes()
            if sha256(root/relative)!=item['sha256'] or data[:4].hex()!=record['magic'] or int.from_bytes(data[4:8],'little')!=3 or data[8:16].hex()!=item['checkedSourceHash']:raise ValueError('Source-cache artifact differs')
            if str(relative) in source_expected:raise ValueError('Duplicate source-cache entry')
            source_expected.add(str(relative))
        if source_expected!={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}:raise ValueError('Unexpected source-cache files')
    if manifest.get('localesIncluded'):
        from locale_assets import LocaleAssets
        LocaleAssets(directory/PREFIX/'locales')
    return dict(verified=True,localesIncluded=bool(manifest.get('localesIncluded')),files=len(expected),payloadBytes=sum(row['bytes'] for row in manifest['files'].values()),releaseReady=False,serviceInstalled=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output',type=Path);group.add_argument('--verify',type=Path);parser.add_argument('--locale-root',type=Path);args=parser.parse_args()
    print(json.dumps(stage(args.output,args.locale_root) if args.output else verify(args.verify),indent=2))

if __name__=='__main__':main()
