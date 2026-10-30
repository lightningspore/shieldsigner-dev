"""Packed ARM frontend proof using public synthetic pixels; no camera or GPIO."""
import argparse
import json
import os
from pathlib import Path
import socket
import struct
import sys
import threading

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('root',type=Path);p.add_argument('reader',type=Path)
a=p.parse_args();root=a.root.resolve()
sys.path[:0]=[str(root/'usr/lib/shieldsigner-camera/python'),str(root/'opt/src')]
os.environ['SHIELDSIGNER_FRONTEND_BACKEND']='rust'
os.environ['SHIELDSIGNER_QR_READER']=str(a.reader.resolve())
from PIL import Image
import qrcode
from qrcode.util import QRData,MODE_8BIT_BYTE
from shieldsigner_lcd import FrameReceiver,PreviewRenderer
from shieldsigner_integration import install_camera_backend,install_small_ram_profile,install_lazy_scan_views
module=install_camera_backend(root/'opt/src')
profile=install_small_ram_profile(root/'opt/src');install_lazy_scan_views(root/'opt/src')
assert module.__shieldsigner_camera_patch__['frontend']=='rust'
assert profile['startupRoutes']['smartcardMenuIdentityPreserved']
from seedsigner.models.decode_qr import DecodeQR
payload=bytes(range(256))
qr=qrcode.QRCode(box_size=4,border=4,error_correction=qrcode.constants.ERROR_CORRECT_M)
qr.add_data(QRData(payload,mode=MODE_8BIT_BYTE));qr.make(fit=True)
image=Image.new('L',(640,480),255);code=qr.make_image().convert('L')
assert code.width<=640 and code.height<=480
image.paste(code,((640-code.width)//2,(480-code.height)//2))
pixels=image.tobytes()+bytes([128])*(640*480//2)
left,right=socket.socketpair();receiver=FrameReceiver(left.fileno(),framerate=120)
packet=struct.pack('<8sIIII',b'SSNV12F1',640,480,1,len(pixels))+pixels
sender=threading.Thread(target=right.sendall,args=(packet,));sender.start()
client=module.__shieldsigner_qr_client__
try:
    frame=receiver.read(0,1);sender.join();assert frame is not None
    assert DecodeQR.extract_qr_data(frame,is_binary=True)==payload
    renderer=PreviewRenderer()
    for angle in (0,90,180,270):
        width,height,actual=renderer.render_frame(frame,angle)
        expected=image.resize((240,180),Image.Resampling.NEAREST).convert('RGB').rotate(angle,expand=True)
        assert (width,height)==expected.size and actual==expected.tobytes()
finally:
    receiver.close();left.close();right.close();client.close()
assert client.stats['errors']==0 and client.stats['lastExitCode']==0
print(json.dumps({'passed':True,'nativeSocketReception':True,'binary256ValuesExact':True,
 'fourPreviewRotationsMatchPackedPillow':True,'installedDecodeQr':True,'guardedStartupRoutesInstalled':True,
 'nativeWorkerClosed':True,'hardwareTouched':False,'imageBootQualified':False}))
