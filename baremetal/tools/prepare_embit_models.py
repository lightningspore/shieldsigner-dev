# SPDX-License-Identifier: MIT
"""Freeze actual embit0.8.0 parsing/model modules; defer only missing curve import."""
import ast,hashlib,io,json,tarfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
raw=(root/'.tools/embit-0.8.0/source.tar.gz').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='8bf4b10073c67400370ce523fb16f035fe759f6fdd987c579bdcc268d75ed770'
class Strip(ast.NodeTransformer):
 def visit_FunctionDef(self,n):
  n.returns=None
  for a in [*n.args.args,*n.args.posonlyargs,*n.args.kwonlyargs,*([n.args.vararg] if n.args.vararg else []),*([n.args.kwarg] if n.args.kwarg else [])]:a.annotation=None
  return self.generic_visit(n)
 def visit_Try(self,n):
  n=self.generic_visit(n)
  if any(h.type is None or (isinstance(h.type,ast.Name) and h.type.id in ('Exception','BaseException')) for h in n.handlers):n.handlers.insert(0,ast.ExceptHandler(type=ast.Name(id='FeatureUnavailable',ctx=ast.Load()),name=None,body=[ast.Raise()]))
  return n
 def visit_AnnAssign(self,n):return ast.copy_location(ast.Assign(targets=[n.target],value=self.visit(n.value)),n) if n.value else None
receipt={'version':'0.8.0','sdistSha256':hashlib.sha256(raw).hexdigest(),'files':{},'scope':'Original parser/model source; curve and entropy operations remain unavailable until actual providers exist'}
with tarfile.open(fileobj=io.BytesIO(raw)) as t:
 for name in ('base','base58','bech32','compact','hashes','networks','script','transaction','ec','bip32','psbt','misc'):
  b=t.extractfile('embit-0.8.0/src/embit/'+name+'.py').read();s=b.decode();changes=['Remove type annotations','Propagate unavailable native dependencies before broad exception handlers']
  if name=='misc':
   assert s.count('    import secp256k1\n')==1
   s=s.replace('    import secp256k1\n',"    from seedsigner_port.deferred_module import DeferredModule\n    secp256k1=DeferredModule('secp256k1')\n")
   changes.append('Defer unavailable secp256k1 module until an actual curve method is requested; never supply curve results or entropy')
  if name=='ec':
   original=ast.parse(s)
   assignment=original.body[-1]
   assert isinstance(assignment,ast.Assign) and ast.unparse(assignment.targets[0])=='NUMS_PUBKEY'
   expr=ast.unparse(assignment.value)
   original.body.pop()
   original.body.extend(ast.parse("def __getattr__(name):\n    if name!='NUMS_PUBKEY':raise AttributeError(name)\n    global NUMS_PUBKEY\n    NUMS_PUBKEY="+expr+"\n    return NUMS_PUBKEY\n").body)
   s=ast.unparse(original)
   changes.append('Compute actual NUMS_PUBKEY lazily through module __getattr__; no fabricated point or curve result')
  tree=ast.parse(s);prefix='\n'.join(s.splitlines()[:tree.body[0].lineno-1])+'\n'
  out=root/'app/embit'/(name+'.py');out.write_text('# Copyright2020 Stepan Snigirev; MIT, see ../LICENSE.embit\n'+prefix+'from seedsigner_port.decode_platform import FeatureUnavailable\n'+ast.unparse(ast.fix_missing_locations(Strip().visit(tree)))+'\n')
  receipt['files'][name]={'sourceSha256':hashlib.sha256(b).hexdigest(),'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest(),'changes':changes}
(root/'app/embit-models-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
