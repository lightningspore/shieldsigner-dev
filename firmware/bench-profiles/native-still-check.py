#!/usr/bin/env python3
"""Actual camera RGB still API check. Stop other apps/owners before running.

No GPIO/display initialization, camera images or decoded QR payloads are saved.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--runtime-python',type=Path,required=True)
p.add_argument('--app-root',type=Path,default=Path('/opt/src'))
p.add_argument('--config',type=Path,default=Path('/usr/lib/shieldsigner-camera/owner.json'))
p.add_argument('--reader',type=Path,default=Path('/usr/lib/shieldsigner-camera/shieldsigner-qr-reader'))
p.add_argument('--report',type=Path,required=True)
a=p.parse_args()
if a.report.exists():p.error('Choose a new report path')
sys.path[:0]=[str(a.runtime_python.resolve()),str(a.app_root.resolve()),'/usr/lib/shieldsigner-camera/python']
os.environ.update(SHIELDSIGNER_SMALL_RAM='1',SHIELDSIGNER_FRONTEND_BACKEND='rust',
                  SHIELDSIGNER_CAMERA_CONFIG=str(a.config.resolve()),SHIELDSIGNER_QR_READER=str(a.reader.resolve()))
from shieldsigner_integration import install_camera_backend
import shieldsigner_lcd
module=install_camera_backend(a.app_root);camera=module.Camera.get_instance()
if not camera._is_luckfox_profile(camera._runtime_profile):raise RuntimeError('Expected reviewed Luckfox profile')
report={'kind':'actual-native-RGB-still-check','passed':False,'imageSaved':False,
        'extensionSha256':hashlib.sha256(Path(shieldsigner_lcd.__file__).read_bytes()).hexdigest()}
try:
    camera.start_single_frame_mode(resolution=(640,480));stream=camera._capture
    assert stream.transport=='rgb' and stream.backend_info['frontend']=='rust'
    images=0;deadline=time.monotonic()+15;shape=None
    while images<3 and time.monotonic()<deadline:
        image=camera.capture_frame()
        if image is None:continue
        assert image.mode=='RGB' and set(image.size)=={480,640}
        assert len(image.getextrema())==3
        shape=list(image.size);images+=1
    assert images==3
    camera.stop_single_frame_mode()
    assert camera._capture is None and stream.owner_exit_code==0
    report.update(passed=True,samples=images,returnedMode='RGB',returnedSize=shape,
                  ownerExitCode=stream.owner_exit_code,captureReferenceCleared=True,
                  runtimeProfile=camera._runtime_profile)
finally:
    if camera._capture is not None:camera.stop_single_frame_mode()
    module.__shieldsigner_qr_client__.close()
    a.report.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
