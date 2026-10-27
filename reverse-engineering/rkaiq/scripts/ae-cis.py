#!/usr/bin/env python3
"""Compare normal SNR metadata with both original AE sensor-feature routines."""

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


class OriginalCis(OriginalArm):
    def run(self, value):
        cpp, core, record, queue = [HEAP + x for x in (0, 0x5000, 0x2000, 0x10000)]
        self.uc.mem_write(cpp, bytes(0x500))
        self.uc.mem_write(core, bytes(0x2400))
        noise = value["noise"]
        if noise is not None:
            self.uc.mem_write(cpp + 0x39C, b"\x01")
            self.uc.mem_write(cpp + 0x3A0, struct.pack("<4I", *noise))
            self.uc.mem_write(core + 0x231C, b"\x01")
            self.uc.mem_write(core + 0x2320, struct.pack("<4I", *noise))
        before_cpp = bytes(self.uc.mem_read(cpp, 0x500))
        before_core = bytes(self.uc.mem_read(core, 0x2400))
        header = bytearray(bytes.fromhex(value["header"]))
        struct.pack_into("<I", header, 20, len(value["records"]))
        self.uc.mem_write(
            queue, bytes(header) + b"".join(bytes.fromhex(r) for r in value["records"])
        )
        assert self.invoke("AecCISFeature", [core, queue]) == 0
        assert bytes(self.uc.mem_read(queue, 24)) == bytes(header)
        expected = []
        for i, r in enumerate(value["records"]):
            self.uc.mem_write(record, bytes.fromhex(r))
            self.invoke("AeCISFeature", [cpp, record])
            single = self.uc.mem_read(record, 244).hex()
            batch = self.uc.mem_read(queue + 24 + i * 244, 244).hex()
            assert single == batch, "Native core/C++ disagreement"
            expected.append(single)
        assert bytes(self.uc.mem_read(cpp, 0x500)) == before_cpp
        assert bytes(self.uc.mem_read(core, 0x2400)) == before_core
        return expected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    rng = random.Random(0x41454349)
    cases = []
    for case in range(1000):
        if case % 3 == 0:
            noise = None
        else:
            divisor = rng.choice([1, 16, 100, 65535, 0xFFFFFFFF])
            upper = rng.randrange(0x100000000)
            lower = rng.randrange(0x100000000)
            if case < 100:
                upper, lower, divisor = 16, 8, 1
            noise = [rng.choice([0, 1, 2, 0xFFFFFFFF]), upper, lower, divisor]
        records = []
        for j in range(case % 7):
            r = bytearray(rng.randbytes(244))
            choices = [f32(rng.uniform(-10, 50))]
            if noise:
                high = f32(f32(noise[1]) / f32(noise[3]))
                low = f32(f32(noise[2]) / f32(noise[3]))
                choices += [
                    high,
                    low,
                    f32((high + low) / 2),
                    f32(high + 1),
                    f32(low - 1),
                ]
            struct.pack_into("<f", r, 4, rng.choice(choices))
            if noise is None and j % 3 == 0:
                struct.pack_into("<I", r, 4, 0x7FC00000)
            struct.pack_into(
                "<i", r, 20, rng.choice([-2147483648, -2, -1, 0, 1, 2, 2147483647])
            )
            r[240] = rng.choice([0, 1, 255])
            records.append(r.hex())
        cases.append(dict(noise=noise, records=records, header=rng.randbytes(24).hex()))
    arm = OriginalCis(BINARY)
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "ae-cis " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    for i, (got, want) in enumerate(zip(actual, expected, strict=True)):
        assert json.loads(got) == want, f"Host/native mismatch {i}"
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
            "/shieldsigner-camera-tests/dev-0.0.34/ae-cis-" + uuid.uuid4().hex + ".txt"
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
        batches=len(cases),
        records=sum(len(v["records"]) for v in cases),
        recordBytesCompared=244,
        mismatches=0,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        scope="Complete native AecCISFeature normal batch path and AeCISFeature normal per-record path independently compared to Rust. All 244 record bytes, batch header and both native contexts checked; no algorithm, math or logging stubs.",
        boundaries=[
            "Optional NR switch direction/unsigned rational thresholds with nonzero divisor and finite gain; disabled switch ignores gain and derives flag from signed DCG>0.",
            "Zero to six records per batch; exact thresholds, reversed/overlapping thresholds, retained flag bytes, signed DCG extremes and unused NaN gain included. Rust rejects zero-divisor switch before output.",
            "HDR policy and AE queue publication integration remain separate. This stage establishes the SNR metadata helper for live BAYNR handoff.",
            "Physical CPU replay makes no ISP writes and loads no vendor library.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
