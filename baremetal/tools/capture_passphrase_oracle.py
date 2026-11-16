# SPDX-License-Identifier: MIT
"""Read-only REF stdlib oracle; public fixtures, no application imports or writes."""

import base64, hashlib, json, random, shlex, subprocess, zlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
rng = random.Random(20261114)
cases = [
    '',
    'é',
    'e\u0301',
    '㍍ガバヴァぱばぐゞちぢ十人十色',
    '\x00',
    '\\u0061',
    '\\\\u0061',
    '\\u005cu0061',
    '\\uD800\\uZ',
    '\\u',
    '\\u123',
    '\\U0001f600',
    '\\n',
    'abc\\',
    '\\x41',
]
atoms = [
    'a',
    'u',
    'U',
    '\\',
    '\\u0061',
    '\\u00e9',
    '\\uD800',
    '\\uDFFF',
    '\\uZ',
    '\\u123',
    '\\x20',
    'é',
    '\x00',
    '😀',
    'ガ',
    '\ufdfa',
]
cases += [''.join(rng.choice(atoms) for _ in range(rng.randrange(1, 15))) for _ in range(500)]
script = r'''import sys,json,re,unicodedata,warnings,base64,zlib
cases=json.loads(zlib.decompress(base64.b64decode('PACKED_CASES')))
warnings.simplefilter('ignore',DeprecationWarning)
rows=[]
for value in cases:
 saved=value
 if value:
  value=re.sub(r'\\(?!u)',r'\\\\',value)
  try:value=bytes(value,encoding='raw_unicode_escape').decode('unicode_escape')
  except UnicodeDecodeError:value=saved
 value=unicodedata.normalize('NFKD',value)
 try:value.encode('utf8');valid=True
 except UnicodeEncodeError:valid=False
 rows.append({'input':saved,'expected':value,'utf8':valid})
print(json.dumps({'refPython':sys.version.split()[0],'unicodeVersion':unicodedata.unidata_version,'cases':rows},ensure_ascii=True))
'''
rows = []
for start in range(0, len(cases), 20):
    packed = base64.b64encode(
        zlib.compress(json.dumps(cases[start : start + 20]).encode())
    ).decode()
    command = 'PYTHONDONTWRITEBYTECODE=1 python3 -c ' + shlex.quote(
        script.replace('PACKED_CASES', packed)
    )
    p = subprocess.run(
        ['adb', '-s', '0a523b8b23110ffc', 'shell', command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors='replace'))
    d = json.loads(p.stdout)
    assert d['refPython'] == '3.12.10' and d['unicodeVersion'] == '15.0.0'
    rows.extend(d['cases'])
d['cases'] = rows
d['sourceSeedSha256'] = hashlib.sha256(
    (root / '.tools/ref-app-source/seedsigner/models/seed.py').read_bytes()
).hexdigest()
assert (
    d['sourceSeedSha256']
    == json.loads((root.parent / 'firmware/lvgl-app/source-guards.json').read_text())[
        'models/seed.py'
    ]
)
d['scope'] = (
    'Read-only REF stdlib execution of original Seed.set_passphrase codec expression; public fixtures'
)
(root / 'unicode/passphrase-ref-oracle.json').write_text(
    json.dumps(d, indent=2, ensure_ascii=True) + '\n'
)
print(len(d['cases']), d['unicodeVersion'])
