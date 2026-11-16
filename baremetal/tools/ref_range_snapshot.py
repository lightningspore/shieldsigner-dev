# SPDX-License-Identifier: MIT
"""REF read-only, word-width snapshots of exact device-tree register resources.

Camera clocks must be held by bm_snapshot_clocks. Rows are framed JSON/base64 so
the REF ADB PTY cannot corrupt raw bytes. Run blocks separately and verify REF
health/capture afterward; some status/data registers can have read side effects.
"""

import argparse
import base64
import json
import mmap
import os
from pathlib import Path
import struct
import time
import zlib

RESOURCES = {
    'cru': (0xFF3A0000, 0x20000),
    'grf': (0xFF000000, 0x68000),
    'ioc': (0xFF538000, 0x40000),
    'ioc-prefix': (0xFF538000, 0x38000),
    'pmu': (0xFF300000, 0x1000),
    'pmuioc': (0xFF388000, 0x1000),
    'dphy': (0xFF3E8000, 0x8000),
    'csi0': (0xFFA20000, 0x10000),
    'vicap': (0xFFA10000, 0x10000),
    'isp': (0xFFA00000, 0x7F00),
}


def emit(item):
    print(json.dumps(item, separators=(',', ':')), flush=True)


def capture(name):
    if name == 'ioc':
        raise RuntimeError(
            'Full IOC span faulted at0xff570000 on REF; use ioc-prefix and preserve the coverage gap'
        )
    if not Path('/sys/module/bm_snapshot_clocks').exists():
        raise RuntimeError('Snapshot clock holder is not loaded')
    base, length = RESOURCES[name]
    start = time.monotonic_ns()
    crc = 0
    total = 0
    emit(
        {
            'block': name,
            'base': base,
            'length': length,
            'startNs': start,
            'kind': 'begin',
            'coverageGap': '0xff570000–0xff577fff not captured; first address faults'
            if name == 'ioc-prefix'
            else None,
        }
    )
    descriptor = os.open('/dev/mem', os.O_RDONLY | os.O_SYNC)
    try:
        for offset in range(0, length, 4096):
            size = min(4096, length - offset)
            data = bytearray(size)
            with mmap.mmap(
                descriptor, 4096, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ, offset=base + offset
            ) as mapping:
                for word in range(0, size, 4):
                    # Aligned32-bit accesses, including on the32-bit ARM REF.
                    struct.pack_into('<I', data, word, struct.unpack_from('<I', mapping, word)[0])
            crc = zlib.crc32(data, crc)
            total += size
            emit({'kind': 'data', 'offset': offset, 'data': base64.b64encode(data).decode('ascii')})
    finally:
        os.close(descriptor)
    emit({'kind': 'end', 'bytes': total, 'crc32': crc, 'endNs': time.monotonic_ns()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('block', choices=RESOURCES)
    args = parser.parse_args()
    capture(args.block)
