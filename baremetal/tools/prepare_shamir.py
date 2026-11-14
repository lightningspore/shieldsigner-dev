# SPDX-License-Identifier: MIT
"""Port REF's exact source archive, retaining full SLIP39 core and recovery code."""
import ast,hashlib,io,json,tarfile,urllib.request,subprocess
from pathlib import Path
from source_records import Records
root=Path(__file__).resolve().parents[1]
url='https://codeload.github.com/3rdIteration/python-shamir-mnemonic/tar.gz/0.3-setuptools'
sha='6fdcfb8d4380a8427ba28805eea63511a793fdfc6732d5c44d0f91a6b273445b'
p=root/'.tools/shamir-ref/source.tar.gz'
if not p.exists():
 b=urllib.request.urlopen(url,timeout=60).read();assert hashlib.sha256(b).hexdigest()==sha;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==sha
class Port(ast.NodeTransformer):
 def visit_ImportFrom(self,n):
  if n.module in ('typing','dataclasses'):return None
  if n.module=='collections' and n.names[0].name=='defaultdict':n.module='seedsigner_port.defaultdict'
  return n
 def visit_Import(self,n):
  if any(a.name in ('secrets','os.path') for a in n.names):return None
  return n
 def visit_FunctionDef(self,n):
  n.returns=None
  for a in n.args.args+n.args.kwonlyargs+n.args.posonlyargs:a.annotation=None
  if n.name=='_load_wordlist':
   assert isinstance(n.body[0],ast.With)
   n.body[0]=ast.parse('wordlist=list(_FROZEN_WORDLIST)').body[0]
  return self.generic_visit(n)
 def visit_AnnAssign(self,n):return ast.copy_location(ast.Assign(targets=[n.target],value=self.visit(n.value)),n) if n.value is not None else None
 def visit_Assign(self,n):
  if len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='RANDOM_BYTES':n.value=ast.Name(id='_random_bytes',ctx=ast.Load())
  return self.generic_visit(n)
 def visit_Try(self,n):
  n=self.generic_visit(n)
  if any(h.type is None or (isinstance(h.type,ast.Name) and h.type.id in ('Exception','BaseException')) for h in n.handlers):n.handlers.insert(0,ast.ExceptHandler(type=ast.Name(id='FeatureUnavailable',ctx=ast.Load()),name=None,body=[ast.Raise()]))
  return n
receipt={'sourceUrl':url,'archiveSha256':sha,'refVersion':'0.3.1','osSourcePin':'python-shamir-mnemonic0.3-setuptools','files':{},'scope':'All core/share/cipher/recovery algorithms; actual entropy provider required for generation'}
with tarfile.open(fileobj=io.BytesIO(b)) as t:
 prefix='python-shamir-mnemonic-0.3-setuptools/'
 def read(name):return t.extractfile(prefix+name).read()
 (root/'app/LICENSE.shamir-mnemonic').write_bytes(read('LICENSE'))
 words=read('shamir_mnemonic/wordlist.txt');assert hashlib.sha256(words).hexdigest()=='bcc4555340332d169718aed8bf31dd9d5248cb7da6e5d355140ef4f1e601eec3'
 receipt['wordlistSha256']=hashlib.sha256(words).hexdigest();receipt['refWordlistMatch']='Read-only REF sha256sum, same hash'
 for name in ('__init__','constants','utils','rs1024','wordlist','cipher','share','shamir','recovery'):
  raw=read('shamir_mnemonic/'+name+'.py');text=raw.decode();tree=ast.parse(text)
  notices='\n'.join(text.splitlines()[:tree.body[0].lineno-1])+'\n'
  header='# Copyright2019 SatoshiLabs; MIT, see ../LICENSE.shamir-mnemonic\n'+notices+'from collections import namedtuple as _namedtuple\nfrom seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable\n'
  if name=='wordlist':header+='_FROZEN_WORDLIST='+repr(tuple(words.decode().splitlines()))+'\n'
  if name=='shamir':header+="def _random_bytes(n):return _dependency('secrets','token_bytes')(n)\n"
  if name=='recovery':header+="def replace(value,**changes):\n    fields=value._asdict()\n    fields.update(changes)\n    return type(value)(**fields)\n"
  tree=Port().visit(Records().visit(tree));out=root/'app/shamir_mnemonic'/(name+'.py');out.parent.mkdir(parents=True,exist_ok=True)
  out.write_text(header+ast.unparse(ast.fix_missing_locations(tree))+'\n')
  receipt['files'][name]={'sourceSha256':hashlib.sha256(raw).hexdigest(),'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest()}
 (root/'app/shamir-vectors.json').write_bytes(read('vectors.json'))
 receipt['vectorsSha256']=hashlib.sha256(read('vectors.json')).hexdigest()
# Actual upstream MicroPython defaultdict; no fake dictionary implementation.
lib=root/'.tools/micropython/lib/micropython-lib'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=lib,text=True).strip()=='6ae440a8a144233e6e703f6759b7e7a0afaa37a4'
raw=(lib/'python-stdlib/collections-defaultdict/collections/defaultdict.py').read_bytes()
(root/'app/seedsigner_port/defaultdict.py').write_bytes(b'# From pinned micropython-lib; see ../LICENSE.micropython-lib\n'+raw+b'\n    # Delegate actual mapping operations required by original RecoveryState.\n    def __getattr__(self,name):return getattr(self.d,name)\n    def __iter__(self):return iter(self.d)\n    def __len__(self):return len(self.d)\n    def __bool__(self):return bool(self.d)\n')
receipt['defaultdict']={'sourceSha256':hashlib.sha256(raw).hexdigest(),'outputSha256':hashlib.sha256((root/'app/seedsigner_port/defaultdict.py').read_bytes()).hexdigest(),'changes':['Delegate mapping methods, iteration, length and truth to actual underlying dictionary for original RecoveryState']}
(root/'app/shamir-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
