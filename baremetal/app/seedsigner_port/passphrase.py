# SPDX-License-Identifier: MIT
"""Explicit native boundary for original Seed.set_passphrase's codec sequence.

Equivalent for UTF8 scalar strings to its re.sub + raw_unicode_escape encoding
+ unicode_escape decoding, including whole-input fallback on malformed \\u.
No recursive unescaping or implicit normalization/version substitution.
"""
import unicodedata

def _scalar(cp):
    if cp<0x80:return bytes((cp,)).decode()
    if cp<0x800:return bytes((0xc0|(cp>>6),0x80|(cp&63))).decode()
    if cp<0x10000:return bytes((0xe0|(cp>>12),0x80|((cp>>6)&63),0x80|(cp&63))).decode()
    return bytes((0xf0|(cp>>18),0x80|((cp>>12)&63),0x80|((cp>>6)&63),0x80|(cp&63))).decode()

def normalize_passphrase(value):
    if not value:return ''
    if not isinstance(value,str):raise TypeError('passphrase must be str')
    parts=[]
    pos=0
    while pos<len(value):
        if value[pos:pos+2]=='\\u':
            digits=value[pos+2:pos+6]
            if len(digits)!=4 or any(c not in '0123456789abcdefABCDEF' for c in digits):
                # Original UnicodeDecodeError handler restores the entire input.
                return unicodedata.normalize('NFKD',value)
            parts.append(int(digits,16))
            pos+=6
        else:
            parts.append(value[pos])
            pos+=1
    for i in range(len(parts)):
        cp=parts[i]
        if isinstance(cp,int):
            if 0xd800<=cp<=0xdfff:
                raise UnicodeError('Surrogate passphrase cannot produce UTF8 seed input')
            parts[i]=_scalar(cp)
    return unicodedata.normalize('NFKD',''.join(parts))
