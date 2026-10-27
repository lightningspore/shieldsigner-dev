#!/usr/bin/env python3
"""Execute both native spatial gain stages, including original gain mixtures."""
import hashlib
import json
import random
import struct
import subprocess
import sys

from awb_reference import OriginalAwb
from differential import BINARY, HEAP, ROOT, f32


def native(arm, value):
    lights = value['lights']
    context = bytearray([0x5a]) * 0x4000
    strategy = bytearray([0x6b]) * 0x400
    reference = bytearray([0x7c]) * (len(lights) * 0xe4)
    results = bytearray([0x8d]) * (len(lights) * 0xa0)
    struct.pack_into('<I', context, 0x8c, HEAP + 0x8000)
    struct.pack_into('<I', context, 0x33d8, value['brightness'])
    struct.pack_into('<II', context, 0x33e0, value['group'], HEAP + 0x20000)
    strategy[0x138] = len(lights)
    struct.pack_into('<I', strategy, 0x368, HEAP + 0x10000)
    for i, light in enumerate(lights):
        struct.pack_into('<II', reference, i * 0xe4 + 0x78, light['high'], light['low'])
        struct.pack_into('<4f', reference, i * 0xe4 + 0x90, *light['high_gain'])
        struct.pack_into('<4f', reference, i * 0xe4 + 0xa0, *light['low_gain'])
        reference[i * 0xe4 + 0x68 + value['group']] = light['percentage']
        struct.pack_into('<4f', results, i * 0xa0 + 0x64, *light['statistics'])
    blocks = [(0, context), (0x8000, strategy), (0x10000, reference), (0x20000, results)]
    for offset, data in blocks:
        if data:
            arm.uc.mem_write(HEAP + offset, bytes(data))
    arm.invoke('_Z19AwbCalGainInSpatialP12awb_contex_s', [HEAP], instructions=1000000)
    spatial = [list(struct.unpack('<4I', arm.uc.mem_read(HEAP + 0x20000 + i * 0xa0 + 0x84, 16)))
               for i in range(len(lights))]
    arm.invoke('_Z32AwbCalGainBySpatialMulStatisticsP12awb_contex_s', [HEAP], instructions=1000000)
    after = bytearray(arm.uc.mem_read(HEAP + 0x20000, len(results))) if results else bytearray()
    output = []
    for i in range(len(lights)):
        output.append(dict(spatial=spatial[i], mixed=list(struct.unpack_from('<4I', after, i * 0xa0 + 0x64)),
                           weight=struct.unpack_from('<I', after, i * 0xa0 + 0x98)[0]))
        assert list(struct.unpack_from('<4I', after, i * 0xa0 + 0x84)) == spatial[i]
        for offset, size in [(0x64, 16), (0x84, 16), (0x98, 4)]:
            start = i * 0xa0 + offset
            after[start:start + size] = results[start:start + size]
    assert after == results, 'Unexpected per-light write'
    for offset, data in blocks[:-1]:
        if data:
            assert bytes(arm.uc.mem_read(HEAP + offset, len(data))) == data
    return output


def main():
    manifest = json.loads((ROOT / 'reverse-engineering/rkaiq/artifacts.json').read_text())
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == next(v['sha256'] for v in manifest['binaries'] if v['name'] == BINARY.name)
    arm = OriginalAwb()
    rng = random.Random(0x53504154)
    cases = []
    expected = []
    boundaries = [0, 99, 100, 101, 199, 200, 201, 0xffffffff, 16777216, 16777217, 16777218]
    for i in range(1024):
        n = 255 if i % 127 == 0 else i % 9
        value = dict(brightness=boundaries[i % len(boundaries)], group=i % 4, lights=[])
        for j in range(n):
            low, high = [(100, 200), (100, 100), (200, 100), (16777216, 16777217),
                         (0, 0xffffffff), (0xffffffff, 0xffffffff)][(i + j) % 6]
            gain = lambda: [f32(rng.uniform(.1, 9.)) for _ in range(4)]
            light = dict(low=low, high=high, low_gain=gain(), high_gain=gain(), statistics=gain(),
                         percentage=[0, 1, 50, 99, 100, 101, 255][(i + j) % 7])
            if i % 13 == 0:
                light['low_gain'] = [0.] * 4
            if i % 17 == 0:
                light['high_gain'] = [6., 7., 8., 9.]
            value['lights'].append(light)
        cases.append(value)
        expected.append(native(arm, value))
    assert not arm.calls and not arm.runtime.calls
    inputs = ''.join('awb-spatial ' + json.dumps(v, separators=(',', ':')) + '\n' for v in cases)

    def compare(command):
        result = subprocess.run(command, input=inputs, text=True, capture_output=True, check=True)
        actual = [json.loads(line) for line in result.stdout.splitlines()]
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
    report = dict(binarySha256=sha, cases=len(cases), illuminationResults=sum(len(v['lights']) for v in cases),
                  mismatches=0, arm=replay, elfEntries=dict(spatial='0xc66d0', spatialStatistics='0xc67a8'),
                  scope='Original spatial selection and statistics mixture run consecutively; exact intermediate/final gain and weight bits, unrelated-memory preservation',
                  limitations=['Finite gain inputs; explicit per-light calibration and statistics, not full AWB calibration loading.',
                               'High/low gain controllers, temporal policy and outer integration remain unfinished.',
                               'Native percentage bytes above 100 extrapolate; this does not establish physical calibration validity.'])
    (ROOT / 'reverse-engineering/rkaiq/awb-spatial-equivalence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
