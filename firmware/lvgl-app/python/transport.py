"""Bounded private IPC to the standalone native LVGL host.

Pixel sink runs on the reader thread; it must not reenter this client. No request,
result text, seed words, QR bytes, or camera frames are logged or written to disk.
"""
import json
import queue
import struct
import subprocess
import threading

class NativeHost:
    def __init__(self, binary, pixel_sink, timeout=15, *, width=240,height=240,frame_sink=None,frame_reset=None):
        if type(width) is not int or type(height) is not int or (width,height) not in ((240,240),(320,240)):raise ValueError('Unsupported LVGL geometry')
        self.width=width;self.height=height
        self.screensaver_active=False
        self.timeout=timeout
        self.pixel_sink=pixel_sink
        self.frame_sink=frame_sink if frame_sink is not None else getattr(getattr(pixel_sink,'__self__',None),'frame_complete',None)
        if self.frame_sink is not None and not callable(self.frame_sink):raise TypeError('Frame sink must be callable')
        self.frame_reset=frame_reset if frame_reset is not None else getattr(getattr(pixel_sink,'__self__',None),'frame_reset',None)
        if self.frame_reset is not None and not callable(self.frame_reset):raise TypeError('Frame reset must be callable')
        self.events=queue.Queue(maxsize=64)
        self.error=None
        self._closed=False
        self._write_lock=threading.Lock()
        command=[str(binary)] if (width,height)==(240,240) else [str(binary),'--width',str(width),'--height',str(height)]
        self.child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,bufsize=0)
        self.reader=threading.Thread(target=self._read_loop,name='lvgl-output',daemon=True)
        self.reader.start()
        try:
            event=self.next_event()
            if event != {'event':'ready','protocol':1}:
                raise RuntimeError('Unexpected LVGL host handshake')
        except BaseException:
            self.close()
            raise

    def _exact(self,size):
        data=bytearray()
        while len(data)<size:
            chunk=self.child.stdout.read(size-len(data))
            if not chunk: raise EOFError('LVGL host exited')
            data.extend(chunk)
        return bytes(data)

    def _read_loop(self):
        try:
            while True:
                magic,version,kind,size=struct.unpack('<2sBBI',self._exact(8))
                if magic!=b'SL' or version!=1 or kind not in (1,2): raise ValueError('Invalid LVGL packet')
                if size>1024*1024 or (kind==1 and not 8<=size<=8+self.width*20*2): raise ValueError('Invalid LVGL packet size')
                body=self._exact(size)
                if kind==1:
                    area=struct.unpack_from('<4H',body)
                    x1,y1,x2,y2=area
                    if not (x1<=x2<self.width and y1<=y2<self.height) or len(body)!=8+(x2-x1+1)*(y2-y1+1)*2:
                        raise ValueError('Invalid LVGL rectangle')
                    self.pixel_sink(area,body[8:])
                else:
                    event=json.loads(body)
                    if event.get('event')=='frame_complete':
                        if event!={'event':'frame_complete'}:raise ValueError('Invalid frame completion')
                        if self.frame_sink is not None:self.frame_sink()
                        continue
                    if event.get('event') in ('overlay_changed','overlay_state'):
                        if type(event.get('screensaver')) is not bool:raise ValueError('Invalid overlay state')
                        self.screensaver_active=event['screensaver']
                    if event.get('event')!='overlay_changed':self.events.put_nowait(event)
        except BaseException as exc:
            if not self._closed:self.error=exc

    def send(self,op,**kwargs):
        raw=json.dumps(dict(op=op,**kwargs),ensure_ascii=False,separators=(',',':')).encode()+b'\n'
        if len(raw)>1024*1024: raise ValueError('LVGL request exceeds limit')
        with self._write_lock:
            if self._closed: raise RuntimeError('LVGL host closed')
            if self.error: raise RuntimeError('LVGL host failed') from self.error
            view=memoryview(raw)
            while view:
                n=self.child.stdin.write(view)
                if not n:raise BrokenPipeError('LVGL host pipe closed')
                view=view[n:]

    def send_preview(self,width,height,pixels,percent=0,status=0):
        if type(width) is not int or type(height) is not int or (width,height) not in ((240,180),(180,240)) or len(pixels)!=240*180*3:
            raise ValueError('Invalid bounded RGB preview')
        if type(percent) is not int or not 0<=percent<=100 or type(status) is not int or not 0<=status<=3:raise ValueError('Invalid preview status')
        header=json.dumps(dict(op='preview',width=width,height=height,bytes=len(pixels),percent=percent,status=status),separators=(',',':')).encode()+b'\n'
        with self._write_lock:
            if self._closed or self.error:raise RuntimeError('LVGL host unavailable')
            for data in (header,pixels):
                view=memoryview(data)
                while view:
                    count=self.child.stdin.write(view)
                    if not count:raise BrokenPipeError('LVGL preview pipe closed')
                    view=view[count:]

    def next_event(self,timeout=None):
        import time
        end=time.monotonic()+(self.timeout if timeout is None else timeout)
        while True:
            if self.error:raise RuntimeError('LVGL host failed') from self.error
            left=end-time.monotonic()
            if left<=0:raise TimeoutError('LVGL event deadline expired')
            try:return self.events.get(timeout=min(left,.05))
            except queue.Empty:pass

    def close(self):
        if self._closed:return
        self._closed=True
        self.child.terminate()
        try:self.child.wait(timeout=2)
        except subprocess.TimeoutExpired:self.child.kill();self.child.wait(timeout=2)
        self.reader.join(timeout=2)
        for pipe in (self.child.stdin,self.child.stdout):pipe.close()
        if self.reader.is_alive():raise TimeoutError('LVGL output thread did not stop')
        if self.frame_reset is not None:self.frame_reset()
