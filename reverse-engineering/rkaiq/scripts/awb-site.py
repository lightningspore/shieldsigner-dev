#!/usr/bin/env python3
"""Execute original runAvaSiteRec against the Rust saved-site gain policy."""

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
        if address == (self.symbols.get("xcam_print_log", 0) & ~1):
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)


def native(arm, v):
    ctx = bytearray(0x4000)
    for offset, name in [
        (4, "application_flag"),
        (0x90, "reference_valid"),
        (0xA8, "matched"),
        (0xB0, "enabled"),
        (0x11C, "reuse_enabled"),
    ]:
        ctx[offset] = v[name]
    for offset, name in [
        (8, "application_mode"),
        (0xAC, "frames"),
        (0xB4, "frame_limit"),
        (0x33AC, "frame"),
    ]:
        struct.pack_into("<I", ctx, offset, v[name] & 0xFFFFFFFF)
    for offset, name in [
        (0xA4, "reference_sample"),
        (0x33DC, "sample"),
        (0x120, "gain_threshold"),
        (0x124, "sample_threshold"),
    ]:
        struct.pack_into("<f", ctx, offset, v[name])
    struct.pack_into("<4f", ctx, 0x94, *v["reference_gain"])
    struct.pack_into("<4f", ctx, 0x353C, *v["gain"])
    arm.uc.mem_write(HEAP, bytes(ctx))
    arm.invoke("_Z13runAvaSiteRecP12awb_contex_s", [HEAP])
    after = bytearray(arm.uc.mem_read(HEAP, len(ctx)))
    result = dict(
        gain=list(struct.unpack_from("<4I", after, 0x353C)),
        matched=bool(after[0xA8]),
        frames=struct.unpack_from("<I", after, 0xAC)[0],
    )
    for offset, length in [(0xA8, 1), (0xAC, 4), (0x353C, 16)]:
        after[offset : offset + length] = ctx[offset : offset + length]
    assert after == ctx
    return result


def main():
    manifest = json.loads(
        (ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text()
    )
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == manifest["binaries"][0]["sha256"]
    arm = Original()
    rng = random.Random(0x53495445)
    cases, expected = [], []
    coverage = {}
    for sequence in range(256):
        reference = [f32(rng.uniform(0.5, 4)), 1.0, 1.0, f32(rng.uniform(0.5, 4))]
        v = dict(
            enabled=bool(sequence % 9),
            frame_limit=[0, 1, 3, 8][sequence % 4],
            reuse_enabled=bool(sequence % 3),
            gain_threshold=[0.0, 0.2, 10.0, 11.0][sequence % 4],
            sample_threshold=[0.0, 0.1, 2.0][sequence % 3],
            reference_gain=reference,
            reference_sample=[0.0, 1e-6, 1.0, 100.0][sequence % 4],
            matched=bool(sequence % 2),
            frames=0,
            application_mode=[0, 1, 2, -1][sequence // 4 % 4],
            application_flag=bool(sequence // 16 % 2),
            reference_valid=bool(sequence // 32 % 2),
        )
        for frame in range(8):
            v["frame"] = frame
            v["sample"] = (
                v["reference_sample"] if frame % 3 else f32(rng.uniform(-1.0, 150.0))
            )
            v["gain"] = (
                reference[:]
                if frame % 2
                else [f32(rng.uniform(0.5, 4)), 1.0, 1.0, f32(rng.uniform(0.5, 4))]
            )
            if sequence % 7 == 0:
                v["gain"][1] = 0.0
            out = native(arm, v)
            cases.append(dict(v))
            expected.append(out)
            key = f"enabled{v['enabled']}:reuse{v['reuse_enabled']}:matched{out['matched']}:gainEqualsReference{out['gain'] == list(struct.unpack('<4I', struct.pack('<4f', *reference)))}"
            coverage[key] = coverage.get(key, 0) + 1
            v["frames"], v["matched"] = out["frames"], out["matched"]
    for directed in range(8):
        v = dict(
            enabled=True,
            frame_limit=3,
            reuse_enabled=True,
            gain_threshold=0.2,
            sample_threshold=2.0,
            reference_gain=[2.0, 1.0, 1.0, 3.0],
            reference_sample=1.0,
            sample=1.0,
            gain=[2.0, 1.0, 1.0, 3.0],
            matched=False,
            frames=0,
            application_mode=1,
            application_flag=False,
            reference_valid=True,
            frame=0,
        )
        if directed == 0:
            v["gain_threshold"] = 0.0
        if directed == 1:
            v["sample_threshold"] = 0.0
        if directed in (2, 3):
            v["reference_valid"] = False
            v["gain_threshold"] = 10.0 if directed == 2 else 11.0
        if directed == 4:
            v["reference_sample"] = v["sample"] = 0.0
        if directed == 5:
            v["gain"][1] = 0.0
        if directed == 6:
            v["reference_gain"][0] = 2.5
            v["gain_threshold"] = 0.5
        if directed == 7:
            v["reference_sample"] = 3.0
            v["sample_threshold"] = 1.0
        cases.append(v)
        expected.append(native(arm, v))
    assert not arm.calls and not arm.runtime_calls
    inputs = "".join(
        "awb-site " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )

    def compare(command):
        process = subprocess.run(
            command, input=inputs, text=True, capture_output=True, check=True
        )
        actual = [json.loads(line) for line in process.stdout.splitlines()]
        assert len(actual) == len(expected)
        for i, (a, b) in enumerate(zip(actual, expected)):
            assert a == b, (i, cases[i], a, b)

    compare([str(ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture")])
    replay = "--arm" in sys.argv
    if replay:
        directory = (
            ROOT / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release"
        )
        compare(
            [
                "docker",
                "run",
                "--rm",
                "-i",
                "--platform",
                "linux/arm/v7",
                "--network=none",
                "--mount",
                f"type=bind,src={directory},dst=/bincheck,readonly",
                "alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd",
                "/bincheck/numeric-fixture",
            ]
        )
    report = dict(
        binarySha256=sha,
        elfEntry="0xc7e70",
        sequences=256,
        directedCases=8,
        events=len(cases),
        mismatchCount=0,
        arm=replay,
        coverage=coverage,
        scope="Saved-site gain override, matched flag, frame counter and unrelated context preservation; original ARM body runs to return.",
        limitations=[
            "Finite synthetic reference/state; no saved-reference file loading or complete outer AWB wrapper integration.",
            "Context +4/+8 application meanings remain unnamed; their exact predicate is modeled.",
            "Sequence state is carried through original outputs, then replayed through Rust inputs.",
        ],
    )
    (ROOT / "reverse-engineering/rkaiq/awb-site-equivalence.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
