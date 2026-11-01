"""Attach a verified offline draft to an existing camera bundle. No OS build."""
import argparse,ast,importlib.util,json,shutil,stat
from pathlib import Path
from image_stage import verify as verify_draft,HERE,ROOT
from build_manifest import sha256

def strip_helper(source):
    """Replace only the pinned SDK strip function; retain other frozen helpers."""
    reviewed=(ROOT/'scripts/camera-image-overlay.py').read_text()
    def span(text):
        node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='configure_sdk_strip')
        return node.lineno-1,node.end_lineno
    lines=source.splitlines(keepends=True);start,end=span(source)
    replacements=reviewed.splitlines(keepends=True);left,right=span(reviewed)
    old=''.join(lines[start:end]);new=''.join(replacements[left:right])
    # Only this reviewed extension of the prior function is accepted.
    old_tree=ast.dump(ast.parse(old),include_attributes=False)
    if old_tree!=ast.dump(ast.parse(new),include_attributes=False):
        # The supported predecessor must be exactly the frozen base helper.
        expected=(HERE/'patches/sdk-strip-base.py.txt').read_text()
        if old!=expected:raise ValueError('Frozen SDK strip helper differs from reviewed predecessor')
    return ''.join(lines[:start])+new+''.join(lines[end:])

def attach(camera,draft,output):
    spec=importlib.util.spec_from_file_location('camera_bundle_tools',ROOT/'scripts/prepare-camera-image.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    original=module.verify(camera);verify_draft(draft)
    plan=json.loads((draft/'integration-plan.json').read_text())
    if original.get('kernelProofPending') or original.get('lcdBackend')!='rust' or original.get('memoryProfile')!='zram16-lzo' or original.get('frontendBackend')!='rust':raise ValueError('LVGL draft requires a complete Rust LCD/frontend + zram16 camera bundle')
    if original.get('lvglOverlay') or any(name.startswith('lvgl-overlay/') for name in original['files']):raise ValueError('Camera bundle already has an LVGL layer')
    output.mkdir(parents=True,exist_ok=False)
    for relative in original['files']:
        destination=output/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(camera/relative,destination)
    files=dict(original['files'])
    helper=output/'image-overlay.py';base_helper_sha=sha256(helper)
    helper.write_text(strip_helper(helper.read_text()))
    files['image-overlay.py']=dict(sha256=sha256(helper),bytes=helper.stat().st_size,mode=stat.S_IMODE(helper.stat().st_mode))
    for source in sorted(draft.rglob('*')):
        if not source.is_file():continue
        if source.is_symlink():raise ValueError('Symlink in LVGL draft')
        relative='lvgl-overlay/'+str(source.relative_to(draft));destination=output/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
        files[relative]=dict(sha256=sha256(destination),bytes=destination.stat().st_size,mode=stat.S_IMODE(destination.stat().st_mode))
    manifest=dict(original,files=files,lvglOverlay=dict(planSha256=sha256(draft/'integration-plan.json'),defaultFrontend=plan['defaultFrontend'],language='en',smartcardWorkExcluded=True,qualified=False,sdkStripBaseHelperSha256=base_helper_sha,sdkStripHelperSha256=sha256(helper)))
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');module.verify(output)
    return dict(verified=True,files=len(files),defaultFrontend=plan['defaultFrontend'],imageBuilt=False,qualified=False)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--camera',required=True,type=Path);parser.add_argument('--draft',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    print(json.dumps(attach(args.camera.resolve(),args.draft.resolve(),args.output.resolve()),indent=2))
if __name__=='__main__':main()
