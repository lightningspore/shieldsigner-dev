# SPDX-License-Identifier: MIT
"""FIPS 202 SHAKE256 XOF (Keccak-f[1600]); pycryptodome SHAKE256 call shape.

Used by the original password generator helpers (Cryptodome.Hash.SHAKE256:
new(seed).read(n)). Pure Python, checked against hashlib.shake_256 vectors.
"""

_M = (1 << 64) - 1
_RC = (
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
)
_ROT = (
    0,
    1,
    62,
    28,
    27,
    36,
    44,
    6,
    55,
    20,
    3,
    10,
    43,
    25,
    39,
    41,
    45,
    15,
    21,
    8,
    18,
    2,
    61,
    56,
    14,
)
_PI = [0] * 25
for _x in range(5):
    for _y in range(5):
        _PI[_x + 5 * _y] = _y + 5 * ((2 * _x + 3 * _y) % 5)


def _rol(v, n):
    return ((v << n) | (v >> (64 - n))) & _M if n else v


def _permute(a):
    for rc in _RC:
        c = [a[x] ^ a[x + 5] ^ a[x + 10] ^ a[x + 15] ^ a[x + 20] for x in range(5)]
        d = [c[(x - 1) % 5] ^ _rol(c[(x + 1) % 5], 1) for x in range(5)]
        a = [a[i] ^ d[i % 5] for i in range(25)]
        b = [0] * 25
        for i in range(25):
            b[_PI[i]] = _rol(a[i], _ROT[i])
        a = [
            b[i] ^ ((~b[(i % 5 + 1) % 5 + 5 * (i // 5)]) & b[(i % 5 + 2) % 5 + 5 * (i // 5)])
            for i in range(25)
        ]
        a[0] ^= rc
    return a


class SHAKE256_XOF:
    RATE = 136

    def __init__(self, data=b''):
        self._buf = bytearray()
        self._state = [0] * 25
        self._squeezing = False
        self._out = b''
        if data:
            self.update(data)

    def update(self, data):
        if self._squeezing:
            raise TypeError('update() after read()')
        self._buf.extend(data)
        while len(self._buf) >= self.RATE:
            self._absorb(self._buf[: self.RATE])
            self._buf = self._buf[self.RATE :]
        return self

    def _absorb(self, block):
        s = self._state
        for i in range(self.RATE // 8):
            s[i] ^= int.from_bytes(bytes(block[8 * i : 8 * i + 8]), 'little')
        self._state = _permute(s)

    def _squeeze(self):
        out = b''.join(self._state[i].to_bytes(8, 'little') for i in range(self.RATE // 8))
        self._state = _permute(self._state)
        return out

    def read(self, length):
        if not self._squeezing:
            pad = bytearray(self._buf)
            pad.append(0x1F)
            while len(pad) < self.RATE:
                pad.append(0)
            pad[-1] |= 0x80
            self._absorb(pad)
            self._buf = bytearray()
            self._squeezing = True
        while len(self._out) < length:
            self._out += self._squeeze()
        result = self._out[:length]
        self._out = self._out[length:]
        return result


def new(data=b''):
    return SHAKE256_XOF(data)
