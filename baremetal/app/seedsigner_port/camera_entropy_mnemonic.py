# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated original selected mnemonic/quality helpers; no RNG substitute.
from seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable
def _counts(data):
    counts={}
    for value in data:counts[value]=counts.get(value,0)+1
    return counts
SUPPORTED_WORD_LENGTHS = [12, 15, 18, 21, 24]
DICE_ROLLS_REQUIRED = {12: 50, 15: 62, 18: 75, 21: 87, 24: 99}
ENTROPY_BYTES_REQUIRED = {12: 16, 15: 20, 18: 24, 21: 28, 24: 32, 20: 16, 33: 32}
ROLL_COUNT_TO_LENGTH = {v: k for k, v in DICE_ROLLS_REQUIRED.items()}

def calculate_checksum(mnemonic, wordlist_language_code=_dependency('seedsigner.models.settings_definition', 'SettingsConstants').WORDLIST_LANGUAGE__ENGLISH):
    """
        Provide 12- or 24-word mnemonic, returns complete mnemonic w/checksum as a list.

        Mnemonic may be a list of words or a string of words separated by spaces or commas.

        If 11- or 23-words are provided, append word `0000` to end of list as temp final
        word.
    """
    if type(mnemonic) == str:
        mnemonic = _dependency('re', None).findall('[^,\\s]+', mnemonic)
    if len(mnemonic) in [11, 14, 17, 20, 23]:
        temp_final_word = ''.join(_dependency('seedsigner.models.seed', 'Seed').get_wordlist(wordlist_language_code)[0])
        mnemonic.append(temp_final_word)
    if len(mnemonic) not in SUPPORTED_WORD_LENGTHS:
        raise Exception('Pass in a 12, 15, 18, 21, or 24-word mnemonic')
    mnemonic_copy = mnemonic.copy()
    mnemonic_bytes = _dependency('embit', 'bip39').mnemonic_to_bytes(_dependency('unicodedata', None).normalize('NFKD', ' '.join(mnemonic_copy)), ignore_checksum=True, wordlist=_dependency('seedsigner.models.seed', 'Seed').get_wordlist(wordlist_language_code))
    return [''.join(w) for w in _dependency('embit', 'bip39').mnemonic_from_bytes(mnemonic_bytes, wordlist=_dependency('seedsigner.models.seed', 'Seed').get_wordlist(wordlist_language_code)).split()]

def generate_mnemonic_from_bytes(entropy_bytes, wordlist_language_code=_dependency('seedsigner.models.settings_definition', 'SettingsConstants').WORDLIST_LANGUAGE__ENGLISH):
    return [''.join(w) for w in _dependency('embit', 'bip39').mnemonic_from_bytes(entropy_bytes, wordlist=_dependency('seedsigner.models.seed', 'Seed').get_wordlist(wordlist_language_code)).split()]

def _hash_dice_rolls(roll_data):
    return _dependency('hashlib', None).sha256(roll_data.encode()).digest()

def generate_mnemonic_from_dice(roll_data, wordlist_language_code=_dependency('seedsigner.models.settings_definition', 'SettingsConstants').WORDLIST_LANGUAGE__ENGLISH):
    """
        Takes a string of dice rolls and returns a mnemonic of the appropriate length.

        Uses the iancoleman.io/bip39 and bitcoiner.guide/seed "Base 10" or "Hex" mode approach:
        * dice rolls are treated as string data.
        * hashed via SHA256.

        Important note: This method is NOT compatible with iancoleman's "Dice" mode.
    """
    entropy_bytes = _hash_dice_rolls(roll_data)
    word_length = ROLL_COUNT_TO_LENGTH.get(len(roll_data), 24)
    entropy_bytes = entropy_bytes[:ENTROPY_BYTES_REQUIRED[word_length]]
    return [''.join(w) for w in _dependency('embit', 'bip39').mnemonic_from_bytes(entropy_bytes, wordlist=_dependency('seedsigner.models.seed', 'Seed').get_wordlist(wordlist_language_code)).split()]

def generate_bytes_from_dice(roll_data, length_bytes=None):
    """Return entropy bytes from dice rolls without converting to mnemonic."""
    entropy_bytes = _hash_dice_rolls(roll_data)
    if length_bytes is None:
        word_length = ROLL_COUNT_TO_LENGTH.get(len(roll_data), 24)
        length_bytes = ENTROPY_BYTES_REQUIRED[word_length]
    return entropy_bytes[:length_bytes]

def _shannon_entropy(data):
    """Return the Shannon entropy of the provided data."""
    if isinstance(data, str):
        data = data.encode()
    counts = _counts(data)
    length = len(data)
    shannon_entropy = -sum((count / length * _dependency('math', None).log2(count / length) for count in counts.values()))
    return shannon_entropy

def dice_entropy_is_sufficient(roll_data, threshold=2.0):
    """Simple randomness check for dice roll input."""
    return _shannon_entropy(roll_data) >= threshold

def byte_entropy_is_sufficient(data, threshold=3.5):
    """Simple randomness check for byte data."""
    return _shannon_entropy(data) >= threshold
