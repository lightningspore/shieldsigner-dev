"""Prepare/verify an INACTIVE image overlay draft. Never install, build OS or flash."""
import argparse,datetime,json,os,shlex,shutil,stat,subprocess
from pathlib import Path
from package import verify as verify_runtime,HERE,ROOT,PREFIX
from build_manifest import sha256

BASE=HERE/'service/base-launcher-pil.sh'
BASE_EXEC='exec python3 -u /usr/lib/shieldsigner-camera/python/shieldsigner_integration.py '
ROLLBACK='/userdata/shieldsigner-lvgl.rollback'

def selector(prefix,default='pil',*,pil='/usr/bin/shieldsigner-launch.pil',lvgl='/usr/lib/shieldsigner-lvgl/launch.sh',rollback=ROLLBACK):
    if default not in ('pil','lvgl'):raise ValueError('Invalid default frontend')
    return '''#!/bin/sh
set -eu
# Existing S99/start-seedsigner supervisor remains the sole process owner.
_shieldsigner_frontend=${SHIELDSIGNER_FRONTEND_OVERRIDE:-'''+default+'''}
if [ -f '''+shlex.quote(str(rollback))+''' ]; then _shieldsigner_frontend=pil; fi
case "$_shieldsigner_frontend" in
 pil) exec '''+shlex.quote(str(pil))+''' "$@" ;;
 lvgl) : ;;
 *) echo "Unknown ShieldSigner frontend selection" >&2; exit 64 ;;
esac
# Exact reviewed camera-image memory/device setup, before Python imports.
'''+prefix+'\nexec '+shlex.quote(str(lvgl))+' "$@"\n'

def prepare(runtime,output,epoch,default='pil'):
    runtime=runtime.resolve();verify_runtime(runtime)
    original=json.loads((runtime/'runtime-manifest.json').read_text())
    if original.get('localesIncluded'):raise ValueError('Current image milestone is English only; stage without locale assets')
    lock=json.loads(BASE.with_name('base-launcher.lock.json').read_text())
    if sha256(BASE)!=lock['sha256']:raise ValueError('Unreviewed base launcher')
    base=BASE.read_text();prefix,tail=base.split(BASE_EXEC,1)
    if not tail.startswith('\\\n  --app-root /opt/src --config /usr/lib/shieldsigner-camera/owner.json') or not tail.endswith('"$@"\n'):raise ValueError('Unexpected base launcher exec')
    prefix=prefix.removeprefix('#!/bin/sh\nset -eu\n')
    base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True))
    identity=sha256(runtime/'runtime-manifest.json')
    timestamp=datetime.datetime.fromtimestamp(epoch,datetime.timezone.utc).isoformat()
    version=dict(name='lvgl-dev.'+identity[:12],fork='lightningspore',short_commit_hash=base_commit[:7]+('-dirty' if dirty else ''),timestamp=timestamp)
    output.mkdir(parents=True,exist_ok=False)
    shutil.copytree(runtime/'payload',output/'payload')
    files={
        'usr/bin/shieldsigner-launch':(selector(prefix,default).encode(),0o755),
        'usr/bin/shieldsigner-launch.pil':(BASE.read_bytes(),0o755),
        'opt/src/seedsigner/version.json':((json.dumps(version,indent=2,sort_keys=True)+'\n').encode(),0o644),
    }
    for relative,(data,mode) in files.items():
        path=output/'payload'/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);path.chmod(mode)
    entries={str(path.relative_to(output)):dict(sha256=sha256(path),bytes=path.stat().st_size,mode=stat.S_IMODE(path.stat().st_mode)) for path in sorted((output/'payload').rglob('*')) if path.is_file()}
    helper=output/'overlay-apply.py';shutil.copyfile(HERE/'overlay_apply.py',helper);helper.chmod(0o755)
    record=dict(applyHelperSha256=sha256(helper),kind='shieldsigner-lvgl-image-overlay-draft',schema=1,imageBuilt=False,installed=False,releaseReady=False,defaultFrontend=default,rollbackFile=ROLLBACK,runtimeManifestSha256=identity,runtimeManifest=original,baseLauncherSha256=lock['sha256'],baseRepositoryCommit=base_commit,worktreeDirty=dirty,sourceDateEpoch=epoch,version=version,scope=dict(language='en',smartcardWorkExcluded=True),files=entries,requiresExistingSupervisor=True,requiresExistingCameraRuntime=True,activationGate='Migration/current-flow/resource/soak acceptance must pass before OS image build; flashing last')
    (output/'integration-plan.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
    return verify(output)

def verify(directory):
    directory=directory.resolve();record=json.loads((directory/'integration-plan.json').read_text())
    if record.get('kind')!='shieldsigner-lvgl-image-overlay-draft' or record.get('schema')!=1:raise ValueError('Unexpected image draft')
    if any(record.get(key) is not False for key in ('imageBuilt','installed','releaseReady')):raise ValueError('Draft does not qualify/install/build an image')
    actual={str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file() or path.is_symlink()}
    expected=set(record['files'])|{'integration-plan.json'}
    if record.get('applyHelperSha256'):
        expected.add('overlay-apply.py')
        if sha256(directory/'overlay-apply.py')!=record['applyHelperSha256']:raise ValueError('Image application helper mismatch')
    if actual!=expected:raise ValueError('Unexpected/missing image draft files')
    for relative,entry in record['files'].items():
        path=directory/relative
        if Path(relative).is_absolute() or '..' in Path(relative).parts or path.is_symlink() or directory not in path.resolve().parents:raise ValueError('Unsafe image draft path')
        if sha256(path)!=entry['sha256'] or path.stat().st_size!=entry['bytes'] or stat.S_IMODE(path.stat().st_mode)!=entry['mode']:raise ValueError('Image draft mismatch: '+relative)
    for relative,entry in record['runtimeManifest']['files'].items():
        if record['files'].get(relative)!=entry:raise ValueError('Runtime payload differs from its provenance')
    from app import verify_native_artifact
    native=verify_native_artifact(directory/PREFIX/'shieldsigner-lvgl',directory/PREFIX/'shieldsigner-lvgl.manifest.json')
    if native!=record['runtimeManifest']['nativeBuild']:raise ValueError('Native image provenance mismatch')
    for relative in ('usr/bin/shieldsigner-launch','usr/bin/shieldsigner-launch.pil','usr/lib/shieldsigner-lvgl/launch.sh'):
        subprocess.run(['sh','-n',str(directory/'payload'/relative)],check=True)
    if sha256(directory/'payload/usr/bin/shieldsigner-launch.pil')!=record['baseLauncherSha256']:raise ValueError('Rollback launcher mismatch')
    if json.loads((directory/'payload/opt/src/seedsigner/version.json').read_text())!=record['version']:raise ValueError('Version identity mismatch')
    return dict(verified=True,files=len(record['files']),bytes=sum(row['bytes'] for row in record['files'].values()),defaultFrontend=record['defaultFrontend'],imageBuilt=False,installed=False,releaseReady=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output',type=Path);group.add_argument('--verify',type=Path)
    parser.add_argument('--runtime',type=Path);parser.add_argument('--source-date-epoch',type=int);parser.add_argument('--default-frontend',choices=['pil','lvgl'],default='pil');args=parser.parse_args()
    if args.output and (args.runtime is None or args.source_date_epoch is None):parser.error('Preparing requires --runtime and explicit --source-date-epoch')
    print(json.dumps(verify(args.verify) if args.verify else prepare(args.runtime,args.output,args.source_date_epoch,args.default_frontend),indent=2))
if __name__=='__main__':main()
