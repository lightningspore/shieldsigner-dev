# SPDX-License-Identifier: MIT
"""Retain upstream MicroPython HMAC stream logic with native API boundaries."""

import pyformat  # noqa: F401  (formats generated Python on write)
from pathlib import Path
import hashlib, json, subprocess

root = Path(__file__).resolve().parents[1]
lib = root / '.tools/micropython/lib/micropython-lib'
assert (
    subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=lib, text=True).strip()
    == '6ae440a8a144233e6e703f6759b7e7a0afaa37a4'
)
p = lib / 'python-stdlib/hmac/hmac.py'
raw = p.read_bytes()
s = raw.decode()
assert (
    hashlib.sha256(raw).hexdigest()
    == '289072406e19751e3bda28b759dbf57469cb918726e8539812252d9c22e12d1c'
)
s = s.replace('digestmod = hashlib.md5', "raise TypeError('Missing required digestmod')")
assert s.count('self.__class__.__new__(self.__class__)') == 1
s = s.replace('self.__class__.__new__(self.__class__)', 'object.__new__(self.__class__)')
s += '''
# Native boundary additions; original HMAC streaming implementation above.
import _native_hash
compare_digest=_native_hash.compare_digest
def digest(key,msg,digest):
    if isinstance(digest,str):
        from hashlib import _info
        return _native_hash.hmac(_info(digest)[1][0],key,msg)
    return HMAC(key,msg,digest).digest()
'''
out = root / 'app/hmac.py'
out.write_text('# Derived from pinned micropython-lib HMAC; see LICENSE.micropython-lib.\n' + s)
(root / 'app/hash-libs-provenance.json').write_text(
    json.dumps(
        {
            'micropythonLibCommit': '6ae440a8a144233e6e703f6759b7e7a0afaa37a4',
            'hmac': {
                'sourceSha256': hashlib.sha256(raw).hexdigest(),
                'outputSha256': hashlib.sha256(out.read_bytes()).hexdigest(),
                'changes': [
                    'Explicit digestmod required, matching current CPython API',
                    'object.__new__ supplies missing inherited MicroPython allocation entry',
                    'Add native one-shot digest and subtle-backed compare_digest',
                ],
            },
        },
        indent=2,
    )
    + '\n'
)
