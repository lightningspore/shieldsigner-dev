"""Apply/verify a draft ONLY in an offline rootfs; never start a service or flash."""
import argparse,hashlib,json,os,shutil,stat,tempfile
from pathlib import Path
RECEIPT='usr/share/shieldsigner-lvgl/image-overlay.json'
CAMERA_RECEIPT='usr/lib/shieldsigner-camera/image-installation.json'
def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(65536),b''):value.update(chunk)
    return value.hexdigest()
def inside(root,relative):
    root=Path(root).resolve()
    part=Path(relative)
    if part.is_absolute() or '..' in part.parts:raise ValueError('Unsafe overlay path')
    path=root/part
    if path.is_symlink() or root not in path.resolve().parents:raise ValueError('Overlay path escapes rootfs')
    for parent in path.parents:
        if parent==root:break
        if parent.is_symlink():raise ValueError('Symlink in rootfs destination')
    return path
def load(draft):
    plan=json.loads((draft/'integration-plan.json').read_text())
    if plan.get('kind')!='shieldsigner-lvgl-image-overlay-draft' or plan.get('schema')!=1:raise ValueError('Unknown overlay draft')
    if any(plan.get(key) is not False for key in ('imageBuilt','installed','releaseReady')):raise ValueError('Expected an unqualified offline draft')
    if plan.get('applyHelperSha256') and digest(inside(draft,'overlay-apply.py'))!=plan['applyHelperSha256']:raise ValueError('Overlay application helper changed')
    for relative,row in plan['files'].items():
        path=inside(draft,relative)
        if not path.is_file() or digest(path)!=row['sha256'] or path.stat().st_size!=row['bytes'] or stat.S_IMODE(path.stat().st_mode)!=row['mode']:raise ValueError('Overlay draft changed: '+relative)
    return plan
def root_check(root):
    root=root.resolve()
    if root==Path('/') or (root/'proc/1/stat').exists():raise ValueError('Refusing a live root filesystem')
    if not (root/'etc/seedsigner-os-release').is_file():raise ValueError('Expected a staged SeedSigner rootfs')
    return root
def camera_receipt(root):
    path=inside(root,CAMERA_RECEIPT);data=json.loads(path.read_text())
    if set(data['startupSha256'])!=set(data['startupModes']):raise ValueError('Incomplete camera startup provenance')
    for name,expected in data['startupSha256'].items():
        candidate=inside(root,name)
        if digest(candidate)!=expected or stat.S_IMODE(candidate.stat().st_mode)!=data['startupModes'][name]:raise ValueError('Camera startup provenance changed: '+name)
    return data

def preflight(root,draft):
    root=root_check(root);plan=load(draft)
    inside(root,RECEIPT)
    camera=camera_receipt(root)
    if camera['startupSha256'].get('usr/bin/shieldsigner-launch')!=plan['baseLauncherSha256']:raise ValueError('Camera receipt does not identify the reviewed base launcher')
    if digest(inside(root,'usr/bin/shieldsigner-launch'))!=plan['baseLauncherSha256']:raise ValueError('Base camera launcher differs from reviewed image')
    for relative in ('usr/bin/shieldsigner-launch.pil','usr/lib/shieldsigner-lvgl',RECEIPT):
        if (root/relative).exists() or (root/relative).is_symlink():raise ValueError('Overlay already present; verify it or use a fresh staged rootfs')
    app=root/'opt/src';base=app/'seedsigner'
    guards=json.loads((draft/'payload/usr/lib/shieldsigner-lvgl/python/source-guards.json').read_text())
    for relative,expected in guards.items():
        path=base/relative
        if path.is_symlink() or app not in path.resolve().parents or digest(path)!=expected:raise ValueError('Staged application source differs: '+relative)
    for relative in plan['files']:
        if not relative.startswith('payload/'):raise ValueError('Unexpected payload prefix')
        inside(root,relative.removeprefix('payload/'))
    if plan.get('displayConfiguration') is not None:
        if plan['displayConfiguration']!='st7789_320x240' or plan['defaultFrontend']!='lvgl':raise ValueError('Unreviewed image display defaults')
        template=inside(root,'opt/src/settings.json')
        if template.exists():raise ValueError('Existing settings template requires review; refusing overwrite')
        source=inside(draft,'payload/opt/src/settings.json')
        if json.loads(source.read_text())!={'display_config':plan['displayConfiguration']}:raise ValueError('Display template differs from plan')
        if plan.get('panelProfile') is not None:
            if plan['panelProfile']!='hothmi_htm_tft028a16_spi':raise ValueError('Unreviewed physical panel profile')
            profile=inside(root,'usr/share/shieldsigner-lvgl/panel-profile.json')
            if profile.exists():raise ValueError('Existing physical panel profile requires review; refusing overwrite')
            source=inside(draft,'payload/usr/share/shieldsigner-lvgl/panel-profile.json')
            if json.loads(source.read_text())!={'profile':plan['panelProfile']}:raise ValueError('Physical panel profile differs from plan')
    return root,plan

def apply(root,draft):
    root,plan=preflight(root,draft)
    camera=camera_receipt(root);previous_camera=digest(inside(root,CAMERA_RECEIPT))
    # All compatibility/path/hash checks precede writes. A failed apply is an
    # invalid disposable staging root; it must never proceed to image packing.
    for relative,row in plan['files'].items():
        destination=inside(root,relative.removeprefix('payload/'));destination.parent.mkdir(parents=True,exist_ok=True)
        fd,temporary=tempfile.mkstemp(prefix='.lvgl-',dir=destination.parent)
        try:
            with os.fdopen(fd,'wb') as stream, (draft/relative).open('rb') as source:shutil.copyfileobj(source,stream)
            os.chmod(temporary,row['mode']);os.replace(temporary,destination)
        finally:
            if os.path.exists(temporary):os.unlink(temporary)
    receipt=inside(root,RECEIPT);receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps(dict(schema=1,previousCameraReceiptSha256=previous_camera,plan=plan,planSha256=digest(draft/'integration-plan.json'),offlineRootfsOnly=True,deviceInstalled=False,imageBuilt=False),sort_keys=True,indent=2)+'\n');receipt.chmod(0o644)
    # Extend the same startup receipt used by the camera/zram/LCD pre-mkfs
    # verifier, after checking its old contents; never relax acceptance rules.
    for relative,row in plan['files'].items():
        name=relative.removeprefix('payload/')
        camera['startupSha256'][name]=row['sha256'];camera['startupModes'][name]=row['mode']
    camera['startupSha256'][RECEIPT]=digest(receipt);camera['startupModes'][RECEIPT]=0o644
    camera['lvglOverlay']=dict(planSha256=digest(draft/'integration-plan.json'),defaultFrontend=plan['defaultFrontend'],previousCameraReceiptSha256=previous_camera)
    inside(root,CAMERA_RECEIPT).write_text(json.dumps(camera,indent=2)+'\n')
    return verify(root,draft)
def verify(root,draft):
    root=root_check(root);plan=load(draft)
    camera=camera_receipt(root)
    if camera.get('lvglOverlay',{}).get('planSha256')!=digest(draft/'integration-plan.json'):raise ValueError('Camera/LVGL overlay lineage mismatch')
    receipt=json.loads(inside(root,RECEIPT).read_text())
    if receipt['plan']!=plan or receipt['planSha256']!=digest(draft/'integration-plan.json'):raise ValueError('Installed draft provenance mismatch')
    for relative,row in plan['files'].items():
        path=inside(root,relative.removeprefix('payload/'))
        if digest(path)!=row['sha256'] or path.stat().st_size!=row['bytes'] or stat.S_IMODE(path.stat().st_mode)!=row['mode']:raise ValueError('Staged LVGL overlay changed: '+relative)
    return dict(verified=True,files=len(plan['files']),defaultFrontend=plan['defaultFrontend'],offlineRootfsOnly=True,deviceInstalled=False,imageBuilt=False)
def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--rootfs',type=Path);group.add_argument('--verify',type=Path);group.add_argument('--preflight',type=Path)
    parser.add_argument('--draft',type=Path,default=Path(__file__).resolve().parent);args=parser.parse_args()
    if args.preflight:
        preflight(args.preflight,args.draft);result=dict(preflightPassed=True,writesPerformed=False)
    else:result=verify(args.verify,args.draft) if args.verify else apply(args.rootfs,args.draft)
    print(json.dumps(result))
if __name__=='__main__':main()
