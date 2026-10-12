#!/usr/bin/env python3
"""Run with KiCad's bundled Python to pin the exact placed footprints locally."""
import wx
app=wx.App(False)
import pcbnew
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
board=pcbnew.LoadBoard(str(ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'))
libraries=set()
for footprint in board.GetFootprints():
    identity=footprint.GetFPID()
    lib=str(identity.GetLibNickname());name=str(identity.GetLibItemName())
    directory=ROOT/'kicad/Footprints'/(lib+'.pretty');directory.mkdir(parents=True,exist_ok=True)
    # First instance pins the library geometry; placed instances remain unchanged.
    if not (directory/(name+'.kicad_mod')).exists():pcbnew.PCB_IO_KICAD_SEXPR().FootprintSave(str(directory),footprint)
    libraries.add(lib)
(ROOT/'kicad/fp-lib-table').write_text('(fp_lib_table (version 7)\n'+'\n'.join(f'(lib (name "{lib}") (type "KiCad") (uri "${{KIPRJMOD}}/Footprints/{lib}.pretty") (options "") (descr "Pinned native board footprint"))' for lib in sorted(libraries))+'\n)\n')
print('Pinned board footprints in',len(libraries),'local libraries.')
