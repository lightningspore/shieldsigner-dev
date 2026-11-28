"""Read-only native drill geometry for independent Excellon comparison."""
import hashlib,json,math
from pathlib import Path
import wx
wx.Log.SetLogLevel(wx.LOG_Error);app=wx.App(False)
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'variants/full-size-pico/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb';b=p.LoadBoard(str(PCB));rows=[]
def add(center,size,angle,plated,owner):
 x,y=center;dx,dy=size
 if dx<.00001 or dy<.00001:return
 d=min(dx,dy);half=(max(dx,dy)-d)/2;t=math.radians(angle);vx,vy=(half,0) if dx>=dy else (0,half);ox,oy=vx*math.cos(t)+vy*math.sin(t),-vx*math.sin(t)+vy*math.cos(t)
 rows.append(dict(owner=owner,plated=plated,diameterMm=d,centerMm=[x-50,130-y],endsMm=[[x-ox-50,130-(y-oy)],[x+ox-50,130-(y+oy)]]))
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):add([p.ToMM(t.GetPosition().x),p.ToMM(t.GetPosition().y)],[p.ToMM(t.GetDrillValue())]*2,0,True,'via:'+t.m_Uuid.AsString())
for f in b.GetFootprints():
 for pad in f.Pads():
  size=pad.GetDrillSize();add([p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y)],[p.ToMM(size.x),p.ToMM(size.y)],pad.GetOrientationDegrees(),pad.GetAttribute()==p.PAD_ATTRIB_PTH,f.GetReference()+':'+pad.GetNumber()+':'+pad.m_Uuid.AsString())
(ROOT/'dist/full-size-pico/native-drills.json').write_text(json.dumps(dict(boardSha256=hashlib.sha256(PCB.read_bytes()).hexdigest(),drills=rows),indent=2)+'\n')
print('Read',len(rows),'native drill/slot objects.')
