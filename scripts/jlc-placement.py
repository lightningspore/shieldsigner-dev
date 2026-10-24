"""Apply reviewed, identity-pinned supplier placement corrections exactly once."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANT = ROOT / 'variants/lcd-module-2.8'


def correct(rows, parts):
    config = json.loads((VARIANT / 'jlc-placement-corrections.json').read_text())
    board = VARIANT / 'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
    if hashlib.sha256(board.read_bytes()).hexdigest() != config['boardSha256']:
        raise ValueError('PCB changed; review supplier placement corrections before export')
    result = copy.deepcopy(rows)
    found = set()
    for row in result:
        ref = row['Designator']
        if ref not in config['corrections']:
            continue
        item = config['corrections'][ref]
        if parts[ref]['lcsc'] != item['lcsc'] or row['Layer'] != 'Bottom':
            raise ValueError('Supplier identity/side changed: ' + ref)
        keys = ['Mid X', 'Mid Y', 'Rotation']
        actual = [float(row[k]) for k in keys]
        if any(abs(a-b) > 0.000001 for a, b in zip(actual, item['native'])):
            raise ValueError('Native datum changed or corrections already applied: ' + ref)
        values = [a+b for a, b in zip(actual, item['delta'])]
        values[2] %= 360
        assert all(abs(a-b) < 0.000001 for a, b in zip(values, item['expected']))
        row.update({k: f'{v:.6f}' for k, v in zip(keys, values)})
        found.add(ref)
    assert found == set(config['corrections'])
    assert len(result) == len(rows)
    return result
