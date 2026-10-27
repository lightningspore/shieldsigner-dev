#!/usr/bin/env python3
"""Native 9x11 lookup and complete AWB gain adjustment, including CCT helpers."""
import hashlib
import json
import random
import struct
import subprocess
import sys

from awb_reference import OriginalAwb
from differential import BINARY, HEAP, ROOT, f32, regs

SHIFT = '_Z11AwbCtShift331CalibDbV2_Awb_Cct_Lut_Cfg_Lv2_s21color_tempture_info_sPS0_'
ADJUST = '_Z14AwbGainAdjust3P12awb_contex_s'


def encode(lut):
    return struct.pack('<219f', lut['sample'], *(lut['x'] + lut['y'] + lut['mapped_x'] + lut['mapped_y']))


class Original(OriginalAwb):
    def hook(self, uc, address, size, user):
        if address == (self.symbols.get('xcam_print_log', 0) & ~1):
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, v):
        if v['kind'] == 'shift':
            lut = encode(v['luts'][0])
            before = bytes([0x5a]) * 20
            self.uc.mem_write(HEAP, before)
            stack = lut[16:] + struct.pack('<I2fI', 0, *v['input'], HEAP + 4)
            self.invoke(SHIFT, struct.unpack_from('<4I', lut), stack=stack)
            after = bytes(self.uc.mem_read(HEAP, 20))
            assert after[:4] == after[16:] == before[:4] and after[5:8] == before[5:8]
            assert after[4] == 1
            return list(struct.unpack_from('<2I', after, 8))
        context = bytearray([0x5a]) * 0x4000
        config = bytearray([0x6b]) * 0x800
        calibration = bytearray([0x7c]) * 0x800
        tables = b''.join(encode(v) for v in v['luts'])
        struct.pack_into('<I', context, 0x8c, HEAP + 0x8000)
        struct.pack_into('<I', context, 0x80, HEAP + 0x9000)
        struct.pack_into('<f', context, 0x5c, v['alternate_sample'])
        struct.pack_into('<f', context, 0x33dc, v['sample'])
        struct.pack_into('<4f', context, 0x353c, *v['gain'])
        struct.pack_into('<2f', context, 0x34f8, 12., 13.)
        struct.pack_into('<2f', context, 0x3504, 14., 15.)
        for offset, values in [(0x348, v['first']), (0x358, v['second'])]:
            struct.pack_into('<3fI', config, offset, *values[:3], values[3])
        calibration[0x538] = 1
        struct.pack_into('<4I', calibration, 0x53c, v['selector'], v['mode'], HEAP + 0x10000, len(v['luts']))
        blocks = [(0, context), (0x8000, config), (0x9000, calibration), (0x10000, tables)]
        for offset, data in blocks:
            self.uc.mem_write(HEAP + offset, bytes(data))
        self.invoke(ADJUST, [HEAP], instructions=1000000)
        after = bytearray(self.uc.mem_read(HEAP, len(context)))
        output = dict(gain=list(struct.unpack_from('<4I', after, 0x353c)), before=list(struct.unpack_from('<2I', after, 0x34f8)),
                      after=list(struct.unpack_from('<2I', after, 0x3504)))
        # Native caches copy temporary validity/padding words, including an
        # uninitialized word on the two-LUT interpolation path. Compare values.
        for offset, size in [(0x353c, 16), (0x34f4, 12), (0x3500, 12)]:
            after[offset:offset + size] = context[offset:offset + size]
        assert after == context
        for offset, data in blocks[1:]:
            assert bytes(self.uc.mem_read(HEAP + offset, len(data))) == data
        return output


def main():
    manifest = json.loads((ROOT / 'reverse-engineering/rkaiq/artifacts.json').read_text())
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == next(v['sha256'] for v in manifest['binaries'] if v['name'] == BINARY.name)
    arm = Original()
    rng = random.Random(0x41444a33)
    cases, expected, rejected = [], [], 0
    def nonfinite(value):
        values = value if isinstance(value, list) else [x for values in value.values() for x in values]
        return any((x & 0x7fffffff) >= 0x7f800000 for x in values)
    for kind in ['shift', 'adjust']:
        for i in range(1024):
            temperature = i % 3 == 1
            x = [float(1000 + 1000 * j) for j in range(9)] if temperature else [f32(.5 + .25 * j) for j in range(9)]
            y = [f32(-.2 + .04 * j) for j in range(11)] if temperature else [f32(.5 + .25 * j) for j in range(11)]
            if i % 2:
                x.reverse()
            if i // 2 % 2:
                y.reverse()
            luts = []
            for k in range(1 + i % 4):
                table = dict(sample=float(10 * k), x=x, y=y, mapped_x=[], mapped_y=[])
                for row in range(11):
                    for col in range(9):
                        table['mapped_x'].append(f32(x[col] + rng.uniform(-.1, .1) * (1000 if temperature else 1) + k * (20 if temperature else .02)))
                        table['mapped_y'].append(f32(y[row] + rng.uniform(-.02, .02) + k * .01))
                luts.append(table)
            input_x = [x[0], x[-1], min(x) - 1., max(x) + 1., f32((x[3] + x[4]) * .5)][i // 4 % 5]
            input_y = [y[0], y[-1], min(y) - .1, max(y) + .1, f32((y[4] + y[5]) * .5)][i // 20 % 5]
            v = dict(kind=kind, luts=luts, input=[input_x, input_y], mode=i % 3, selector=i % 2,
                     gain=[f32(rng.uniform(.2, 5.)) for _ in range(4)], sample=[-1., 0., 5., 10., 15., 50.][i // 4 % 6],
                     alternate_sample=[-1., 0., 5., 10., 15., 50.][i // 24 % 6],
                     first=[-.8, -.6, -2.4, i % 11 != 0], second=[1., -.0002, .5, i % 17 != 0])
            if i % 13 == 0:
                v['gain'][1 + i % 2] = [0., -1., f32(.00001), f32(.000010001)][i // 13 % 4]
            if len(luts) > 1 and i % 29 == 0:
                for k, table in enumerate(luts):
                    table['sample'] = f32(k * .000001)
                v['sample'] = v['alternate_sample'] = f32(.0000005)
            if len(luts) > 2 and i % 31 == 0:
                luts[-1]['sample'] = luts[-2]['sample']
            cases.append(v)
            result = arm.run(v)
            if nonfinite(result):
                rejected += 1
                result = dict(rejected=True)
            expected.append(result)
    assert set(arm.calls) <= {'memcpy'} and not arm.runtime.calls
    inputs = ''.join('awb-gain-adjust ' + json.dumps(v, separators=(',', ':')) + '\n' for v in cases)

    def compare(command):
        p = subprocess.run(command, input=inputs, text=True, capture_output=True)
        assert p.returncode == 0, (len(p.stdout.splitlines()), p.stderr)
        actual = [json.loads(line) for line in p.stdout.splitlines()]
        assert len(actual) == len(expected)
        mismatches = [(i, {k: v for k, v in cases[i].items() if k != 'luts'}, a, b) for i, (a, b) in enumerate(zip(expected, actual)) if a != b]
        assert not mismatches, (len(mismatches), mismatches[:3])

    compare([str(ROOT / 'firmware/rkaiq-rs/target/release/numeric-fixture')])
    replay = '--arm' in sys.argv
    if replay:
        directory = ROOT / 'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
        compare(['docker', 'run', '--rm', '-i', '--platform', 'linux/arm/v7', '--network=none',
                 '--mount', f'type=bind,src={directory},dst=/bincheck,readonly',
                 'alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd',
                 '/bincheck/numeric-fixture'])
    report = dict(binarySha256=sha, cases=len(cases), casesPerFunction=1024, exactFiniteCases=len(cases)-rejected,
                  rejectedNativeNonfiniteCases=rejected, mismatches=0, arm=replay,
                  elfEntries=dict(shift='0xca340', adjust='0xcad70'),
                  scope='Complete original 9x11 lookup and gain-adjustment call trees; exact gain/cache coordinate bits and unrelated-memory preservation',
                  limitations=['Exact bits are compared for finite native results. Native endpoint 0/0 NaN cases must be rejected by the checked API and are counted separately.',
                               'Finite checked values, strict monotonic LUT axes and nondecreasing level samples. Remaining native endpoint zero-weight out-of-array reads are replaced by bounded endpoint cells.',
                               'Undefined temporary validity/padding cache words are excluded; defined coordinate values are compared.',
                               'Standard memory copy/logging are adapters; original LUT/index/interpolation/CCT/normalization bodies execute.',
                               'Complete outer AWB composition, calibration loading and live integration remain unfinished.'])
    (ROOT / 'reverse-engineering/rkaiq/awb-gain-adjust-equivalence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
