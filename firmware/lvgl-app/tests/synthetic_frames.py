"""Public synthetic NV12 source using the real native receiver; no disk images."""
import socket,struct,threading
import qrcode
from qrcode.util import QRData,MODE_8BIT_BYTE
from PIL import Image
from shieldsigner_lcd import FrameReceiver
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


def blank_source():
    source=Source([])
    pixels=bytes([255])*(640*480)+bytes([128])*(640*480//2)
    source.packets=[struct.pack('<8sIIII',b'SSNV12F1',640,480,1,len(pixels))+pixels]
    return source

class LazySource(Source):
    """Render one public fixture frame at a time, avoiding N full NV12 copies."""
    def __init__(self,payloads):
        self.payloads=list(payloads)
        if not self.payloads:raise ValueError('Synthetic source needs payloads')
        self.index=0;self.owner_exit_code=None;self.is_stopped=True
    def read(self):
        self.packets=Source([self.payloads[self.index%len(self.payloads)]]).packets
        try:return super().read()
        finally:self.packets.clear()
