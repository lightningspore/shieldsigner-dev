# Copyright2020 Stepan Snigirev; MIT, see ../LICENSE.embit

from seedsigner_port.decode_platform import FeatureUnavailable
"""Misc utility functions used across embit"""
import sys
if sys.implementation.name == 'micropython':
    from micropython import const
    from seedsigner_port.deferred_module import DeferredModule
    secp256k1 = DeferredModule('secp256k1')
else:
    from .util import secp256k1

    def const(x):
        return x
try:
    from os import urandom as urandom
except ImportError:

    def urandom(n):
        with open('/dev/urandom', 'rb') as f:
            return f.read(n)

def getrandbits(k):
    b = urandom(k // 8 + 1)
    return int.from_bytes(b, 'big') % 2 ** k

def secure_randint(vmin, vmax):
    """
    Normal random.randint uses PRNG that is not suitable
    for cryptographic applications.
    This one uses os.urandom for randomness.
    """
    import math
    assert vmax > vmin
    delta = vmax - vmin
    nbits = math.ceil(math.log2(delta + 1))
    randn = getrandbits(nbits)
    while randn > delta:
        randn = getrandbits(nbits)
    return vmin + randn

def copy(a):
    """Ugly copy that works everywhere incl micropython"""
    if len(a) == 0:
        return b''
    return a[:1] + a[1:]

def read_until(s, chars=b',)(#'):
    """Read from stream until one of `char` characters.
    By default `chars=,)(#`.

    Return a tuple (result: bytes, char: bytes | None)
    where result is bytes read from the stream until char,
    char contains this character or None if the end of stream reached.
    """
    res = b''
    chunk = b''
    while True:
        chunk = s.read(1)
        if len(chunk) == 0:
            return (res, None)
        if chunk in chars:
            return (res, chunk)
        res += chunk
