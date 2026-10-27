#!/usr/bin/env python3
"""Audit original selected-region reads from contiguous prepared light records."""
import hashlib
import json
import struct

from awb_reference import OriginalAwb
from differential import BINARY, HEAP, ROOT


def main():
    manifest = json.loads((ROOT / 'reverse-engineering/rkaiq/artifacts.json').read_text())
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == next(x['sha256'] for x in manifest['binaries'] if x['name'] == BINARY.name)
    arm = OriginalAwb()
    cases = []
    for n in (1, 4, 8, 255):
        # A separately identified trailing word is necessary for the final
        # region-3 blue read. It is not part of any prepared light record.
        stats = bytearray(n * 0xac + 4)
        for i in range(n):
            for region in range(3):
                struct.pack_into('<I4f', stats, i * 0xac + region * 0x34,
                                 100 + i + region, 2., 1., 1., 3.)
            struct.pack_into('<4f', stats, i * 0xac + 0x9c, 4., 1., 1., 5.)
        struct.pack_into('<I', stats, n * 0xac, 0x12345678)
        for region in range(4):
            ctx = bytearray(0x4000)
            cfg = bytearray(0x400)
            reference = bytearray(n * 0xe4)  # Extra mixing disabled.
            result = bytearray([0x5a]) * (n * 0xa0)
            struct.pack_into('<I', ctx, 0x8c, HEAP + 0x8000)
            struct.pack_into('<I', ctx, 0x134, HEAP + 0x30000)
            struct.pack_into('<I', ctx, 0x33e4, HEAP + 0x20000)
            cfg[0x138] = n
            struct.pack_into('<I', cfg, 0x368, HEAP + 0x10000)
            blocks = [(0, ctx), (0x8000, cfg), (0x10000, reference),
                      (0x20000, result), (0x30000, stats)]
            for offset, data in blocks:
                arm.uc.mem_write(HEAP + offset, bytes(data))
            arm.invoke('_Z29AwbCalGainForDiffIlluminationiP12awb_contex_s',
                       [region, HEAP], instructions=3000000)
            actual = bytes(arm.uc.mem_read(HEAP + 0x20000, len(result)))
            expected = bytearray(result)
            for i in range(n):
                source = i * 0xac + region * 0x34 + 4
                expected[i * 0xa0 + 0x64:i * 0xa0 + 0x74] = stats[source:source + 16]
            assert actual == expected, (n, region)
            for offset, before in blocks:
                if offset != 0x20000:
                    assert bytes(arm.uc.mem_read(HEAP + offset, len(before))) == before
            cases.append(dict(lights=n, region=region, exact=True))
    assert not arm.calls and not arm.runtime_calls
    report = dict(binarySha256=sha, cases=cases, mismatchCount=0,
                  scope='Original ARM selected-gain copies with extra mixing disabled; contiguous prepared records and explicit final guard word.',
                  region3=dict(countOffset='0x9c (pre-gain red bits)',
                               gainOffsets=['0xa0 (pre-gain Gr)', '0xa4 (pre-gain Gb)',
                                            '0xa8 (pre-gain blue)', '0xac (next light Normal count bits)'],
                               lastBlue='Reads beyond final 0xac-byte record; explicit guard word 0x12345678 observed bit-for-bit.'),
                  limitations=['Does not establish reachability with production IQ/state, allocation boundary contents, or intended vendor semantics.',
                               'Does not validate a complete mode-1/2 Exclusion controller call or define a safe replacement policy.'])
    (ROOT / 'reverse-engineering/rkaiq/awb-prepared-layout-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(cases=len(cases), mismatchCount=0, region3=report['region3']), indent=2))


if __name__ == '__main__':
    main()
