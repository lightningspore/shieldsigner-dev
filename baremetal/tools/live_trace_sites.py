# SPDX-License-Identifier: MIT
"""Whitelist original camera-module write calls and describe post-barrier address calculation.

This reads GPL module ELF files for observation. It never patches a device and does
not inspect closed Rockchip blobs. Unsupported sequences abort generation.
"""
from pathlib import Path
import hashlib
import json
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from capstone.arm import ARM_OP_REG, ARM_OP_IMM, ARM_OP_MEM, ARM_SFT_INVALID, ARM_SFT_LSL

ROOT=Path(__file__).resolve().parents[1]
MODULES=['video_rkcif','phy-rockchip-csi2-dphy-hw','sc3336']
TARGETS={'arm_heavy_mb':'mmio','regmap_write':'regmap','i2c_transfer_buffer_flags':'sensor'}
# This call follows a register read and has no subsequent MMIO store.
READ_BARRIERS={('video_rkcif',71394)}

def reg_id(decoder,reg):
    name=decoder.reg_name(reg)
    aliases={'sb':9,'sl':10,'fp':11,'ip':12,'sp':13,'lr':14,'pc':15}
    if name in aliases:return aliases[name]
    if name.startswith('r') and name[1:].isdigit():return int(name[1:])
    raise ValueError('Unsupported register '+name)

def operand(decoder,op):
    if op.type==ARM_OP_IMM:return {'immediate':op.imm}
    if op.type==ARM_OP_REG:
        if op.shift.type not in (ARM_SFT_INVALID,ARM_SFT_LSL):raise ValueError('Unsupported shift')
        return {'register':reg_id(decoder,op.reg),'shift':op.shift.value}
    raise ValueError('Unsupported arithmetic operand')

def memory(decoder,op):
    if op.type!=ARM_OP_MEM or op.shift.type not in (ARM_SFT_INVALID,ARM_SFT_LSL):raise ValueError('Unsupported memory operand')
    return {'base':reg_id(decoder,op.mem.base),'index':reg_id(decoder,op.mem.index) if op.mem.index else None,
            'shift':op.shift.value,'displacement':op.mem.disp}

def store_program(text,offset,decoder):
    program=[]
    for ins in decoder.disasm(text[offset+4:offset+28],offset+4):
        if len(program)>=4:raise ValueError('No store within four instructions')
        if ins.writeback:raise ValueError('Writeback not supported')
        mnemonic=ins.mnemonic.removesuffix('.w');ops=ins.operands
        entry={'pcOffset':ins.address,'bytes':ins.bytes.hex()}
        if mnemonic in ('ldr','str'):
            entry.update(kind='load' if mnemonic=='ldr' else 'store',register=reg_id(decoder,ops[0].reg),memory=memory(decoder,ops[1]))
        elif mnemonic in ('mov','movs'):
            entry.update(kind='move',register=reg_id(decoder,ops[0].reg),operand=operand(decoder,ops[1]))
        elif mnemonic in ('add','adds'):
            dest=reg_id(decoder,ops[0].reg)
            lhs={'register':dest,'shift':0} if len(ops)==2 else operand(decoder,ops[1])
            entry.update(kind='add',register=dest,left=lhs,right=operand(decoder,ops[-1]))
        else:raise ValueError('Unsupported instruction '+ins.mnemonic+' '+ins.op_str)
        program.append(entry)
        if entry['kind']=='store':return program
    raise ValueError('Missing store')

def read_module(name):
    path=ROOT/'logs/phase-7/original-modules'/f'{name}.ko'
    decoder=Cs(CS_ARCH_ARM,CS_MODE_THUMB);decoder.detail=True
    with path.open('rb') as stream:
        elf=ELFFile(stream);text=elf.get_section_by_name('.text').data()
        rels=elf.get_section_by_name('.rel.text');symbols=elf.get_section(rels['sh_link'])
        sites=[];excluded=[]
        for rel in rels.iter_relocations():
            target=symbols.get_symbol(rel['r_info_sym']).name
            if target not in TARGETS:continue
            offset=rel['r_offset']
            if rel['r_info_type'] not in (10,30):raise ValueError('Expected Thumb call/tail-call relocation')
            if (name,offset) in READ_BARRIERS:
                excluded.append({'offset':offset,'reason':'post-read barrier, no store'});continue
            site={'module':name,'offset':offset,'target':target,'kind':TARGETS[target],'link':rel['r_info_type']==10}
            if site['kind']=='mmio':site['program']=store_program(text,offset,decoder)
            sites.append(site)
        return {'module':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'textSize':len(text),'sites':sites,'excluded':excluded},text

def predict(program,registers,module_base,read_word):
    """Evaluate only address/value calculation; never perform a device write."""
    regs=list(registers)
    def value(op):return op['immediate'] if 'immediate' in op else regs[op['register']]<<op.get('shift',0)
    for ins in program:
        regs[15]=(module_base+ins['pcOffset']+4)&~3
        if ins['kind'] in ('load','store'):
            mem=ins['memory'];address=(regs[mem['base']]+mem['displacement']+(0 if mem['index'] is None else regs[mem['index']]<<mem['shift']))&0xffffffff
            if ins['kind']=='store':return address,regs[ins['register']]&0xffffffff
            regs[ins['register']]=read_word(address)
        elif ins['kind']=='move':regs[ins['register']]=value(ins['operand'])&0xffffffff
        elif ins['kind']=='add':regs[ins['register']]=(value(ins['left'])+value(ins['right']))&0xffffffff
    raise ValueError('No predicted store')

def thumb_call(pc,target,link=True):
    offset=(target&~1)-(pc+4)
    if offset&1 or not -(1<<24)<=offset<(1<<24):raise ValueError('Thumb call out of range')
    bits=offset&0x1ffffff;s=(bits>>24)&1;i1=(bits>>23)&1;i2=(bits>>22)&1
    first=0xf000|(s<<10)|((bits>>12)&1023)
    second=(0xd000 if link else 0x9000)|(((~(i1^s))&1)<<13)|(((~(i2^s))&1)<<11)|((bits>>1)&2047)
    return first.to_bytes(2,'little')+second.to_bytes(2,'little')

def c_operand(item):
    return '{%d,%d,0x%08xU}'%(item.get('register',-1),item.get('shift',0),item.get('immediate',0)&0xffffffff)

def c_program_op(item):
    kind={'load':0,'store':1,'move':2,'add':3}[item['kind']]
    a=b='{-1,0,0}';mem='{0,-1,0,0}'
    if kind<2:
        m=item['memory']
        mem='{%d,%d,%d,%d}'%(m['base'],m['index'] if m['index'] is not None else -1,m['shift'],m['displacement'])
    elif kind==2:a=c_operand(item['operand'])
    else:a,b=c_operand(item['left']),c_operand(item['right'])
    return '{%d,%d,%d,%s,%s,%s}'%(kind,item['register'],item['pcOffset'],a,b,mem)

def generate_header(modules,destination):
    """Emit data only. Runtime validation must still precede any redirection."""
    lines=['/* Generated from original GPL camera-module ELF relocations. */',
           '#ifndef BM_LIVE_SITES_H','#define BM_LIVE_SITES_H','#include "live_ir.h"',
           'struct bm_module_spec { const char *name,*sha256; bm_u32 text_size; };',
           'struct bm_site_spec { bm_u32 module,offset,kind,link,count; struct bm_op ops[4]; };',
           'static const struct bm_module_spec bm_modules[] = {']
    for module in modules:
        lines.append('{"%s","%s",%d},'%(module['module'].replace('-','_'),module['sha256'],module['textSize']))
    lines.extend(['};','static const struct bm_site_spec bm_sites[] = {'])
    for index,module in enumerate(modules):
        for site in module['sites']:
            program=site.get('program',[])
            ops=','.join(c_program_op(op) for op in program) if program else '{0}'
            lines.append('{%d,%d,%d,%d,%d,{%s}},'%(index,site['offset'],{'mmio':0,'regmap':1,'sensor':2}[site['kind']],site['link'],len(program),ops))
    lines.extend(['};','static const unsigned char bm_post_bytes[][24] = {'])
    lengths=[]
    for module in modules:
        for site in module['sites']:
            data=b''.join(bytes.fromhex(op['bytes']) for op in site.get('program',[]))
            if len(data)>24:raise ValueError('Post-call guard too long')
            lines.append('{'+(','.join(str(value) for value in data) if data else '0')+'},')
            lengths.append(len(data))
    lines.extend(['};','static const unsigned char bm_post_lengths[] = {'+','.join(map(str,lengths))+'};','#endif',''])
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text('\n'.join(lines))

def generate():
    modules=[read_module(name)[0] for name in MODULES]
    assert sum(len(m['sites']) for m in modules)==18
    destination=ROOT/'logs/phase-7/live-write-sites.json'
    destination.write_text(json.dumps({'modules':modules,'appliedToHardware':False},indent=2)+'\n')
    generate_header(modules,ROOT/'build/kernel-trace/live_sites.h')
    print('Whitelisted',sum(len(m['sites']) for m in modules),'write calls; excluded one read barrier; no device writes.')
    return modules

if __name__=='__main__':generate()
