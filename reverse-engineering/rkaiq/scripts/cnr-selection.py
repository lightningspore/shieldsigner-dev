#!/usr/bin/env python3
"""Complete native chroma NR ISO selection and record preservation."""

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import uuid
from differential import ROOT, BINARY, HEAP, OriginalArm, f32


class OriginalSelection(OriginalArm):
    def run(self, value):
        table, out, exp = [HEAP + x for x in (0, 0x10000, 0x11000)]
        raw = bytes.fromhex(value["table"])
        before = bytes.fromhex(value["output"])
        exposure = bytearray(bytes.fromhex(value["exposure"]))
        struct.pack_into("<i", exposure, 0, value["mode"])
        struct.pack_into("<3i", exposure, 60, *value["iso"])
        self.uc.mem_write(table, raw)
        self.uc.mem_write(out, before)
        self.uc.mem_write(exp, bytes(exposure))
        assert self.invoke("cnr_select_params_by_ISO_V30", [table, out, exp]) == 0
        after = bytearray(self.uc.mem_read(exp, 88))
        bracket = list(struct.unpack_from("<2i", after, 72))
        after[72:80] = exposure[72:80]
        assert bytes(after) == bytes(exposure), "Unexpected exposure mutation"
        assert bytes(self.uc.mem_read(table, len(raw))) == raw, "Calibration mutated"
        return dict(output=self.uc.mem_read(out, 180).hex(), bracket=bracket)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    rng = random.Random(0x434E5253)
    cases = []
    for case in range(1000):
        raw = bytearray(rng.randbytes(2396))
        struct.pack_into("<i", raw, 0, [0, 1, -1, 7][case % 4])
        knots = [50 * (1 << i) for i in range(13)] if case < 100 else [50]
        if len(knots) == 1:
            for _ in range(12):
                knots.append(knots[-1] + rng.randrange(1, 1000))
        # Fractional ISO knots test float comparisons followed by integer bounds.
        iso = [
            f32(k + (0 if case < 100 else rng.choice([0.0, 0.25, 0.75]))) for k in knots
        ]
        struct.pack_into("<13f", raw, 4, *iso)
        for i in range(13):
            p = 56 + i * 180
            for field in [*range(4, 52, 4), *range(56, 140, 4)]:
                struct.pack_into("<f", raw, p + field, f32(rng.uniform(-16, 16)))
        samples = [
            rng.randrange(-100, 50),
            knots[-1],
            rng.choice(knots[:-1]),
            rng.choice(knots[:-1]) + 1,
            rng.randrange(50, knots[-1] + 1),
            knots[-1] + 1000,
            (knots[4] + knots[5]) // 2,
        ]
        sample = samples[case % len(samples)]
        if case == 1:
            sample = (knots[10] + knots[11]) // 2
        elif case == 2:
            sample = knots[6]
        elif case == 3:
            sample = knots[6] + 1
        elif case == 4:
            sample = knots[-1]
        mode = case % 3
        input_iso = [rng.randrange(0, 200000) for _ in range(3)]
        input_iso[mode] = sample
        cases.append(
            dict(
                table=raw.hex(),
                output=rng.randbytes(180).hex(),
                exposure=rng.randbytes(88).hex(),
                iso=input_iso,
                mode=mode,
            )
        )
    arm = OriginalSelection(BINARY)
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "cnr-select " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    for i, (got, want) in enumerate(zip(actual, expected, strict=True)):
        assert json.loads(got) == want, f"Host/native mismatch case {i}"
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
        board = "/shieldsigner-camera-tests/dev-0.0.34/bin/numeric-fixture"
        board_sha = subprocess.check_output(
            adb + ["shell", "sha256sum " + board], text=True
        ).split()[0]
        assert (
            board_sha
            == hashlib.sha256(
                (
                    ROOT
                    / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture"
                ).read_bytes()
            ).hexdigest()
        )
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/cnr-" + uuid.uuid4().hex + ".txt"
        )
        with tempfile.TemporaryDirectory() as temporary:
            p = Path(temporary) / "input"
            p.write_text(lines)
            subprocess.run(
                adb + ["push", str(p), remote], check=True, capture_output=True
            )
            try:
                output = subprocess.check_output(
                    adb + ["shell", board + " < " + remote], text=True
                ).splitlines()
                assert output == actual, "Physical ARM mismatch"
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = dict(
        passed=True,
        cases=len(cases),
        selectedRecordBytesComparedPerCase=180,
        mismatches=0,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        scope="Complete native cnr_select_params_by_ISO_V30, all selected bytes including retained padding and both chosen ISO indices. Full calibration and all unrelated exposure bytes verified unchanged. No algorithm/math/log stubs executed.",
        boundaries=[
            "Thirteen positive strictly increasing float ISO knots with distinct truncated integer bounds. Malformed knots/nonfinite arithmetic and overflowing signed distances are rejected transactionally.",
            "Power-of-two, nonstandard and fractional ISO knots; below/above-range extrapolation, exact knots, interior samples, nearest-row ties, raw discrete fields and poisoned padding included.",
            "Synthetic SDK records; actual JSON calibration preparation and fixed-register quantization remain separate. Selecting exposure slots 0/1/2 does not qualify HDR camera operation.",
            "Physical CPU replay makes no ISP writes; live CNR remains disabled.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
