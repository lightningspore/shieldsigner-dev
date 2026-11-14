# SPDX-License-Identifier: MIT
"""Public native pixel→original DecodeQR model fixtures."""
import base64
from pathlib import Path
import qrcode
root=Path(__file__).resolve().parents[1]
payload=b'settings::v1 name=public lang=en'
q=qrcode.QRCode(border=4,error_correction=qrcode.constants.ERROR_CORRECT_M);q.add_data(payload,optimize=0);q.make(fit=True)
rows=tuple(''.join('1' if v else '0' for v in row) for row in q.get_matrix())
code='''# SPDX-License-Identifier: MIT
# Generated public fixtures; source model is unchanged except documented boundaries.
from seedsigner_port.decode_qr import DecodeQR,DecodeQRStatus
from seedsigner_port.decode_platform import FeatureUnavailable
import camera
import base64
import gc
assert DecodeQR.is_qr_scanner_available()
assert DecodeQR.is_base64('Zm9v')
assert not DecodeQR.is_base64('settings::public')
assert DecodeQR().add_image(None)==DecodeQRStatus.FALSE
for mode,getter in [('is_text','get_text'),('is_passphrase','get_passphrase')]:
    for payload in [b'public', 'é🙂 public'.encode(), b'']:
        d=DecodeQR(**{mode:True})
        assert d.add_data(payload)==DecodeQRStatus.COMPLETE
        assert d.is_complete and d.get_percent_complete()==100
        assert getattr(d,getter)()==payload.decode()
    d=DecodeQR(**{mode:True})
    assert d.add_data(bytes([255]))==DecodeQRStatus.INVALID
    assert d.is_nonUTF8 and not d.is_complete
settings=b'settings::v1 name=public lang=en'
d=DecodeQR()
assert d.add_data(settings)==DecodeQRStatus.COMPLETE
assert d.is_settings and d.get_settings_data()==settings.decode()
assert d.get_percent_complete()==100
parts=['p2of2 "descriptor":"public fixture"}','p2of2 "descriptor":"public fixture"}','p1of2 {"label":"test",']
d=DecodeQR()
assert [d.add_data(p) for p in parts]==[1,2,3]
assert d.is_complete and d.get_wallet_descriptor()=='public fixture'
invalid=DecodeQR()
assert invalid.add_data('p1of2 {\"label\":')==1
assert invalid.add_data('p2of2 }')==5
assert invalid.get_wallet_descriptor() is None
for payload in ['ur:bytes/abcd','unknown public text','cHNidP8=']:
    try:DecodeQR().add_data(payload)
    except FeatureUnavailable:pass
    else:raise AssertionError('missing model dependency hidden')
'''
for value in [b'',b'f',b'foobar',bytes(range(32))]:
 code+='assert base64.b64encode('+repr(value)+')=='+repr(base64.b64encode(value))+'\n'
 code+='assert base64.b64decode('+repr(base64.b64encode(value))+')=='+repr(value)+'\n'
code+='rows='+repr(rows)+'''\nimage=bytearray(bytes([255])*(640*480))
width=len(rows)*6
left=(640-width)//2
top=(480-width)//2
for y,row in enumerate(rows):
    line=b''.join(bytes([0 if bit=='1' else 255])*6 for bit in row)
    for j in range(6):
        offset=(top+y*6+j)*640+left
        image[offset:offset+width]=line
for i in range(5):
    d=DecodeQR()
    assert d.add_image(image)==DecodeQRStatus.COMPLETE
    assert d.is_settings and d.get_settings_data()==settings.decode()
    if i==0:baseline=camera.settings()['rust_heap_bytes']
    assert camera.settings()['rust_heap_bytes']==baseline
    del d
    gc.collect()
print('@@PASS original-decode-qr-native-pixels')
from seedsigner_port.scan_screen import NativeScanScreen,CooperativePreview
class Source:
    def __init__(self,frames):
        self.frames=frames
        self.index=0
        self.active=False
        self.stops=0
    def start_video_stream_mode(self):self.active=True
    def read_video_stream(self):
        if self.index>=len(self.frames):raise RuntimeError('fixture source exhausted')
        frame=self.frames[self.index]
        self.index+=1
        return frame
    def stop_video_stream_mode(self):
        if self.active:self.active=False;self.stops+=1
class Input:
    def __init__(self,back=False):self.back=back
    def reset_input(self):pass
    def check_for_low(self,key):return self.back
blank=bytes([255])*(640*480)
for mode in ('complete','back','dependency-error'):
    source=Source([blank,image] if mode=='complete' else [blank] if mode=='back' else [image])
    preview=CooperativePreview(lambda frame:None)
    decoder=DecodeQR(is_encryptionkey=mode=='dependency-error')
    screen=NativeScanScreen(decoder,camera=source,preview=preview,buttons=Input(mode=='back'))
    try:
        result=screen.run()
        assert mode!='dependency-error'
        if mode=='complete':
            assert result is None and decoder.is_complete and decoder.get_settings_data()==settings.decode()
            assert preview.frames==2
        else:
            assert result is False and not decoder.is_complete and preview.frames==1
    except FeatureUnavailable:
        assert mode=='dependency-error'
    assert not source.active and source.stops==1
    del screen,source,preview,decoder
    gc.collect()
    assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS original-scan-loop-native-qr-complete-back-error')
'''
(root/'micropython/decode_qr_gate.py').write_text(code)
