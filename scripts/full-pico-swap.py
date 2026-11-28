#!/usr/bin/env python3
"""Prepare the isolated full-size Pico/Plus SMT-socket module excursion.

The main PCB is read-only. The original Mini lands are replaced by two 20-contact
SMT sockets, with three nearby passive/strap moves. Local copper must be rerouted and
validated before this excursion can be considered an electrical candidate.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/'variants/full-size-pico'
K=V/'kicad'
SOURCE=ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
PCB=K/SOURCE.name
OUT=ROOT/'dist/full-size-pico'
APP=ROOT/'.tools/kicad-10/KiCad/KiCad.app/Contents'
MAP={1:40,2:3,3:36,4:1,5:2,6:12,7:14,8:15,9:16,10:7,11:6,
     12:19,13:20,14:9,15:10,16:5,17:4,18:17,19:31,20:32,21:38}
NAMES={1:'GPIO1_B2 / UART2_TX',2:'GPIO1_B3 / UART2_RX',3:'GND',4:'GPIO1_C7',5:'GPIO1_C6',6:'GPIO1_C5',7:'GPIO1_C4',8:'GND',9:'GPIO1_D2',10:'GPIO1_D3',11:'GPIO1_A2',12:'GPIO1_C0 / SPI0_CS0',13:'GND',14:'GPIO1_C1 / SPI0_CLK',15:'GPIO1_C2 / SPI0_MOSI',16:'GPIO1_C3 / SPI0_MISO',17:'GPIO0_A4',18:'GND',19:'GPIO1_D0',20:'GPIO1_D1',21:'GPIO4_B1 (Pico) / GPIO3_A6 (Plus)',22:'GPIO4_B0 (Pico) / GPIO3_A7 (Plus)',23:'GND',24:'GPIO4_A6 (Pico) / GPIO3_A5 (Plus)',25:'GPIO4_A2 (Pico) / GPIO3_A4 (Plus)',26:'GPIO4_A3 (Pico) / GPIO3_A2 (Plus)',27:'GPIO4_A4 (Pico) / GPIO3_A3 (Plus)',28:'GND',29:'NC (Pico) / GPIO3_A1 (Plus)',30:'NC',31:'GPIO4_C0 / 1V8',32:'GPIO4_C1 / 1V8',33:'GND',34:'NC',35:'NC',36:'3V3_OUT',37:'3V3_EN',38:'GND',39:'VSYS',40:'VBUS'}
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'))


def uid(name):return str(uuid.uuid5(uuid.NAMESPACE_URL,'shieldsigner-full-pico:'+name))
def font():return '(effects (font (size 1.27 1.27)))'
def block(text,prefix):
    return next(raw for _,_,raw in sx['expressions'](text) if raw.startswith(prefix))


def prepare():
    assert not PCB.exists(),'Excursion already prepared; inspect rather than overwrite'
    K.mkdir(parents=True);OUT.mkdir(parents=True,exist_ok=True)
    for path in (ROOT/'kicad').iterdir():
        if path.suffix in {'.kicad_sch','.kicad_pro','.kicad_sym'} or path.name in {'fp-lib-table','sym-lib-table'}:
            shutil.copyfile(path,K/path.name)
    for name in ['Footprints','Library.pretty','symbols','3dmodels']:
        (K/name).symlink_to(Path('../../../kicad')/name,target_is_directory=True)
    (V/'models').mkdir();(V/'reference').mkdir()
    for name in ['Luckfox-Pico.step','Luckfox-Pico-Plus.step']:
        shutil.copyfile(ROOT/'.tools/full-pico'/name,V/'models'/name)
    for name in ['Luckfox-Pico.pdf','Luckfox-Pico-Plus.pdf','dimensions.jpg','pinout.jpg','plus-dimensions.jpg','plus-pinout.jpg']:
        shutil.copyfile(ROOT/'.tools/full-pico'/name,V/'reference'/name)
    (V/'source-board.kicad_pcb').write_bytes(SOURCE.read_bytes())
    (V/'source.json').write_text(json.dumps({'mainBoardSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'vendorCommit':'290cfa600f07b5aecf75cbe743c86e30ccfe1f9a',
        'vendorRepository':'https://github.com/LuckfoxTECH/Luckfox-Pico-docs',
        'moduleCenterMm':[80,86],'moduleComponentSide':'outward / carrier back',
        'oldMiniToFullPin':MAP,'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['reference','models'] for p in (V/folder).iterdir()}},indent=2)+'\n')
    sheet=K/'rpi_interface.kicad_sch';text=sheet.read_text()
    original=block(text,'(symbol "Luckfox:LuckFox_Pico_MINI"')
    lib=original
    pin22=next(raw for _,_,raw in sx['expressions'](lib) if raw.startswith('(pin power_out') and '(number "22"' in raw)
    lib=lib.replace(pin22,'')
    lib=re.sub(r'\(number "(\d+)"',lambda m:f'(number "{MAP[int(m[1])]}"',lib)
    lib=lib.replace('Luckfox:LuckFox_Pico_MINI','LuckfoxFull:Luckfox_Pico').replace('LuckFox_Pico_MINI','Luckfox_Pico')
    common=block(lib,'(symbol "Luckfox_Pico_0_1"');rectangle=block(common,'(rectangle')
    lib=lib.replace(common,'').replace('(symbol "Luckfox_Pico_1_1"','(symbol "Luckfox_Pico_1_1" '+rectangle)
    spare=sorted(set(range(1,41))-set(MAP.values()))
    pins=[]
    for i,n in enumerate(spare):
        kind='power_in' if NAMES[n]=='GND' or n==39 else 'input' if n==37 else 'passive'
        name=NAMES[n].replace('GPIO4_','IO4_').replace('GPIO3_','IO3_')
        pins.append(f'(pin {kind} line (at -35.56 {22.86-i*2.54:.2f} 0) (length 2.54) (name {json.dumps(name)} {font()}) (number "{n}" {font()}))')
    extra='(symbol "Luckfox_Pico_2_1" (rectangle (start -33.02 25.4) (end 33.02 -25.4) (stroke (width .254) (type default)) (fill (type background)))'+''.join(pins)+')'
    lib=lib.rstrip()[:-1]+extra+')'
    text=text.replace(original,lib).replace('(paper "A4")','(paper "A3")')
    instance=next(raw for _,_,raw in sx['expressions'](text) if raw.startswith('(symbol\n') and '(property "Reference" "U202"' in raw)
    new=instance.replace('Luckfox:LuckFox_Pico_MINI','LuckfoxFull:Luckfox_Pico').replace('LuckFox_Pico_MINI','Luckfox_Pico').replace('Library:LUCKFOX_PICO_MINI_reversed','LuckfoxFull:Luckfox_Pico_SMD_Sockets')
    old22=block(new,'(pin "22"');new=new.replace(old22,'')
    new=re.sub(r'\(pin "(\d+)"',lambda m:f'(pin "{MAP[int(m[1])]}"',new)
    text=text.replace(instance,new)
    nc=next(raw for _,_,raw in sx['expressions'](text) if raw.startswith('(no_connect') and sx['one'](sx['parse'](raw),'at')[1:]==['264.16000','85.09000'])
    text=text.replace(nc,'')
    # Same reference, unit 2: all otherwise unused full-size pins are visible
    # and explicitly terminated; extra grounds join the existing GND net.
    inst=sx['parse'](instance);instances=block(instance,'(instances')
    instances=re.sub(r'\(unit 1\)','(unit 2)',instances)
    x,y=229.87,218.44
    second=f'(symbol (lib_id "LuckfoxFull:Luckfox_Pico") (at {x} {y} 0) (unit 2) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid("unit2")}") '+f'(property "Reference" "U202" (at {x} {y-29} 0) {font()}) (property "Value" "Luckfox_Pico" (at {x} {y-27} 0) {font()}) (property "Footprint" "LuckfoxFull:Luckfox_Pico_SMD_Sockets" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes))) '+''.join(f'(pin "{n}" (uuid "{uid("pin"+str(n))}"))' for n in spare)+instances+')'
    terminators=[]
    for i,n in enumerate(spare):
        px,py=x-35.56,round(y-22.86+i*2.54,2)
        if NAMES[n]=='GND':
            terminators.append(f'(global_label "GND" (shape input) (at {px} {py} 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid "{uid("gnd"+str(n))}"))')
        else:terminators.append(f'(no_connect (at {px} {py}) (uuid "{uid("nc"+str(n))}"))')
    text=text.rstrip()[:-1]+second+''.join(terminators)+')\n';sheet.write_text(text)
    symbol=lib.replace('LuckfoxFull:Luckfox_Pico','Luckfox_Pico',1)
    (K/'LuckfoxFull.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") '+symbol+')\n')
    for name,entry in [('sym-lib-table','(lib (name "LuckfoxFull") (type "KiCad") (uri "${KIPRJMOD}/LuckfoxFull.kicad_sym") (options "") (descr "Full-size Pico common host interface"))'),('fp-lib-table','(lib (name "LuckfoxFull") (type "KiCad") (uri "${KIPRJMOD}/LuckfoxFull.pretty") (options "") (descr "Full-size castellated module excursion"))')]:
        p=K/name;s=p.read_text();p.write_text(s.rstrip()[:-1]+entry+')\n')
    (K/'LuckfoxFull.pretty').mkdir()
    PCB.write_bytes(SOURCE.read_bytes())
    print('Prepared separate Pico/Plus schematic and source-pinned variant.',flush=True)


def place():
    baseline=(V/'source-board.kicad_pcb').read_text()
    assert PCB.read_text()==baseline,'Bootstrap only: refusing to replace an edited candidate layout'
    old=next(raw for _,_,raw in sx['expressions'](baseline) if raw.startswith('(footprint ') and '(property "Reference" "U202"' in raw)
    tree=sx['parse'](old);o=sx['one']
    properties=''.join(raw for _,_,raw in sx['expressions'](old) if raw.startswith('(path ') or raw.startswith('(sheetname ') or raw.startswith('(sheetfile '))
    pins={}
    for net in ET.parse(OUT/'netlist.xml').findall('./nets/net'):
        for node in net.findall('node'):
            if node.attrib['ref']=='U202':pins[int(node.attrib['pin'])]=net.attrib['name']
    pads=[]
    for n in range(1,41):
        row_index=n-1 if n<=20 else 40-n
        x=(8.89 if n<=20 else -8.89)+(1.65 if row_index%2==0 else -1.65)
        y=-24.13+row_index*2.54
        pads.append(f'(pad "{n}" smd roundrect (at {x:.6f} {y}) (size 1.9 1.02) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio .12) (net {json.dumps(pins[n])}) (uuid "{uid("land"+str(n))}"))')
    # Raw native geometry avoids a SWIG lifetime issue in the vendor's model
    # vector wrapper; the board is subsequently loaded and checked by KiCad.
    models=[]
    for filename,hidden in [('Luckfox-Pico.step',False),('Luckfox-Pico-Plus.step',True)]:
        models.append('(model "${KIPRJMOD}/../models/'+filename+'" '+('(hide yes) ' if hidden else '')+'(offset (xyz 10.5 -25.5 11.04)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 180)))')
    for x in [-8.89,8.89]:
        models.append(f'(model "${{KIPRJMOD}}/../models/Harwin-M20-7862042-nominal.step" (offset (xyz {x} 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
    models.append('(model "${KIPRJMOD}/../models/Pico-mating-headers-nominal.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
    for x in [-8.89,8.89]:
        for half,y,layer,width in [(2.85,25.75,'B.CrtYd',.05),(1.25,25.5,'B.Fab',.1)]:
            models.append(f'(fp_rect (start {x-half:.3f} {-y}) (end {x+half:.3f} {y}) (stroke (width {width}) (type default)) (fill none) (layer "{layer}"))')
    footprint=f'(footprint "LuckfoxFull:Luckfox_Pico_SMD_Sockets" (layer "B.Cu") (uuid "{o(tree,"uuid")[1]}") (at 94.2375 81.449) '+properties+'(attr smd) (property "Reference" "U202" (at 0 0) (layer "B.Fab") (hide yes) (effects (font (size 1 1)))) (property "Value" "Luckfox_Pico" (at 0 0) (layer "B.Fab") (hide yes) (effects (font (size 1 1)))) '+''.join(pads)+''.join(models)+')'
    PCB.write_text(baseline.replace(old,footprint))
    (K/'LuckfoxFull.pretty/Luckfox_Pico_SMD_Sockets.kicad_mod').write_text(footprint.replace('(footprint "LuckfoxFull:Luckfox_Pico_SMD_Sockets"','(footprint "Luckfox_Pico_SMD_Sockets"',1))
    print('Placed two 20-contact SMT socket land patterns; original Mini lands removed.')


def worker():
    import wx
    wx.Log.SetLogLevel(wx.LOG_Error);app=wx.App(False)
    import pcbnew as p
    b=p.LoadBoard(str(PCB));host=next(f for f in b.GetFootprints() if f.GetReference()=='U202')
    v=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
    # Built-in tscircuit autorouter input; no bespoke routing algorithm.
    obstacles=[]
    route_layers=[('top',p.F_Cu),('inner1',p.In2_Cu),('bottom',p.B_Cu)]
    all_layers=[name for name,_ in route_layers]
    def obstacle(cx,cy,w,h,layers,net='',angle=0):
        obstacles.append(dict(type='rect',center=dict(x=cx,y=cy),width=w,height=h,layers=layers,connectedTo=[net] if net else [],ccwRotationDegrees=angle))
    for f in b.GetFootprints():
        for pad in f.Pads():
            layers=[name for name,layer in route_layers if pad.IsOnLayer(layer)]
            if not layers:continue
            bb=pad.GetBoundingBox();obstacle(p.ToMM(bb.GetCenter().x),p.ToMM(bb.GetCenter().y),p.ToMM(bb.GetWidth())+.2,p.ToMM(bb.GetHeight())+.2,layers,pad.GetNetname())
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA):
            pt=t.GetPosition();d=p.ToMM(t.GetWidth(p.F_Cu))+.2;obstacle(p.ToMM(pt.x),p.ToMM(pt.y),d,d,all_layers,t.GetNetname())
        elif t.GetLayer() in [p.F_Cu,p.In2_Cu,p.B_Cu]:
            a,z=t.GetStart(),t.GetEnd();dx,dy=p.ToMM(z.x-a.x),p.ToMM(z.y-a.y);w=p.ToMM(t.GetWidth())+.2
            # Rotation is metadata in SRJ and is not honored by every pipeline
            # stage. Cover native copper with short axis-aligned rectangles.
            steps=max(1,math.ceil(math.hypot(dx,dy)/.75))
            for i in range(steps):
                x1,y1=p.ToMM(a.x)+dx*i/steps,p.ToMM(a.y)+dy*i/steps
                x2,y2=p.ToMM(a.x)+dx*(i+1)/steps,p.ToMM(a.y)+dy*(i+1)/steps
                if max(x1,x2)+w<80 or min(x1,x2)-w>124 or max(y1,y2)+w<55 or min(y1,y2)-w>108:continue
                obstacle((x1+x2)/2,(y1+y2)/2,abs(x2-x1)+w,abs(y2-y1)+w,[next(name for name,layer in route_layers if t.GetLayer()==layer)],t.GetNetname())
    for zone in b.Zones():
        if zone.GetIsRuleArea():
            bb=zone.GetBoundingBox();obstacle(p.ToMM(bb.GetCenter().x),p.ToMM(bb.GetCenter().y),p.ToMM(bb.GetWidth()),p.ToMM(bb.GetHeight()),all_layers)
    b.BuildConnectivity()
    connectivity=b.GetConnectivity()
    connections=[]
    # Native DRC supplies authoritative disconnected islands. Every reported
    # item position is a legal point on its existing copper or module land.
    drc=json.loads((OUT/'drc-pruned.json').read_text()) if (OUT/'drc-pruned.json').exists() else None
    if drc:
        points={}
        byid={item.m_Uuid.AsString():item for item in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]}
        for issue in drc.get('unconnected_items',[]):
            # Ground-plane fragments require native stitching review; a zone's
            # anchor is not a route terminal. Keep this finding in native DRC.
            if all(entry['description'].startswith('Zone [GND]') for entry in issue['items']):
                continue
            for entry in issue['items']:
                item=byid[entry['uuid']];net=item.GetNetname()
                if not net:continue
                pt=item.GetPosition()
                layers=[name for name,layer in route_layers if item.IsOnLayer(layer)]
                if not layers:continue
                point=dict(x=p.ToMM(pt.x),y=p.ToMM(pt.y))
                point.update(dict(layer=layers[0]) if len(layers)==1 else dict(layers=layers))
                points.setdefault(net,{})[(point['x'],point['y'],tuple(layers))]=point
        connections=[dict(name=net,pointsToConnect=list(pts.values())) for net,pts in points.items()]
    (OUT/'routing-input.json').write_text(json.dumps(dict(layerCount=3,minTraceWidth=.25,obstacles=obstacles,connections=connections,bounds=dict(minX=80,maxX=124,minY=55,maxY=108)),indent=2)+'\n')
    print('Replaced module interface; prepared',len(connections),'local connections for built-in routing.',flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','place','worker']);ap.add_argument('--input-only',action='store_true');args=ap.parse_args()
    if args.action=='prepare':
        prepare()
        cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']()
        subprocess.run([str(cli),'sch','export','netlist','--format','kicadxml','--output',str(OUT/'netlist.xml'),str(PCB.with_suffix('.kicad_sch'))],check=True)
        place()
    elif args.action=='place':place()
    else:worker()


if __name__=='__main__':main()
