"""Build pinned upstream locale assets with the original app's translation pin.

Offline pinned-container build after image acquisition, with closed-set shaping
supplements for the original catalogs. No device deployment or image build.
"""
import argparse,hashlib,json,os,subprocess,types
from pathlib import Path
from sources import HERE,DIST,LOCK,fetch
from build_manifest import sha256
ENVIRONMENT=json.loads((HERE/'locale-builder.lock.json').read_text())

def revision(path):return subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()

def verify(directory):
    directory=Path(directory).resolve();index=json.loads((directory/'runtime-index.json').read_text())
    if index.get('schema')!=1 or index.get('kind')!='shieldsigner-lvgl-locale-assets':raise ValueError('Unknown locale asset index')
    for relative,entry in index['files'].items():
        path=directory/relative
        if Path(relative).is_absolute() or '..' in Path(relative).parts or path.is_symlink() or directory not in path.resolve().parents:raise ValueError('Unsafe locale asset path')
        if not path.is_file() or path.stat().st_size!=entry['bytes'] or sha256(path)!=entry['sha256']:raise ValueError('Locale asset mismatch: '+relative)
    return dict(verified=True,directory=str(directory),locales=len(index['locales']),fontLocales=len(index['manifests']),runtimeFiles=len(index['files']),runtimeBytes=sum(row['bytes'] for row in index['files'].values()),unsupportedShapingTemplates=index['unsupportedShapingTemplates'],runtimeIntegrated=False)

def build(output=None):
    application=fetch('application');packs=fetch('language-packs')
    relative=ENVIRONMENT['translationsSubmodule'];translations=application/relative
    tree=subprocess.check_output(['git','-C',str(application),'ls-tree','HEAD',relative],text=True).split()
    if len(tree)<3 or tree[2]!=ENVIRONMENT['translationsCommit']:raise ValueError('App translation gitlink differs from reviewed pin')
    if not (translations/'.git').exists():subprocess.run(['git','-C',str(application),'submodule','update','--init','--depth','1',relative],check=True)
    if revision(translations)!=ENVIRONMENT['translationsCommit'] or subprocess.check_output(['git','-C',str(translations),'status','--porcelain'],text=True).strip():raise ValueError('Unreviewed/modified translation source')
    policy_path=packs/'tools/locales_h.py';policy=types.ModuleType('pinned_locale_policy');policy.__file__=str(policy_path)
    exec(compile(policy_path.read_bytes(),str(policy_path),'exec'),policy.__dict__)
    available=sorted(path.parent.parent.name for path in (translations/'l10n').glob('*/LC_MESSAGES/messages.po'))
    selected=sorted(set(available)&set(policy.manifest_locales()))
    provenance=dict(sourcePins=LOCK,environment=ENVIRONMENT,producerSha256=sha256(Path(__file__)),supplementSha256=sha256(HERE/'locale_supplement.py'),fontLocales=selected,translationLocales=available)
    fingerprint=hashlib.sha256(json.dumps(provenance,sort_keys=True).encode()).hexdigest()
    output=Path(output).resolve() if output else DIST/'locale-assets'/fingerprint[:16]
    if output.exists():
        if json.loads((output/'runtime-index.json').read_text()).get('inputs')!=provenance:raise ValueError('Existing output has different inputs; choose a new directory')
        return dict(**verify(output),cached=True)
    tool_key=hashlib.sha256(json.dumps(dict(environment=ENVIRONMENT,source=LOCK['language-packs']),sort_keys=True).encode()).hexdigest()[:16]
    output.mkdir(parents=True);tools=DIST/'locale-pack-build-tools'/tool_key;tools.mkdir(parents=True,exist_ok=True)
    image=ENVIRONMENT['image']
    if subprocess.run(['docker','image','inspect',image],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
        subprocess.run(['docker','pull','--platform',ENVIRONMENT['platform'],image],check=True)
    command=['docker','run','--rm','--platform',ENVIRONMENT['platform'],'--network','none','--user',f'{os.getuid()}:{os.getgid()}','-e','PYTHONDONTWRITEBYTECODE=1']
    for source,target,readonly in ((HERE/'locale_supplement.py','/supplement.py',True),(packs,'/work',True),(translations,'/translations',True),(tools,'/build',False),(output,'/out',False)):
        if ',' in str(source):raise ValueError('Docker mount path contains a comma')
        command+=['--mount',f'type=bind,source={source},target={target}'+(',readonly' if readonly else '')]
    command+=['--workdir','/work',image,'sh','-c','cmake -S tools/shaper -B /build -DCMAKE_BUILD_TYPE=Release -DLVGL_ROOT=/opt/lvgl > /build/configure.log && cmake --build /build -j 4 > /build/compile.log && exec python3 /supplement.py "$@"','build-locales','--translations-dir','/translations','--shaper-bin','/build/lv_shape','--out-dir','/out']
    for locale in selected:command+=['--locale',locale]
    subprocess.run(command,check=True)
    files={};manifests={};unsupported={}
    def include(relative):
        path=output/relative
        if path.is_symlink() or not path.is_file() or path.stat().st_size>ENVIRONMENT['maxRuntimeFileBytes']:raise ValueError('Missing/oversized runtime locale file: '+relative)
        files[relative]=dict(bytes=path.stat().st_size,sha256=sha256(path))
    for locale in selected:
        manifest=json.loads((output/locale/'manifest.json').read_text());manifests[locale]=manifest
        include(locale+'/manifest.json')
        fonts=manifest.get('fonts',[]) or [manifest['font']]
        for font in fonts:
            name=locale+'/'+font['file'];include(name)
            if files[name]['sha256']!=font['sha256']:raise ValueError('Upstream font hash mismatch')
        if manifest.get('shaping'):
            run=manifest['runs'];name=locale+'/'+run['file'];include(name)
            if files[name]['sha256']!=run['sha256']:raise ValueError('Upstream glyph-run hash mismatch')
            if run.get('unsupported'):unsupported[locale]=run['unsupported']
        endonym=manifest['endonym_images']['240'];include(locale+'/'+endonym['file'])
    index=dict(kind='shieldsigner-lvgl-locale-assets',schema=1,inputs=provenance,locales=['en',*available],manifests=manifests,files=files,unsupportedShapingTemplates=unsupported,signed=False,runtimeIntegrated=False)
    (output/'runtime-index.json').write_text(json.dumps(index,sort_keys=True,indent=2)+'\n')
    return dict(**verify(output),cached=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group();group.add_argument('--output',type=Path);group.add_argument('--verify',type=Path)
    args=parser.parse_args();print(json.dumps(verify(args.verify) if args.verify else build(args.output),indent=2))

if __name__=='__main__':main()
