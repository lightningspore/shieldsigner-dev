#!/usr/bin/env python3
"""Native low-WP strategy, single-color explicitly disabled, complete return."""
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
        name = self.stubs.get(address)
        if name in ('malloc', 'free'):
            value = uc.reg_read(regs.UC_ARM_REG_R0)
            if name == 'malloc':
                assert value == 12
                pointer = self.arena
                self.arena += 16
                self.live.add(pointer)
                uc.mem_write(pointer, bytes(value))
                uc.reg_write(regs.UC_ARM_REG_R0, pointer)
            else:
                assert value in self.live
                self.live.remove(value)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)


def native(arm, v):
    n = len(v['lights'])
    context = bytearray([0x5a]) * 0x4000
    config = bytearray(0x800)
    calibration = bytearray(0x800)
    reference = bytearray([0x7c]) * (n * 0xe4)
    results = bytearray([0x8d]) * (n * 0xa0)
    statistics = bytearray([0x9e]) * 0x2cb0
    for offset, pointer in [(0x8c, 0x8000), (0x80, 0x9000), (0x33e4, 0x20000), (0x134, 0x50000)]:
        struct.pack_into('<I', context, offset, HEAP + pointer)
    struct.pack_into('<I', context, 0x33c8, v['retained'])
    struct.pack_into('<I', context, 0x33d8, v['brightness'])
    context[0x3419] = v['used_previous']
    for offset, number in [(0x353c, 2.), (0x342c, 3.), (0x3440, 4.), (0x3464, 5.), (0x33e8, 6.)]:
        struct.pack_into('<4f', context, offset, *([number] * 4))
    struct.pack_into('<f', context, 0x3474, .25)
    config[0x138] = n
    struct.pack_into('<I', config, 0x368, HEAP + 0x10000)
    struct.pack_into('<I', config, 0x1a8, v['low'])
    struct.pack_into('<II', config, 0x1b4, v['high'], v['threshold'])
    struct.pack_into('<4f', config, 0x1d8, *v['default'])
    calibration[0x644] = 0
    struct.pack_into('<iH', calibration, 0x658, v['color_value'], v['target'])
    for i, light in enumerate(v['lights']):
        struct.pack_into('<II', reference, i * 0xe4 + 0x78, light['high'], light['low'])
        struct.pack_into('<4f', reference, i * 0xe4 + 0x90, *light['high_gain'])
        struct.pack_into('<4f', reference, i * 0xe4 + 0xa0, *light['low_gain'])
        struct.pack_into('<4f', results, i * 0xa0 + 0x64, *([7.] * 4))
        struct.pack_into('<4f', results, i * 0xa0 + 0x84, *([8.] * 4))
        struct.pack_into('<f', results, i * 0xa0 + 0x74, light['probability'])
        struct.pack_into('<2f', results, i * 0xa0 + 0x98, .5, .75)
    gain_head, color_head = HEAP + 0x3498, HEAP + 0x35a0
    gain_nodes = [HEAP + 0x30000 + 24 * i for i in range(len(v['history']))]
    color_nodes = [HEAP + 0x31000 + 16 * i for i in range(len(v['colors']))]
    for offset, head, nodes in [(0x3498, gain_head, gain_nodes), (0x35a0, color_head, color_nodes)]:
        struct.pack_into('<II', context, offset, nodes[0] if nodes else head, nodes[-1] if nodes else head)
    for i, node in enumerate(gain_nodes):
        arm.uc.mem_write(node, struct.pack('<II4f', gain_nodes[i + 1] if i + 1 < len(gain_nodes) else gain_head,
                                        gain_nodes[i - 1] if i else gain_head, *v['history'][i]))
    for i, node in enumerate(color_nodes):
        arm.uc.mem_write(node, struct.pack('<III', color_nodes[i + 1] if i + 1 < len(color_nodes) else color_head,
                                        color_nodes[i - 1] if i else color_head, v['colors'][i]))
    extra = arm.setup_single(v, context, config, calibration) if 'single' in v else []
    blocks = [(0, context), (0x8000, config), (0x9000, calibration), (0x10000, reference),
              (0x20000, results), (0x50000, statistics)]
    blocks += extra
    for offset, data in blocks:
        arm.uc.mem_write(HEAP + offset, bytes(data))
    arm.arena, arm.live = HEAP + 0x40000, set()
    arm.invoke('_Z19AwbCalGainWpTypeLowP12awb_contex_s', [HEAP], instructions=3000000)
    after = bytearray(arm.uc.mem_read(HEAP, len(context)))
    output = {name: list(struct.unpack_from('<4I', after, offset)) for name, offset in
              [('current', 0x353c), ('low_result', 0x342c), ('temporal_result', 0x3440),
               ('spatial_result', 0x3464), ('temporal_source', 0x33e8)]}
    output.update(weight=struct.unpack_from('<I', after, 0x3474)[0], used_previous=bool(after[0x3419]), colors=[], lights=[])
    word = lambda address: struct.unpack('<I', arm.uc.mem_read(address, 4))[0]
    node, previous = word(color_head), color_head
    while node != color_head:
        assert len(output['colors']) < 32 and word(node + 4) == previous
        output['colors'].append(word(node + 8))
        previous, node = node, word(node)
    assert word(color_head + 4) == previous
    assert len(arm.live) == len(output['colors']) - len(v['colors']) + (2 * arm.single_calls if 'single' in v else 0)
    if 'single' in v:
        output['single'] = arm.read_single(after)
        for offset, size in [(0x3450, 20), (0x35bc, 0x88)]:
            after[offset:offset + size] = context[offset:offset + size]
    for offset, size in [(0x353c, 16), (0x342c, 16), (0x3440, 16), (0x3464, 20), (0x33e8, 16), (0x3419, 1), (0x35a0, 8)]:
        after[offset:offset + size] = context[offset:offset + size]
    assert after == context, 'Unexpected low-gain context write'
    after = bytearray(arm.uc.mem_read(HEAP + 0x20000, len(results)))
    for i in range(n):
        output['lights'].append(dict(statistic=list(struct.unpack_from('<4I', after, i * 0xa0 + 0x64)),
                                     spatial=list(struct.unpack_from('<4I', after, i * 0xa0 + 0x84)),
                                     spatial_weight=struct.unpack_from('<I', after, i * 0xa0 + 0x98)[0],
                                     extra_weight=struct.unpack_from('<I', after, i * 0xa0 + 0x9c)[0]))
        for offset in (0x64, 0x84):
            start = i * 0xa0 + offset
            after[start:start + 16] = results[start:start + 16]
    assert after == results
    for offset, data in blocks:
        if offset not in (0, 0x20000):
            assert bytes(arm.uc.mem_read(HEAP + offset, len(data))) == data
    for i, node in enumerate(gain_nodes):
        assert bytes(arm.uc.mem_read(node, 24)) == struct.pack('<II4f', gain_nodes[i + 1] if i + 1 < len(gain_nodes) else gain_head,
                                                            gain_nodes[i - 1] if i else gain_head, *v['history'][i])
    return output


def main():
    manifest = json.loads((ROOT / 'reverse-engineering/rkaiq/artifacts.json').read_text())
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == next(v['sha256'] for v in manifest['binaries'] if v['name'] == BINARY.name)
    arm = Original()
    rng = random.Random(0x4c4f5747)
    cases, expected, branches = [], [], {}
    for i in range(1024):
        gain = lambda: [f32(rng.uniform(.1, 9.)) for _ in range(4)]
        low, high = [(100, 200), (100, 100), (200, 100), (16777216, 16777217)][i % 4]
        brightness = [0, low, max(0, low - 1), min(0xffffffff, low + 1), high, min(0xffffffff, high + 1), 0xffffffff][i // 4 % 7]
        v = dict(brightness=brightness, low=low, high=high, threshold=[0, 100, 0x80000000, 0xffffffff][i // 7 % 4],
                 retained=[0, 99, 100, 0x80000000, 0xffffffff][i // 11 % 5], default=gain(),
                 used_previous=bool(i % 2), history=[gain() for _ in range(i % 5)] if i % 3 == 0 else [],
                 colors=[rng.randrange(2**32) for _ in range(i % 8)], color_value=rng.randrange(-2**31, 2**31),
                 target=[0, 2, 4, 8][i % 4], lights=[])
        for j in range(255 if i % 127 == 0 else 1 + i % 8):
            v['lights'].append(dict(low=low, high=high, low_gain=gain(), high_gain=gain(), probability=0. if i % 13 == 0 else f32(rng.uniform(0, 1))))
        branch = 'count' if v['retained'] >= v['threshold'] else 'history' if v['history'] else 'temporal' if brightness <= low else 'spatial' if brightness > high else 'blend'
        branches[branch] = branches.get(branch, 0) + 1
        cases.append(v)
        expected.append(native(arm, v))
    assert arm.calls == ['memcpy'] * len(cases) and not arm.runtime.calls
    inputs = ''.join('awb-low-gain ' + json.dumps(v, separators=(',', ':')) + '\n' for v in cases)

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
    report = dict(binarySha256=sha, cases=len(cases), mismatches=0, arm=replay, branches=branches, elfEntry='0xc6a90', modeledMemoryCalls={'memcpy': len(arm.calls)},
                  scope='Original low-WP strategy with single-color disabled, complete return: gain fields, per-light values, history updates and memory preservation',
                  limitations=['Single-color explicitly disabled in this suite; its enabled branch is covered separately by awb-low-single-color.py.',
                               'Memory copy, allocation and logging are explicit adapters; original strategy and numerical/list helpers execute.',
                               'Explicit finite inputs and bounded histories; native corrupting singleton target-1 case is excluded and rejected by Rust.',
                               'Calibration initialization, complete outer AWB and live integration remain unfinished.'])
    (ROOT / 'reverse-engineering/rkaiq/awb-low-gain-equivalence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
