#!/usr/bin/env python3
"""Original inverse-CCT conversion and complete AWB gain clipping call tree."""
import hashlib
import json
import random
import struct
import subprocess
import sys

from awb_reference import OriginalAwb
from differential import BINARY, HEAP, ROOT, f32, regs

INVERSE = '_Z17AwbCalcWBgainbyCT21color_tempture_info_s6line_sS0_Pf'
CLIP = '_Z11AwbGainClipP12awb_contex_s'


class Original(OriginalAwb):
    def hook(self, uc, address, size, user):
        if address == (self.symbols.get('xcam_print_log', 0) & ~1):
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, v):
        first, second = v['first'], v['second']
        if v['kind'] == 'inverse':
            before = bytes([0x5a]) * 4 + struct.pack('<4f', *v['gain']) + bytes([0x5a]) * 4
            self.uc.mem_write(HEAP, before)
            bits = lambda v: struct.unpack('<I', struct.pack('<f', v))[0]
            stack = struct.pack('<2fI3fII', *first[1:3], first[3], *second[:3], second[3], HEAP + 4)
            status = self.invoke(INVERSE, [v['valid'], bits(v['cct']), bits(v['ccri']), bits(first[0])], stack=stack)
            assert status in (0, 0xffffffff)
            after = bytes(self.uc.mem_read(HEAP, 24))
            assert after[:4] == after[20:] == bytes([0x5a]) * 4
            return dict(gain=list(struct.unpack_from('<4I', after, 4)), converted=status == 0)
        context = bytearray([0x5a]) * 0x4000
        config = bytearray([0x6b]) * 0x800
        curves = bytearray(12 * len(v['knots']))
        struct.pack_into('<I', context, 0x8c, HEAP + 0x8000)
        struct.pack_into('<I', context, 0x33d8, v['brightness'])
        struct.pack_into('<4f', context, 0x353c, *v['gain'])
        context[0x348c] = v['clipped']
        config[0x122], config[0x123] = v['bounds'], v['daylight']
        struct.pack_into('<I', config, 0x1d4, v['daylight_threshold'])
        struct.pack_into('<f4I', config, 0x36c, v['daylight_minimum'], len(v['knots']), HEAP + 0x9000,
                         HEAP + 0x9000 + 4 * len(v['knots']), HEAP + 0x9000 + 8 * len(v['knots']))
        for offset, line in [(0x348, first), (0x358, second)]:
            struct.pack_into('<3fI', config, offset, *line[:3], line[3])
        struct.pack_into('<' + 'f' * (len(v['knots']) * 3), curves, 0, *(v['knots'] + v['lower'] + v['upper']))
        for offset, data in [(0, context), (0x8000, config), (0x9000, curves)]:
            self.uc.mem_write(HEAP + offset, bytes(data))
        self.invoke(CLIP, [HEAP])
        after = bytearray(self.uc.mem_read(HEAP, len(context)))
        output = dict(gain=list(struct.unpack_from('<4I', after, 0x353c)), clipped=bool(after[0x348c]))
        for offset, size in [(0x353c, 16), (0x348c, 1)]:
            after[offset:offset + size] = context[offset:offset + size]
        assert after == context
        for offset, data in [(0x8000, config), (0x9000, curves)]:
            assert bytes(self.uc.mem_read(HEAP + offset, len(data))) == data
        return output


def main():
    manifest = json.loads((ROOT / 'reverse-engineering/rkaiq/artifacts.json').read_text())
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == next(v['sha256'] for v in manifest['binaries'] if v['name'] == BINARY.name)
    arm = Original()
    rng = random.Random(0x434c4950)
    cases, expected = [], []
    for kind in ['inverse', 'clip']:
        for i in range(1024):
            n = 1 + i % 8
            v = dict(kind=kind, gain=[f32(rng.uniform(.1, 9.)) for _ in range(4)],
                     first=[f32(rng.uniform(-1, -.1)), f32(rng.uniform(-1, -.1)), f32(rng.uniform(-3, -1)), i % 11 != 0],
                     second=[f32(rng.uniform(.1, 2)), f32(rng.uniform(-.005, -.0001)), f32(rng.uniform(.1, 1)), i % 13 != 0],
                     valid=bool(i % 2), cct=f32(rng.uniform(-10000, 10000)), ccri=f32(rng.uniform(-2, 2)),
                     daylight=bool(i % 2), daylight_threshold=100, daylight_minimum=[2000., 5000., 10000.][i % 3],
                     bounds=bool(i // 2 % 2), brightness=[0, 100, 101, 0xffffffff][i // 4 % 4], clipped=bool(i // 16 % 2),
                     knots=[1000. * (j + 1) for j in range(n)], lower=[f32(rng.uniform(0, 1)) for _ in range(n)],
                     upper=[f32(rng.uniform(0, 1)) for _ in range(n)])
            if i % 7 == 0:
                v['second'][0] = [0., f32(.00001), f32(.000010001), -f32(.000010001)][i // 7 % 4]
            if i % 17 == 0:
                v['gain'][1 + i % 2] = [0., -1., f32(.00001), f32(.000010001)][i // 17 % 4]
            if i % 19 == 0:
                v['second'][1] = [0., f32(.00001), -f32(.00001), -f32(.000010001)][i // 19 % 4]
            if n > 1 and i % 3 == 0:
                v['knots'][-1] = v['knots'][-2]
            if i % 23 == 0:
                v['lower'] = [-1.] * n
                v['upper'] = [-2.] * n
            cases.append(v)
            expected.append(arm.run(v))
    assert not arm.calls and not arm.runtime.calls
    inputs = ''.join('awb-gain-clip ' + json.dumps(v, separators=(',', ':')) + '\n' for v in cases)

    def compare(command):
        p = subprocess.run(command, input=inputs, text=True, capture_output=True)
        assert p.returncode == 0, (len(p.stdout.splitlines()), p.stderr)
        actual = [json.loads(line) for line in p.stdout.splitlines()]
        assert len(actual) == len(expected)
        mismatches = [(i, cases[i], a, b) for i, (a, b) in enumerate(zip(expected, actual)) if a != b]
        assert not mismatches, (len(mismatches), mismatches[:2])

    compare([str(ROOT / 'firmware/rkaiq-rs/target/release/numeric-fixture')])
    replay = '--arm' in sys.argv
    if replay:
        directory = ROOT / 'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
        compare(['docker', 'run', '--rm', '-i', '--platform', 'linux/arm/v7', '--network=none',
                 '--mount', f'type=bind,src={directory},dst=/bincheck,readonly',
                 'alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd',
                 '/bincheck/numeric-fixture'])
    report = dict(binarySha256=sha, cases=len(cases), casesPerFunction=1024, mismatches=0, arm=replay,
                  elfEntries=dict(inverseColorTemperature='0xca908', clip='0xca9c0'),
                  scope='Original inverse CCT conversion and complete AwbGainClip forward/clamp/inverse call tree; exact gain bits, status/flag and unrelated-memory preservation',
                  limitations=['Finite checked active inputs/outputs and nondecreasing finite bounds; first-line B zero division/nonfinite result domains are rejected.',
                               'Only logging is adapted; original numerical/interpolation/normalization helpers execute.',
                               'Gain adjustment LUT, complete outer composition and live AWB remain unfinished.'])
    (ROOT / 'reverse-engineering/rkaiq/awb-gain-clip-equivalence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
