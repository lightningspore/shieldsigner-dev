"""Translate the built-in autorouter result to native KiCad tracks and vias."""
import hashlib,json,math,runpy,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import wx
wx.Log.SetLogLevel(wx.LOG_Error);app=wx.App(False)
import pcbnew as p
PCB=ROOT/'variants/full-size-pico/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
OUT=ROOT/'dist/full-size-pico'
b=p.LoadBoard(str(PCB));before=PCB.read_bytes();(OUT/'before-router-apply.kicad_pcb').write_bytes(before)
routes=json.loads((OUT/'routing-output.json').read_text())['traces']
assert routes,'No routed connections'
vec=lambda pt:p.VECTOR2I(p.FromMM(pt['x']),p.FromMM(pt['y']))
layer={'top':p.F_Cu,'inner1':p.In2_Cu,'bottom':p.B_Cu};via_positions=set();newids=[];count=0
for ti,trace in enumerate(routes):
 expanded=[]
 for point in trace['route']:
  if point['route_type']=='through_obstacle':
   assert math.dist(tuple(point['start'].values()),tuple(point['end'].values()))<.000002
   expanded.append(dict(route_type='wire',**point['start'],layer=point['from_layer'],width=point['width']))
   expanded.append(dict(route_type='wire',**point['end'],layer=point['to_layer'],width=point['width']))
  elif point['route_type']=='via':
   expanded.append(dict(route_type='wire',x=point['x'],y=point['y'],layer=point['from_layer'],width=.25))
   expanded.append(point)
   expanded.append(dict(route_type='wire',x=point['x'],y=point['y'],layer=point['to_layer'],width=.25))
  else:
   assert point['width']>=.15, 'Autorouter returned a below-rule trace width'
   expanded.append(point)
 trace['route']=expanded
 net=b.FindNet(trace['connection_name']);assert net
 previous=None
 for i,point in enumerate(trace['route']):
  if point['route_type']=='via':
   assert point['via_diameter']>=.6 and point['via_hole_diameter']>=.3
   key=(round(point['x'],6),round(point['y'],6),net.GetNetname())
   if key not in via_positions:
    via=p.PCB_VIA(b);via.SetPosition(vec(point));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(net)
    via.SetFrontTentingMode(p.TENTING_MODE_TENTED);via.SetBackTentingMode(p.TENTING_MODE_TENTED)
    b.Add(via);newids.append(via.m_Uuid.AsString());via_positions.add(key)
   previous=dict(x=point['x'],y=point['y'],width=.25,layer=point['to_layer'])
  else:
   if previous and previous['layer']==point['layer'] and math.dist((point['x'],point['y']),(previous['x'],previous['y']))>.000002:
    t=p.PCB_TRACK(b);t.SetStart(vec(previous));t.SetEnd(vec(point));t.SetLayer(layer[point['layer']]);t.SetWidth(p.FromMM(point['width']));t.SetNet(net)
    b.Add(t);newids.append(t.m_Uuid.AsString());count+=1
   previous=point
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(PCB),b)
(OUT/'router-apply.json').write_text(json.dumps({'beforeSha256':hashlib.sha256(before).hexdigest(),'boardSha256':hashlib.sha256(PCB.read_bytes()).hexdigest(),'traces':count,'vias':len(via_positions),'newIds':newids},indent=2)+'\n')
print('Added',count,'native track segments and',len(via_positions),'through-vias; ground zones persisted.')
