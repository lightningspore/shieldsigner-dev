# SPDX-License-Identifier: MIT
"""Audit captured REF AWB fields; never use register-read bytes as write values.

The SDK hw.c explicitly excludes AWB1 gain registers from ordinary readback
restore because read and write representations differ. The captured values use
12-bit spacing on read, while isp_params_v32.c writes packed16-bit halves.
Gain2 readback remains unresolved here and is not silently treated as matching.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct


def audit(parameters, snapshot):
    params = parameters.read_bytes()
    registers = (snapshot / 'isp.bin').read_bytes()
    if len(params) != 11145 or len(registers) != 0x7F00:
        raise ValueError('Wrong parameter/register layout')
    entry = next(
        e for e in json.loads((snapshot / 'manifest.json').read_text()) if e['block'] == 'isp'
    )
    if hashlib.sha256(registers).hexdigest() != entry['sha256']:
        raise ValueError('Snapshot hash mismatch')
    rows = []
    names = [
        'AWB1_G',
        'AWB1_RB',
        'GAIN0_G',
        'GAIN0_RB',
        'GAIN1_G',
        'GAIN1_RB',
        'GAIN2_G',
        'GAIN2_RB',
    ]
    for i, name in enumerate(names):
        desired = struct.unpack_from('<HH', params, 0x1225 + i * 4)
        offset = 0x530 + i * 4
        raw = struct.unpack_from('<I', registers, offset)[0]
        shift = 12 if i < 2 else 16
        mask = (1 << shift) - 1
        decoded = (raw & mask, (raw >> shift) & mask)
        rows.append(
            {
                'name': name,
                'offset': hex(offset),
                'desiredChannels': desired,
                'readValue': hex(raw),
                'readChannels': decoded,
                'readSpacing': shift,
                'channelsMatch': decoded == desired,
                'interpretation': 'SDK-documented read/write difference; observed12-bit read spacing'
                if i < 2
                else 'unresolved gain2 readback; do not claim applied'
                if i >= 6
                else 'ordinary packed16-bit readback',
            }
        )
    module_ens = struct.unpack_from('<Q', params, 8)[0]
    control = struct.unpack_from('<I', registers, 0x400)[0]
    return {
        'scope': 'selected REF AWB fields only; no full-module/frame-timing/DUT qualification',
        'parameterSha256': hashlib.sha256(params).hexdigest(),
        'registerSha256': hashlib.sha256(registers).hexdigest(),
        'awbEnableMatches': bool(module_ens & (1 << 5)) == bool(control & (1 << 7)),
        'matchingChannelPairs': sum(row['channelsMatch'] for row in rows),
        'unresolvedChannelPairs': sum(not row['channelsMatch'] for row in rows),
        'registers': rows,
        'warning': 'AWB1 read values must not be replayed as packed16-bit write values.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parameters', type=Path)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = audit(args.parameters, args.snapshot)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(
        json.dumps(
            {
                key: report[key]
                for key in [
                    'awbEnableMatches',
                    'matchingChannelPairs',
                    'unresolvedChannelPairs',
                    'warning',
                ]
            }
        )
    )
