#!/usr/bin/env python3
"""Execute native persistent non-blended selectCCM sequences."""

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


class OriginalRuntime(OriginalArm):
    def hook(self, uc, address, size, user):
        name = self.stubs.get(address)
        if name in ("strcmp", "strcpy"):
            from differential import regs

            a, b = [uc.reg_read(r) for r in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1)]

            def string(p):
                result = bytearray()
                for i in range(100):
                    v = uc.mem_read(p + i, 1)[0]
                    if v == 0:
                        return bytes(result)
                    result.append(v)
                raise AssertionError("Unterminated oracle string")

            if name == "strcpy":
                uc.mem_write(a, string(b) + bytes(1))
            else:
                x, y = string(a), string(b)
                uc.reg_write(
                    regs.UC_ARM_REG_R0,
                    (0 if x == y else (-1 if x < y else 1)) & 0xFFFFFFFF,
                )
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, value):
        context, source, updated = [HEAP + x for x in (0, 0x10000, 0x20000)]
        self.uc.mem_write(context, bytes(0x1000))
        self.uc.mem_write(context + 0x264, bytes([0xA5]) * 50)
        for i, cal in enumerate(value["calibration"]):
            record = source + i * 56
            self.uc.mem_write(record, bytes(56))
            self.uc.mem_write(record + 4, struct.pack("<2f", *cal["gains"]))
            self.uc.mem_write(record + 20, struct.pack("<I", len(cal["profiles"])))
            self.uc.mem_write(
                record + 24,
                struct.pack("<8f", *cal["sensorGains"], *cal["saturations"]),
            )
            for j, p in enumerate(cal["profiles"]):
                address = HEAP + 0x30000 + i * 0x1000 + j * 0x100
                name = address + 128
                self.uc.mem_write(name, p["name"].encode() + bytes(1))
                self.uc.mem_write(
                    address,
                    struct.pack(
                        "<II13f", name, 0, p["saturation"], *p["matrix"], *p["offsets"]
                    ),
                )
                self.uc.mem_write(
                    context + 0x180 + i * 20 + j * 4, struct.pack("<I", address)
                )
        output = []
        for frame in value["frames"]:
            self.uc.mem_write(
                context + 0x234,
                struct.pack("<3f", frame["sensorGain"], *frame["gains"]),
            )
            self.uc.mem_write(
                context + 0x55F, bytes([frame["force"], frame["pending"]])
            )
            self.uc.mem_write(updated, bytes([frame["updated"]]))
            status = self.invoke(
                "selectCCM",
                [source, len(value["calibration"]), context, updated],
                [0.0],
            )
            output.append(
                dict(
                    status=status if status < 0x80000000 else status - 0x100000000,
                    illuminant=struct.unpack(
                        "<I", self.uc.mem_read(context + 0x260, 4)
                    )[0],
                    saturation=struct.unpack(
                        "<I", self.uc.mem_read(context + 0x254, 4)
                    )[0],
                    high=bytes(self.uc.mem_read(context + 0x264, 25)).hex(),
                    low=bytes(self.uc.mem_read(context + 0x27D, 25)).hex(),
                    result=bytes(self.uc.mem_read(context + 0x298, 48)).hex(),
                    updated=bool(self.uc.mem_read(updated, 1)[0]),
                )
            )
        return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    rng = random.Random(0x43434D52)
    cases = []
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    tuning = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "ccm_calib_v2"
    ]["TuningPara"]
    matrices = {p["name"]: p for p in tuning["matrixAll"]}
    actual = []
    for i, ill in enumerate(tuning["aCcmCof"]):
        profiles = []
        for j, name in enumerate(ill["matrixUsed"]):
            p = matrices[name]
            profiles.append(
                dict(
                    name=f"i{i}p{j}",
                    saturation=f32(p["saturation"]),
                    matrix=[f32(v) for v in p["ccMatrix"]],
                    offsets=[f32(v) for v in p["ccOffsets"]],
                )
            )
        profiles.sort(key=lambda p: -p["saturation"])
        actual.append(
            dict(
                gains=ill["awbGain"],
                sensorGains=ill["gain_sat_curve"]["gains"],
                saturations=ill["gain_sat_curve"]["sat"],
                profiles=profiles,
            )
        )
    for sequence in range(100):
        calibration = (
            actual
            if sequence < 10
            else [
                dict(
                    gains=[1.0 + i, 2.0 + i * 0.3],
                    sensorGains=[1.0, 2.0, 4.0, 8.0],
                    saturations=[100.0, 75.0, 50.0, 25.0],
                    profiles=[
                        dict(
                            name=f"i{i}p{j}",
                            saturation=s,
                            matrix=[f32(rng.uniform(-4, 4)) for _ in range(9)],
                            offsets=[f32(rng.uniform(-100, 100)) for _ in range(3)],
                        )
                        for j, s in enumerate([100.0, 60.0, 20.0])
                    ],
                )
                for i in range(9 if sequence >= 90 else 3)
            ]
        )
        frames = []
        for i in range(24):
            if i % 4 == 1:
                frame = dict(frames[-1])
                frame.update(force=False, pending=False, updated=bool(i % 2))
            else:
                cal = rng.choice(calibration)
                frame = dict(
                    sensorGain=f32(rng.choice([1.0, 2.0, 4.0, 8.0, rng.uniform(1, 8)])),
                    gains=cal["gains"],
                    force=i % 7 == 0,
                    pending=i % 5 == 0,
                    updated=i % 3 == 0,
                )
            frames.append(frame)
        for sensor_gain, gains, force, pending, updated in [
            (3.0, calibration[0]["gains"], True, False, False),
            (f32(3.000000238418579), calibration[0]["gains"], False, False, False),
            (f32(3.000000238418579), calibration[0]["gains"], False, True, True),
            (3.0, calibration[1]["gains"], False, False, False),
        ]:
            frames.append(
                dict(
                    sensorGain=sensor_gain,
                    gains=gains,
                    force=force,
                    pending=pending,
                    updated=updated,
                )
            )
        cases.append(dict(calibration=calibration, frames=frames))
    profile_cases = 10
    arm = OriginalRuntime(BINARY)
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "ccm-runtime " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
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
            "/shieldsigner-camera-tests/dev-0.0.34/ccm-runtime-"
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
        maxIlluminants=max(len(v["calibration"]) for v in cases),
        frames=sum(len(v["frames"]) for v in cases),
        selectedProfileCases=profile_cases,
        iqSha256=hashlib.sha256(iq.read_bytes()).hexdigest(),
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        seed="0x43434d52",
        scope="Complete native selectCCM call tree across persistent 28-frame sequences; all cached matrix/offset bits, saturation bits, names, illuminant, update flag and native return status. Only libc string/memory boundaries are modeled.",
        limitations=[
            "Finite calibrated/current gain pairs; nonfinite Rust inputs rejected.",
            "Constructor/JSON loading, outer flags, damping and live CCM remain separate.",
            "Physical CPU replay does not write ISP registers.",
        ],
    )
    report["nativeStatusCounts"] = {
        str(code): sum(
            frame["status"] == code for sequence in expected for frame in sequence
        )
        for code in [0, -1, -21]
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
