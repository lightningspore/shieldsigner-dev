#!/usr/bin/env python3
"""Compare complete supported native AccmConfig/AccmAutoConfig sequences."""

import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import uuid
from differential import ROOT, BINARY, HEAP, OriginalArm, regs
from exposure import RUNTIME

reference = importlib.import_module("ccm-tables")


class OriginalAutomatic(reference.OriginalTables):
    def __init__(self, path):
        super().__init__(path)
        self.math = OriginalArm(RUNTIME, tls=True)

    def hook(self, uc, address, size, user):
        if self.stubs.get(address) == "floorf":
            value = struct.unpack(
                "<f", struct.pack("<I", uc.reg_read(regs.UC_ARM_REG_S0))
            )[0]
            self.math.invoke("floorf", floats=[value])
            uc.reg_write(regs.UC_ARM_REG_S0, self.math.uc.reg_read(regs.UC_ARM_REG_S0))
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, value):
        c = value["calibration"]
        super().run(c)
        source = HEAP + 0x60000
        context = HEAP
        self.uc.mem_write(source, bytes(2164))
        self.uc.mem_write(context, bytes(0x564))

        def put(offset, values):
            self.uc.mem_write(
                source + offset, struct.pack("<" + "f" * len(values), *values)
            )

        luma = c["lumaCCM"]
        e = c["enhCCM"]
        t = c["TuningPara"]
        self.uc.mem_write(source, bytes([c["control"]["enable"]]))
        put(4, [c["control"]["wbgain_tolerance"], c["control"]["gain_tolerance"]])
        put(12, luma["rgb2y_para"])
        self.uc.mem_write(source + 0x1C, bytes([luma["y_alp_sym"]["highy_adj_en"]]))
        put(0x20, [luma["y_alp_sym"]["bound_pos_bit"]])
        for i, row in enumerate(luma["y_alp_sym"]["gain_yalp_curve"]):
            put(0x24 + i * 72, [row["iso"], *row["y_alpha_curve"]])
        put(0x7B0, luma["gain_alphaScale_curve"]["gain"])
        put(0x7D4, luma["gain_alphaScale_curve"]["scale"])
        self.uc.mem_write(source + 0x7F8, bytes([e["enh_adj_en"]]))
        put(0x7FC, e["enh_rat"]["gains"])
        put(0x820, e["enh_rat"]["enh_rat_max"])
        self.uc.mem_write(source + 0x844, bytes(e["enh_rgb2y_para"]))
        self.uc.mem_write(source + 0x848, bytes([t["damp_enable"]]))
        self.uc.mem_write(
            source + 0x864,
            struct.pack(
                "<4I",
                HEAP + 0x10000,
                len(t["aCcmCof"]),
                HEAP + 0x30000,
                len(t["matrixAll"]),
            ),
        )
        self.uc.mem_write(context, struct.pack("<I", source))
        self.uc.mem_write(context + 0xAC, struct.pack("<I", 2))
        self.uc.mem_write(
            context + 0x258, struct.pack("<II", context + 0x258, context + 0x258)
        )
        self.uc.mem_write(context + 0x234, struct.pack("<3f", 1, 1, 1))
        self.uc.mem_write(context + 0x2D4, struct.pack("<3f", 1, 1, 1))
        self.uc.mem_write(
            context + 0x140,
            struct.pack("<16f", *[1.0] * 4, *[0.0] * 4, *[1.0] * 4, *[50.0] * 4),
        )
        self.uc.mem_write(context + 0x55C, bytes([1]))
        self.uc.mem_write(context + 0x560, bytes([1]))
        assert self.invoke("ConfigbyCalib", [context]) == 0
        self.uc.mem_write(context + 0x2C8, struct.pack("<3f", 1, 0, 100))
        output = []

        def integer(offset):
            return struct.unpack("<I", self.uc.mem_read(context + offset, 4))[0]

        for frame in value["frames"]:
            self.uc.mem_write(context + 0x234, struct.pack("<3f", *frame["current"]))
            self.uc.mem_write(context + 0x240, struct.pack("<f", frame["damping"]))
            self.uc.mem_write(context + 0x248, bytes([frame["gray"]]))
            self.uc.mem_write(
                context + 0x55C,
                bytes(
                    [
                        frame["active"],
                        frame["attributes"],
                        0,
                        frame["reconfigure"],
                        frame["publish"],
                    ]
                ),
            )
            assert self.invoke("AccmConfig", [context]) == 0
            selection = (
                bytes(self.uc.mem_read(context + 0x254, 4))
                + bytes(self.uc.mem_read(context + 0x260, 4))
                + bytes(self.uc.mem_read(context + 0x264, 50))
                + bytes(self.uc.mem_read(context + 0x298, 48))
            )
            inputs = bytes(self.uc.mem_read(context + 0x2D4, 12)) + bytes(
                self.uc.mem_read(context + 0x234, 12)
            )
            output.append(
                dict(
                    result=bytes(self.uc.mem_read(context + 4, 156)).hex(),
                    selection=selection.hex(),
                    inputs=inputs.hex(),
                    alpha=integer(0x2C8),
                    saturation=integer(0x2D0),
                    converged=bool(self.uc.mem_read(context + 0x250, 1)[0]),
                    frames=integer(0x558),
                    inputsChanged=bool(self.uc.mem_read(context + 0x55E, 1)[0]),
                    published=bool(self.uc.mem_read(context + 0x560, 1)[0]),
                )
            )
        return output


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--adb")
    args = p.parse_args()
    manifest = json.loads(
        (ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text()
    )
    assert (
        hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
        == manifest["uclibcRuntime"]["memberSha256"]
    )
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    original = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0][
        "scene_isp32"
    ]["ccm_calib_v2"]
    rng = random.Random(0x43434D41)
    cases = []
    for sequence in range(32):
        c = copy.deepcopy(original)
        if sequence >= 24:
            c["control"]["enable"] = 0
        if sequence % 4 == 1:
            c["TuningPara"]["damp_enable"] = 0
        if sequence % 4 == 2:
            c["enhCCM"]["enh_adj_en"] = 1
        if 0 < sequence < 24:
            c["lumaCCM"]["gain_alphaScale_curve"]["scale"] = [
                rng.uniform(0.1, 1.0) for _ in range(9)
            ]
            c["enhCCM"]["enh_rat"]["enh_rat_max"] = [
                rng.uniform(0, 2) for _ in range(9)
            ]
            if sequence % 3 == 0:
                c["control"]["wbgain_tolerance"] = 0.1
        frames = []
        for i in range(24):
            current = [
                rng.choice([1.0, 2.0, 4.0, 8.0]),
                *rng.choice(c["TuningPara"]["aCcmCof"])["awbGain"],
            ]
            if i % 4 == 1:
                current = frames[-1]["current"]
            frames.append(
                dict(
                    current=current,
                    damping=rng.choice([0.0, 0.5, 0.9, 1.0]),
                    active=not (sequence % 5 == 0 and i < 2),
                    attributes=i % 9 == 0,
                    reconfigure=i % 11 == 0,
                    gray=sequence % 7 == 0 and i in [6, 7],
                    publish=i % 13 == 0,
                )
            )
        cases.append(dict(calibration=c, frames=frames))
    arm = OriginalAutomatic(BINARY)
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "ccm-automatic " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = [
        json.loads(line)
        for line in subprocess.check_output(
            [str(binary)], input=lines, text=True
        ).splitlines()
    ]
    for seq, (a, b) in enumerate(zip(actual, expected)):
        for frame, (x, y) in enumerate(zip(a, b)):
            assert x == y, (seq, frame, {k: (x[k], y[k]) for k in x if x[k] != y[k]})
    assert len(actual) == len(expected)
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
        board = "/shieldsigner-camera-tests/dev-0.0.34/bin/numeric-fixture"
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/ccm-auto-"
            + uuid.uuid4().hex
            + ".txt"
        )
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
            path = Path(temporary) / "input"
            path.write_text(lines)
            subprocess.run(
                adb + ["push", str(path), remote], check=True, capture_output=True
            )
            try:
                assert [
                    json.loads(line)
                    for line in subprocess.check_output(
                        adb + ["shell", board + " < " + remote], text=True
                    ).splitlines()
                ] == actual
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = dict(
        passed=True,
        sequences=len(cases),
        frames=sum(len(v["frames"]) for v in cases),
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        uclibcRuntimeSha256=hashlib.sha256(RUNTIME.read_bytes()).hexdigest(),
        iqSha256=hashlib.sha256(iq.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        scope="Whole native ConfigbyCalib, AccmConfig and AccmAutoConfig call trees; full results and numerical/cache/control state.",
        limitations=[
            "Native full constructor/JSON parser not executed; SDK calibration and documented constructor defaults are explicit input boundaries.",
            "Symmetric, non-blended profile and default user inhibition/saturation only.",
            "Libc string/memory boundaries modeled; original uClibc floorf executes. No live ISP writes.",
        ],
    )
    flattened = [frame for sequence in expected for frame in sequence]
    report["publishedFrames"] = sum(v["published"] for v in flattened)
    report["nonconvergedFrames"] = sum(not v["converged"] for v in flattened)
    report["heldInputFrames"] = sum(not v["inputsChanged"] for v in flattened)
    report["resultBytesComparedPerFrame"] = 156
    report["stateKeysCompared"] = list(flattened[0])
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
