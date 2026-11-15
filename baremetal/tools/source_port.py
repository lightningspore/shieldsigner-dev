# SPDX-License-Identifier: MIT
"""Scope-aware import/type/platform boundary shared by original app source ports."""
import ast
class Bound(ast.NodeVisitor):
 def __init__(self):self.names=set()
 def visit_Name(self,n):
  if isinstance(n.ctx,ast.Store):self.names.add(n.id)
 def visit_Import(self,n):self.names.update(a.asname or a.name.split('.')[0] for a in n.names)
 def visit_ImportFrom(self,n):self.names.update(a.asname or a.name for a in n.names)
 def visit_FunctionDef(self,n):self.names.add(n.name)
 def visit_ClassDef(self,n):self.names.add(n.name)
class Port(ast.NodeTransformer):
 def __init__(self,tree,module,classes=(),bindings=None):
  self.module=module;self.package=module.rsplit('.',1)[0];self.classes=set(classes);self.locals=[];self.bindings={}
  for n in tree.body:
   if isinstance(n,ast.Import):
    for a in n.names:self.bindings[a.asname or a.name]=(a.name,None)
   elif isinstance(n,ast.ImportFrom):
    for a in n.names:self.bindings[a.asname or a.name]=(self.absolute(n),a.name)
  self.bindings.pop('logging',None);self.bindings.pop('dataclass',None);self.bindings.pop('field',None)
  if bindings:self.bindings.update(bindings)
 def absolute(self,n):
  if not n.level:return n.module
  p=self.package.split('.')
  return '.'.join(p[:len(p)-n.level+1]+([n.module] if n.module else []))
 def call(self,module,attribute):return ast.Call(func=ast.Name(id='_dependency',ctx=ast.Load()),args=[ast.Constant(module),ast.Constant(attribute)],keywords=[])
 def visit_Name(self,n):
  if not isinstance(n.ctx,ast.Load) or any(n.id in s for s in self.locals):return n
  if n.id in self.classes:return ast.copy_location(ast.Call(func=ast.Name(id='_resolve',ctx=ast.Load()),args=[ast.Constant(n.id)],keywords=[]),n)
  if n.id in self.bindings:return ast.copy_location(self.call(*self.bindings[n.id]),n)
  return n
 def visit_FunctionDef(self,n):
  n.returns=None
  n.decorator_list=[self.visit(d) for d in n.decorator_list]
  n.args.defaults=[self.visit(d) for d in n.args.defaults]
  n.args.kw_defaults=[self.visit(d) if d else None for d in n.args.kw_defaults]
  args=[*n.args.args,*n.args.kwonlyargs,*n.args.posonlyargs,*([n.args.vararg] if n.args.vararg else []),*([n.args.kwarg] if n.args.kwarg else [])]
  for a in args:a.annotation=None
  bound=Bound()
  for b in n.body:bound.visit(b)
  bound.names.update(a.arg for a in args);self.locals.append(bound.names)
  n.body=self._body(n.body);self.locals.pop();return n
 def _body(self,body):
  out=[]
  for n in body:
   value=self.visit(n)
   if isinstance(value,list):out.extend(value)
   elif value is not None:out.append(value)
  return out or [ast.Pass()]
 def visit_Import(self,n):return [ast.Assign(targets=[ast.Name(id=a.asname or a.name,ctx=ast.Store())],value=self.call(a.name,None)) for a in n.names]
 def visit_ImportFrom(self,n):
  if n.module in ('typing','__future__'):return None
  return [ast.Assign(targets=[ast.Name(id=a.asname or a.name,ctx=ast.Store())],value=self.call(self.absolute(n),a.name)) for a in n.names]
 def visit_AnnAssign(self,n):return ast.copy_location(ast.Assign(targets=[n.target],value=self.visit(n.value)),n) if n.value is not None else None
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id in ('logger','logging','traceback'):return ast.copy_location(ast.Pass(),n)
  return self.generic_visit(n)
 def visit_Try(self,n):
  n=self.generic_visit(n)
  if any(h.type is None or (isinstance(h.type,ast.Name) and h.type.id in ('Exception','BaseException')) for h in n.handlers):n.handlers.insert(0,ast.ExceptHandler(type=ast.Name(id='FeatureUnavailable',ctx=ast.Load()),name=None,body=[ast.Raise()]))
  return n
