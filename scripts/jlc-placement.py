"""Apply reviewed, identity-pinned supplier placement corrections exactly once."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANT = ROOT / 'hardware'


def correct(rows, parts):
    config = json.loads((VARIANT / 'jlc-placement-corrections.json').read_text())
    board = VARIANT / 'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
    if hashlib.sha256(board.read_bytes()).hexdigest() != config['boardSha256']:
        raise ValueError('PCB changed; review supplier placement corrections before export')
    # A new artwork hash may retain the old compensation only with exact
    # protected-geometry evidence, never by silently replacing the hash guard.
    if 'artworkCompatibility' in config:
        evidence = config['artworkCompatibility']
        proof_path = VARIANT / evidence['audit']
        if hashlib.sha256(proof_path.read_bytes()).hexdigest() != evidence['auditSha256']:
            raise ValueError('Artwork compatibility evidence changed; re-review corrections')
        proof = json.loads(proof_path.read_text())
        if (proof.get('passed') is not True
                or proof['baseline']['sha256'] != config['previousBoardSha256']
                or proof['candidate']['sha256'] != config['boardSha256']
                or proof['baseline']['protectedSha256'] != proof['candidate']['protectedSha256']
                or proof.get('protectedChangedTags') != []):
            raise ValueError('Artwork compatibility does not preserve the reviewed PCB')
    if 'serviceCompatibility' in config:
        evidence = config['serviceCompatibility']
        proof_path = VARIANT / evidence['audit']
        if hashlib.sha256(proof_path.read_bytes()).hexdigest() != evidence['auditSha256']:
            raise ValueError('Service placement evidence changed; re-review corrections')
        proof = json.loads(proof_path.read_text())
        if (proof.get('passed') is not True or proof['boardSha256'] != config['boardSha256']
                or proof.get('correctedComponentsUnchanged') != ['J301', 'J601', 'U601']):
            raise ValueError('Corrected component placement changed in service revision')
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
