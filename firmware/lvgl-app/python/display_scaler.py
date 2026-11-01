"""ST7735 presentation: retained 240-square RGB565 canvas, full-frame LANCZOS."""
import array
class FrameScaler:
    def __init__(self):
        self.buffer=bytearray(240*240*2);self.dirty=False
    def update(self,area,raw):
        x1,y1,x2,y2=area
        if any(type(value) is not int for value in area) or not (0<=x1<=x2<240 and 0<=y1<=y2<240):raise ValueError('Invalid scaling rectangle')
        stride=(x2-x1+1)*2
        if len(raw)!=stride*(y2-y1+1):raise ValueError('Invalid scaling pixel size')
        for row,y in enumerate(range(y1,y2+1)):
            self.buffer[(y*240+x1)*2:(y*240+x2+1)*2]=raw[row*stride:(row+1)*stride]
        self.dirty=True
    def complete(self):
        if not self.dirty:return None
        from PIL import Image
        # Native SPI packets are big-endian RGB565; Pillow's BGR;16 decoder
        # expects little-endian words. byteswap reverses each byte pair.
        words=array.array('H',self.buffer);words.byteswap()
        image=Image.frombytes('RGB',(240,240),words.tobytes(),'raw','BGR;16')
        try:result=image.resize((128,128),Image.Resampling.LANCZOS)
        finally:image.close()
        self.dirty=False
        return result
    def wipe(self):
        self.buffer[:]=b'\0'*len(self.buffer);self.dirty=False
