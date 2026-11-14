# Copyright2019 SatoshiLabs; MIT, see ../LICENSE.shamir-mnemonic

from collections import namedtuple as _namedtuple
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
from .constants import CHECKSUM_LENGTH_WORDS

def _polymod(values):
    GEN = (14737472, 29474944, 58949888, 117899776, 235798537, 470557714, 940076068, 814808136, 565311632, 66318624)
    chk = 1
    for v in values:
        b = chk >> 20
        chk = (chk & 1048575) << 10 ^ v
        for i in range(10):
            chk ^= GEN[i] if b >> i & 1 else 0
    return chk

def create_checksum(data, customization_string):
    values = list(customization_string) + list(data) + [0] * CHECKSUM_LENGTH_WORDS
    polymod = _polymod(values) ^ 1
    return [polymod >> 10 * i & 1023 for i in reversed(range(CHECKSUM_LENGTH_WORDS))]

def verify_checksum(data, customization_string):
    return _polymod(list(customization_string) + list(data)) == 1
