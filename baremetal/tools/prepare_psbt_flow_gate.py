# SPDX-License-Identifier: MIT
"""Prepare public native original review/approval/UR export gate; never runs it."""

import pyformat  # noqa: F401  (formats generated Python on write)
import json, hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
oracle = json.loads((root / 'app/psbt-review-public-oracle.json').read_text())
case = next(c for c in oracle['signingData'] if c['name'] == 'NORMAL-1_p2wpkh')
template = root / 'tools/psbt_flow_gate_template.py'
out = root / 'micropython/psbt_flow_gate.py'
out.write_text(
    template.read_text().replace('PUBLIC_FIXTURE = None', 'PUBLIC_FIXTURE = ' + repr(case))
)
print(
    'Prepared original native PSBT flow gate',
    case['name'],
    hashlib.sha256(out.read_bytes()).hexdigest(),
)
