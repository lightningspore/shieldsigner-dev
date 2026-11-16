# SPDX-License-Identifier: MIT
"""Public independent QR pixel fixtures for original confirmation navigation."""

import pyformat  # noqa: F401  (formats generated Python on write)
import re
from pathlib import Path
from embit import bip39
import qrcode

root = Path(__file__).resolve().parents[1]
fixtures = []


def rows(data):
    if data is None:
        return tuple('0' * 33 for _ in range(33))
    q = qrcode.QRCode(border=4, error_correction=qrcode.constants.ERROR_CORRECT_L)
    q.add_data(data)
    q.make(fit=True)
    return tuple(''.join('1' if bit else '0' for bit in row) for row in q.get_matrix())


def data(entropy, compact):
    words = bip39.mnemonic_from_bytes(entropy).split()
    return words, entropy if compact else ''.join(
        '%04d' % bip39.WORDLIST.index(word) for word in words
    )


for size in (16, 32):
    for compact in (False, True):
        words, payload = data(bytes(range(size)), compact)
        fixtures.append(('match', words, compact, rows(payload), ''))
for compact in (False, True):
    words, _ = data(bytes(range(16)), compact)
    _, payload = data(bytes(16), compact)
    fixtures.append(('wrong', words, compact, rows(payload), ''))
words, _ = data(bytes(range(16)), False)
for mode, payload in (
    ('nonseed', 'ShieldSigner public QR confirmation test'),
    ('bad-checksum', '0000' * 12),
):
    fixtures.append((mode, words, False, rows(payload), ''))
fixtures.append(('address', words, False, rows('1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'), ''))
for cancel in ('left', 'right'):
    fixtures.append(('cancel', words, False, rows(None), cancel))
p = root / 'micropython/seedqr_confirm_gate.py'
p.write_text(
    pyformat.sub_assignment(
        'fixtures',
        lambda match: 'fixtures = ' + repr(fixtures) + ' # PUBLIC independent CPython oracle.',
        p.read_text(),
        flags=re.M,
    )
)
print('Prepared', len(fixtures), 'public confirmation cases')
