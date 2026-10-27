#!/usr/bin/env python3
"""Native persistent AWB gain update/freeze gate and convergence call chain."""
import hashlib
import json
import random
import struct
import subprocess
import sys

from awb_reference import OriginalAwb
from differential import BINARY, HEAP, ROOT, f32, regs

UPDATE = '_Z16UpdateWbGainListP9list_headPfi'
CONVERGED = '_Z17IsWbGainConvergedP9list_headfPf'
GATE = '_Z14IsUpdateWbGainP9list_headPfif'


class Original(OriginalAwb):
    def hook(self, uc, address, size, user):
        if address == (self.symbols.get('xcam_print_log', 0) & ~1):
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        if self.stubs.get(address) == 'malloc':
            assert uc.reg_read(regs.UC_ARM_REG_R0) == 24
            pointer = self.arena
            self.arena += 32
            self.allocated += 1
            uc.mem_write(pointer, bytes([0xa7]) * 24)
            uc.reg_write(regs.UC_ARM_REG_R0, pointer)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def values(self):
        word = lambda address: struct.unpack('<I', self.uc.mem_read(address, 4))[0]
        node, previous, output = word(HEAP), HEAP, []
        while node != HEAP:
            assert len(output) < 32 and word(node + 4) == previous
            output.append(list(struct.unpack('<4I', self.uc.mem_read(node + 8, 16))))
            previous, node = node, word(node)
        assert word(HEAP + 4) == previous
        return output

    def run(self, v):
        addresses = [HEAP + 0x1000 + i * 32 for i in range(len(v['history']))]
        self.uc.mem_write(HEAP, struct.pack('<II', addresses[0] if addresses else HEAP, addresses[-1] if addresses else HEAP))
        for i, gain in enumerate(v['history']):
            self.uc.mem_write(addresses[i], struct.pack('<II4f', addresses[i + 1] if i + 1 < len(addresses) else HEAP,
                                                      addresses[i - 1] if i else HEAP, *gain))
        self.arena, self.allocated = HEAP + 0x8000, 0
        output = []
        for step in v['steps']:
            current = struct.pack('<4f', *step['gain'])
            self.uc.mem_write(HEAP + 0x400, bytes([0x5a]) * 32)
            self.uc.mem_write(HEAP + 0x408, current)
            before = bytes(self.uc.mem_read(HEAP, 0x10000))
            updated = self.invoke(GATE, [HEAP, HEAP + 0x408, step['target']], floats=[step['tolerance']])
            assert updated in (0, 1)
            assert bytes(self.uc.mem_read(HEAP, 0x10000)) == before
            if updated:
                self.invoke(UPDATE, [HEAP, HEAP + 0x408, step['target']])
                gain = list(struct.unpack('<4I', current))
            else:
                gain = self.values()[-1]
            before = bytes(self.uc.mem_read(HEAP, 0x10000))
            convergence = self.invoke(CONVERGED, [HEAP, 0], floats=[f32(step['convergence'] * 2)])
            assert convergence in (0, 1)
            assert bytes(self.uc.mem_read(HEAP, 0x10000)) == before
            assert bytes(self.uc.mem_read(HEAP + 0x400, 32)) == bytes([0x5a]) * 8 + current + bytes([0x5a]) * 8
            values = self.values()
            assert self.allocated == len(values) - len(v['history'])
            output.append(dict(gain=gain, updated=bool(updated), converged=bool(convergence), history=values))
        return output


def main():
    manifest = json.loads((ROOT / 'reverse-engineering/rkaiq/artifacts.json').read_text())
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == next(v['sha256'] for v in manifest['binaries'] if v['name'] == BINARY.name)
    arm = Original()
    rng = random.Random(0x474e4853)
    cases, expected = [], []
    for i in range(64):
        value = dict(history=[[1.] * 4 for _ in range(i % 7)], steps=[])
        for j in range(16):
            gain = [1.] * 4 if i % 3 == 0 else [f32(rng.uniform(-.1, 5.)) for _ in range(4)]
            if i % 5 == 0:
                gain = [f32(1. + .01 * j)] * 4
            value['steps'].append(dict(gain=gain, target=[0, 1, 2, 4, 8][(i + j) % 5],
                                       tolerance=[0., .001, .05, .25, 1.][j % 5], convergence=[0., .001, .1, .5][j % 4]))
        if i == 0:
            value['history'] = [[1.] * 4] * 2
            value['steps'][0] = dict(gain=[2.] * 4, target=2, tolerance=.25, convergence=.1)
        cases.append(value)
        expected.append(arm.run(value))
    assert not arm.calls and not arm.runtime.calls
    inputs = ''.join('awb-gain-history ' + json.dumps(v, separators=(',', ':')) + '\n' for v in cases)

    def compare(command):
        result = subprocess.run(command, input=inputs, text=True, capture_output=True)
        assert result.returncode == 0, (len(result.stdout.splitlines()), result.stderr)
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
    events = [event for sequence in expected for event in sequence]
    report = dict(binarySha256=sha, sequences=len(cases), events=len(events), mismatches=0, arm=replay,
                  updated=sum(v['updated'] for v in events), frozen=sum(not v['updated'] for v in events), converged=sum(v['converged'] for v in events),
                  elfEntries=dict(update='0xc9c2e', converged='0xc9cb0', gate='0xc9e24'),
                  scope='Persistent original IsUpdateWbGain -> conditional UpdateWbGainList -> IsWbGainConverged, exact gain/list bits and immutable gate/convergence memory',
                  limitations=['Bounded successful allocation and logging adapters; original list/gate/convergence bodies execute.',
                               'Finite gains/thresholds and bounded nonnegative targets. Native negative-target unsafe domains are rejected.',
                               'Clipping, adjustment, full caller composition and live frame integration remain unfinished.'])
    (ROOT / 'reverse-engineering/rkaiq/awb-gain-history-equivalence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
