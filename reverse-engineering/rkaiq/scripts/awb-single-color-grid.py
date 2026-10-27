#!/usr/bin/env python3
"""Complete native single-color classifier, including original runtime math."""
import hashlib
import importlib.util
import json
import random
import struct
import subprocess
import sys

from differential import BINARY, HEAP, ROOT, STACK, f32, regs

spec = importlib.util.spec_from_file_location('awb_color_reference', __file__.replace('awb-single-color-grid.py', 'awb-color.py'))
color_reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(color_reference)
SYMBOL = '_Z22AwbSingleColorProcess226rk_aiq_awb_stat_res_full_sP19CalibDbV2_Awb_Sgc_s6line_sS2_P12sgc_result_sP9list_headPfS7_'


class Original(color_reference.OriginalColor):
    def __init__(self):
        super().__init__()
        self.uc.mem_map(STACK + 0x100000, 0x10000)

    def hook(self, uc, address, size, user):
        if address == (self.symbols.get('xcam_print_log', 0) & ~1):
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        name = self.stubs.get(address)
        if name in ('malloc', 'free'):
            value = uc.reg_read(regs.UC_ARM_REG_R0)
            if name == 'malloc':
                assert 0 < value <= 60
                pointer = self.arena
                self.arena += 64
                self.live[pointer] = value
                uc.mem_write(pointer, bytes([0xa7]) * value)
                uc.reg_write(regs.UC_ARM_REG_R0, pointer)
            else:
                assert value in self.live
                del self.live[value]
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, v):
        stats = bytearray(0x2cb0)
        struct.pack_into('<675f', stats, 0xe48, *(channel for rgb in v['grid'] for channel in rgb))
        config = bytearray(0x140)
        struct.pack_into('<IIIIH', config, 8, HEAP + 0x2000, len(v['colors']), HEAP + 0x3000, len(v['candidates']), v['target'])
        struct.pack_into('<f', config, 0x1c, v['alpha'])
        struct.pack_into('<i', config, 0x12c, -1)
        colors = bytearray(36 * len(v['colors']))
        for i, color in enumerate(v['colors']):
            struct.pack_into('<I8f', colors, i * 36, color.get('index', i), color['chroma'], color['hue'], *color['knots'], *color['thresholds'])
        candidates = bytearray(28 * len(v['candidates']))
        for i, gain in enumerate(v['candidates']):
            struct.pack_into('<2f', candidates, i * 28 + 20, *gain)
        result = bytes([0x5a]) * 0x90
        head = HEAP + 0x5000
        nodes = [HEAP + 0x5100 + i * 16 for i in range(len(v['history']))]
        self.uc.mem_write(head, struct.pack('<II', nodes[0] if nodes else head, nodes[-1] if nodes else head))
        for i, node in enumerate(nodes):
            self.uc.mem_write(node, struct.pack('<III', nodes[i + 1] if i + 1 < len(nodes) else head,
                                              nodes[i - 1] if i else head, v['history'][i]))
        prior = struct.pack('<4f', *v['prior']) if v['prior'] is not None else bytes(16)
        blocks = [(0x1000, config), (0x2000, colors), (0x3000, candidates), (0x4000, result), (0x6000, prior)]
        for offset, data in blocks:
            self.uc.mem_write(HEAP + offset, bytes(data))
        self.uc.mem_write(HEAP + 0x7000, bytes([0x6b]) * 24)
        first, second = v['first'], v['second']
        lines = struct.pack('<3fI3fI', *first[:3], first[3], *second[:3], second[3])
        stack = bytes(stats[16:]) + struct.pack('<I', HEAP + 0x1000) + lines + struct.pack('<4I', HEAP + 0x4000, head, HEAP + 0x6000 if v['prior'] is not None else 0, HEAP + 0x7004)
        self.arena, self.live = HEAP + 0x20000, {}
        self.invoke(SYMBOL, struct.unpack_from('<4I', stats), stack=stack, instructions=12000000)
        after = bytearray(self.uc.mem_read(HEAP + 0x4000, len(result)))
        output = dict(selected=struct.unpack_from('<i', after, 4)[0], color=struct.unpack_from('<i', after, 8)[0],
                      candidate_counts=list(struct.unpack_from('<14i', after, 0xc)), color_counts=list(struct.unpack_from('<14i', after, 0x44)),
                      valid=bool(struct.unpack_from('<I', after, 0x7c)[0]), disagreements=struct.unpack_from('<i', after, 0x80)[0],
                      votes=struct.unpack_from('<i', after, 0x84)[0], mean=struct.unpack_from('<I', after, 0x88)[0], history=[])
        word = lambda p: struct.unpack('<I', self.uc.mem_read(p, 4))[0]
        node, previous = word(head), head
        while node != head:
            assert len(output['history']) < 32 and word(node + 4) == previous
            output['history'].append(word(node + 8))
            previous, node = node, word(node)
        assert word(head + 4) == previous
        # Native retains its two candidate scratch allocations on return.
        # The Rust implementation uses bounded owned scratch instead.
        assert len(self.live) == 2 + len(output['history']) - len(v['history'])
        gain = bytes(self.uc.mem_read(HEAP + 0x7000, 24))
        assert gain[:4] == gain[20:] == bytes([0x6b]) * 4
        output['gain'] = list(struct.unpack_from('<4I', gain, 4))
        n = len(v['candidates']) + int(v['prior'] is not None and v['prior'][1] > .00001 and v['prior'][2] > .00001)
        for offset, size in [(4, 8), (0xc, n * 4), (0x44, len(v['colors']) * 4), (0x7c, 16)]:
            after[offset:offset + size] = result[offset:offset + size]
        assert after == result
        for offset, data in blocks:
            if offset != 0x4000:
                assert bytes(self.uc.mem_read(HEAP + offset, len(data))) == data
        assert bytes(self.uc.mem_read(STACK + 0xff000, len(stack))) == stack
        return output


def main():
    manifest = json.loads((ROOT / 'reverse-engineering/rkaiq/artifacts.json').read_text())
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    math_sha = hashlib.sha256(color_reference.MATH.read_bytes()).hexdigest()
    assert sha == next(v['sha256'] for v in manifest['binaries'] if v['name'] == BINARY.name)
    assert math_sha == manifest['uclibcRuntime']['memberSha256']
    arm = Original()
    rng = random.Random(0x53474347)
    cases, expected = [], []
    for i in range(48):
        n = 14 if i == 45 else 13 if i == 47 else 1 + i % 4
        v = dict(candidates=[[f32(rng.uniform(.5, 3)), f32(rng.uniform(.5, 3))] for _ in range(n)],
                 colors=[], history=[rng.randrange(n) for _ in range(i % 5)], target=[0, 2, 4, 8][i % 4],
                 first=[-.8, -.6, -2.4, bool(i % 5)], second=[1., -.0002, .5, bool(i % 7)],
                 alpha=f32([0., .5, .9, 1.][i % 4]), prior=None if i % 3 == 0 else [2., 1., 1., 1.5], grid=[])
        if i % 7 == 0 and v['prior'] is not None:
            v['prior'][1] = 0.
        if i % 11 == 0:
            v['candidates'] = [v['candidates'][0][:] for _ in range(n)]
        for j in range(1 + i % 3):
            threshold = [-1., 0., 2000., 1000000.][i // 3 % 4]
            v['colors'].append(dict(chroma=f32(20 + 30 * j), hue=f32(-120 + 120 * j), knots=[1000., 5000., 9000.], thresholds=[threshold] * 3))
        if i % 13 == 0:
            v['colors'] = [v['colors'][0].copy() for _ in v['colors']]
        base = [f32(rng.uniform(.05, .8)) for _ in range(3)]
        for cell in range(225):
            if i % 4 == 0:
                rgb = base
            elif i % 4 == 1:
                rgb = [.1, .4, .7] if cell % 15 < 7 else [.7, .3, .1]
            elif i % 4 == 2:
                rgb = [f32(rng.uniform(.01, 1.2)) for _ in range(3)]
            else:
                rgb = [.1, .1, .1] if cell < 112 else [.8, .8, .8]
            v['grid'].append(rgb)
        cases.append(v)
        expected.append(arm.run(v))
        if (i + 1) % 8 == 0:
            print(f'Native grid reference: {i + 1}/48', file=sys.stderr, flush=True)
    assert set(arm.calls) <= {'memcpy', 'memset'} and not arm.runtime.calls and not arm.math.calls
    inputs = ''.join('awb-single-color-grid ' + json.dumps(v, separators=(',', ':')) + '\n' for v in cases)

    def compare(command):
        p = subprocess.run(command, input=inputs, text=True, capture_output=True)
        assert p.returncode == 0, (len(p.stdout.splitlines()), p.stderr)
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
    report = dict(binarySha256=sha, mathRuntimeSha256=math_sha, cases=len(cases), cells=len(cases) * 225,
                  mismatches=0, arm=replay, valid=sum(v['valid'] for v in expected), elfEntry='0xcb208', nativeMathCalls=arm.math_calls,
                  scope='Complete original single-color grid process through normal return: result words, gain, history and unrelated-memory preservation',
                  limitations=['Allocation, standard memory and logging are explicit adapters; classifier, list, color and original uClibc math bodies execute.',
                               'Finite checked inputs, 1-14 available candidates/colors, bounded valid history indices; native unsafe index domains are rejected.',
                               'Enabled low-count orchestration, calibration loading and live AWB integration remain unfinished.'])
    (ROOT / 'reverse-engineering/rkaiq/awb-single-color-grid-equivalence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
