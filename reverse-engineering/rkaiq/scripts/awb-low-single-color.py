#!/usr/bin/env python3
"""Complete native low-count AWB with single-color processing enabled."""
import hashlib
import importlib.util
import json
import random
import struct
import subprocess
import sys

from differential import BINARY, HEAP, ROOT, f32, regs


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, __file__.replace('awb-low-single-color.py', filename))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


low = module('awb_low_reference', 'awb-low-gain.py')
color = module('awb_color_reference', 'awb-color.py')
PROCESS = '_Z22AwbSingleColorProcess226rk_aiq_awb_stat_res_full_sP19CalibDbV2_Awb_Sgc_s6line_sS2_P12sgc_result_sP9list_headPfS7_'


class Original(color.OriginalColor):
    def hook(self, uc, address, size, user):
        if address == (self.symbols.get(PROCESS, 0) & ~1):
            self.single_calls += 1
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
                self.live.add(pointer)
                uc.mem_write(pointer, bytes([0xa7]) * value)
                uc.reg_write(regs.UC_ARM_REG_R0, pointer)
            else:
                assert value in self.live
                self.live.remove(value)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def setup_single(self, v, context, config, calibration):
        self.single_calls = 0
        s = v['single']
        context[0xf79] = s['grid_valid']
        struct.pack_into('<675f', context, 0xf7c, *(x for rgb in s['grid'] for x in rgb))
        struct.pack_into('<f', context, 0x33cc, s['density'])
        struct.pack_into('<f', context, 0x33dc, s['brightness_sample'])
        struct.pack_into('<4f', context, 0x3450, *([9.] * 4))
        struct.pack_into('<f', context, 0x3460, .75)
        struct.pack_into('<4f', context, 0x35a8, *s['estimated'])
        for offset, values in [(0x348, s['first']), (0x358, s['second'])]:
            struct.pack_into('<3fI', config, offset, *values[:3], values[3])
        base = 0x644
        calibration[base] = 1
        struct.pack_into('<i', calibration, base + 4, s['mode'])
        struct.pack_into('<IIIIH', calibration, base + 8, HEAP + 0x60000, len(s['colors']), HEAP + 0x61000, len(s['candidates']), v['target'])
        struct.pack_into('<f', calibration, base + 0x1c, s['alpha'])
        struct.pack_into('<i', calibration, base + 0x12c, -1)
        struct.pack_into('<f', calibration, 0x774, s['threshold'])
        c = s['confidence']
        for key, offset in [('brightness_knots', 0xbc), ('brightness_weights', 0xdc), ('density_knots', 0xfc),
                            ('density_weights', 0x114), ('distance_knots', 0x50), ('cct_knots', 0x68),
                            ('disagreement_knots', 0x20), ('disagreement_weights', 0x38)]:
            struct.pack_into('<' + 'f' * len(c[key]), calibration, base + offset, *c[key])
        for i, values in enumerate(c['distance_weights']):
            struct.pack_into('<6f', calibration, base + 0x74 + 24 * i, *values)
        colors = bytearray(36 * len(s['colors']))
        for i, value in enumerate(s['colors']):
            struct.pack_into('<I8f', colors, 36 * i, i, value['chroma'], value['hue'], *value['knots'], *value['thresholds'])
        candidates = bytearray(28 * len(s['candidates']))
        for i, gain in enumerate(s['candidates']):
            struct.pack_into('<2f', candidates, 28 * i + 20, *gain)
        head = HEAP + 0x3598
        addresses = [HEAP + 0x62000 + 24 * i for i in range(len(s['high_history']))]
        struct.pack_into('<II', context, 0x3598, addresses[0] if addresses else head, addresses[-1] if addresses else head)
        nodes = bytearray(len(addresses) * 24)
        for i, gain in enumerate(s['high_history']):
            struct.pack_into('<II4f', nodes, i * 24, addresses[i + 1] if i + 1 < len(addresses) else head,
                             addresses[i - 1] if i else head, *gain)
        return [(0x60000, colors), (0x61000, candidates)] + ([(0x62000, nodes)] if nodes else [])

    def read_single(self, context):
        base = 0x35b8
        return dict(selected=struct.unpack_from('<i', context, base + 4)[0], color=struct.unpack_from('<i', context, base + 8)[0],
                    candidate_counts=list(struct.unpack_from('<14i', context, base + 0xc)), color_counts=list(struct.unpack_from('<14i', context, base + 0x44)),
                    valid=bool(struct.unpack_from('<I', context, base + 0x7c)[0]), disagreements=struct.unpack_from('<i', context, base + 0x80)[0],
                    votes=struct.unpack_from('<i', context, base + 0x84)[0], mean=struct.unpack_from('<I', context, base + 0x88)[0],
                    gain=list(struct.unpack_from('<4I', context, 0x3450)), weight=struct.unpack_from('<I', context, 0x3460)[0])


def main():
    manifest = json.loads((ROOT / 'reverse-engineering/rkaiq/artifacts.json').read_text())
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    math_sha = hashlib.sha256(color.MATH.read_bytes()).hexdigest()
    assert sha == next(v['sha256'] for v in manifest['binaries'] if v['name'] == BINARY.name)
    assert math_sha == manifest['uclibcRuntime']['memberSha256']
    arm = Original()
    rng = random.Random(0x4c4f5753)
    cases, expected, calls, coverage = [], [], 0, {}
    for i in range(64):
        n = 1 + i % 3
        v = dict(brightness=[50, 150, 250, 150][i // 4 % 4], low=100, high=200, threshold=100,
                 retained=100 if i % 8 == 0 else 10, default=[2., 1., 1., 3.], used_previous=bool(i % 2),
                 history=[] if i % 4 < 2 else [[3., 1., 1., 2.], [4., 1., 1., 3.]], colors=[rng.randrange(n) for _ in range(i % 4)],
                 color_value=n, target=[0, 2, 4, 8][i % 4], lights=[])
        for j in range(1 + i % 4):
            v['lights'].append(dict(low=100, high=200, low_gain=[2., 1., 1., 4.], high_gain=[3., 1., 1., 2.], probability=f32(1 / (1 + i % 4))))
        confidence = dict(brightness_knots=[float(j) for j in range(8)], brightness_weights=[.25 if i % 2 else .75] * 8,
                          density_knots=[float(j) for j in range(6)], density_weights=[1.] * 6,
                          distance_knots=[float(j) for j in range(6)], distance_weights=[[1.] * 6 for _ in range(3)], cct_knots=[1000., 5000., 9000.],
                          disagreement_knots=[float(j) for j in range(6)], disagreement_weights=[1.] * 6)
        s = dict(mode=[0, 1, 2, 1][i // 4 % 4], grid_valid=i % 7 != 0, candidates=[[1. + .5 * j, 1. + .25 * j] for j in range(n)],
                 colors=[dict(chroma=30., hue=60., knots=[1000., 5000., 9000.], thresholds=[-1. if i % 5 == 0 else 1000000.] * 3)],
                 alpha=.5, first=[-.8, -.6, -2.4, True], second=[1., -.0002, .5, True],
                 confidence=confidence, brightness_sample=3., density=2., threshold=.5,
                 estimated=[0. if i % 3 == 0 else 2., 1., 1., 3.], high_history=[] if i % 3 == 0 else [[2., 1., 1., 3.]],
                 grid=[[.2, .4, .6] if i % 3 else [.6, .4, .2] for _ in range(225)])
        v['single'] = s
        cases.append(v)
        expected.append(low.native(arm, v))
        calls += arm.single_calls
        key = f'mode{s["mode"]}:history{bool(v["history"])}:grid{s["grid_valid"]}'
        coverage[key] = coverage.get(key, 0) + 1
        if (i + 1) % 8 == 0:
            print(f'Native enabled low-WP reference: {i + 1}/64', file=sys.stderr, flush=True)
    assert set(arm.calls) <= {'memcpy', 'memset'} and not arm.runtime.calls and not arm.math.calls
    inputs = ''.join('awb-low-single-color ' + json.dumps(v, separators=(',', ':')) + '\n' for v in cases)

    def compare(command):
        p = subprocess.run(command, input=inputs, text=True, capture_output=True)
        assert p.returncode == 0, (len(p.stdout.splitlines()), p.stderr)
        actual = [json.loads(line) for line in p.stdout.splitlines()]
        assert len(actual) == len(expected)
        for i, (a, b) in enumerate(zip(expected, actual)):
            assert a == b, (i, {k: v for k, v in cases[i].items() if k != 'single'}, a, b)

    compare([str(ROOT / 'firmware/rkaiq-rs/target/release/numeric-fixture')])
    replay = '--arm' in sys.argv
    if replay:
        directory = ROOT / 'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
        compare(['docker', 'run', '--rm', '-i', '--platform', 'linux/arm/v7', '--network=none',
                 '--mount', f'type=bind,src={directory},dst=/bincheck,readonly',
                 'alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd',
                 '/bincheck/numeric-fixture'])
    report = dict(binarySha256=sha, mathRuntimeSha256=math_sha, cases=len(cases), classifierCalls=calls, coverage=coverage,
                  mismatches=0, arm=replay, elfEntry='0xc6a90',
                  scope='Complete original low-WP strategy with enabled single-color classifier/manager and actual runtime math, including gain/history/result preservation',
                  limitations=['Standard allocation, memory and logging boundaries are adapted; native strategy, classifier, confidence, color and math bodies execute.',
                               'Explicit checked finite calibration, bounded valid candidate histories; native unsafe index domains are rejected.',
                               'Calibration loading, complete outer AWB lifecycle/postprocessing and live integration remain unfinished.'])
    (ROOT / 'reverse-engineering/rkaiq/awb-low-single-color-equivalence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
