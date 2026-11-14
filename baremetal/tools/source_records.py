# SPDX-License-Identifier: MIT
"""AST representation boundary for required immutable records on MicroPython."""
import ast
class Records(ast.NodeTransformer):
 def visit_ClassDef(self,n):
  frozen=any(isinstance(d,ast.Call) and isinstance(d.func,ast.Name) and d.func.id=='dataclass' and any(k.arg=='frozen' and isinstance(k.value,ast.Constant) and k.value.value for k in d.keywords) for d in n.decorator_list)
  named=any(isinstance(b,ast.Name) and b.id=='NamedTuple' for b in n.bases)
  if frozen or named:
   fields=[a.target.id for a in n.body if isinstance(a,ast.AnnAssign)]
   assert all(a.value is None for a in n.body if isinstance(a,ast.AnnAssign))
   base=ast.Call(func=ast.Name(id='_namedtuple',ctx=ast.Load()),args=[ast.Constant('_'+n.name+'Fields'),ast.Tuple(elts=[ast.Constant(f) for f in fields],ctx=ast.Load())],keywords=[])
   if named:
    n.bases=[base];n.decorator_list=[]
    n.body=[a for a in n.body if not isinstance(a,ast.AnnAssign)]
    n.body.append(ast.Assign(targets=[ast.Name(id='_fields',ctx=ast.Store())],value=ast.Tuple(elts=[ast.Constant(f) for f in fields],ctx=ast.Load())))
    n.body+=ast.parse("def __setattr__(self,name,value):raise AttributeError('frozen record')\ndef __delattr__(self,name):raise AttributeError('frozen record')\n").body
    return self.generic_visit(n)
   n.bases=[base];n.decorator_list=[];n.body=[a for a in n.body if not isinstance(a,ast.AnnAssign)]
   n.body+=ast.parse('''def __setattr__(self,name,value):raise AttributeError('frozen record')
def __delattr__(self,name):raise AttributeError('frozen record')
def __eq__(self,other):return type(self) is type(other) and tuple(self)==tuple(other)
def __ne__(self,other):return not self==other
def __hash__(self):return hash(tuple(self))
''').body
  return self.generic_visit(n)
