# SPDX-License-Identifier: MIT
"""Public original multipart PSBT pixel stream with known progressive decode states."""

import pyformat  # noqa: F401  (formats generated Python on write)
import base64, json, re
from pathlib import Path
import qrcode

root = Path(__file__).resolve().parents[1]
vectors = json.loads((root / 'app/psbt-framing-vectors.json').read_text())['cases']
raw = bytes.fromhex(next(v['rawHex'] for v in vectors if v['name'] == 'valid-v0'))
encoded = base64.b64encode(raw).decode()
step = (len(encoded) + 3) // 4
parts = ['p%dof4 ' % (i + 1) + encoded[i * step : (i + 1) * step] for i in range(4)]
rows = []
for payload in (parts[0], parts[0], None, parts[2], parts[1], parts[3]):
    if payload is None:
        rows.append(tuple('0' * 33 for _ in range(33)))
        continue
    q = qrcode.QRCode(border=4, error_correction=qrcode.constants.ERROR_CORRECT_L)
    q.add_data(payload)
    q.make(fit=True)
    rows.append(tuple(''.join('1' if bit else '0' for bit in row) for row in q.get_matrix()))
reference = {}
exec(
    compile(
        (
            root.parent / 'dist/firmware/sources/lvgl/application/src/seedsigner/helpers/base43.py'
        ).read_text(),
        '<original public Base43 encoder>',
        'exec',
    ),
    reference,
)
p = root / 'micropython/scan_overlay_flow_gate.py'
code = p.read_text()
code = pyformat.sub_assignment(
    'rows',
    lambda m: 'rows = ' + repr(rows) + ' # PUBLIC independent CPython QR modules.',
    code,
    flags=re.M,
)
code = pyformat.sub_assignment(
    'raw', lambda m: 'raw = ' + repr(raw) + ' # PUBLIC minimal PSBT.', code, flags=re.M
)
code = pyformat.sub_assignment(
    'b43',
    lambda m: 'b43 = ' + repr(reference['base43_encode'](raw)) + ' # PUBLIC CPython token.',
    code,
    flags=re.M,
)
code = pyformat.sub_assignment(
    'b64', lambda m: 'b64 = ' + repr(encoded) + ' # PUBLIC CPython token.', code, flags=re.M
)
p.write_text(code)
print('Prepared6public frames: added/repeat/miss/out-of-order/complete')
