# SPDX-License-Identifier: MIT
"""Retain all locked original Seed classes; adapt platform boundaries explicitly."""
import ast,hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];repo=root.parent
source=repo/'dist/firmware/sources/lvgl/application'
lock=json.loads((repo/'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==lock['commit']
p=source/'src/seedsigner/models/seed.py';raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()==json.loads((repo/'firmware/lvgl-app/source-guards.json').read_text())['models/seed.py']
tree=ast.parse(raw);bindings={}
for n in tree.body:
 if isinstance(n,ast.Import):
  for a in n.names:bindings[a.asname or a.name]=(a.name,None)
 elif isinstance(n,ast.ImportFrom):
  for a in n.names:bindings[a.asname or a.name]=(n.module,a.name)
for name in ('logging','unicodedata','hashlib','hmac','List','SettingsConstants','wipe_bytes','wipe_string','wipe_list'):bindings.pop(name,None)
class Port(ast.NodeTransformer):
 def __init__(self):self.current=None
 def visit_ClassDef(self,n):
  old=self.current;self.current=n.name;n=self.generic_visit(n);self.current=old;return n
 def visit_FunctionDef(self,n):
  n.returns=None
  for a in [*n.args.args,*n.args.posonlyargs,*n.args.kwonlyargs,*([n.args.vararg] if n.args.vararg else []),*([n.args.kwarg] if n.args.kwarg else [])]:a.annotation=None
  if n.name=='set_passphrase' and self.current in ('Seed','ElectrumSeed'):
   value='_normalize_passphrase(passphrase)'
   if self.current=='ElectrumSeed':value='ElectrumSeed.normalize_electrum_passphrase('+value+')'
   n.body=ast.parse('self._passphrase='+value+'\nif regenerate_seed:self._generate_seed()').body
  return self.generic_visit(n)
 def visit_AnnAssign(self,n):
  return ast.copy_location(ast.Assign(targets=[n.target],value=self.visit(n.value)),n) if n.value is not None else None
 def visit_Name(self,n):
  if isinstance(n.ctx,ast.Load) and n.id in bindings:
   module,attr=bindings[n.id]
   return ast.copy_location(ast.Call(func=ast.Name(id='_dependency',ctx=ast.Load()),args=[ast.Constant(module),ast.Constant(attr)],keywords=[]),n)
  return n
 def visit_ImportFrom(self,n):
  return [ast.copy_location(ast.Assign(targets=[ast.Name(id=a.asname or a.name,ctx=ast.Store())],value=ast.Call(func=ast.Name(id='_dependency',ctx=ast.Load()),args=[ast.Constant(n.module),ast.Constant(a.name)],keywords=[])),n) for a in n.names]
 def visit_Import(self,n):
  return [ast.copy_location(ast.Assign(targets=[ast.Name(id=a.asname or a.name,ctx=ast.Store())],value=ast.Call(func=ast.Name(id='_dependency',ctx=ast.Load()),args=[ast.Constant(a.name),ast.Constant(None)],keywords=[])),n) for a in n.names]
 def visit_Try(self,n):
  n=self.generic_visit(n)
  if any(h.type is None or (isinstance(h.type,ast.Name) and h.type.id in ('Exception','BaseException')) for h in n.handlers):n.handlers.insert(0,ast.ExceptHandler(type=ast.Name(id='FeatureUnavailable',ctx=ast.Load()),name=None,body=[ast.Raise()]))
  return n
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=='logger':return ast.copy_location(ast.Pass(),n)
  return self.generic_visit(n)
classes=[n for n in tree.body if isinstance(n,ast.ClassDef)]
original={n.name:hashlib.sha256(ast.get_source_segment(raw.decode(),n).encode()).hexdigest() for n in classes}
classes=[Port().visit(n) for n in classes]
header='''# SPDX-License-Identifier: MIT
# Copyright2021 SeedSigner; upstream notice: ../LICENSE.SeedSigner.
# Generated from all original Seed classes; unported features fail explicitly.
import unicodedata
import hashlib
import hmac
from seedsigner_port.settings_schema import SettingsConstants
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
from seedsigner_port.secure_delete import wipe_bytes,wipe_string,wipe_list
from seedsigner_port.passphrase import normalize_passphrase as _normalize_passphrase
'''
out=root/'app/seedsigner_port/seed.py';out.write_text(header+ast.unparse(ast.fix_missing_locations(ast.Module(body=classes,type_ignores=[])))+'\n')
(root/'app/seed-provenance.json').write_text(json.dumps({'application':lock,'source':'src/seedsigner/models/seed.py','sourceSha256':hashlib.sha256(raw).hexdigest(),'classes':original,'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest(),'transformations':['Remove type annotations','Defer actual imports; unavailable dependencies propagate before broad parse handlers','Replace Seed and Electrum set_passphrase codec boundary with REF-tested adapter; preserve Electrum normalization','Use native GC-guarded best-effort secure_delete boundary','Remove logger payload calls'],'scope':'All original classes retained; class presence does not qualify alternate seed, curve or workflow paths'},indent=2)+'\n')
