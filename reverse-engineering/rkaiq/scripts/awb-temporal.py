#!/usr/bin/env python3
"""Execute native temporal sources and brightness-dependent blend in sequence."""
import hashlib
import json
import random
import struct
import subprocess
import sys

from awb_reference import OriginalAwb
from differential import BINARY, HEAP, ROOT, f32


def native(arm, v):
    context = bytearray([0x5a]) * 0x4000
    config = bytearray([0x6b]) * 0x400
    nodes = bytearray(24 * len(v['history']))
    weights = bytes(v['weights'])
    head = HEAP + 0x3498
    addresses = [HEAP + 0x10000 + 24 * i for i in range(len(v['history']))]
    struct.pack_into('<II', context, 0x3498, addresses[0] if addresses else head, addresses[-1] if addresses else head)
    for i, gain in enumerate(v['history']):
        struct.pack_into('<II4f', nodes, i * 24, addresses[i + 1] if i + 1 < len(addresses) else head,
                         addresses[i - 1] if i else head, *gain)
    struct.pack_into('<I', context, 0x8c, HEAP + 0x8000)
    struct.pack_into('<I', context, 0x33d8, v['brightness'])
    struct.pack_into('<4f', context, 0x353c, *v['current'])
    struct.pack_into('<16I', config, 0x168, *v['knots'])
    struct.pack_into('<4f', config, 0x1d8, *v['default'])
    struct.pack_into('<I', config, 0x1ec, HEAP + 0x20000)
    config[0x1f8:0x208] = bytes(v['percentages'])
    blocks = [(0, context), (0x8000, config), (0x10000, nodes), (0x20000, weights)]
    for offset, data in blocks:
        if data:
            arm.uc.mem_write(HEAP + offset, bytes(data))
    source = '_Z25AwbCalGainInTemporalGain2P12awb_contex_s' if v['direct'] else '_Z24AwbCalGainInTemporalGainP12awb_contex_s'
    arm.invoke(source, [HEAP])
    temporal = list(struct.unpack('<4I', arm.uc.mem_read(HEAP + 0x33e8, 16)))
    arm.invoke('_Z22AwbCalGainTotalMulTempP12awb_contex_s', [HEAP])
    after = bytearray(arm.uc.mem_read(HEAP, len(context)))
    output = dict(temporal=temporal, gain=list(struct.unpack_from('<4I', after, 0x353c)),
                  weight=struct.unpack_from('<I', after, 0x33f8)[0])
    for offset, size in [(0x33e8, 20), (0x353c, 16)]:
        after[offset:offset + size] = context[offset:offset + size]
    assert after == context
    for offset, data in blocks[1:]:
        if data:
            assert bytes(arm.uc.mem_read(HEAP + offset, len(data))) == data
    return output


def main():
    manifest = json.loads((ROOT / 'reverse-engineering/rkaiq/artifacts.json').read_text())
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == next(v['sha256'] for v in manifest['binaries'] if v['name'] == BINARY.name)
    arm = OriginalAwb()
    rng = random.Random(0x54454d50)
    cases, expected = [], []
    for i in range(1024):
        gain = lambda: [f32(rng.uniform(.1, 9.)) for _ in range(4)]
        knots = [100 * j for j in range(16)]
        mode = i % 5
        if mode == 1:
            knots = [16777216 + j for j in range(16)]
        elif mode == 2:
            knots = [0] * 8 + [100] * 8
        elif mode == 3:
            knots = sorted(rng.randrange(2**32) for _ in range(16))
        elif mode == 4:
            knots = [0] + [rng.randrange(1, 1499) for _ in range(14)] + [1500]
        brightness = [0, 0xffffffff, knots[0], knots[-1], knots[i % 16],
                      min(0xffffffff, knots[i % 16] + 1), max(0, knots[i % 16] - 1)][i // 5 % 7]
        count = i % 17
        value = dict(direct=bool(i % 2), history=[gain() for _ in range(count)],
                     weights=[rng.choice([0, 1, 50, 100, 255]) for _ in range(count)],
                     default=gain(), current=gain(), brightness=brightness, knots=knots,
                     percentages=[rng.choice([0, 1, 50, 99, 100, 101, 255]) for _ in range(16)])
        if count:
            value['weights'][0] = 1
        if i % 11 == 0:
            value['current'] = [0.] * 4
        if i % 13 == 0:
            value['default'] = [6., 7., 8., 9.]
        cases.append(value)
        expected.append(native(arm, value))
    assert not arm.calls and not arm.runtime.calls
    inputs = ''.join('awb-temporal ' + json.dumps(v, separators=(',', ':')) + '\n' for v in cases)

    def compare(command):
        p = subprocess.run(command, input=inputs, text=True, capture_output=True, check=True)
        actual = [json.loads(line) for line in p.stdout.splitlines()]
        assert len(actual) == len(expected)
        for i, (a, b) in enumerate(zip(expected, actual)):
            assert a == b, (i, cases[i], a, b)

    compare([str(ROOT / 'firmware/rkaiq-rs/target/release/numeric-fixture')])
    replay = '--arm' in sys.argv
    if replay:
        directory = ROOT / 'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
        compare(['docker', 'run', '--rm', '-i', '--platform', 'linux/arm/v7', '--network=none',
                 '--mount', f'type=bind,src={directory},dst=/bincheck,readonly',
                 'alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd',
                 '/bincheck/numeric-fixture'])
    report = dict(binarySha256=sha, cases=len(cases), mismatches=0, arm=replay,
                  elfEntries=dict(default='0xc5d3c', history='0xc5d5c', blend='0xc6860'),
                  scope='Both native temporal source routines followed by the original brightness-dependent blend; exact gain/weight bits and unrelated-memory preservation',
                  limitations=['Finite gains; nonempty weighted-history cases have nonzero total weight. Rust rejects nonfinite results, including all-zero history weights.',
                               'Caller supplies calibration and list-order history; list update/lifetime and full gain controllers remain unfinished.',
                               'Synthetic calibration includes unordered knots and percentages above 100; no physical calibration validity is claimed.'])
    (ROOT / 'reverse-engineering/rkaiq/awb-temporal-equivalence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
