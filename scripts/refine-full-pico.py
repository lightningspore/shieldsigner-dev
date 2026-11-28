"""Five explicit manual vertex moves after native review of built-in autorouting.

This is a recorded layout edit, not a routing algorithm. Board rules, via sizes
and trace widths remain unchanged. Native DRC must be rerun after applying it.
"""
import hashlib,json
from pathlib import Path
import wx
wx.Log.SetLogLevel(wx.LOG_Error);app=wx.App(False)
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'variants/full-size-pico/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
b=p.LoadBoard(str(PCB));before=hashlib.sha256(PCB.read_bytes()).hexdigest()
# Native DRC found five gaps 0.011–0.044 mm below the 0.2 mm rule.
edits=[
 ('LCD_DC','In2.Cu',[(109.394307,81.509692),(109.394307,78.941807)],(.055693,0)),
 ('UART_TX','In2.Cu',[(114.051398,68.593601),(114.051398,78.846740)],(.078602,0)),
 ('RPI_SPI_CS','In2.Cu',[(94.255479,86.916728),(96.068126,86.916728)],(0,.063272)),
 ('UART_TX','B.Cu',[(109.406540,81.354273),(105.292854,81.354273)],(0,-.054273)),
 ('LCD_DC','In2.Cu',[(108.698259,78.245759),(108.698259,74.016740)],(-.068259,0)),
]
record=[]
for net,layer,points,delta in edits:
 changed=0
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA) or t.GetNetname()!=net or b.GetLayerName(t.GetLayer())!=layer:continue
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   pt=get()
   if any(abs(p.ToMM(pt.x)-x)<.000002 and abs(p.ToMM(pt.y)-y)<.000002 for x,y in points):
    setter(p.VECTOR2I(pt.x+p.FromMM(delta[0]),pt.y+p.FromMM(delta[1])));changed+=1
 assert changed>=4,(net,layer,changed)
 record.append(dict(net=net,layer=layer,verticesBeforeMm=points,deltaMm=delta,changedEndpoints=changed))
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(PCB),b)
(ROOT/'variants/full-size-pico/routing-adjustments.json').write_text(json.dumps(dict(beforeSha256=before,afterSha256=hashlib.sha256(PCB.read_bytes()).hexdigest(),edits=record),indent=2)+'\n')
print('Applied five reviewed vertex moves; run native DRC.')
