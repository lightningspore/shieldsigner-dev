# SPDX-License-Identifier: MIT
# Generated from CPython re; public data only.
import re
import camera
import gc

assert len('é🙂') == 2
assert 'é🙂'[1] == '🙂'
assert 'é🙂'.encode().decode() == 'é🙂'
try:
    bytes([255]).decode('utf-8')
except UnicodeError:
    pass
else:
    raise AssertionError('invalid UTF8 accepted')
baseline = camera.settings()['rust_heap_bytes']
m = re.search('^UR:CRYPTO-PSBT/', 'ur:crypto-psbt/abc', 2)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(1))) == (
    'ur:crypto-psbt/',
    (),
    ((0, 15),),
)
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.search('^p(\\d+)of(\\d+) ([A-Za-z0-9+\\/=]+$)', 'p2of3 cHNidP8=', 2)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(4))) == (
    'p2of3 cHNidP8=',
    ('2', '3', 'cHNidP8='),
    ((0, 14), (1, 2), (4, 5), (6, 14)),
)
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.search('^B\\$[2HZ]P[0-9A-Z]{4}', 'B$ZP0100part', 0)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(1))) == ('B$ZP0100', (), ((0, 8),))
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.fullmatch('(?:\\d{4}){12,24}', '000100010001000100010001000100010001000100010001', 0)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(1))) == (
    '000100010001000100010001000100010001000100010001',
    (),
    ((0, 48),),
)
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.fullmatch('(?:\\d{4}){12,24}', 'prefix000100010001000100010001000100010001000100010001', 0)
assert m is None
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.match('^oT(\\d{12}(\\.\\d{2})?|0)$', 'oT261114123456.78', 0)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(3))) == (
    'oT261114123456.78',
    ('261114123456.78', '.78'),
    ((0, 17), (2, 17), (14, 17)),
)
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.match('^oT(\\d{12}(\\.\\d{2})?|0)$', 'oT0', 0)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(3))) == (
    'oT0',
    ('0', None),
    ((0, 3), (2, 3), (-1, -1)),
)
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.search('^(\\d+)\\D*(\\d+)', '2 of 3', 0)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(3))) == (
    '2 of 3',
    ('2', '3'),
    ((0, 6), (0, 1), (5, 6)),
)
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.search('^bitcoin\\:.*', 'BITCOIN:bc1qpublic', 2)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(1))) == (
    'BITCOIN:bc1qpublic',
    (),
    ((0, 18),),
)
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.search('(?P<name>ab)(c)?', 'é🙂 ab', 0)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(3))) == (
    'ab',
    ('ab', None),
    ((3, 5), (3, 5), (-1, -1)),
)
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.search('(β+)', 'é🙂 ββ', 0)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(2))) == (
    'ββ',
    ('ββ',),
    ((3, 5), (3, 5)),
)
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.fullmatch('\\w+', 'café', 0)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(1))) == ('café', (), ((0, 4),))
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.fullmatch('\\w+', 'café', 256)
assert m is None
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.search('^b.$', 'a\nbx\nc', 8)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(1))) == ('bx', (), ((2, 4),))
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.fullmatch('a.*c', 'a\nbc', 16)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(1))) == ('a\nbc', (), ((0, 4),))
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.fullmatch('a b # comment', 'ab', 64)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(1))) == ('ab', (), ((0, 2),))
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.search(b'(\x00\xff)', b'prefix\x00\xfftail', 0)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(2))) == (
    b'\x00\xff',
    (b'\x00\xff',),
    ((6, 8), (6, 8)),
)
assert camera.settings()['rust_heap_bytes'] == baseline
m = re.search('', 'é🙂', 0)
assert (m.group(), m.groups(), tuple(m.span(i) for i in range(1))) == ('', (), ((0, 0),))
assert camera.settings()['rust_heap_bytes'] == baseline
assert re.search('a', 'abc').group(0) == 'a'
assert re.search('(a)(b)', 'ab').group(1, 2) == ('a', 'b')
assert re.search('(a)?b', 'b').groups('x') == ('x',)
for pattern in ('[', '('):
    try:
        re.search(pattern, 'text')
    except re.error:
        pass
    else:
        raise AssertionError('invalid pattern accepted')
for pattern, subject, flags in [
    ('()' * 64, '', 0),
    ('a', 'a', 4),
    (b'a', b'a', 32),
    ('a', 'a', 288),
]:
    try:
        re.search(pattern, subject, flags)
    except re.error:
        pass
    else:
        raise AssertionError('unsupported regex request accepted')
assert camera.settings()['rust_heap_bytes'] == baseline
try:
    re.search(b'a', 'a')
except TypeError:
    pass
else:
    raise AssertionError('mixed types accepted')
gc.collect()
assert camera.settings()['rust_heap_bytes'] == baseline
print('@@PASS native-regex-unicode')
