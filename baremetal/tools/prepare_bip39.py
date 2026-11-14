# SPDX-License-Identifier: MIT
"""Prepare actual embit0.8.0 BIP39 leaf modules, without importing curve backends."""
import ast,hashlib,io,json,tarfile,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]
url='https://files.pythonhosted.org/packages/83/88/b054b00ade6d2a41749e15976cdcec4b7ec4656ac1cb917ce3de395528d1/embit-0.8.0.tar.gz'
sha='8bf4b10073c67400370ce523fb16f035fe759f6fdd987c579bdcc268d75ed770'
cache=root/'.tools/embit-0.8.0/source.tar.gz'
if not cache.exists():
 data=urllib.request.urlopen(url,timeout=60).read();assert hashlib.sha256(data).hexdigest()==sha
 cache.parent.mkdir(parents=True,exist_ok=True);cache.write_bytes(data)
data=cache.read_bytes();assert hashlib.sha256(data).hexdigest()==sha
with tarfile.open(fileobj=io.BytesIO(data)) as archive:
 def read(p):return archive.extractfile('embit-0.8.0/'+p).read()
 (root/'app/LICENSE.embit').write_bytes(read('LICENSE'))
 receipt={'version':'0.8.0','sdistUrl':url,'sdistSha256':sha,'scope':'Actual BIP39 leaf only; no curve or Seed model qualification','files':{}}
 class Strip(ast.NodeTransformer):
  def visit_FunctionDef(self,n):
   n.returns=None
   for a in n.args.args+n.args.kwonlyargs+n.args.posonlyargs:a.annotation=None
   return self.generic_visit(n)
 for name in ('__init__.py','wordlists/__init__.py','wordlists/bip39.py','bip39.py'):
  raw=read('src/embit/'+name);text=raw.decode();changes=[]
  if name=='bip39.py':
   assert text.count('from .misc import const')==1
   text=text.replace('from .misc import const','from micropython import const')
   text=ast.unparse(ast.fix_missing_locations(Strip().visit(ast.parse(text))))+'\n'
   changes=['Use actual micropython.const directly; avoid unrelated eager secp256k1 import in misc','Remove Python type annotations only']
  if name=='__init__.py':
   assert not text.strip()
   text='from . import bip39\n';changes=['Expose only the actually frozen BIP39 leaf']
  out=root/'app/embit'/name;out.parent.mkdir(parents=True,exist_ok=True)
  out.write_text('# Copyright (c)2020 Stepan Snigirev; MIT, see ../LICENSE.embit\n'+text)
  receipt['files'][name]={'sourceSha256':hashlib.sha256(raw).hexdigest(),'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest(),'changes':changes}
 (root/'app/bip39-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
