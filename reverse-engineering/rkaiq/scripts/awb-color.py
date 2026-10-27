#!/usr/bin/env python3
"""Original color transforms, with pinned uClibc ARM math bodies, not host math."""
import hashlib
import json
import random
import struct
import subprocess
import sys

from awb_reference import OriginalAwb
from differential import BINARY, HEAP, ROOT, OriginalArm, f32, regs

MATH = ROOT / '.tools/reverse-engineering/uclibc-runtime/libuClibc-1.0.31.so'
SYMBOLS = dict(transfer='_Z1ff', xyz='_Z7rgb2xyzfffPfS_S_', lab='_Z7xyz2labfffPfS_S_', lch='_Z7lab2lchffPfS_')


class OriginalColor(OriginalAwb):
    def __init__(self):
        super().__init__()
        self.math = OriginalArm(MATH, tls=True)
        self.math_calls = {}

    def hook(self, uc, address, size, user):
        name = self.stubs.get(address)
        if name in ('powf', 'sqrtf', 'atan2f'):
            count = 1 if name == 'sqrtf' else 2
            values = [struct.unpack('<f', struct.pack('<I', uc.reg_read(getattr(regs, f'UC_ARM_REG_S{i}'))))[0]
                      for i in range(count)]
            self.math.invoke(name, floats=values)
            self.math_calls[name] = self.math_calls.get(name, 0) + 1
            uc.reg_write(regs.UC_ARM_REG_S0, self.math.uc.reg_read(regs.UC_ARM_REG_S0))
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def transform(self, kind, values):
        pointers = [HEAP + 0x100 + i * 8 for i in range(3)]
        self.uc.mem_write(HEAP + 0x100, bytes([0x5a]) * 24)
        if kind == 'transfer':
            self.invoke(SYMBOLS[kind], floats=[values[0]])
            assert bytes(self.uc.mem_read(HEAP + 0x100, 24)) == bytes([0x5a]) * 24
            return [self.uc.reg_read(regs.UC_ARM_REG_S0)]
        n = 2 if kind == 'lch' else 3
        self.invoke(SYMBOLS[kind], pointers[:n], floats=values[:n])
        output = [struct.unpack('<I', self.uc.mem_read(pointer, 4))[0] for pointer in pointers[:n]]
        after = bytearray(self.uc.mem_read(HEAP + 0x100, 24))
        for i in range(n):
            after[i * 8:i * 8 + 4] = bytes([0x5a]) * 4
        assert after == bytes([0x5a]) * 24
        return output

    def run(self, value):
        if value['kind'] != 'pipeline':
            return self.transform(value['kind'], value['input'])
        floats = lambda values: [struct.unpack('<f', struct.pack('<I', v))[0] for v in values]
        xyz = self.transform('xyz', value['input'])
        lab = self.transform('lab', floats(xyz))
        lch = self.transform('lch', floats(lab)[1:])
        return xyz + lab + lch


def main():
    manifest = json.loads((ROOT / 'reverse-engineering/rkaiq/artifacts.json').read_text())
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    math_sha = hashlib.sha256(MATH.read_bytes()).hexdigest()
    assert sha == next(v['sha256'] for v in manifest['binaries'] if v['name'] == BINARY.name)
    assert math_sha == manifest['uclibcRuntime']['memberSha256']
    arm = OriginalColor()
    rng = random.Random(0x434f4c52)
    cases, expected = [], []
    for kind in ['transfer', 'xyz', 'lab', 'lch', 'pipeline']:
        for i in range(1024):
            values = [f32(rng.uniform(-.1, 1.5)) for _ in range(3)]
            if kind == 'transfer':
                if i % 4 == 0:
                    values[0] = [0., f32(.008856451), f32(.008856452), 1., -1., 1e-20, 100.][i // 4 % 7]
            elif kind == 'lch':
                values[:2] = [f32(rng.uniform(-150, 150)) for _ in range(2)]
                if i % 5 == 0:
                    values[:2] = [[0., 0.], [0., -0.], [-0., 0.], [-0., -0.], [1., 0.], [0., 1.], [-1., 0.], [0., -1.], [1e-20, -1e-20]][i // 5 % 9]
            elif i % 7 == 0:
                values = [[0., 0., 0.], [1., 1., 1.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.], [.008856451] * 3][i // 7 % 6]
            v = dict(kind=kind, input=values)
            cases.append(v)
            expected.append(arm.run(v))
    assert not arm.calls and not arm.runtime.calls and not arm.math.calls
    inputs = ''.join('awb-color ' + json.dumps(v, separators=(',', ':')) + '\n' for v in cases)

    def compare(command):
        p = subprocess.run(command, input=inputs, text=True, capture_output=True)
        assert p.returncode == 0, (len(p.stdout.splitlines()), p.stderr)
        actual = [json.loads(line) for line in p.stdout.splitlines()]
        assert len(actual) == len(expected)
        mismatches = [(i, cases[i], a, b) for i, (a, b) in enumerate(zip(expected, actual)) if a != b]
        assert not mismatches, (len(mismatches), mismatches[:3])

    compare([str(ROOT / 'firmware/rkaiq-rs/target/release/numeric-fixture')])
    replay = '--arm' in sys.argv
    if replay:
        directory = ROOT / 'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
        compare(['docker', 'run', '--rm', '-i', '--platform', 'linux/arm/v7', '--network=none',
                 '--mount', f'type=bind,src={directory},dst=/bincheck,readonly',
                 'alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd',
                 '/bincheck/numeric-fixture'])
    report = dict(binarySha256=sha, mathRuntimeSha256=math_sha, cases=len(cases), casesPerStage=1024,
                  mismatches=0, arm=replay, nativeMathCalls=arm.math_calls,
                  elfEntries=dict(transfer='0xcbda0', xyz='0xcbce8', lab='0xcbdf0', lch='0xcbeb4'),
                  scope='Original transfer, RGB-to-XYZ, XYZ-to-Lab, Lab-to-LCh and joined RGB pipeline; exact output bits and output padding preservation',
                  limitations=['Finite checked inputs/outputs; synthetic RGB/XYZ range includes negative values and values above one, not physical calibration validity.',
                               'Pinned original uClibc powf/sqrtf/atan2f ARM bodies execute in an isolated emulator and return their actual result bits.',
                               'Corpus equivalence does not prove f64 libm equality for every possible input.',
                               'Grid classification, candidate/history construction and complete single-color orchestration remain unfinished.'])
    (ROOT / 'reverse-engineering/rkaiq/awb-color-equivalence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
