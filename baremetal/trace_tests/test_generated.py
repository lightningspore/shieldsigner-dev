"""Compile generated observer tables and compare their ABI/data with the ELF whitelist."""
import ctypes as C
import subprocess
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from live_trace_sites import MODULES,read_module,generate_header
from c_ir_backend import Op,operand,Memory

ROOT=Path(__file__).resolve().parents[1]

class Site(C.Structure):
    _fields_=[('module',C.c_uint32),('offset',C.c_uint32),('kind',C.c_uint32),
              ('link',C.c_uint32),('count',C.c_uint32),('ops',Op*4)]

class GeneratedTableTest(unittest.TestCase):
    def test_compiled_tables_match_elf(self):
        modules=[read_module(name)[0] for name in MODULES]
        folder=ROOT/'build/trace-generated-test';folder.mkdir(parents=True,exist_ok=True)
        generate_header(modules,folder/'live_sites.h')
        source=folder/'tables.c'
        source.write_text('#include "live_sites.h"\nconst struct bm_site_spec *sites(void){return bm_sites;}\n'
                          'unsigned count(void){return sizeof(bm_sites)/sizeof(*bm_sites);}\n'
                          'unsigned modules_count(void){return sizeof(bm_modules)/sizeof(*bm_modules);}\n'
                          'unsigned guard_length(unsigned i){return bm_post_lengths[i];}\n'
                          'const unsigned char *guard(unsigned i){return bm_post_bytes[i];}\n')
        library=folder/'tables.so'
        subprocess.run(['cc','-shared','-fPIC','-Wall','-Wextra','-Werror',
                        '-I'+str(ROOT/'tools/kernel-trace'),str(source),'-o',str(library)],check=True)
        lib=C.CDLL(str(library));lib.sites.restype=C.POINTER(Site)
        lib.guard.restype=C.POINTER(C.c_ubyte)
        self.assertEqual(lib.count(),18);self.assertEqual(lib.modules_count(),3)
        index=0
        for module_id,module in enumerate(modules):
            for site in module['sites']:
                actual=lib.sites()[index]
                guard=b''.join(bytes.fromhex(op['bytes']) for op in site.get('program',[]))
                self.assertEqual(lib.guard_length(index),len(guard))
                self.assertEqual(bytes(lib.guard(index)[:len(guard)]),guard)
                index+=1
                self.assertEqual((actual.module,actual.offset,actual.kind,actual.link,actual.count),
                    (module_id,site['offset'],{'mmio':0,'regmap':1,'sensor':2}[site['kind']],site['link'],len(site.get('program',[]))))
                for n,item in enumerate(site.get('program',[])):
                    op=actual.ops[n]
                    self.assertEqual((op.kind,op.reg,op.pc),({'load':0,'store':1,'move':2,'add':3}[item['kind']],item['register'],item['pcOffset']))
                    if op.kind<2:
                        m=item['memory'];expected=Memory(m['base'],m['index'] if m['index'] is not None else -1,m['shift'],m['displacement'])
                        self.assertEqual(bytes(op.memory),bytes(expected))
                    elif op.kind==2:self.assertEqual(bytes(op.a),bytes(operand(item['operand'])))
                    else:
                        self.assertEqual(bytes(op.a),bytes(operand(item['left'])))
                        self.assertEqual(bytes(op.b),bytes(operand(item['right'])))
