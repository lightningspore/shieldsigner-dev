# SPDX-License-Identifier: MIT
"""CPython reference outputs for original app patterns and UTF8 spans."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
cases=[
('search',r'^UR:CRYPTO-PSBT/','ur:crypto-psbt/abc',re.I),
('search',r'^p(\d+)of(\d+) ([A-Za-z0-9+\/=]+$)','p2of3 cHNidP8=',re.I),
('search',r'^B\$[2HZ]P[0-9A-Z]{4}','B$ZP0100part',0),
('fullmatch',r'(?:\d{4}){12,24}','0001'*12,0),
('fullmatch',r'(?:\d{4}){12,24}','prefix'+'0001'*12,0),
('match',r'^oT(\d{12}(\.\d{2})?|0)$','oT261114123456.78',0),
('match',r'^oT(\d{12}(\.\d{2})?|0)$','oT0',0),
('search',r'^(\d+)\D*(\d+)','2 of 3',0),
('search',r'^bitcoin\:.*','BITCOIN:bc1qpublic',re.I),
('search',r'(?P<name>ab)(c)?','é🙂 ab',0),
('search',r'(β+)','é🙂 ββ',0),
('fullmatch',r'\w+','café',0),
('fullmatch',r'\w+','café',re.A),
('search',r'^b.$','a\nbx\nc',re.M),
('fullmatch',r'a.*c','a\nbc',re.S),
('fullmatch',r'a b # comment','ab',re.X),
('search',b'(\x00\xff)',b'prefix\x00\xfftail',0),
('search',r'','é🙂',0),
]
code='''# SPDX-License-Identifier: MIT
# Generated from CPython re; public data only.
import re
import camera
import gc
assert len('é🙂')==2
assert 'é🙂'[1]=='🙂'
assert 'é🙂'.encode().decode()=='é🙂'
try:bytes([255]).decode('utf-8')
except UnicodeError:pass
else:raise AssertionError('invalid UTF8 accepted')
baseline=camera.settings()['rust_heap_bytes']
'''
for method,pattern,text,flags in cases:
 m=getattr(re,method)(pattern,text,flags)
 result=None if m is None else (m.group(),m.groups(),tuple(m.span(i) for i in range(len(m.groups())+1)))
 code+='m=re.'+method+'('+repr(pattern)+','+repr(text)+','+str(int(flags))+')\n'
 code+='assert '+('m is None' if result is None else '(m.group(),m.groups(),tuple(m.span(i) for i in range('+str(len(m.groups())+1)+'))) == '+repr(result))+'\n'
 code+="assert camera.settings()['rust_heap_bytes']==baseline\n"
code+='''assert re.search('a','abc').group(0)=='a'
assert re.search('(a)(b)','ab').group(1,2)==('a','b')
assert re.search('(a)?b','b').groups('x')==('x',)
for pattern in ('[','('):
    try:re.search(pattern,'text')
    except re.error:pass
    else:raise AssertionError('invalid pattern accepted')
for pattern,subject,flags in [('()'*64,'',0),('a','a',4),(b'a',b'a',32),('a','a',288)]:
    try:re.search(pattern,subject,flags)
    except re.error:pass
    else:raise AssertionError('unsupported regex request accepted')
assert camera.settings()['rust_heap_bytes']==baseline
try:re.search(b'a','a')
except TypeError:pass
else:raise AssertionError('mixed types accepted')
gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS native-regex-unicode')
'''
(root/'micropython/regex_gate.py').write_text(code)
