# SPDX-License-Identifier: MIT
"""Native boundaries for the original Text QR / Password Generator Views.

Each function mirrors a CPython/original behaviour MicroPython lacks; none of
them invents entropy or reports success for an unavailable feature.
"""
from seedsigner_port.decode_platform import FeatureUnavailable
from base64 import b64encode

_B85='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_`{|}~'
def b85encode(b,pad=False):
    """CPython base64.b85encode."""
    b=bytes(b);padding=(-len(b))%4
    data=b+b'\0'*padding;out=bytearray()
    for i in range(0,len(data),4):
        word=int.from_bytes(data[i:i+4],'big');chunk=bytearray(5)
        for j in range(4,-1,-1):chunk[j]=ord(_B85[word%85]);word//=85
        out.extend(chunk)
    if padding and not pad:out=out[:-padding]
    return bytes(out)

def capitalize(s):
    """CPython str.capitalize for the ASCII/BIP39/EFF words used here."""
    return s[:1].upper()+s[1:].lower()

_HEX='0123456789abcdefABCDEF'
def text_unescape(text):
    """Equivalent of the original Text QR entry decode:
    bytes(re.sub(r'\\\\(?!u)', r'\\\\\\\\', t), 'raw_unicode_escape').decode('unicode_escape')
    with fallback to t on UnicodeError. Only \\uXXXX escapes are interpreted."""
    out=[];i=0;n=len(text)
    while i<n:
        c=text[i]
        if c=='\\' and i+1<n and text[i+1]=='u':
            digits=text[i+2:i+6]
            if len(digits)!=4 or any(d not in _HEX for d in digits):return text
            code=int(digits,16)
            if 0xd800<=code<=0xdfff:return text  # CPython yields a lone surrogate; not representable here
            out.append(chr(code));i+=6
        else:
            out.append(c);i+=1
    return ''.join(out)

def hardware_rng_unavailable():
    raise FeatureUnavailable('System RNG is not available on this device')

# helpers/diceware.py: same API over the generated ordered wordlists.
_maps={}
def _build(words,rolls):
    keys=['']
    for _ in range(rolls):keys=[p+d for p in keys for d in '123456']
    return dict(zip(keys,words.split('\n')))
def eff_large_map():
    if 'large' not in _maps:
        from seedsigner_port.diceware_words import EFF_LARGE
        _maps['large']=_build(EFF_LARGE,5)
    return dict(_maps['large'])
def eff_short_map():
    if 'short' not in _maps:
        from seedsigner_port.diceware_words import EFF_SHORT
        _maps['short']=_build(EFF_SHORT,4)
    return dict(_maps['short'])
def diceware_words_from_rolls(rolls,word_map,rolls_per_word):
    if len(rolls)%rolls_per_word!=0:
        raise ValueError('Roll count must be divisible by rolls per word')
    words=[]
    for idx in range(0,len(rolls),rolls_per_word):
        key=rolls[idx:idx+rolls_per_word]
        word=word_map.get(key)
        if not word:
            raise ValueError('Invalid dice roll sequence')
        words.append(word)
    return words

class PasswordDiceEntryScreen:
    """Original six-face dice keyboard for password roll counts (native keyboard)."""
    def __init__(self,return_after_n_chars):
        if type(return_after_n_chars) is not int or not 1<=return_after_n_chars<=1000:raise ValueError('Unsupported dice roll count')
        self.total=return_after_n_chars
    def display(self):
        from seedsigner_port.camera_entropy_dice import ToolsDiceEntropyEntryScreen
        # Same native dice keyboard/result checks; only the roll-count gate differs.
        return ToolsDiceEntropyEntryScreen.display(self)
