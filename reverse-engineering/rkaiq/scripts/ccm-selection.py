#!/usr/bin/env python3
"""Execute native saturation selection and matrix/offset interpolation."""

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import uuid
from differential import ROOT, BINARY, HEAP, OriginalArm


def f32(v):
    return struct.unpack("<f", struct.pack("<f", v))[0]


class OriginalSelection(OriginalArm):
    def run(self, value):
        pointers, high, low, result = [HEAP + x for x in (0, 0x1000, 0x1004, 0x2000)]
        profiles = value["profiles"]
        addresses = []
        for i, p in enumerate(profiles):
            address = HEAP + 0x4000 + i * 0x100
            addresses.append(address)
            self.uc.mem_write(
                address,
                bytes(8)
                + struct.pack("<13f", p["saturation"], *p["matrix"], *p["offsets"]),
            )
        self.uc.mem_write(pointers, struct.pack("<" + "I" * len(addresses), *addresses))
        status = self.invoke(
            "SatSelectCcmProfiles",
            [len(profiles), pointers, high, low],
            [value["saturation"]],
        )
        a, b = struct.unpack("<II", self.uc.mem_read(high, 8))
        assert status in (0, 0xFFFFFFEB)
        if status == 0:
            assert (
                self.invoke(
                    "SatInterpolateMatrices", [a, b, result], [value["saturation"]]
                )
                == 0
            )
            assert (
                self.invoke(
                    "SatInterpolateOffset", [a, b, result + 36], [value["saturation"]]
                )
                == 0
            )
            output = bytes(self.uc.mem_read(result, 48))
        else:
            assert a == b
            output = bytes(self.uc.mem_read(a + 12, 48))
        return dict(
            high=addresses.index(a),
            low=addresses.index(b),
            clamped=status != 0,
            result=output.hex(),
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    rng = random.Random(0x43434D53)
    cases = []
    for i in range(1000):
        count = rng.randrange(1, 6)
        sats = [f32(rng.uniform(50, 100))]
        for _ in range(count - 1):
            sats.append(f32(sats[-1] - rng.uniform(0.01, 10)))
        profiles = [
            dict(
                saturation=s,
                matrix=[f32(rng.uniform(-4, 4)) for _ in range(9)],
                offsets=[f32(rng.uniform(-100, 100)) for _ in range(3)],
            )
            for s in sats
        ]
        saturation = f32(
            rng.choice(
                [
                    sats[0] + 1,
                    sats[-1] - 1,
                    rng.choice(sats),
                    rng.uniform(sats[-1], sats[0]),
                ]
            )
        )
        cases.append(dict(profiles=profiles, saturation=saturation))
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    tuning = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "ccm_calib_v2"
    ]["TuningPara"]
    matrices = {m["name"]: m for m in tuning["matrixAll"]}
    profile_cases = 0
    for illuminant in tuning["aCcmCof"]:
        profiles = [
            dict(
                saturation=f32(matrices[name]["saturation"]),
                matrix=[f32(v) for v in matrices[name]["ccMatrix"]],
                offsets=[f32(v) for v in matrices[name]["ccOffsets"]],
            )
            for name in illuminant["matrixUsed"]
        ]
        profiles.sort(key=lambda p: -p["saturation"])
        hi, lo = profiles[0]["saturation"], profiles[-1]["saturation"]
        for saturation in [hi + 1, hi, (hi + lo) / 2, lo, lo - 1]:
            cases.append(dict(profiles=profiles, saturation=f32(saturation)))
            profile_cases += 1
    arm = OriginalSelection(BINARY)
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "ccm-selection " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = [
        json.loads(line)
        for line in subprocess.check_output(
            [str(binary)], input=lines, text=True
        ).splitlines()
    ]
    for i, (a, b) in enumerate(zip(actual, expected)):
        assert a == b, (i, a, b, cases[i])
    assert len(actual) == len(expected)
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/ccm-selection-"
            + uuid.uuid4().hex
            + ".txt"
        )
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
        with tempfile.TemporaryDirectory() as temporary:
            p = Path(temporary) / "input"
            p.write_text(lines)
            subprocess.run(
                adb + ["push", str(p), remote], check=True, capture_output=True
            )
            try:
                output = [
                    json.loads(line)
                    for line in subprocess.check_output(
                        adb + ["shell", board + " < " + remote], text=True
                    ).splitlines()
                ]
                assert output == actual
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = dict(
        passed=True,
        cases=len(cases),
        selectedProfileCases=profile_cases,
        iqSha256=hashlib.sha256(iq.read_bytes()).hexdigest(),
        clampedCases=sum(x["clamped"] for x in expected),
        interpolatedCases=sum(not x["clamped"] for x in expected),
        matrixAndOffsetBytesCompared=48,
        exactFloatBits=True,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        seed="0x43434d53",
        scope="Complete native SatSelectCcmProfiles, SatInterpolateMatrices and SatInterpolateOffset execution; profile indices, native clamp status and all output float bits.",
        limitations=[
            "Finite profiles with strictly descending saturation; malformed native inputs excluded.",
            "Illuminant estimation, gain-to-saturation calibration, temporal state and live CCM remain separate.",
            "Physical CPU replay does not write ISP registers.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
