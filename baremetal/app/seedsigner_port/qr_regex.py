# SPDX-License-Identifier: MIT
"""Compiled binary-pattern facade over the actual bounded native PCRE2 engine.

Only used by the pinned QR encoder. No Python regex interpreter or pattern stub.
"""
import re as _re
class Pattern:
    def __init__(self,pattern,flags=0):
        if not isinstance(pattern,(str,bytes)):raise TypeError('Expected regex pattern')
        self.pattern=pattern;self.flags=flags
    def match(self,data):
        # CPython \Z is a strict end; PCRE2 \Z also allows a final newline.
        end=b'\\Z' if isinstance(self.pattern,bytes) else '\\Z'
        return (_re.fullmatch if self.pattern.endswith(end) else _re.match)(self.pattern,data,self.flags)
    def search(self,data):return _re.search(self.pattern,data,self.flags)

def compile(pattern,flags=0):return Pattern(pattern,flags)
def search(pattern,data):return pattern.search(data) if isinstance(pattern,Pattern) else _re.search(pattern,data)
def escape(pattern):
    if isinstance(pattern,bytes):
        out=bytearray()
        for value in pattern:
            if value in b'()[]{}?*+-|^$\\.&~# \t\n\r\v\f':out.append(92)
            out.append(value)
        return bytes(out)
    if isinstance(pattern,str):
        return ''.join(('\\'+value) if value in '()[]{}?*+-|^$\\.&~# \t\n\r\v\f' else value for value in pattern)
    raise TypeError('Expected str or bytes')
