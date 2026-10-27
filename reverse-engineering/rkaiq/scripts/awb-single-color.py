#!/usr/bin/env python3
"""Execute native gain-to-CCT and complete single-color confidence manager."""
import hashlib
import json
import random
import struct
import subprocess
import sys

from awb_reference import OriginalAwb
from differential import BINARY, HEAP, ROOT, f32, regs

CCT = '_Z22AwbCalCCTandCCRIByGainPf6line_sS0_P21color_tempture_info_s'
MANAGER = '_Z21AwbSingleColorManagerP19CalibDbV2_Awb_Sgc_sP12sgc_result_sff6line_sS3_PfS4_'


class Original(OriginalAwb):
    def hook(self, uc, address, size, user):
        if address == (self.symbols.get('xcam_print_log', 0) & ~1):
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)


def native(arm, v):
    first, second = v['first'], v['second']
    gain = struct.pack('<4f', *v['gain'])
    arm.uc.mem_write(HEAP, gain)
    bits = lambda x: struct.unpack('<I', struct.pack('<f', x))[0]
    if v['kind'] == 'temperature':
        before = bytes([0x5a]) * 12
        arm.uc.mem_write(HEAP + 0x100, before)
        stack = struct.pack('<I3fII', first[3], *second[:3], second[3], HEAP + 0x100)
        arm.invoke(CCT, [HEAP, *map(bits, first[:3])], stack=stack)
        after = bytearray(arm.uc.mem_read(HEAP + 0x100, 12))
        assert after[1:4] == before[1:4]
        assert arm.uc.reg_read(regs.UC_ARM_REG_R0) == (0 if after[0] else 0xffffffff)
        assert bytes(arm.uc.mem_read(HEAP, 16)) == gain
        return dict(valid=bool(after[0]), cct=struct.unpack_from('<I', after, 4)[0], ccri=struct.unpack_from('<I', after, 8)[0])
    c = v['calibration']
    config = bytearray([0x6b]) * 0x140
    stats = bytearray([0x7c]) * 0x90
    for key, offset in [('brightness_knots', 0xbc), ('brightness_weights', 0xdc),
                        ('density_knots', 0xfc), ('density_weights', 0x114),
                        ('distance_knots', 0x50), ('cct_knots', 0x68),
                        ('disagreement_knots', 0x20), ('disagreement_weights', 0x38)]:
        struct.pack_into('<' + 'f' * len(c[key]), config, offset, *c[key])
    for i, values in enumerate(c['distance_weights']):
        struct.pack_into('<6f', config, 0x74 + 24 * i, *values)
    struct.pack_into('<i', stats, 0x80, v['disagreements'])
    struct.pack_into('<f', stats, 0x88, v['distance'])
    arm.uc.mem_write(HEAP + 0x1000, bytes(config))
    arm.uc.mem_write(HEAP + 0x2000, bytes(stats))
    arm.uc.mem_write(HEAP + 0x3000, bytes([0x8d]) * 12)
    stack = struct.pack('<fI3fIII', first[2], first[3], *second[:3], second[3], HEAP, HEAP + 0x3004)
    arm.invoke(MANAGER, [HEAP + 0x1000, HEAP + 0x2000, bits(first[0]), bits(first[1])],
               floats=[v['brightness'], v['density']], stack=stack)
    result = bytes(arm.uc.mem_read(HEAP + 0x3000, 12))
    assert result[:4] == result[8:] == bytes([0x8d]) * 4
    for pointer, data in [(HEAP, gain), (HEAP + 0x1000, config), (HEAP + 0x2000, stats)]:
        assert bytes(arm.uc.mem_read(pointer, len(data))) == data
    return dict(weight=struct.unpack_from('<I', result, 4)[0])


def main():
    manifest = json.loads((ROOT / 'reverse-engineering/rkaiq/artifacts.json').read_text())
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == next(v['sha256'] for v in manifest['binaries'] if v['name'] == BINARY.name)
    arm = Original()
    rng = random.Random(0x5347434d)
    cases, expected = [], []
    for kind in ['temperature', 'confidence']:
        for i in range(1024):
            v = dict(kind=kind, gain=[f32(rng.uniform(.1, 9.)) for _ in range(4)],
                     first=[f32(rng.uniform(-2, 2)) for _ in range(3)] + [i % 7 != 0],
                     second=[f32(rng.uniform(-2, 2)) for _ in range(3)] + [i % 11 != 0])
            if i % 13 == 0:
                v['gain'][1 + i % 2] = [0., -1., f32(.00001), f32(.000010001)][i // 13 % 4]
            if i % 17 == 0:
                v['second'][1] = [0., f32(.00001), f32(.000010001), -f32(.000010001)][i // 17 % 4]
            if kind == 'confidence':
                weights = lambda n: [f32(rng.uniform(-.25, 1.25)) for _ in range(n)]
                c = dict(brightness_knots=[float(j * 10) for j in range(8)], brightness_weights=weights(8),
                         density_knots=[float(j * 5) for j in range(6)], density_weights=weights(6),
                         distance_knots=[float(j * 10) for j in range(6)], cct_knots=[-100., 0., 100.],
                         distance_weights=[weights(6) for _ in range(3)],
                         disagreement_knots=[float(j * 100) for j in range(6)], disagreement_weights=weights(6))
                if i % 3 == 0:
                    for key in ['brightness_knots', 'density_knots', 'distance_knots', 'disagreement_knots']:
                        c[key][-1] = c[key][-2]
                if i % 7 == 0:
                    c['distance_knots'] = [0.] * 6
                if i % 11 == 0:
                    c['cct_knots'] = [0.] * 3
                v.update(calibration=c, brightness=f32(rng.uniform(-10, 90)), density=f32(rng.uniform(-5, 30)),
                         distance=f32(rng.uniform(-10, 60)), disagreements=rng.choice([-2**31, -1, 0, 100, 500, 2**31 - 1, rng.randrange(1000)]))
                if i % 5 == 0:
                    v['brightness'] = c['brightness_knots'][i % 8]
                    v['density'] = c['density_knots'][i % 6]
                    v['distance'] = c['distance_knots'][i % 6]
            cases.append(v)
            expected.append(native(arm, v))
    assert not arm.calls and not arm.runtime.calls
    inputs = ''.join('awb-single-color ' + json.dumps(v, separators=(',', ':')) + '\n' for v in cases)

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
    report = dict(binarySha256=sha, cases=len(cases), casesPerFunction=1024, mismatches=0, arm=replay,
                  elfEntries=dict(colorTemperature='0xca840', confidenceManager='0xcbaf0'),
                  scope='Complete original gain-to-CCT/CCRI and single-color confidence manager with all interpolation and CCT helper bodies; exact result bits and input/output padding preservation',
                  limitations=['Finite values and nondecreasing finite calibration knots, including repeated endpoints; native nonfinite/invalid-pointer domains are outside the checked API.',
                               'Logging is an explicit adapter; numerical helper bodies execute without replacement.',
                               'Grid classification and enabled low-count orchestration are covered separately; complete outer integration remains unfinished.'])
    (ROOT / 'reverse-engineering/rkaiq/awb-single-color-equivalence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
