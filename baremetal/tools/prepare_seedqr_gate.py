# SPDX-License-Identifier: MIT
"""Independent unmodified CPython qrcode7.3.1/embit oracle for PUBLIC SeedQRs."""

import pyformat  # noqa: F401  (formats generated Python on write)
import hashlib, json, importlib.metadata
from pathlib import Path
from embit import bip39
import qrcode

assert importlib.metadata.version('qrcode') == '7.3.1'
root = Path(__file__).resolve().parents[1]
cases = []
for count in (12, 15, 18, 21, 24):
    n = count * 4 // 3
    for entropy in (bytes(n), bytes(range(n))):
        words = bip39.mnemonic_from_bytes(entropy).split()
        for compact in (False, True):
            data = entropy if compact else ''.join('%04d' % bip39.WORDLIST.index(w) for w in words)
            q = qrcode.QRCode(
                version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=5, border=0
            )
            q.add_data(data)
            q.make(fit=True)
            size = len(q.modules)
            packed = bytearray(1 + (size * size + 7) // 8)
            packed[0] = size
            for y, row in enumerate(q.modules):
                for x, v in enumerate(row):
                    if v:
                        packed[1 + (y * size + x) // 8] |= 1 << ((y * size + x) % 8)
            cases.append((words, compact, data, hashlib.sha256(packed).hexdigest(), size))
# Entropy chosen to challenge QR segmentation, alphanumeric classification and NUL.
for entropy in (
    b'12345678901234567890' + bytes(range(12)),
    b'A' * 31 + b'\n',
    b'A' * 31 + b'\0',
    bytes(range(224, 256)),
    b'01234567890123456789012345678901',
):
    words = bip39.mnemonic_from_bytes(entropy).split()
    q = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, border=0)
    q.add_data(entropy)
    q.make(fit=True)
    size = len(q.modules)
    packed = bytearray(1 + (size * size + 7) // 8)
    packed[0] = size
    for y, row in enumerate(q.modules):
        for x, v in enumerate(row):
            if v:
                packed[1 + (y * size + x) // 8] |= 1 << ((y * size + x) % 8)
    cases.append((words, True, entropy, hashlib.sha256(packed).hexdigest(), size))
code = (
    '''# SPDX-License-Identifier: MIT
# Generated PUBLIC oracle; no private QR payload output.
from seedsigner_port.encode_qr import SeedQrEncoder,CompactSeedQrEncoder
from seedsigner_port.qr_helper import matrix,QR
from seedsigner_port.transcription import pack_matrix
from seedsigner_port.decode_qr import SeedQrDecoder,DecodeQRStatus
from seedsigner_port.qr_type import QRType
from seedsigner_port.settings_schema import SettingsConstants as C
import hashlib,gc,time,qr
cases='''
    + repr(cases)
    + '''
started=time.ticks_ms()
for number,(words,compact,expected,digest,size) in enumerate(cases):
    encoder=(CompactSeedQrEncoder if compact else SeedQrEncoder)(mnemonic=words)
    data=encoder.next_part()
    assert data==expected and encoder.cur_part()==data and encoder.seq_len()==1 and encoder.is_complete
    rows=matrix(data)
    packed=bytes.fromhex(pack_matrix(rows,size))
    assert len(rows)==size and hashlib.sha256(packed).hexdigest()==digest
    decoder=SeedQrDecoder(C.WORDLIST_LANGUAGE__ENGLISH)
    assert decoder.add(data,QRType.SEED__COMPACTSEEDQR if compact else QRType.SEED__SEEDQR)==DecodeQRStatus.COMPLETE
    assert decoder.get_seed_phrase()==words
    # The existing real ZXing decoder reads rendered modules, not a known answer.
    scale=8;border=4;width=(size+border*2)*scale
    line=bytearray(b'\\xff'*width);pixels=bytearray()
    for y in range(size+border*2):
        row=bytearray(line)
        if border<=y<size+border:
            for x in range(size):
                if rows[y-border][x]:row[(x+border)*scale:(x+border+1)*scale]=bytes(scale)
        for _ in range(scale):pixels.extend(row)
    assert qr.decode(pixels,width,width)==(data.encode() if type(data) is str else data)
    gc.collect()
    print('@@PASS original-seedqr-matrix-payload-native-zxing',number,len(words),compact,size)
print('@@SEEDQR_CORE_MS',(time.ticks_ms()-started)&0xffffffff)
'''
)
(root / 'micropython/seedqr_core_gate.py').write_text(code)
(root / 'app/seedqr-public-oracle.json').write_text(
    json.dumps(
        {
            'provider': 'CPython qrcode7.3.1 and embit0.8.0',
            'cases': len(cases),
            'gateSha256': hashlib.sha256(
                (root / 'micropython/seedqr_core_gate.py').read_bytes()
            ).hexdigest(),
            'scope': 'Public entropy/payloads only; includes numeric, bytes, NUL, final LF, optimized segments.',
        },
        indent=2,
    )
    + '\n'
)
print('Prepared', len(cases), 'public independent SeedQR cases')

import re

p = root / 'micropython/seedqr_flow_gate.py'
p.write_text(
    pyformat.sub_assignment(
        'fixtures',
        lambda match: 'fixtures = ' + repr(cases[2:4] + cases[18:20]) + ' # PUBLIC CPython oracle.',
        p.read_text(),
        flags=re.M,
    )
)
