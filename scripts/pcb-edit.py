#!/usr/bin/env python3
"""Apply a JSON edit recipe with KiCad's bundled Python; retain backup and audit."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
APP=ROOT/'.tools/kicad-10/KiCad/KiCad.app/Contents'
if not os.environ.get('SHIELDSIGNER_PCB_WORKER'):
 env=os.environ.copy();env['SHIELDSIGNER_PCB_WORKER']='1'
 sys.exit(subprocess.call([str(APP/'Frameworks/Python.framework/Versions/3.9/bin/python3'),__file__,*sys.argv[1:]],env=env))
import wx
wx.Log.SetLogLevel(wx.LOG_Error)
app=wx.App(False)
import pcbnew as p
parser=argparse.ArgumentParser();parser.add_argument('recipe',type=Path);args=parser.parse_args()
recipe=json.loads(args.recipe.read_text())
pcb=ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb';pro=pcb.with_suffix('.kicad_pro')
backup=ROOT/'.tools/pcb-edits'/str(time.time_ns());backup.mkdir(parents=True)
before=pcb.read_bytes();project_before=pro.read_bytes()
if 'expectedBeforeSha256' in recipe:
 assert hashlib.sha256(before).hexdigest()==recipe['expectedBeforeSha256'],'Recipe already applied or board changed; inspect before replay'
(backup/pcb.name).write_bytes(before);(backup/pro.name).write_bytes(project_before)
(backup/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
b=p.LoadBoard(str(pcb));fps={f.GetReference():f for f in b.GetFootprints()}
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def route(points,net,layer=p.B_Cu,width=.2):
 for start,end in zip(points,points[1:]):
  t=p.PCB_TRACK(b);t.SetStart(vec(*start));t.SetEnd(vec(*end));t.SetLayer(layer);t.SetWidth(p.FromMM(width));t.SetNetCode(net);b.Add(t)
def reconnect(pad,old):
 # Connect to every original same-net track endpoint within the old pad land.
 candidates=[]
 for t in list(b.GetTracks()):
  if isinstance(t,p.PCB_VIA) or t.GetNetCode()!=pad.GetNetCode():continue
  for pt in [t.GetStart(),t.GetEnd()]:
   delta=pt-old
   if delta.EuclideanNorm() <= max(pad.GetSize().x,pad.GetSize().y)/2+10000:
    candidates.append((pt,t.GetLayer(),t.GetWidth()))
 for pt,layer,width in candidates:
  if pt==pad.GetPosition():continue
  t=p.PCB_TRACK(b);t.SetStart(pt);t.SetEnd(pad.GetPosition());t.SetLayer(layer);t.SetWidth(min(width,p.FromMM(.25)));t.SetNetCode(pad.GetNetCode());b.Add(t)
audit=[]
try:
 for edit in recipe['edits']:
  action=edit['action'];f=fps.get(edit.get('ref'))
  if action=='move':
   assert 'from' in edit,'Move edits require an explicit original position'
   expected=vec(*edit['from']);assert f.GetPosition()==expected,f"{edit['ref']} position changed; recipe not replayed"
   old={pad.m_Uuid.AsString():p.VECTOR2I(pad.GetPosition()) for pad in f.Pads()}
   f.SetPosition(f.GetPosition()+vec(*edit['delta']))
   for pad in f.Pads():
    if 'routes' in edit:
     if pad.GetNumber() in edit['routes']:route(edit['routes'][pad.GetNumber()],pad.GetNetCode())
    else:reconnect(pad,old[pad.m_Uuid.AsString()])
  elif action=='switch-courtyard':
   # Assembly envelope from XKB body/terminal drawing; copper lands unchanged.
   angle=f.GetOrientationDegrees();center=f.GetPosition()
   import math
   # Update existing primitives in place; avoid SWIG Add/Remove lifetime issues.
   courtyard=[d for d in f.GraphicalItems() if d.GetLayer() in [p.F_CrtYd,p.B_CrtYd]]
   assert len(courtyard)==4
   corners=[(-4.55,-3.25),(4.55,-3.25),(4.55,3.25),(-4.55,3.25)]
   def world(pt):
    a=math.radians(angle);return center+vec(pt[0]*math.cos(a)+pt[1]*math.sin(a),-pt[0]*math.sin(a)+pt[1]*math.cos(a))
   for d,start,end in zip(courtyard,corners,corners[1:]+corners[:1]):
    d.SetStart(world(start));d.SetEnd(world(end));d.SetWidth(p.FromMM(.05))
   for d in f.GraphicalItems():
    if d.GetLayer() in [p.F_SilkS,p.B_SilkS]:d.SetLayer(p.F_Fab if f.GetLayer()==p.F_Cu else p.B_Fab)
  elif action in ['layer','text-position']:
   item=next(x for x in list(b.GetDrawings())+[d for fp in b.GetFootprints() for d in fp.GraphicalItems()]+[fp.Reference() for fp in b.GetFootprints()] if x.m_Uuid.AsString()==edit['uuid'])
   if action=='layer':item.SetLayer(getattr(p,edit['layer']))
   else:
    position=vec(*edit['position'])
    assert b.GetBoardEdgesBoundingBox().Contains(position),'Text position is outside the board bounding box; use absolute board coordinates'
    item.SetPosition(position)
  elif action=='footprint-id':
   f.SetFPIDAsString(edit['value'])
  elif action=='pad-layers':
   for pad in f.Pads():
    if pad.GetNumber() in edit['pads']:
     layers=p.LSET()
     for name in edit['layers']:layers.AddLayer(getattr(p,name))
     pad.SetLayerSet(layers)
  else:raise ValueError('Unknown action '+action)
  audit.append(edit)
 p.ZONE_FILLER(b).Fill(b.Zones())
 tmp=backup/'edited.kicad_pcb';p.SaveBoard(str(tmp),b)
 tmp.with_suffix('.kicad_pro').write_bytes(project_before)
 (backup/'fp-lib-table').write_text((ROOT/'kicad/fp-lib-table').read_text().replace('${KIPRJMOD}',str(ROOT/'kicad')))
 # Check serialized object counts before replacing the working board.
 check=p.LoadBoard(str(tmp));assert len(list(check.GetFootprints()))==len(fps)
 def drc(path,name):
  output=backup/name
  command=[str(APP/'MacOS/kicad-cli'),'pcb','drc','--refill-zones','--severity-all','--format','json','--output',str(output),str(path)]
  subprocess.run(command,check=True,stdout=subprocess.DEVNULL)
  report=json.loads(output.read_text())
  active=[e for e in report['violations'] if not e.get('excluded')]
  signature=lambda e:(e['severity'],e['type'],tuple(sorted(i['uuid'] for i in e['items'])))
  return report,{signature(e) for e in active}
 baseline,old_issues=drc(pcb,'before-drc.json');candidate,new_issues=drc(tmp,'candidate-drc.json')
 assert not new_issues-old_issues,'Candidate introduces DRC issues; working board restored. Inspect candidate-drc.json in backup.'
 assert len(candidate.get('unconnected_items',[]))<=len(baseline.get('unconnected_items',[])),'Candidate breaks connectivity'
 original_board=p.LoadBoard(str(backup/pcb.name))
 original_tracks={t.m_Uuid.AsString():t.GetNetname() for t in original_board.GetTracks()}
 checked_tracks={t.m_Uuid.AsString():t.GetNetname() for t in check.GetTracks()}
 assert all(checked_tracks.get(uid)==net for uid,net in original_tracks.items()),'Original track net assignments changed'
 original_pads={pad.m_Uuid.AsString():(pad.GetNumber(),pad.GetNetname()) for fp in original_board.GetFootprints() for pad in fp.Pads()}
 checked_pads={pad.m_Uuid.AsString():(pad.GetNumber(),pad.GetNetname()) for fp in check.GetFootprints() for pad in fp.Pads()}
 assert original_pads==checked_pads,'Pad identities or net assignments changed'
 pcb.write_bytes(tmp.read_bytes())
 for ref in recipe.get('syncFootprints',[]):
  fp=fps[ref];lib=str(fp.GetFPID().GetLibNickname());directory=ROOT/'kicad/Footprints'/(lib+'.pretty');directory.mkdir(parents=True,exist_ok=True)
  p.PCB_IO_KICAD_SEXPR().FootprintSave(str(directory),fp)
 (backup/'audit.json').write_text(json.dumps({'beforeSha256':hashlib.sha256(before).hexdigest(),'afterSha256':hashlib.sha256(pcb.read_bytes()).hexdigest(),'edits':audit},indent=2)+'\n')
 print('Applied',len(audit),'edits. Backup/audit:',backup.relative_to(ROOT))
except Exception:
 pcb.write_bytes(before);raise
finally:
 pro.write_bytes(project_before)
