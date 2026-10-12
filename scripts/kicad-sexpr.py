"""Small KiCad S-expression reader and span scanner for metadata tooling."""
import json,re

def parse(text):
 stack=[];root=None
 for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',text):
  if token=='(':
   node=[]
   if stack:stack[-1].append(node)
   stack.append(node)
  elif token==')':root=stack.pop()
  else:stack[-1].append(json.loads(token) if token.startswith('"') else token)
 return root

def children(node,key):return [x for x in node if isinstance(x,list) and x and x[0]==key]
def one(node,key):return next(iter(children(node,key)),[])
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
   start=stack.pop();yield start,i+1,text[start:i+1]
