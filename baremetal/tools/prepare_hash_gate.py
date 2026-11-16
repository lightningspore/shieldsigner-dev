# SPDX-License-Identifier: MIT
"""Public CPython/RFC reference vectors for the real native RustCrypto gate."""

import pyformat  # noqa: F401  (formats generated Python on write)
import hashlib, hmac, json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
names = ('sha224', 'sha256', 'sha384', 'sha512', 'sha1', 'ripemd160')
code = '''# SPDX-License-Identifier: MIT
# Generated public data only; CPython reference plus RFC4231/RFC6070/BIP39 cases.
import hashlib
import hmac
import binascii
import gc
import time
import camera
baseline=camera.settings()['rust_heap_bytes']
'''
for name in names:
    sample = hashlib.new(name)
    code += 'name=' + repr(name) + '\n'
    code += f"assert (hashlib.new(name).digest_size,hashlib.new(name).block_size)==({sample.digest_size},{sample.block_size})\n"
    for length in (0, 1, 55, 56, 63, 64, 65, 111, 112, 127, 128, 129, 1024):
        data = bytes((i * 17 + 11) & 255 for i in range(length))
        expected = hashlib.new(name, data).hexdigest()
        extended = hashlib.new(name, data + b'public suffix').hexdigest()
        code += 'data=bytes((i*17+11)&255 for i in range(' + str(length) + '))\n'
        code += "state=hashlib.new(name)\nfor offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])\n"
        code += 'assert state.hexdigest()==' + repr(expected) + '\n'
        code += 'assert state.digest()==state.digest()\ncopy=state.copy()\nstate.update(b\'public suffix\')\n'
        code += (
            'assert state.hexdigest()=='
            + repr(extended)
            + '\nassert copy.hexdigest()=='
            + repr(expected)
            + '\n'
        )
        code += 'del state,copy\n'
    for key, msg in [
        (b'public key', b'public message'),
        (bytes([11]) * 20, b'Hi There'),
        (b'K' * 200, b'public long-key message'),
        (b'', b''),
    ]:
        expected = hmac.digest(key, msg, name).hex()
        code += 'key=' + repr(key) + '\nmsg=' + repr(msg) + '\n'
        code += (
            'assert binascii.hexlify(hmac.digest(key,msg,name)).decode()==' + repr(expected) + '\n'
        )
        code += "state=hmac.new(key,msg[:3],name)\ncopy=state.copy()\nstate.update(msg[3:])\ncopy.update(msg[3:])\n"
        code += (
            'assert state.hexdigest()=='
            + repr(expected)
            + '\nassert copy.digest()==state.digest()\n'
        )
        code += 'assert state.digest()==state.digest()\nassert state.name==\'hmac-\'+name\ndel state,copy\n'
    for rounds, length in [
        (1, 1),
        (2, sample.digest_size),
        (65, sample.digest_size + 1),
        (127, sample.digest_size * 2 + 1),
    ]:
        expected = hashlib.pbkdf2_hmac(
            name, b'public password', b'public salt', rounds, length
        ).hex()
        code += (
            'assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b\'public password\',b\'public salt\','
            + str(rounds)
            + ','
            + str(length)
            + ')).decode()=='
            + repr(expected)
            + '\n'
        )
    code += "gc.collect()\nassert camera.settings()['rust_heap_bytes']==baseline\nprint('@@HASH_ALGORITHM_PASS',name)\n"
# Published KAT inputs: RFC6070 SHA1 vectors and BIP39 English first vector.
for name, password, salt, rounds, length in [
    ('sha1', b'password', b'salt', 4096, 20),
    ('sha1', b'pass\0word', b'sa\0lt', 4096, 16),
    ('sha512', ('abandon ' * 11 + 'about').encode(), b'mnemonicTREZOR', 2048, 64),
]:
    expected = hashlib.pbkdf2_hmac(name, password, salt, rounds, length).hex()
    code += (
        'start=time.ticks_ms()\nvalue=hashlib.pbkdf2_hmac('
        + repr(name)
        + ','
        + repr(password)
        + ','
        + repr(salt)
        + ','
        + str(rounds)
        + ','
        + str(length)
        + ')\n'
    )
    code += 'assert binascii.hexlify(value).decode()==' + repr(expected) + '\n'
    code += (
        "print('@@PBKDF2_VECTOR_MS',"
        + repr(name)
        + ','
        + str(rounds)
        + ",(time.ticks_ms()-start)&0xffffffff)\n"
    )
code += '''for name in hashlib.algorithms_available:
    assert hashlib.new(name,bytearray()).digest()==hashlib.new(name,b'').digest()
    state=hashlib.new(name)
    state.update(memoryview(bytearray()))
    assert state.digest()==hashlib.new(name,b'').digest()
assert hmac.digest(bytearray(),bytearray(),'sha256')==hmac.digest(b'',b'','sha256')
assert hashlib.pbkdf2_hmac('sha256',bytearray(),bytearray(),2)==hashlib.pbkdf2_hmac('sha256',b'',b'',2)
assert hmac.compare_digest(bytearray(),bytearray())
assert hmac.digest(b'key',b'message',hashlib.sha512)==hmac.digest(b'key',b'message','sha512')
assert hmac.compare_digest(b'public',b'public')
assert not hmac.compare_digest(b'public',b'Public')
assert not hmac.compare_digest(b'public',b'public extra')
assert hmac.compare_digest('public','public')
for a,b in [('é','é'),('public',b'public')]:
    try:hmac.compare_digest(a,b)
    except TypeError:pass
    else:raise AssertionError('invalid digest comparison accepted')
for value in ['text',123]:
    try:hashlib.sha256(value)
    except TypeError:pass
    else:raise AssertionError('invalid hash data accepted')
for rounds,length in [(0,32),(-1,32),(1,0),(1,4097),(1000001,32),(1000000,65)]:
    try:hashlib.pbkdf2_hmac('sha256',b'p',b's',rounds,length)
    except ValueError:pass
    else:raise AssertionError('invalid KDF work accepted')
state=hashlib.sha256(b'public')
state._state.__del__()
try:state.digest()
except ValueError:pass
else:raise AssertionError('cleared hash state reused')
del state
for i in range(300):
    state=hashlib.sha512(b'public')
    temporary=state.copy().digest()
del state,temporary
gc.collect()
gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS native-hash-hmac-pbkdf2')
'''
(root / 'micropython/hash_gate.py').write_text(code)
(root / 'app/hash-vectors-provenance.json').write_text(
    json.dumps(
        {
            'reference': 'CPython hashlib/hmac',
            'algorithms': list(names),
            'publishedInputs': [
                'https://www.rfc-editor.org/rfc/rfc4231.html',
                'https://www.rfc-editor.org/rfc/rfc6070.html',
                'https://github.com/trezor/python-mnemonic/blob/master/vectors.json',
            ],
            'generatedSha256': hashlib.sha256(
                (root / 'micropython/hash_gate.py').read_bytes()
            ).hexdigest(),
        },
        indent=2,
    )
    + '\n'
)
