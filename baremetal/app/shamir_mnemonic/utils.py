# Copyright2019 SatoshiLabs; MIT, see ../LICENSE.shamir-mnemonic

from collections import namedtuple as _namedtuple
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
class MnemonicError(Exception):
    pass

def _round_bits(n, radix_bits):
    """Get the number of `radix_bits`-sized digits required to store a `n`-bit value."""
    return (n + radix_bits - 1) // radix_bits

def bits_to_bytes(n):
    """Round up bit count to whole bytes."""
    return _round_bits(n, 8)

def bits_to_words(n):
    """Round up bit count to a multiple of word size."""
    from . import constants
    assert hasattr(constants, 'RADIX_BITS'), 'Declare RADIX_BITS *before* calling this'
    return _round_bits(n, constants.RADIX_BITS)

def int_to_indices(value, length, radix_bits):
    """Convert an integer value to indices in big endian order."""
    mask = (1 << radix_bits) - 1
    return (value >> i * radix_bits & mask for i in reversed(range(length)))
