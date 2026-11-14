# SPDX-License-Identifier: MIT
"""PCRE2-backed match/search/fullmatch for the original app's regex patterns.

No JIT or threads. Explicit native resource limits; unsupported API fails rather
than silently interpreting a pattern using MicroPython's smaller re1.5 syntax.
"""
import _regex
IGNORECASE=I=2
MULTILINE=M=8
DOTALL=S=16
UNICODE=U=32
VERBOSE=X=64
ASCII=A=256
class error(ValueError):
    pass
PatternError=error
class Match:
    def __init__(self,string,result):
        self.string=string
        self._groups,self._spans=result
    def group(self,*indices):
        if not indices:return self._groups[0]
        values=[]
        for index in indices:
            if not isinstance(index,int) or index<0 or index>=len(self._groups):raise IndexError('no such group')
            values.append(self._groups[index])
        return values[0] if len(values)==1 else tuple(values)
    def groups(self,default=None):
        return tuple(default if v is None else v for v in self._groups[1:])
    def span(self,index=0):
        if not isinstance(index,int) or index<0 or index>=len(self._spans):raise IndexError('no such group')
        return self._spans[index]
    def start(self,index=0):return self.span(index)[0]
    def end(self,index=0):return self.span(index)[1]
def _run(pattern,string,flags,mode):
    try:result=_regex.run(pattern,string,flags,mode)
    except ValueError as exc:raise error(str(exc))
    return None if result is None else Match(string,result)
def search(pattern,string,flags=0):return _run(pattern,string,flags,0)
def match(pattern,string,flags=0):return _run(pattern,string,flags,1)
def fullmatch(pattern,string,flags=0):return _run(pattern,string,flags,2)
