#!/usr/bin/env python3
"""Verify pinned kernel parameter ABI with an ARM-targeting C compiler."""
from pathlib import Path
import hashlib,json,subprocess,struct,shutil
from elftools.elf.elffile import ELFFile
ROOT=Path(__file__).resolve().parents[3]
cache=ROOT/'.tools/reverse-engineering/kernel-uapi'
manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text())
for item in manifest['kernelHeaders']:
    assert hashlib.sha256((cache/'linux'/item['name']).read_bytes()).hexdigest()==item['sha256']
# Kernel headers_install removes kernel-only compiler includes and __user
# annotations. Keep original pinned downloads intact and sanitize a build copy.
installed=cache/'installed';(installed/'linux').mkdir(parents=True,exist_ok=True)
for item in manifest['kernelHeaders']:
    source=cache/'linux'/item['name'];target=installed/'linux'/item['name']
    if item['name'] in ('videodev2.h','media.h'):
        target.write_text(source.read_text().replace('#include <linux/compiler.h>','').replace('__user',''))
    else:shutil.copyfile(source,target)
obj=cache/'layout-arm.o'
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-I',str(installed),'-c',str(Path(__file__).with_suffix('.c')),'-o',str(obj)],check=True)
with obj.open('rb') as source:
    elf=ELFFile(source)
    assert elf['e_machine']=='EM_ARM'
    symbol=elf.get_section_by_name('.symtab').get_symbol_by_name('recovered_layout')[0]
    section=elf.get_section(symbol['st_shndx'])
    offset=symbol['st_value']-section['sh_addr']
    layout=struct.unpack('<3I',section.data()[offset:offset+12])
assert layout==(11145,4645,32),layout
print('PASS: ARM kernel parameter bytes=%d, AWB offset=%d, AWB bytes=%d'%layout)
