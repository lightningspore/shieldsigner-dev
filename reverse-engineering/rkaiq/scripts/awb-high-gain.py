#!/usr/bin/env python3
"""Compare complete, unmodified native high-WP gain orchestration with Rust."""
import hashlib
import json
import random
import struct
import subprocess
import sys

from awb_reference import OriginalAwb
from differential import BINARY, HEAP, ROOT, f32, regs


class Original(OriginalAwb):
    def hook(self, uc, address, size, user):
        if address == (self.symbols.get('xcam_print_log', 0) & ~1):
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)


def native(arm, v):
    n = len(v['lights'])
    context = bytearray([0x5a]) * 0x4000
    config = bytearray([0x6b]) * 0x400
    reference = bytearray([0x7c]) * (n * 0xe4)
    results = bytearray([0x8d]) * (n * 0xa0)
    statistics = bytearray([0x9e]) * (n * 0xac + 32)
    mode = bytearray(0x100)
    mode[0x1c:0x1c + 11] = b'FASTAWBACT\0' if v['fast'] else b'NORMAL\0\0\0\0\0'
    for offset, pointer in [(0x8c, 0x8000), (0x2dec, 0xa000), (0x33e4, 0x20000), (0x134, 0x30000)]:
        struct.pack_into('<I', context, offset, HEAP + pointer)
    struct.pack_into('<I', context, 0x33d8, v['brightness'])
    struct.pack_into('<I', context, 0x33e0, v['group'])
    context[0x33fc] = v['xy']
    config[0x138] = n
    struct.pack_into('<I', config, 0x368, HEAP + 0x10000)
    struct.pack_into('<16I', config, 0x168, *v['knots'])
    struct.pack_into('<4f', config, 0x1d8, *v['default'])
    config[0x1f8:0x208] = bytes(v['percentages'])
    for i, light in enumerate(v['lights']):
        struct.pack_into('<II', reference, i * 0xe4 + 0x78, light['high'], light['low'])
        struct.pack_into('<4f', reference, i * 0xe4 + 0x90, *light['high_gain'])
        struct.pack_into('<4f', reference, i * 0xe4 + 0xa0, *light['low_gain'])
        reference[i * 0xe4 + 0xb0] = light['extra_enabled']
        reference[i * 0xe4 + 0x68 + v['group']] = light['percentage']
        struct.pack_into('<I4f', statistics, i * 0xac + v['xy'] * 0x34, light['selected_count'], *light['selected_gain'])
        struct.pack_into('<I4f', statistics, i * 0xac + 0x68, light['extra_count'], *light['extra_gain'])
        struct.pack_into('<f', results, i * 0xa0 + 0x74, light['probability'])
        struct.pack_into('<2f', results, i * 0xa0 + 0x98, .25, .75)
    blocks = [(0, context), (0x8000, config), (0xa000, mode), (0x10000, reference),
              (0x20000, results), (0x30000, statistics)]
    for offset, data in blocks:
        arm.uc.mem_write(HEAP + offset, bytes(data))
    try:
        arm.invoke('_Z20AwbCalGainWpTypeHighP12awb_contex_s', [HEAP], instructions=3000000)
    except Exception:
        print('native failure', {name: hex(arm.uc.reg_read(reg)) for name, reg in
              [('pc', regs.UC_ARM_REG_PC), ('r0', regs.UC_ARM_REG_R0), ('r1', regs.UC_ARM_REG_R1), ('r2', regs.UC_ARM_REG_R2), ('r3', regs.UC_ARM_REG_R3)]}, file=sys.stderr)
        raise
    after = bytearray(arm.uc.mem_read(HEAP, len(context)))
    gain = list(struct.unpack_from('<4I', after, 0x353c))
    assert gain == list(struct.unpack_from('<4I', after, 0x341c))
    output = dict(gain=gain, temporal=list(struct.unpack_from('<4I', after, 0x33e8)),
                  weight=struct.unpack_from('<I', after, 0x33f8)[0], lights=[])
    for offset, size in [(0x33e8, 20), (0x341c, 16), (0x353c, 16)]:
        after[offset:offset + size] = context[offset:offset + size]
    assert after == context, 'Unexpected high-gain context write'
    after = bytearray(arm.uc.mem_read(HEAP + 0x20000, len(results)))
    for i in range(n):
        output['lights'].append(dict(statistic=list(struct.unpack_from('<4I', after, i * 0xa0 + 0x64)),
                                     spatial=list(struct.unpack_from('<4I', after, i * 0xa0 + 0x84)),
                                     spatial_weight=struct.unpack_from('<I', after, i * 0xa0 + 0x98)[0],
                                     extra_weight=struct.unpack_from('<I', after, i * 0xa0 + 0x9c)[0]))
        for offset, size in [(0x64, 16), (0x84, 16), (0x98, 8)]:
            start = i * 0xa0 + offset
            after[start:start + size] = results[start:start + size]
    assert after == results
    for offset, data in blocks:
        if offset not in (0, 0x20000):
            assert bytes(arm.uc.mem_read(HEAP + offset, len(data))) == data
    return output


def main():
    manifest = json.loads((ROOT / 'reverse-engineering/rkaiq/artifacts.json').read_text())
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == next(v['sha256'] for v in manifest['binaries'] if v['name'] == BINARY.name)
    arm = Original(stdlib=True)
    rng = random.Random(0x48494748)
    cases, expected = [], []
    for i in range(1024):
        gain = lambda: [f32(rng.uniform(.1, 9.)) for _ in range(4)]
        knots = [100 * j for j in range(16)] if i % 3 else [16777216 + j for j in range(16)]
        brightness = [0, 99, 100, 101, 199, 200, 201, 0xffffffff, knots[i % 16]][i % 9]
        v = dict(brightness=brightness, group=i % 4, xy=[0, 1, 3][i % 3], fast=bool(i % 2),
                 default=gain(), knots=knots, percentages=[rng.choice([0, 50, 100, 255]) for _ in range(16)], lights=[])
        n = 255 if i % 127 == 0 else 1 + i % 8
        for j in range(n):
            low, high = [(100, 200), (100, 100), (200, 100), (16777216, 16777217)][(i + j) % 4]
            light = dict(selected_gain=gain(), selected_count=rng.choice([0, 1, 100, 0x80000000, 0xffffffff]),
                         extra_gain=gain(), extra_count=rng.choice([0, 1, 100, 0x80000000, 0xffffffff]),
                         extra_enabled=bool((i + j) % 2), low=low, high=high, low_gain=gain(), high_gain=gain(),
                         percentage=[0, 50, 100, 255][(i + j) % 4], probability=f32(rng.uniform(0, 1)))
            if i % 11 == 0:
                light['probability'] = 0.
            if i % 13 == 0:
                light['selected_gain'] = [0.] * 4
            v['lights'].append(light)
        cases.append(v)
        expected.append(native(arm, v))
    assert not arm.calls and not arm.runtime.calls
    assert arm.standard_calls == {'strcmp': len(cases)}
    inputs = ''.join('awb-high-gain ' + json.dumps(v, separators=(',', ':')) + '\n' for v in cases)

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
    report = dict(binarySha256=sha, cases=len(cases), illuminationResults=sum(len(v['lights']) for v in cases),
                  mismatches=0, arm=replay, elfEntry='0xc6a20', modeledCalls=arm.standard_calls,
                  scope='Complete original AwbCalGainWpTypeHigh call tree; final/stored gain, temporal source/weight, every represented per-light result and unrelated-memory preservation',
                  limitations=['Bounded strcmp and logging adapters only; gain orchestration and all numerical helper bodies execute natively.',
                               'Explicit finite calibration, selected-region statistics and precomputed total probabilities; upstream derivation and full outer AWB controller are separate.',
                               'Low-count strategy, calibration loading and live sensor integration remain unfinished.'])
    (ROOT / 'reverse-engineering/rkaiq/awb-high-gain-equivalence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
