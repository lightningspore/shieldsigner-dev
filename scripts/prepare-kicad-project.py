#!/usr/bin/env python3
"""Make the working project libraries portable, retaining the embedded symbols."""
import collections,json,re,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
DIR=ROOT/'kicad'
def expressions(text):
    stack=[];quoted=False;escaped=False
    for i,c in enumerate(text):
        if quoted:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=False
        elif c=='"':quoted=True
        elif c=='(':stack.append(i)
        elif c==')':
            start=stack.pop()
            yield start,i+1,text[start:i+1]

symbols=collections.defaultdict(dict)
for file in DIR.glob('*.kicad_sch'):
    text=file.read_text()
    for start,end,expr in expressions(text):
        match=re.match(r'\(symbol\s+"([^"\n]+:[^"\n]+)"',expr)
        if match:
            lib,name=match[1].split(':',1)
            body=expr.replace('"'+match[1]+'"','"'+name+'"',1)
            if name in symbols[lib] and symbols[lib][name]!=body:raise RuntimeError('Conflicting embedded symbols')
            symbols[lib][name]=body
out=DIR/'symbols';out.mkdir(exist_ok=True)
for lib,items in symbols.items():
    (out/(lib+'.kicad_sym')).write_text('(kicad_symbol_lib (version 20241209) (generator kicad_symbol_editor)\n'+'\n'.join(items.values())+'\n)\n')
(DIR/'sym-lib-table').write_text('(sym_lib_table (version 7)\n'+'\n'.join(f'(lib (name "{lib}") (type "KiCad") (uri "${{KIPRJMOD}}/symbols/{lib}.kicad_sym") (options "") (descr "Pinned embedded symbol snapshot"))' for lib in sorted(symbols))+'\n)\n')
print('Created',sum(map(len,symbols.values())),'exact symbol snapshots in',len(symbols),'project-local libraries.')
