# SPDX-License-Identifier: MIT
"""Host-controlled QR target display for optical scan tests (PUBLIC data only).

  qr_screen.py serve [--display-x -1440 --display-w 1440 --display-h 900]
  qr_screen.py text 'bc1q...'                      static QR
  qr_screen.py ur-psbt --hex 70736274ff... [--fragment 60 --fps 6]
  qr_screen.py frames a b c --fps 4                arbitrary animated frames
  qr_screen.py blank | status

`serve` shows a full-height page in Safari on the second display, and keeps
running as an HTTP control server on 127.0.0.1:8766. Other commands POST to it,
and tests can import set_text/set_frames/set_ur_psbt/blank. UR parts use the
upstream SeedSigner ur2 encoder (dist sources), upper-cased like SeedSigner so
the QR uses alphanumeric mode. Never put private keys or seeds of value here.
"""
import argparse,io,json,subprocess,sys,threading,time,urllib.request
from pathlib import Path
import http.server
ROOT=Path(__file__).resolve().parents[2]
URL='http://127.0.0.1:8766'
STATE={'version':0,'frames':[],'fps':0,'label':'blank','png':{},'size':94,'y':0}
PAGE=b'''<html><body style="margin:0;background:#fff;overflow:hidden;font:14px monospace">
<div style="display:flex;align-items:center;justify-content:center;height:100vh"><img id=q style="height:94vh;image-rendering:pixelated"></div>
<div id=l style="position:fixed;bottom:2px;left:6px;color:#999"></div>
<script>
let ver=-1,imgs=[],idx=0,timer=null;
async function poll(){try{let s=await (await fetch('/state')).json();if(s.version!==ver){ver=s.version;load(s)}}catch(e){}}
function load(s){clearInterval(timer);imgs=[];idx=0;let q=document.getElementById('q');
 for(let i=0;i<s.count;i++){let im=new Image();im.src='/f/'+s.version+'/'+i+'.png';imgs.push(im)}
 document.getElementById('l').textContent=s.label;document.getElementById('q').style.height=s.size+'vh';document.getElementById('q').style.transform='translateY('+s.y+'vh)';
 if(!s.count){q.style.visibility='hidden';return}q.style.visibility='visible';q.src=imgs[0].src;
 if(s.count>1&&s.fps>0)timer=setInterval(()=>{idx=(idx+1)%imgs.length;q.src=imgs[idx].src;document.getElementById('l').textContent=s.label+'  '+(idx+1)+'/'+s.count},1000/s.fps)}
setInterval(poll,250);poll();
</script></body></html>'''

def _png(text):
    import segno
    out=io.BytesIO();segno.make(text,error='l',boost_error=False).save(out,kind='png',scale=8,border=2);return out.getvalue()

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def _send(self,body,ctype):
        self.send_response(200);self.send_header('Content-Type',ctype);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if self.path=='/state':
            self._send(json.dumps({'version':STATE['version'],'count':len(STATE['frames']),'fps':STATE['fps'],'label':STATE['label'],'size':STATE['size'],'y':STATE['y']}).encode(),'application/json')
        elif self.path.startswith('/f/'):
            _,_,ver,name=self.path.split('/');i=int(name.split('.')[0])
            if int(ver)!=STATE['version'] or i>=len(STATE['frames']):self.send_error(404);return
            key=(STATE['version'],i)
            if key not in STATE['png']:STATE['png'][key]=_png(STATE['frames'][i])
            self._send(STATE['png'][key],'image/png')
        else:self._send(PAGE,'text/html')
    def do_POST(self):
        req=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        frames=[str(f) for f in req.get('frames',[])]
        STATE.update(size=float(req.get('size',STATE['size'])),y=float(req.get('y',STATE['y'])),frames=frames,fps=float(req.get('fps',0)),label=str(req.get('label','')),png={},version=STATE['version']+1)
        for i in range(len(frames)):STATE['png'][(STATE['version'],i)]=_png(frames[i]) # pre-render: page timing is exact
        self._send(json.dumps({'version':STATE['version'],'count':len(frames)}).encode(),'application/json')

def serve(a):
    server=http.server.ThreadingHTTPServer(('127.0.0.1',8766),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    subprocess.run(['osascript','-e','tell application "Safari" to make new document with properties {URL:"%s/"}'%URL,
                    '-e','tell application "Safari" to set bounds of front window to {%d, 0, %d, %d}'%(a.display_x,a.display_x+a.display_w,a.display_h)],check=False)
    print('qr screen serving',URL,flush=True)
    try:
        while True:time.sleep(3600)
    except KeyboardInterrupt:pass

SIZE=None;Y=None
def _post(frames,fps=0,label=''):
    req={'frames':frames,'fps':fps,'label':label}
    if SIZE is not None:req['size']=SIZE
    if Y is not None:req['y']=Y
    data=json.dumps(req).encode()
    with urllib.request.urlopen(urllib.request.Request(URL+'/set',data=data,headers={'Content-Type':'application/json'}),timeout=60) as r:return json.loads(r.read())
def set_text(text,label=None):return _post([text],0,label or text[:60])
def set_frames(frames,fps=4,label='animated'):return _post(list(frames),fps,label)
def blank():return _post([],0,'blank')
def ur_parts(ur_type,cbor,fragment=60,extra=0):
    sys.path.insert(0,str(ROOT/'dist/firmware/sources/lvgl/application/src'))
    from seedsigner.helpers.ur2.ur_encoder import UREncoder
    from seedsigner.helpers.ur2.ur import UR
    enc=UREncoder(UR(ur_type,cbor),fragment,0)
    count=enc.fountain_encoder.seq_len()+extra
    return [enc.next_part().upper() for _ in range(count)]
def set_ur_psbt(psbt_bytes,fragment=60,fps=6,extra=0):
    from urtypes.crypto import PSBT
    parts=ur_parts('crypto-psbt',PSBT(psbt_bytes).to_cbor(),fragment,extra)
    return set_frames(parts,fps,'ur:crypto-psbt %d bytes fragment %d @%sfps'%(len(psbt_bytes),fragment,fps)),parts

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('serve');s.add_argument('--display-x',type=int,default=-1440);s.add_argument('--display-w',type=int,default=1440);s.add_argument('--display-h',type=int,default=900)
    t=sub.add_parser('text');t.add_argument('text')
    f=sub.add_parser('frames');f.add_argument('frames',nargs='+');f.add_argument('--fps',type=float,default=4)
    u=sub.add_parser('ur-psbt');u.add_argument('--hex',required=True);u.add_argument('--fragment',type=int,default=60);u.add_argument('--fps',type=float,default=6);u.add_argument('--extra',type=int,default=0)
    sub.add_parser('blank');sub.add_parser('status')
    ap.add_argument('--y',type=float,help='vertical offset in %% of screen height (negative = up)')
    ap.add_argument('--size',type=float,help='QR height in %% of screen height (default keeps current)')
    a=ap.parse_args()
    global SIZE,Y;SIZE=a.size;Y=a.y
    if a.cmd=='serve':serve(a)
    elif a.cmd=='text':print(set_text(a.text))
    elif a.cmd=='frames':print(set_frames(a.frames,a.fps))
    elif a.cmd=='ur-psbt':r,parts=set_ur_psbt(bytes.fromhex(a.hex),a.fragment,a.fps,a.extra);print(r,len(parts),parts[0][:50])
    elif a.cmd=='blank':print(blank())
    else:print(urllib.request.urlopen(URL+'/state').read().decode())
if __name__=='__main__':main()
