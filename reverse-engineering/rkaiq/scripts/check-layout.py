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

with obj.open('rb') as source:
    elf=ELFFile(source);symbol=elf.get_section_by_name('.symtab').get_symbol_by_name('statistics_layout')[0]
    section=elf.get_section(symbol['st_shndx']);offset=symbol['st_value']-section['sh_addr']
    statistics=struct.unpack('<14I',section.data()[offset:offset+56])
assert statistics==(13036,13024,13028,13032,2736,4096,11008,12816,12944,12960,225,4,8,4),statistics
print('PASS: full ISP32 statistics payload=13036, measurements=0x32e0; AE/AWB offsets and counts verified')

# Compile the verbatim SDK output-record declaration independently of Rust.
import re
item=next(x for x in manifest['headers'] if x['name']=='rk_aiq_types_ae_hw.h')
header=ROOT/'.tools/reverse-engineering/headers'/item['name']
assert hashlib.sha256(header.read_bytes()).hexdigest()==item['sha256']
text=header.read_text()
def declaration(pattern):
    match=re.search(pattern,text,re.S);assert match,pattern;return match.group(0)
record=declaration(r'typedef struct rawaebig_stat \{.*?\} rawaebig_stat_t;')
macros='\n'.join(declaration(r'#define '+name+r'[^\n]*') for name in ['RAWAEBIG_WIN_NUM','RAWAEBIG_SUBWIN_NUM'])
source=cache/'ae-sdk-layout.c'
source.write_text('#include <stdint.h>\n#include <stddef.h>\n'+macros+'\n'+record+'''
_Static_assert(sizeof(rawaebig_stat_t)==1928,"big AE record size");
_Static_assert(offsetof(rawaebig_stat_t,wndx_channelr)==1800,"preserved window channel offset");
_Static_assert(offsetof(rawaebig_stat_t,wndx_sumr)==1832,"red sums offset");
_Static_assert(offsetof(rawaebig_stat_t,wndx_sumg)==1864,"green sums offset");
_Static_assert(offsetof(rawaebig_stat_t,wndx_sumb)==1896,"blue sums offset");
''')
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-c',str(source),'-o',str(cache/'ae-sdk-layout.o')],check=True)
print('PASS: pinned SDK big AE record=1928 bytes; preserved channels and RGB sum offsets verified')

# Extract the exact SDK input declaration, without importing unrelated algorithm
# headers or substituting a hand-written equivalent struct.
item=next(x for x in manifest['headers'] if x['name']=='rk_aiq_types_ablc_algo_int_v32.h')
header=ROOT/'.tools/reverse-engineering/headers'/item['name']
assert hashlib.sha256(header.read_bytes()).hexdigest()==item['sha256']
match=re.search(r'typedef struct AblcProc_V32_s \{.*?\} AblcProc_V32_t;',header.read_text(),re.S);assert match
source=cache/'blc-sdk-layout.c'
source.write_text('#include <stdbool.h>\n#include <stddef.h>\n'+match.group(0)+'''
_Static_assert(sizeof(AblcProc_V32_t)==32,"black-level SDK input size");
_Static_assert(offsetof(AblcProc_V32_t,enable)==0,"main enable");
_Static_assert(offsetof(AblcProc_V32_t,blc_r)==2,"fixed channels");
_Static_assert(offsetof(AblcProc_V32_t,blc1_enable)==10,"stage1 enable");
_Static_assert(offsetof(AblcProc_V32_t,blc1_r)==12,"stage1 channels");
_Static_assert(offsetof(AblcProc_V32_t,blc_ob_enable)==20,"optical-black enable");
_Static_assert(offsetof(AblcProc_V32_t,isp_ob_offset)==22,"optical-black offset");
_Static_assert(offsetof(AblcProc_V32_t,isp_ob_predgain)==24,"optical-black predgain");
_Static_assert(offsetof(AblcProc_V32_t,isp_ob_max)==28,"optical-black maximum");
''')
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-c',str(source),'-o',str(cache/'blc-sdk-layout.o')],check=True)
print('PASS: pinned SDK black-level input=32 bytes; full kernel BLS block=44 bytes at 0x7ae')
