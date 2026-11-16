# SPDX-License-Identifier: MIT
"""Native RustCrypto streaming hashes and cancellable PBKDF2.

This exposes the algorithms required by the port, not every OpenSSL hash alias.
"""

import _native_hash
import binascii

_INFO = {
    'sha224': (0, 28, 64),
    'sha256': (1, 32, 64),
    'sha384': (2, 48, 128),
    'sha512': (3, 64, 128),
    'sha1': (4, 20, 64),
    'ripemd160': (5, 20, 64),
}
algorithms_available = set(_INFO)
algorithms_guaranteed = set(_INFO)


def _info(name):
    if not isinstance(name, str):
        raise TypeError('hash name must be str')
    name = name.lower().replace('-', '')
    if name not in _INFO:
        raise ValueError('unsupported hash algorithm')
    return name, _INFO[name]


class _Hash:
    def __init__(self, name, data=b''):
        self.name, info = _info(name)
        self.digest_size = info[1]
        self.block_size = info[2]
        self._state = _native_hash.context(info[0], data)

    def update(self, data):
        self._state.update(data)

    def digest(self):
        return self._state.digest()

    def hexdigest(self):
        return binascii.hexlify(self.digest()).decode()

    def copy(self):
        result = object.__new__(_Hash)
        result.name = self.name
        result.digest_size = self.digest_size
        result.block_size = self.block_size
        result._state = self._state.copy()
        return result


def new(name, data=b'', *, usedforsecurity=True):
    return _Hash(name, data)


def sha224(data=b'', *, usedforsecurity=True):
    return _Hash('sha224', data)


def sha256(data=b'', *, usedforsecurity=True):
    return _Hash('sha256', data)


def sha384(data=b'', *, usedforsecurity=True):
    return _Hash('sha384', data)


def sha512(data=b'', *, usedforsecurity=True):
    return _Hash('sha512', data)


def sha1(data=b'', *, usedforsecurity=True):
    return _Hash('sha1', data)


def ripemd160(data=b'', *, usedforsecurity=True):
    return _Hash('ripemd160', data)


def pbkdf2_hmac(hash_name, password, salt, iterations, dklen=None):
    name, info = _info(hash_name)
    if dklen is None:
        dklen = info[1]
    return _native_hash.pbkdf2(info[0], password, salt, iterations, dklen)
