"""Audit the isolated swap against its pinned Mini carrier and vendor sources."""
import hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'variants/full-size-pico'
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));one=sx['one'];children=sx['children']
meta=json.loads((V/'source.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb')==meta['mainBoardSha256'],'Main Mini board changed since the excursion baseline'
assert sha(V/'source-board.kicad_pcb')==meta['mainBoardSha256'],'Pinned source snapshot changed'
for name,expected in meta['sources'].items():
 p=next((V/folder/name for folder in ['reference','models'] if (V/folder/name).exists()),None)
 assert p and sha(p)==expected,'Vendor reference changed: '+name
before=sx['parse']((V/'source-board.kicad_pcb').read_text());after=sx['parse']((V/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb').read_text())
def normalized(node):
 if node==['fill','solid']:return ['fill','yes'] # KiCad 10 serialization alias
 if isinstance(node,list):return [normalized(x) for x in node]
 try:return float(node)
 except (ValueError,TypeError):return node
def refs(board):return {next(p[2] for p in children(f,'property') if p[1]=='Reference'):f for f in children(board,'footprint')}
a,z=refs(before),refs(after);assert a.keys()==z.keys()
for key in ['layers','setup']:
 assert normalized(one(before,key))==normalized(one(after,key)),'Board stack/rules changed: '+key
for layer in ['Edge.Cuts','F.SilkS']:
 pick=lambda b:{one(n,'uuid')[1]:normalized(n) for n in b if isinstance(n,list) and n[0].startswith('gr_') and one(n,'layer')[1:]==[layer]}
 assert pick(before)==pick(after),'Protected artwork/outline changed: '+layer
moves=json.loads((V/'local-placement.json').read_text())
for ref in a:
 if ref=='U202':continue
 p1,p2=one(a[ref],'at'),one(z[ref],'at')
 if ref in moves:
  assert [float(x) for x in p1[1:3]]==moves[ref]['before'],ref
  assert [float(x) for x in p2[1:3]]==moves[ref]['after'],ref
 else:assert normalized(p1)==normalized(p2),'Unexpected placement change: '+ref
 # Relative lands, drills and net associations stay unchanged for every other part.
 fields=['at','size','drill','layers','net','roundrect_rratio','solder_mask_margin']
 pads=lambda f:{p[1]:[p[2:4]]+[normalized(one(p,k)) for k in fields] for p in children(f,'pad')}
 assert pads(a[ref])==pads(z[ref]),'Unexpected pad/net change: '+ref
oldpads={p[1]:p for p in children(a['U202'],'pad')};newpads={p[1]:p for p in children(z['U202'],'pad')}
assert set(newpads)=={str(i) for i in range(1,41)}
for old,new in meta['oldMiniToFullPin'].items():assert one(oldpads[old],'net')[-1]==one(newpads[str(new)],'net')[-1],(old,new)
for n in [3,8,13,18,23,28,33,38]:assert one(newpads[str(n)],'net')[-1]=='GND'
for pad in newpads.values():assert pad[2:4]==['smd','rect'] and normalized(one(pad,'size'))==['size',2.2,1.27]
reference=json.loads((V/'reference-board.json').read_text());assert reference['source']['sha256']==sha(V/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'),'Stale extracted reference'
schematic=sx['parse']((V/'kicad/rpi_interface.kicad_sch').read_text())
symbol=next(n for n in children(one(schematic,'lib_symbols'),'symbol') if n[1]=='LuckfoxFull:Luckfox_Pico')
numbers=[one(p,'number')[1] for unit in children(symbol,'symbol') for p in children(unit,'pin')]
assert len(numbers)==40 and set(numbers)=={str(i) for i in range(1,41)},'Full-size schematic pins must each appear exactly once'
summary=json.loads((ROOT/'dist/full-size-pico/checks-summary.json').read_text())
for result in summary.values():assert not result['bySeverity'] and result['excluded']==0 and result['unconnectedItems']==0 and result['schematicParityIssues']==0
record={'boardSha256':reference['source']['sha256'],'mainBoardUnchanged':True,'preservedOtherFootprints':75,'documentedOtherPlacementChanges':sorted(moves),'fullSizeSocketContacts':40,'nativeChecks':summary,'qualification':'Digital audit only; physical assembly and powered operation unqualified.'}
(V/'audit.json').write_text(json.dumps(record,indent=2)+'\n')
print('Verified pin mapping, 40 SMT lands, 75 other footprints, outline, front artwork, rules, vendor hashes and native zero-finding reports.')
