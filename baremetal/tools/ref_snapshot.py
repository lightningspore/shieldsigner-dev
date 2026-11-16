# SPDX-License-Identifier: MIT
"""Run on REF: read only an explicit address list through read-only /dev/mem maps.

The caller supplies source-reviewed registers and must ensure their clocks are on.
This does not probe reserved addresses or enable clocks. Full-range snapshots remain
a separate requirement; this helper deliberately describes its partial coverage.
"""

import argparse
import json
import mmap
import os
import struct
import time


def snapshot(spec):
    pages = {}
    values = []
    descriptor = os.open('/dev/mem', os.O_RDONLY | os.O_SYNC)
    start = time.monotonic_ns()
    try:
        for item in spec['registers']:
            address = int(item['address'], 0)
            if address & 3:
                raise ValueError('Unaligned register')
            page = address & ~4095
            if page not in pages:
                pages[page] = mmap.mmap(
                    descriptor, 4096, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ, offset=page
                )
            value = struct.unpack_from('<I', pages[page], address - page)[0]
            values.append(dict(item, value=f'0x{value:08x}'))
    finally:
        for mapping in pages.values():
            mapping.close()
        os.close(descriptor)
    by_address = {int(item['address'], 0): int(item['value'], 0) for item in values}
    for requirement in spec.get('require', []):
        if by_address[int(requirement['address'], 0)] & int(requirement['mask'], 0) != int(
            requirement['value'], 0
        ):
            raise RuntimeError('Snapshot clock-state requirement failed: ' + str(requirement))
    return {
        'scope': spec['scope'],
        'requirements': spec.get('require', []),
        'startNs': start,
        'endNs': time.monotonic_ns(),
        'registers': values,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('specification')
    args = parser.parse_args()
    with open(args.specification) as stream:
        spec = json.load(stream)
    print(json.dumps(snapshot(spec), indent=2))
