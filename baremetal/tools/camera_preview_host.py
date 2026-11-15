# SPDX-License-Identifier: MIT
"""Live DUT camera preview for aiming, plus on-device QR decode status.

RAM-only console use: streams downsampled luma (320x240) and the device's own
full-frame qr.decode() result over USB CDC; serves http://127.0.0.1:8765/.
Ctrl-C stops (sends ^C to the device, which stops the preview cleanly).
"""
import signal,argparse,binascii,glob,http.server,io,json,threading,time,zlib,struct
import serial
DEVICE=r'''
import camera,qr,ubinascii,time
{settings}
camera.start_preview()
try:
    n=0
    while True:
        f=camera.next_preview();y=bytes(f[:640*480])
        t=time.ticks_ms();d=qr.decode(y,640,480);dt=time.ticks_ms()-t
        small=bytearray(320*240);i=0
        for r in range(0,480,2):
            b=r*640
            for c in range(0,640,2):small[i]=y[b+c];i+=1
        print('@@F',n,dt,camera.settings().get('exposure_lines') if n%10==0 else '-',repr(d),ubinascii.hexlify(small).decode())
        n+=1
finally:
    camera.stop_preview()
'''
STATE={'png':b'','info':{}}
def png(w,h,gray):
    raw=b''.join(b'\0'+gray[r*w:(r+1)*w] for r in range(h))
    chunk=lambda t,d:struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,0,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
PAGE=b'''<html><body style="background:#111;color:#eee;font:16px monospace">
<button onclick="t('h')">flip H</button> <button onclick="t('v')">flip V</button> <span id=o></span><br><img id=i style="width:640px;height:480px;image-rendering:pixelated;border:1px solid #555"><pre id=t></pre>
<script>let f=JSON.parse(localStorage.f||'{"h":0,"v":0}');function a(){document.getElementById('i').style.transform='scale('+(f.h?-1:1)+','+(f.v?-1:1)+')';document.getElementById('o').textContent='H='+f.h+' V='+f.v;localStorage.f=JSON.stringify(f)}function t(k){f[k]^=1;a()}a();setInterval(async()=>{document.getElementById('i').src='/frame.png?'+Date.now();
let r=await fetch('/info');document.getElementById('t').textContent=JSON.stringify(await r.json(),null,1)},300)</script></body></html>'''
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_GET(self):
        body,ctype=(STATE['png'],'image/png') if self.path.startswith('/frame') else (json.dumps(STATE['info']).encode(),'application/json') if self.path.startswith('/info') else (PAGE,'text/html')
        self.send_response(200);self.send_header('Content-Type',ctype);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
def _stop(*_):raise KeyboardInterrupt
def main():
    # Background launches ignore SIGINT; SIGTERM/SIGINT both stop the device loop with ^C.
    signal.signal(signal.SIGTERM,_stop);signal.signal(signal.SIGINT,_stop)
    ap=argparse.ArgumentParser();ap.add_argument('--serial',default='rv1103-dut1');ap.add_argument('--port',type=int,default=8765);ap.add_argument('--ae-target',type=int);a=ap.parse_args()
    dev=[p for p in glob.glob('/dev/cu.usbmodem*') if a.serial.replace('-','_') in p][0]
    threading.Thread(target=http.server.ThreadingHTTPServer(('127.0.0.1',a.port),H).serve_forever,daemon=True).start()
    script=DEVICE.replace('{settings}','camera.settings(ae_target=%d)'%a.ae_target if a.ae_target else '')
    s=serial.Serial(dev,115200,timeout=0.2)
    s.write(b'\x03\x02\r');time.sleep(0.3);s.reset_input_buffer();s.write(b'\x05');time.sleep(0.2)
    for i in range(0,len(script),128):s.write(script[i:i+128].encode());time.sleep(0.01)
    s.write(b'\x04');print('preview: http://127.0.0.1:%d/'%a.port,flush=True)
    buf=b'';decoded=[]
    try:
        while True:
            buf+=s.read(65536)
            while b'\n' in buf:
                line,buf=buf.split(b'\n',1);line=line.strip()
                if line.startswith(b'@@F '):
                    _,n,dt,exp,rest=line.split(b' ',4);d,hexdata=rest.rsplit(b' ',1)
                    try:STATE['png']=png(320,240,binascii.unhexlify(hexdata))
                    except Exception:continue
                    d=d.decode()
                    if d!='None':decoded.append(d);print('DECODED',n.decode(),d,flush=True)
                    STATE['info']={'frame':int(n),'decode_ms':int(dt),'exposure':exp.decode(),'decode':d,'decoded_total':len(decoded),'last_decoded':decoded[-1] if decoded else None}
                elif line and not line.startswith(b'==='):print('dev:',line.decode(errors='replace')[:200],flush=True)
    except KeyboardInterrupt:pass
    finally:s.write(b'\x03');time.sleep(0.5);s.close()
if __name__=='__main__':main()
