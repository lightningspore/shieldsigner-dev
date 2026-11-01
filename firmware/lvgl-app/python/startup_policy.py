"""Reuse the working image's guarded small-RAM policy before Controller startup.

No copied wallet routing or crypto. This is a shared dependency on the existing
camera integration module, verified before import and again by its own guards.
"""
import hashlib,importlib,sys,os
from pathlib import Path
INTEGRATION_SHA256='1fe021f06ccbc5f8b428bf9b4de8df3722c60d3a280a0a23354a7d60d0a69dd9'

def install(app_root,camera_python_root):
    root=Path(camera_python_root).resolve();path=root/'shieldsigner_integration.py'
    digest=hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda:source.read(65536),b''):digest.update(chunk)
    if digest.hexdigest()!=INTEGRATION_SHA256:raise ValueError('Unreviewed shared startup integration')
    sys.path.insert(0,str(root))
    module=importlib.import_module('shieldsigner_integration')
    if Path(module.__file__).resolve()!=path:raise RuntimeError('Shared startup integration imported from wrong path')
    profile=module.install_small_ram_profile(app_root)
    scan=module.install_lazy_scan_views(app_root)
    # Camera transport/log bounds are selected separately from Controller imports.
    # Set both parts of the explicit small-RAM policy before any camera starts.
    os.environ['SHIELDSIGNER_SMALL_RAM']='1'
    return dict(integrationSha256=INTEGRATION_SHA256,smallRam=profile,lazyScan=scan,cameraSmallRamEnabled=True)
