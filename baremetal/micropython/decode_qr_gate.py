# SPDX-License-Identifier: MIT
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
assert invalid.add_data('p1of2 {"label":')==1
assert invalid.add_data('p2of2 }')==5
assert invalid.get_wallet_descriptor() is None
for payload in ['ur:bytes/abcd','unknown public text','cHNidP8=']:
    try:DecodeQR().add_data(payload)
    except FeatureUnavailable:pass
    else:raise AssertionError('missing model dependency hidden')
assert base64.b64encode(b'')==b''
assert base64.b64decode(b'')==b''
assert base64.b64encode(b'f')==b'Zg=='
assert base64.b64decode(b'Zg==')==b'f'
assert base64.b64encode(b'foobar')==b'Zm9vYmFy'
assert base64.b64decode(b'Zm9vYmFy')==b'foobar'
assert base64.b64encode(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f')==b'AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8='
assert base64.b64decode(b'AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=')==b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
rows=('0000000000000000000000000000000000000', '0000000000000000000000000000000000000', '0000000000000000000000000000000000000', '0000000000000000000000000000000000000', '0000111111100011000110100011111110000', '0000100000101011011010100010000010000', '0000101110101001110100001010111010000', '0000101110101111100011011010111010000', '0000101110100110100110111010111010000', '0000100000100110000101100010000010000', '0000111111101010101010101011111110000', '0000000000001110101110010000000000000', '0000100000101110000011100110011100000', '0000111010000011110010110000111100000', '0000001001101011011110101101100000000', '0000010001010110110000101000110000000', '0000001001101000110110010010010010000', '0000101010001000000011111010101110000', '0000000011101100100000000010010000000', '0000100100001000000100101001111110000', '0000010000111111100001001001001000000', '0000111111011010111000111011111010000', '0000110110100101100111110111010010000', '0000100011001011010110001100010110000', '0000101011110110101001011111101100000', '0000000000001111101101111000111100000', '0000111111100000100111011010111000000', '0000100000100011101010101000110000000', '0000101110100111111110011111100110000', '0000101110100101101110110101000010000', '0000101110100101101111010110111100000', '0000100000100001110000000100001010000', '0000111111101000001011110000011000000', '0000000000000000000000000000000000000', '0000000000000000000000000000000000000', '0000000000000000000000000000000000000', '0000000000000000000000000000000000000')
image=bytearray(bytes([255])*(640*480))
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
