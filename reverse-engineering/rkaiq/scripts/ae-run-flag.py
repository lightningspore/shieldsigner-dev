#!/usr/bin/env python3
"""Compare complete native AecGetRunFlag with the Rust reconstruction."""
import hashlib, itertools, json, random, struct, subprocess, sys
from differential import OriginalArm, ROOT, BINARY, HEAP


def main():
    digest = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert digest == 'ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9'
    native = OriginalArm(BINARY)
    assert struct.unpack('<d', native.uc.mem_read(0xc3398, 8))[0] == 0.03
    cases = []
    for old, new in [(0, 0), (0, 1), (1, 0), (100, 97), (100, 103), (100, 96), (100, 104), (10000, 9700), (10000, 10300), (65535, 65535), (65535, 0)]:
        for enabled, mode, unchanged, override in itertools.product([0, 1, 2], [0, 1, 2], [0, 1, 3], [0, 1, 4]):
            cases.append(dict(previous=[old], current=[new], enabled=enabled, mode=mode, unchanged=[unchanged, 0, 0], overrides=[override, 0, 0]))
    # Mixed unchanged/changed channels exercise the accumulating skip result
    # and precedence of each channel override, rather than only random deltas.
    for count in [2, 3]:
        for samples in itertools.product([0, 100, 103, 104], repeat=count):
            for unchanged in [[0, 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 3], [1, 2, 3]]:
                for overrides in [[0, 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 4]]:
                    cases.append(dict(previous=[100]*count, current=list(samples), enabled=1, mode=1, unchanged=unchanged, overrides=overrides))
    rng = random.Random(0x52554e)
    for _ in range(600):
        n = rng.randrange(4)
        cases.append(dict(previous=[rng.randrange(65536) for _ in range(n)], current=[rng.randrange(65536) for _ in range(n)], enabled=rng.randrange(3), mode=rng.randrange(1, 3), unchanged=[rng.randrange(3) for _ in range(3)], overrides=[rng.randrange(3) for _ in range(3)]))
    expected = []
    for v in cases:
        context = bytearray(0x5998)
        context[0x4fb9] = v['enabled']
        context[0x23cd] = v['mode']
        context[0x23cf:0x23d2] = bytes(v['unchanged'])
        context[0x22f4] = len(v['previous'])
        context[0x3d3c:0x3d3f] = bytes(v['overrides'])
        struct.pack_into('<'+'H'*len(v['previous']), context, 0x404, *v['previous'])
        native.uc.mem_write(HEAP, bytes(context))
        samples = struct.pack('<3H', *(v['current']+[0]*3)[:3])
        native.uc.mem_write(HEAP+0x50000, samples)
        result = native.invoke('_Z13AecGetRunFlagP12AecContext_sPt', [HEAP, HEAP+0x50000])
        assert bytes(native.uc.mem_read(HEAP, len(context))) == bytes(context)
        assert bytes(native.uc.mem_read(HEAP+0x50000, 6)) == samples
        expected.append(str(result))
    assert native.invoke('_Z13AecGetRunFlagP12AecContext_sPt', [0, HEAP+0x50000]) == 0
    inputs = ''.join('ae-run-flag '+json.dumps(v, separators=(',', ':'))+'\n' for v in cases)
    def compare(command):
        actual = subprocess.run(command, input=inputs, text=True, capture_output=True, check=True).stdout.splitlines()
        assert len(actual) == len(expected)
        for i, (a, b) in enumerate(zip(expected, actual)):
            assert a == b, (i, cases[i], a, b)
    compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
    if '--arm' in sys.argv:
        binary = ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture'
        compare(['docker', 'run', '--rm', '-i', '--platform', 'linux/arm/v7', '--network=none', '--mount', f'type=bind,src={binary.parent},dst=/bincheck,readonly', 'alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd', '/bincheck/numeric-fixture'])
    report = dict(binarySha256=digest, cases=len(cases), mismatches=0, armReplayPassed='--arm' in sys.argv, scope='complete native AecGetRunFlag through normal return; context and samples preserved', limitations=['Context flag lifecycle and previous-mean publication remain external.', 'Channel mode is bounded to zero through three channels; raw flag bytes are preserved.', 'Logging is inactive; native null-context return is separately checked, while Rust uses typed non-null inputs.'])
    (ROOT/'reverse-engineering/rkaiq/ae-run-flag-equivalence.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
