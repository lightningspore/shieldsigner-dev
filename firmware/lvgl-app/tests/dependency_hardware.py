"""Fresh-process dependency closure and real native binary-QR compatibility.

Public generated pixels only. Run after interactive testing, never concurrently
with the wallet app. This does not measure a production memory improvement.
"""
import json,sys
from pathlib import Path
sys.path[:0]=['/opt/src','/usr/lib/shieldsigner-camera/python']
from dependency_policy import install
restore=install('/opt/src',Path(__file__).parent/'source-guards.json')
try:
    from seedsigner.helpers.qr import QR
    QR()
    assert 'qrcode' not in sys.modules and 'qrcode.image.styledpil' not in sys.modules
    from seedsigner.models.encode_qr import BaseQrEncoder
    from seedsigner.models.decode_qr import DecodeQR
    legacy=('pyzbar','cv2','numpy','qrcode.image.styledpil')
    assert not any(name==prefix or name.startswith(prefix+'.') for name in sys.modules for prefix in legacy)
    assert DecodeQR.is_qr_scanner_available()
    import qrcode
    checks=0
    for payload in (b'public QR',b'\0\xffbinary\0',bytes(range(256))):
        qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=4,border=4)
        qr.add_data(payload,optimize=0);qr.make(fit=True)
        image=qr.make_image().convert('RGB')
        try:assert DecodeQR.extract_qr_data(image,is_binary=True)==payload
        finally:image.close()
        checks+=1
    assert DecodeQR.extract_qr_data(None) is None
    assert not any(name==prefix or name.startswith(prefix+'.') for name in sys.modules for prefix in legacy)
    print(json.dumps(dict(passed=True,publicBinaryQRCases=checks,originalPayloadParser=True,legacyBackendModulesLoaded=False,legacyStyledRendererLoaded=False,installedFilesModified=False,memorySavingsMeasured=False)),flush=True)
finally:restore()
