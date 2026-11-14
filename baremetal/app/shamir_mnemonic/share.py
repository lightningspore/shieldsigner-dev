# Copyright2019 SatoshiLabs; MIT, see ../LICENSE.shamir-mnemonic

from collections import namedtuple as _namedtuple
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
from . import rs1024, wordlist
from .constants import CUSTOMIZATION_STRING_EXTENDABLE, CUSTOMIZATION_STRING_ORIG, EXTENDABLE_FLAG_LENGTH_BITS, ID_EXP_LENGTH_WORDS, ITERATION_EXP_LENGTH_BITS, METADATA_LENGTH_WORDS, MIN_MNEMONIC_LENGTH_WORDS, RADIX, RADIX_BITS
from .utils import MnemonicError, bits_to_bytes, bits_to_words, int_to_indices
WordIndex = int

def _int_to_word_indices(value, length):
    """Converts an integer value to a list of base 1024 indices in big endian order."""
    return list(int_to_indices(value, length, radix_bits=RADIX_BITS))

def _int_from_word_indices(indices):
    """Converts a list of base 1024 indices in big endian order to an integer value."""
    value = 0
    for index in indices:
        value = value * RADIX + index
    return value

def _customization_string(extendable):
    if extendable:
        return CUSTOMIZATION_STRING_EXTENDABLE
    else:
        return CUSTOMIZATION_STRING_ORIG

class ShareCommonParameters(_namedtuple('_ShareCommonParametersFields', ('identifier', 'extendable', 'iteration_exponent', 'group_threshold', 'group_count'))):
    """Parameters that are common to all shares of a master secret."""
    _fields = ('identifier', 'extendable', 'iteration_exponent', 'group_threshold', 'group_count')

    def __setattr__(self, name, value):
        raise AttributeError('frozen record')

    def __delattr__(self, name):
        raise AttributeError('frozen record')

class ShareGroupParameters(_namedtuple('_ShareGroupParametersFields', ('identifier', 'extendable', 'iteration_exponent', 'group_index', 'group_threshold', 'group_count', 'member_threshold'))):
    """Parameters that are common to all shares of a master secret, which belong to the same group."""
    _fields = ('identifier', 'extendable', 'iteration_exponent', 'group_index', 'group_threshold', 'group_count', 'member_threshold')

    def __setattr__(self, name, value):
        raise AttributeError('frozen record')

    def __delattr__(self, name):
        raise AttributeError('frozen record')

class Share(_namedtuple('_ShareFields', ('identifier', 'extendable', 'iteration_exponent', 'group_index', 'group_threshold', 'group_count', 'index', 'member_threshold', 'value'))):
    """Represents a single mnemonic share and its metadata"""

    def common_parameters(self):
        """Return values that uniquely identify a matching set of shares."""
        return ShareCommonParameters(self.identifier, self.extendable, self.iteration_exponent, self.group_threshold, self.group_count)

    def group_parameters(self):
        """Return values that uniquely identify shares belonging to the same group."""
        return ShareGroupParameters(self.identifier, self.extendable, self.iteration_exponent, self.group_index, self.group_threshold, self.group_count, self.member_threshold)

    def _encode_id_exp(self):
        id_exp_int = self.identifier << ITERATION_EXP_LENGTH_BITS + EXTENDABLE_FLAG_LENGTH_BITS
        id_exp_int += self.extendable << ITERATION_EXP_LENGTH_BITS
        id_exp_int += self.iteration_exponent
        return _int_to_word_indices(id_exp_int, ID_EXP_LENGTH_WORDS)

    def _encode_share_params(self):
        val = self.group_index
        val <<= 4
        val += self.group_threshold - 1
        val <<= 4
        val += self.group_count - 1
        val <<= 4
        val += self.index
        val <<= 4
        val += self.member_threshold - 1
        return _int_to_word_indices(val, 2)

    def words(self):
        """Convert share data to a share mnemonic."""
        value_word_count = bits_to_words(len(self.value) * 8)
        value_int = int.from_bytes(self.value, 'big')
        value_data = _int_to_word_indices(value_int, value_word_count)
        share_data = self._encode_id_exp() + self._encode_share_params() + value_data
        checksum = rs1024.create_checksum(share_data, _customization_string(self.extendable))
        return list(wordlist.words_from_indices(share_data + checksum))

    def mnemonic(self):
        """Convert share data to a share mnemonic."""
        return ' '.join(self.words())

    @classmethod
    def from_mnemonic(cls, mnemonic):
        """Convert a share mnemonic to share data."""
        mnemonic_data = wordlist.mnemonic_to_indices(mnemonic)
        if len(mnemonic_data) < MIN_MNEMONIC_LENGTH_WORDS:
            raise MnemonicError(f'Invalid mnemonic length. The length of each mnemonic must be at least {MIN_MNEMONIC_LENGTH_WORDS} words.')
        padding_len = RADIX_BITS * (len(mnemonic_data) - METADATA_LENGTH_WORDS) % 16
        if padding_len > 8:
            raise MnemonicError('Invalid mnemonic length.')
        id_exp_data = mnemonic_data[:ID_EXP_LENGTH_WORDS]
        id_exp_int = _int_from_word_indices(id_exp_data)
        identifier = id_exp_int >> EXTENDABLE_FLAG_LENGTH_BITS + ITERATION_EXP_LENGTH_BITS
        extendable = bool(id_exp_int >> ITERATION_EXP_LENGTH_BITS & 1)
        iteration_exponent = id_exp_int & (1 << ITERATION_EXP_LENGTH_BITS) - 1
        if not rs1024.verify_checksum(mnemonic_data, _customization_string(extendable)):
            raise MnemonicError('Invalid mnemonic checksum for "{} ...".'.format(' '.join(mnemonic.split()[:ID_EXP_LENGTH_WORDS + 2])))
        share_params_data = mnemonic_data[ID_EXP_LENGTH_WORDS:ID_EXP_LENGTH_WORDS + 2]
        share_params_int = _int_from_word_indices(share_params_data)
        share_params = int_to_indices(share_params_int, 5, 4)
        group_index, group_threshold, group_count, index, member_threshold = share_params
        if group_count < group_threshold:
            raise MnemonicError('Invalid mnemonic "{} ...". Group threshold cannot be greater than group count.'.format(' '.join(mnemonic.split()[:ID_EXP_LENGTH_WORDS + 2])))
        value_data = mnemonic_data[ID_EXP_LENGTH_WORDS + 2:-rs1024.CHECKSUM_LENGTH_WORDS]
        value_byte_count = bits_to_bytes(RADIX_BITS * len(value_data) - padding_len)
        value_int = _int_from_word_indices(value_data)
        try:
            value = value_int.to_bytes(value_byte_count, 'big')
        except OverflowError:
            raise MnemonicError('Invalid mnemonic padding for "{} ...".'.format(' '.join(mnemonic.split()[:ID_EXP_LENGTH_WORDS + 2]))) from None
        return cls(identifier, extendable, iteration_exponent, group_index, group_threshold + 1, group_count + 1, index, member_threshold + 1, value)

    def __setattr__(self, name, value):
        raise AttributeError('frozen record')

    def __delattr__(self, name):
        raise AttributeError('frozen record')

    def __eq__(self, other):
        return type(self) is type(other) and tuple(self) == tuple(other)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(self))
