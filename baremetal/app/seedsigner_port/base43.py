# Original SeedSigner/Krux source; see LICENSE.SeedSigner and LICENSE.Krux-QR
# Generated format providers; unavailable crypto remains explicit.
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable

try:
    UnicodeDecodeError
except NameError:
    UnicodeDecodeError = UnicodeError
BASE43_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ$*+-./:'


def base43_encode(data):
    count = 0
    for b in data:
        if b == 0:
            count += 1
        else:
            break
    num = 0
    for b in data:
        num = num * 256 + b
    result = ''
    while num > 0:
        num, mod = divmod(num, 43)
        result = BASE43_ALPHABET[mod] + result
    return BASE43_ALPHABET[0] * count + result


def base43_decode(s):
    num = 0
    for c in s:
        if c not in BASE43_ALPHABET:
            raise ValueError('Invalid character in base43: {}'.format(c))
        num = num * 43 + BASE43_ALPHABET.index(c)
    result = []
    while num > 0:
        num, mod = divmod(num, 256)
        result.insert(0, mod)
    count = 0
    for c in s:
        if c == BASE43_ALPHABET[0]:
            count += 1
        else:
            break
    return bytes([0] * count) + bytes(result)
