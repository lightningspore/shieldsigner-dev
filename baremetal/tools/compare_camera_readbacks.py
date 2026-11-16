# SPDX-License-Identifier: MIT
"""Compare explicit DUT configuration readbacks with captured REF resources.

Report intentional DMA/polling differences and dynamic status separately. This
checks only the emitted readbacks, not every register or a completed camera gate.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from ref_range_snapshot import RESOURCES

MASKS = {
    0xFF3B036C: 3,
    0xFF3B4300: 0x7F,
    0xFF3B4800: 0xFC07,
    0xFF3B4804: 0x401F,
    0xFF3B4A00: 0xFC00,
    0xFF3B4A04: 0x4017,
    0xFF558054: 0xF0FF,
    0xFF558058: 15,
}


def compare(serial, reference):
    data = serial.read_bytes()
    values = {}
    resources = []
    manifest = json.loads((reference / 'manifest.json').read_text())
    for entry in manifest:
        raw = (reference / (entry['block'] + '.bin')).read_bytes()
        base, length = RESOURCES[entry['block']]
        if (
            len(raw) != length
            or entry['bytes'] != length
            or entry['base'] != base
            or hashlib.sha256(raw).hexdigest() != entry['sha256']
        ):
            raise ValueError('REF snapshot does not match validated manifest')
        resources.append((base, raw))
    for address, value in re.findall(rb'@@CAM_REG (0x[0-9a-f]+) (0x[0-9a-f]+)', data):
        address = int(address, 16)
        if address in values:
            raise ValueError('Repeated readback address')
        values[address] = int(value, 16)
    if not values:
        raise ValueError('No DUT readbacks')
    rows = []
    for address, actual in sorted(values.items()):
        expected = None
        for base, raw in resources:
            if base <= address < base + len(raw):
                expected = struct.unpack_from('<I', raw, address - base)[0]
                break
        if expected is None:
            raise ValueError('No captured REF register ' + hex(address))
        original_expected = expected
        reason = 'same configuration'
        mask = MASKS.get(address, 0xFFFFFFFF)
        if address == 0xFFA10124:
            expected = 0x03000000
            reason = 'DUT DMA slot0 remap'
        elif address == 0xFFA10128:
            expected = 0x03400000
            reason = 'DUT DMA slot1 remap'
        elif address == 0xFFA10174:
            expected = 0
            reason = 'DUT polling; peripheral IRQ sources disabled'
        elif address == 0xFFA10178:
            mask = 0
            reason = 'dynamic W1C frame/interrupt status; not compared'
        rows.append(
            {
                'address': hex(address),
                'reference': hex(original_expected),
                'expectedDut': hex(expected),
                'actualDut': hex(actual),
                'mask': hex(mask),
                'reason': reason,
                'matches': (actual & mask) == (expected & mask),
                'compared': mask != 0,
            }
        )
    return {
        'scope': 'selected emitted configuration registers only; not full-state or phase qualification',
        'serialSha256': hashlib.sha256(data).hexdigest(),
        'referenceManifestSha256': hashlib.sha256(
            (reference / 'manifest.json').read_bytes()
        ).hexdigest(),
        'compared': sum(row['compared'] for row in rows),
        'mismatches': sum(not row['matches'] for row in rows),
        'registers': rows,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('serial', type=Path)
    parser.add_argument('--reference', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = compare(args.serial, args.reference)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('Compared', report['compared'], 'registers; mismatches', report['mismatches'])
    for row in report['registers']:
        if not row['matches']:
            print(row)
