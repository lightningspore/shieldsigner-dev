"""Public synthetic camera frames through real native RX/ZXing/DecodeQR/LVGL.

Only the physical camera source is injected. Full NV12 frames traverse the actual
native receiver, full-resolution QR worker, original decoder, and native preview.
No payloads or images are written to the receipt. Not optical qualification.
"""
import json
import os
from pathlib import Path
import socket
import struct
import sys
import threading
import time
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parent),'/usr/lib/shieldsigner-camera/python','/opt/src']
os.environ['SHIELDSIGNER_SMALL_RAM']='1'
import qrcode
from qrcode.util import QRData,MODE_8BIT_BYTE
from PIL import Image
from shieldsigner_lcd import FrameReceiver
from runtime import Runtime,install_view_dispatch
from seedsigner.gui.screens.scan_screens import ScanScreen
from seedsigner.models.decode_qr import DecodeQR,DecodeQRStatus
from seedsigner.helpers.ur2.ur import UR
from seedsigner.helpers.ur2.ur_encoder import UREncoder
from urtypes.crypto import PSBT as UR_PSBT
from embit import bip39,psbt,transaction,script

class Source:
    def __init__(self,payloads):
        self.packets=[]
        for i,payload in enumerate(payloads):
            code=qrcode.QRCode(box_size=4,border=4,error_correction=qrcode.constants.ERROR_CORRECT_M)
            code.add_data(QRData(payload,mode=MODE_8BIT_BYTE));code.make(fit=True)
            image=code.make_image().convert('L')
            frame=Image.new('L',(640,480),255);frame.paste(image,((640-image.width)//2,(480-image.height)//2))
            pixels=frame.tobytes()+bytes([128])*(640*480//2)
            self.packets.append(struct.pack('<8sIIII',b'SSNV12F1',640,480,i+1,len(pixels))+pixels)
        self.index=0;self.owner_exit_code=None;self.is_stopped=True
    def start(self):
        self.left,self.right=socket.socketpair();self.receiver=FrameReceiver(self.left.fileno(),framerate=120);self.is_stopped=False;return self
    def read(self):
        sender=threading.Thread(target=self.right.sendall,args=(self.packets[self.index%len(self.packets)],));sender.start()
        try:frame=self.receiver.read(0,1)
        finally:sender.join(timeout=2)
        assert not sender.is_alive() and frame is not None
        self.index+=1;return frame
    def stop(self):
        self.receiver.close();self.left.close();self.right.close();self.is_stopped=True

class Decoder(DecodeQR):
    def __init__(self,expected,**kwargs):
        super().__init__(**kwargs);self.expected=expected;self.received=[];self.statuses=[];self.reference=DecodeQR(**kwargs)
    def add_data(self,data):
        assert data==self.expected[len(self.received)%len(self.expected)],'QR bytes changed'
        self.received.append(data)
        actual=super().add_data(data);assert actual==self.reference.add_data(data)
        self.statuses.append(int(actual));return actual

hardware=None
if '--display' in sys.argv:
    from luckfox import LuckfoxHardware
    hardware=LuckfoxHardware()
rectangles=0
def pixels(area,data):
    global rectangles
    rectangles+=1
    if hardware is not None:hardware.pixels(area,data)
started=None
def buttons():
    global started
    if started is None:started=time.monotonic()
    return {'KEY_LEFT'} if time.monotonic()-started>15 else set()
runtime=Runtime(sys.argv[1],pixels,buttons)
restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
results=[]
try:
    def run(name,payloads,options=None):
        global started
        decoder=Decoder(payloads,**(options or {}));source=Source(payloads);started=None
        with patch('shieldsigner_native_stream.NativeVideoStream',lambda **kwargs:source):
            outcome=ScanScreen(decoder=decoder,instructions_text='Public QR fixture').display()
        assert outcome is None and source.is_stopped
        assert runtime.camera_stats['qr']['errors']==0 and runtime.camera_stats['qr']['lastExitCode']==0
        results.append(dict(name=name,frames=len(decoder.received),byteExact=True,originalDecoderStatusParity=True,complete=bool(decoder.is_complete),statuses=decoder.statuses,cleanStop=True))
        return decoder
    for length in (16,32):
        data=bytes(range(length));decoder=run('compact-seed-'+str(length),[data])
        assert decoder.get_seed_phrase()==bip39.mnemonic_from_bytes(data).split()
    run('all-256-byte-values',[bytes(range(256))])
    run('bitcoin-address',[b'1BoatSLRHtKNngkdXEeobR76b53LETtpyT'])
    text='  public café e\u0301  '
    decoder=run('unicode-passphrase',[text.encode()],dict(is_passphrase=True))
    assert decoder.get_passphrase()==text
    tx=transaction.Transaction(vin=[transaction.TransactionInput(bytes(32),0)],vout=[transaction.TransactionOutput(0,script.Script(b'\x6a\x4c\xc8'+bytes(range(200))))])
    payload=psbt.PSBT(tx).serialize()
    encoder=UREncoder(UR('crypto-psbt',UR_PSBT(payload).to_cbor()),max_fragment_len=60)
    fragments=[]
    for _ in range(20):
        fragments.append(encoder.next_part().encode())
        if encoder.is_complete():break
    assert len(fragments)>1
    parts=list(reversed(fragments))
    decoder=run('animated-ur-reverse-duplicate',[parts[0],*parts])
    assert decoder.get_data_psbt()==payload
    assert len(decoder.received)>len(fragments) and decoder.received[0]==decoder.received[1]
    print(json.dumps(dict(passed=True,cases=results,rectangles=rectangles,physicalCamera=False,physicalDisplay=hardware is not None,nativeReceiverQrPreview=True,opticalQualified=False)))
finally:
    restore();runtime.close()
    if hardware is not None:hardware.close()
