# SPDX-License-Identifier: MIT
"""Freeze complete original raw PSBT framing, with actual native embit parsing."""
import ast,hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];repo=root.parent
src=repo/'dist/firmware/sources/lvgl/application/src/seedsigner/models'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=src,text=True).strip()==json.loads((repo/'firmware/lvgl-app/sources.lock.json').read_text())['application']['commit']
guards=json.loads((repo/'firmware/lvgl-app/source-guards.json').read_text())
guards['models/psbt_framing.py']='d75feed7b2128507b3b32428ab28aef2df720ea0770fb1b0d44987577ffd3e10'
class Strip(ast.NodeTransformer):
 def visit_FunctionDef(self,n):
  n.returns=None
  for a in n.args.args+n.args.kwonlyargs+n.args.posonlyargs:a.annotation=None
  return self.generic_visit(n)
 def visit_AnnAssign(self,n):return ast.copy_location(ast.Assign(targets=[n.target],value=self.visit(n.value)),n) if n.value else None
 def visit_ImportFrom(self,n):
  if n.module=='__future__':return None
  if n.module=='seedsigner.models.psbt_parser':n.module='seedsigner_port.psbt_errors'
  return n
 def visit_Call(self,n):
  if ast.unparse(n)=='len(stream.getbuffer())':return ast.Call(func=ast.Name(id='_stream_length',ctx=ast.Load()),args=[ast.Name(id='stream',ctx=ast.Load())],keywords=[])
  return self.generic_visit(n)
 def visit_Try(self,n):
  n=self.generic_visit(n)
  if any(h.type is None or (isinstance(h.type,ast.Name) and h.type.id in ('Exception','BaseException')) for h in n.handlers):n.handlers.insert(0,ast.ExceptHandler(type=ast.Name(id='FeatureUnavailable',ctx=ast.Load()),name=None,body=[ast.Raise()]))
  return n
receipt={}
for filename in ('psbt_parser.py','psbt_framing.py'):
 raw=(src/filename).read_bytes();assert hashlib.sha256(raw).hexdigest()==guards['models/'+filename]
 tree=ast.parse(raw)
 if filename=='psbt_parser.py':tree=ast.Module(body=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in ('RejectCode','InvalidPSBTError')],type_ignores=[])
 result=ast.unparse(ast.fix_missing_locations(Strip().visit(tree)))+'\n'
 header='# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\nfrom seedsigner_port.decode_platform import FeatureUnavailable\n'
 if filename=='psbt_framing.py':header+='''def _stream_length(stream):
    pos=stream.tell()
    stream.seek(0,2)
    size=stream.tell()
    stream.seek(pos)
    return size
'''
 name='psbt_errors.py' if filename=='psbt_parser.py' else filename
 out=root/'app/seedsigner_port'/name;out.write_text(header+result)
 receipt[filename]={'sourceSha256':hashlib.sha256(raw).hexdigest(),'output':name,'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest(),'scope':'Actual RejectCode/InvalidPSBTError classes only; PSBTParser remains unported' if filename=='psbt_parser.py' else 'Whole original framing module; BytesIO length from seek/tell, native embit; unavailable dependencies propagate'}
(root/'app/psbt-framing-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
