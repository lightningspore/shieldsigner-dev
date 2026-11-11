#!/usr/bin/env python3
"""Widen the factory power clip row and add a second Keystone ground loop."""
from pathlib import Path
import hashlib,json,re,runpy,shutil,subprocess,sys,uuid
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb';V=ROOT/'variants/lcd-module-2.8'
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));one,children,parse=sx['one'],sx['children'],sx['parse']
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,'shieldsigner-power-clips:'+key))
def expression(text,predicate):return next(raw for _,_,raw in sx['expressions'](text) if predicate(parse(raw)))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
BACKUP=ROOT/'.tools/pcb-edits/power-clips-0.0.12'
if '--worker' not in sys.argv:
 assert not BACKUP.exists(),'Clip revision already prepared; inspect the existing backup'
 assert digest(PCB)=='2f949d76b53bf75e4b6f56e5e68623900b1f3e9c2403770409e647953aabc93d','Unexpected starting board'
 BACKUP.mkdir(parents=True)
 for p in [PCB,*PCB.parent.glob('*.kicad_sch')]:shutil.copyfile(p,BACKUP/p.name)
 sch=PCB.parent/'Power.kicad_sch';text=sch.read_text()
 symbol=expression(text,lambda n:n[0]=='symbol' and any(p[1:3]==['Reference','TP902'] for p in children(n,'property')))
 node=parse(symbol);old_symbol=one(node,'uuid')[1];new_symbol=uid('TP909:symbol');dx=213.36
 clone=re.sub(r'\(uuid "([^"]+)"\)',lambda m:'(uuid "'+(new_symbol if m[1]==old_symbol else uid('schematic:'+m[1]))+'")',symbol.replace('"TP902"','"TP909"'))
 def shift_at(m):return '(at '+format(float(m[1])+dx,'.6f').rstrip('0').rstrip('.')+' '+m[2]+m[3]+')'
 clone=re.sub(r'\(at ([\d.-]+) ([\d.-]+)([^)]*)\)',shift_at,clone)
 wire=expression(text,lambda n:n[0]=='wire' and one(one(n,'pts'),'xy')[1:3]==['66.04','139.7'])
 wire=re.sub(r'\(uuid "([^"]+)"\)',lambda m:'(uuid "'+uid('wire:'+m[1])+'")',wire)
 wire=re.sub(r'\(xy ([\d.-]+) ([\d.-]+)\)',lambda m:f'(xy {float(m[1])+dx:.6f} {m[2]})',wire)
 label=expression(text,lambda n:n[:2]==['global_label','GND'] and one(n,'at')[1:3]==['66.04','144.78'])
 label=re.sub(r'\(uuid "([^"]+)"\)',lambda m:'(uuid "'+uid('label:'+m[1])+'")',label);label=re.sub(r'\(at ([\d.-]+) ([\d.-]+)([^)]*)\)',shift_at,label)
 text=text.rstrip()[:-1]+'\n'+clone+'\n'+wire+'\n'+label+'\n)\n'
 text=text.replace('TP901 / TP902 replace the optional J302 header:', 'TP901 (+5 V), TP902 and TP909 (GND) form a 15 mm pitch front clip row:').replace('All eight loops are factory SMT placements.','All nine loops are factory SMT placements.')
 sch.write_text(text)
 text=PCB.read_text();fp=expression(text,lambda n:n[0]=='footprint' and any(q[1:3]==['Reference','TP902'] for q in children(n,'property')))
 fp=re.sub(r'\(uuid "([^"]+)"\)',lambda m:'(uuid "'+uid('footprint:'+m[1])+'")',fp.replace('"TP902"','"TP909"').replace('/'+old_symbol+'"','/'+new_symbol+'"'))
 fp=fp.replace('(at 112 120)','(at 143 120)',1);assert '(at 143 120)' in fp
 PCB.write_text(text.rstrip()[:-1]+'\n'+fp+'\n)\n')
 config=json.loads((V/'serviceability.json').read_text());config['revision']='0.0.12-dev'
 for point in config['testpoints']:
  if point['ref']=='TP901':point['xy']=[128,120]
  if point['ref']=='TP902':point['xy']=[113,120]
 config['testpoints'].append({'ref':'TP909','label':'GND','net':'GND','xy':[143,120],'layer':'F.Cu'})
 config['powerClipRow']={'leftToRight':['TP902','TP901','TP909'],'pitchMm':15,'previousPitchMm':7,'purpose':'Small alligator clips; two ground attachment positions','padWidthMm':3.4,'adjacentPadEdgeGapMm':11.6,'physicalClipFitVerified':False}
 (V/'serviceability.json').write_text(json.dumps(config,indent=2)+'\n')
 p=V/'bom-selection-extra.json';d=json.loads(p.read_text());d['TP909']={'lcsc':'C2906768','mpn':'5015'};p.write_text(json.dumps(d,indent=2)+'\n')
 for p in PCB.parent.glob('*.kicad_sch'):p.write_text(p.read_text().replace('0.0.11-dev','0.0.12-dev'))
 cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']();python=cli.parent.parent/'Frameworks/Python.framework/Versions/3.9/bin/python3'
 subprocess.run([str(python),__file__,'--worker'],check=True)
 sys.exit(0)
import wx
wx.Log.SetLogLevel(wx.LOG_Error);app=wx.App(False)
import pcbnew as p
remove={'56fd2af8-79db-4d41-927a-c41409eb5d2f','8fdb18c6-8b0b-4276-861e-2915c93aa190','c0599721-6440-47b9-af8d-88d82928a6bf'}
raw=PCB.read_text();edits=[]
initial=next(f for f in children(parse(raw),'footprint') if any(q[1:3]==['Reference','TP901'] for q in children(f,'property')))
assert one(initial,'at')[1:3]==['105','120'],'Worker already applied; do not duplicate clip routes'
for begin,end,entry in sx['expressions'](raw):
 node=parse(entry)
 if (node[0]=='segment' and one(node,'uuid')[1] in remove) or (node[0]=='gr_text' and node[1] in ['TP901\n+5V','TP902\nGND']):edits.append((begin,end))
for begin,end in sorted(edits,reverse=True):raw=raw[:begin]+raw[end:]
PCB.write_text(raw)
b=p.LoadBoard(str(PCB));fps={f.GetReference():f for f in b.GetFootprints()}
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
for ref,x in [('TP901',128),('TP902',113),('TP909',143)]:fps[ref].SetPosition(vec(x,120))
for t in b.GetTracks():
 if t.m_Uuid.AsString()=='699b489a-78d6-49d1-b040-dfa3ee8a44b7':t.SetPosition(vec(113,121.7))
def route(points,net):
 for start,end in zip(points,points[1:]):
  t=p.PCB_TRACK(b);t.SetStart(vec(*start));t.SetEnd(vec(*end));t.SetWidth(p.FromMM(.5));t.SetLayer(p.F_Cu);t.SetNet(b.FindNet(net));b.Add(t)
route([[102,115],[105,118],[126,118],[128,120]],'+5V')
route([[113,120],[113,121.7]],'GND')
route([[143,120],[143,118]],'GND')
v=p.PCB_VIA(b);v.SetPosition(vec(143,118));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet('GND'));b.Add(v)
for ref,label,x in [('TP902','GND',113),('TP901','+5V',128),('TP909','GND',143)]:
 t=p.PCB_TEXT(b);t.SetText(ref+'\n'+label);t.SetPosition(vec(x,122.4));t.SetTextSize(vec(.8,.8));t.SetTextThickness(p.FromMM(.15));t.SetLayer(p.F_SilkS);b.Add(t)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(PCB),b)
print('Saved 15 mm pitch GND / +5 V / GND clip row with nine factory Keystone loops')
