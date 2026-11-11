"""Final service silk: designator + net, with 0.15 mm strokes."""
from pathlib import Path
import json,runpy,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'hardware';PCB=V/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
if '--worker' not in sys.argv:
 cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']();sys.exit(subprocess.call([str(cli.parent.parent/'Frameworks/Python.framework/Versions/3.9/bin/python3'),__file__,'--worker']))
import wx
wx.Log.SetLogLevel(wx.LOG_Error);app=wx.App(False)
import pcbnew as p
b=p.LoadBoard(str(PCB));config=json.loads((V/'serviceability.json').read_text())
for point in config['testpoints']:
 x,y=point['xy'];label_y=y+2.4 if point['layer']=='F.Cu' else y-2.5
 matches=[n for n in b.GetDrawings() if isinstance(n,p.PCB_TEXT) and n.GetText() in [point['label'],point['ref']+'\n'+point['label']] and abs(p.ToMM(n.GetPosition().x)-x)<.001 and abs(p.ToMM(n.GetPosition().y)-label_y)<.001]
 assert len(matches)==1,(point['ref'],len(matches));n=matches[0];n.SetText(point['ref']+'\n'+point['label']);n.SetTextThickness(p.FromMM(.15))
for n in b.GetDrawings():
 if isinstance(n,p.PCB_TEXT) and n.GetText() in [f'H{i} M2.5' for i in range(705,709)]:n.SetTextThickness(p.FromMM(.15))
fps={f.GetReference():f for f in b.GetFootprints()}
fps['U202'].Reference().SetTextThickness(p.FromMM(.15))
fps['R606'].Reference().SetTextSize(p.VECTOR2I(p.FromMM(.8),p.FromMM(.8)))
p.SaveBoard(str(PCB),b)
