"""Run the complete public multisig Controller fixture under the LVGL import policy."""
import json,runpy,sys
from pathlib import Path
sys.path[:0]=['/opt/src','/usr/lib/shieldsigner-camera/python']
from dependency_policy import install
restore=install('/opt/src',Path(__file__).parent/'source-guards.json')
try:
    runpy.run_path(str(Path(__file__).with_name('controller_multisig_flow.py')),run_name='__main__')
    legacy=('pyzbar','cv2','numpy','qrcode.image.styledpil')
    loaded=any(name==prefix or name.startswith(prefix+'.') for name in sys.modules for prefix in legacy)
    assert not loaded
    from seedsigner.models.decode_qr import DecodeQR
    assert DecodeQR.is_qr_scanner_available()
    print(json.dumps(dict(event='diagnostic-dependency-state',legacyBackendsLoaded=loaded,nativeScannerAvailable=True)),flush=True)
finally:restore()
