#!/usr/bin/env python3
"""Complete native Bayer spatial NR ISO selection and record preservation."""

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
        struct.pack_into("<3i", exposure, 68, *value["iso"])
        self.uc.mem_write(table, raw)
        self.uc.mem_write(out, before)
        self.uc.mem_write(exp, bytes(exposure))
        assert self.invoke("bayer2dnr_select_params_by_ISO_V23", [table, out, exp]) == 0
        after = bytearray(self.uc.mem_read(exp, 88))
        bracket = list(struct.unpack_from("<2i", after, 80))
        after[80:88] = exposure[80:88]
        assert bytes(after) == bytes(exposure), "Unexpected exposure mutation"
        assert bytes(self.uc.mem_read(table, len(raw))) == raw, "Calibration mutated"
        return dict(output=self.uc.mem_read(out, 252).hex(), bracket=bracket)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    rng = random.Random(0x42415953)
    cases = []
    for case in range(1000):
        raw = bytearray(rng.randbytes(3336))
        struct.pack_into("<i", raw, 0, [0, 1, -1, 7][case % 4])
        raw[4] = [0, 1, 2, 255][case % 4]
        gains = [1 << i for i in range(13)] if case < 100 else [1]
        if len(gains) == 1:
            for _ in range(12):
                gains.append(gains[-1] + rng.randrange(1, 300))
        iso = [f32(g * 50 + (0 if case < 100 else rng.randrange(50))) for g in gains]
        struct.pack_into("<13f", raw, 8, *iso)
        for i in range(13):
            p = 60 + i * 252
            for field in (136, 140, 144, 148, 172, 244, 248):
                struct.pack_into("<f", raw, p + field, f32(rng.uniform(0, 16)))
            for j in range(16):
                sigma = rng.randrange(-65536, 65536)
                if case % 10 == 0:
                    sigma = rng.choice([-2147483648, -1, 0, 1, 2147483647])
                struct.pack_into("<i", raw, p + 68 + j * 4, sigma)
        samples = [
            rng.randrange(-100, 50),
            gains[-1] * 50,
            rng.choice(gains[:-1]) * 50,
            rng.choice(gains[:-1]) * 50 + 49,
            rng.randrange(50, gains[-1] * 50 + 1),
        ]
        sample = samples[case % len(samples)]
        if case == 1:
            sample = ((gains[10] + gains[11]) // 2) * 50
        elif case == 2:
            sample = gains[6] * 50
        elif case == 3:
            sample = gains[6] * 50 + 49
        elif case == 4:
            sample = gains[-1] * 50
        mode = case % 3
        input_iso = [rng.randrange(0, 200000) for _ in range(3)]
        input_iso[mode] = sample
        cases.append(
            dict(
                table=raw.hex(),
                output=rng.randbytes(252).hex(),
                exposure=rng.randbytes(88).hex(),
                iso=input_iso,
                mode=mode,
            )
        )
    arm = OriginalSelection(BINARY)
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "baynr-select " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
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
            "/shieldsigner-camera-tests/dev-0.0.34/baynr-" + uuid.uuid4().hex + ".txt"
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
        selectedRecordBytesComparedPerCase=252,
        mismatches=0,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        scope="Complete native bayer2dnr_select_params_by_ISO_V23, all selected bytes including retained padding and both chosen ISO indices. Full calibration and all unrelated exposure bytes verified unchanged. No algorithm/math/log stubs executed.",
        boundaries=[
            "Thirteen positive strictly increasing truncated gain knots; sample min-one integer gain lies within covered range. Native unsupported out-of-range zero-bracket/nonfinite behavior is rejected transactionally by Rust.",
            "Power-of-two and nonstandard ISO knots; ISO<50, exact knots, +49 quantization and interior samples; nearest-row ties, signed sigma extremes and noncanonical flag bytes included.",
            "Synthetic SDK records; actual JSON calibration preparation and fixed-register quantization remain separate. Selecting exposure slots 0/1/2 does not qualify HDR camera operation.",
            "Physical CPU replay makes no ISP writes; live BAYNR remains disabled.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
