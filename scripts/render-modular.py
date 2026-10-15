#!/usr/bin/env python3
"""Regenerate assembly views and mechanical interchange files using pinned KiCad."""
import runpy,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'variants/lcd-module-2.8';OUT=ROOT/'dist/lcd-module-2.8';OUT.mkdir(exist_ok=True,parents=True);board=V/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
subprocess.run([sys.executable,str(ROOT/'scripts/check-modular-mechanics.py')],check=True)
cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']()
subprocess.run([str(cli),'sch','export','pdf','--output',str(OUT/'shieldsigner-modular-schematic.pdf'),str(board.with_suffix('.kicad_sch'))],check=True)
for side,angles,name in [('top','325,0,15','front'),('bottom','335,0,345','back')]:subprocess.run([str(cli),'pcb','render','--width','1600','--height','1000','--background','transparent','--side',side,'--rotate',angles,'--zoom','1.2','--output',str(V/f'assembly-{name}.png'),str(board)],check=True)
for extension in ['step','glb']:subprocess.run([str(cli),'pcb','export',extension,'--force','--no-dnp','--output',str(OUT/f'shieldsigner-modular-assembly.{extension}'),str(board)],check=True)
print('Assembled views and STEP/GLB files regenerated.')
