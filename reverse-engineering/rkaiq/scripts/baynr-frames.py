#!/usr/bin/env python3
"""Full native BAYNR constructor, prepare and normal processing sequences."""

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
from differential import ROOT, BINARY, HEAP, regs, u32, f32

fix = importlib.import_module("baynr-quantize")
calibration = importlib.import_module("baynr-calibration")


class OriginalFrames(fix.OriginalFix, calibration.OriginalCalibration):
    def __init__(self):
        super().__init__()
        self.stubs[self.symbols["xcam_print_log"] & ~1] = "xcam_print_log"
        descriptor = 0x10000 + 0x1A72CC
        assert u32(self.uc.mem_read(descriptor + 36, 4)) & ~1 == 0xF3F78
        assert u32(self.uc.mem_read(descriptor + 28, 4)) & ~1 == 0xF42CC
        self.symbols["baynr-frame"] = self.resolve_symbol("processing", 0xF3F78)
        self.symbols["baynr-prepare"] = self.resolve_symbol("prepare", 0xF42CC)

    def hook(self, uc, address, size, user):
        name = self.stubs.get(address)
        if name in ("malloc", "strcmp", "strcpy", "xcam_print_log"):
            a, b = [uc.reg_read(r) for r in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1)]
            if name == "malloc":
                assert a == 0x1038
                result = HEAP + 0x60000
            elif name == "strcmp":
                left, right = self.string(a), self.string(b)
                result = (left > right) - (left < right)
            elif name == "strcpy":
                uc.mem_write(a, self.string(b) + b"\0")
                result = a
            else:
                result = 0
            uc.reg_write(regs.UC_ARM_REG_R0, result & 0xFFFFFFFF)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, value):
        root = self.sdk_graph(value["calibration"])
        before = bytes(self.uc.mem_read(HEAP, 0x30000))

        def u(a):
            return u32(self.uc.mem_read(a, 4))

        got = (u(0xF4720) + 0xF465A + u(0xF472C)) & 0xFFFFFFFF
        self.uc.mem_write(u(got), struct.pack("<I", 32))
        lookup = (u(0xF4730) + 0xF46B8) & 0xFFFFFFFF
        assert u(lookup) == 32
        modules = u(lookup + 4)
        offset = None
        for i in range(100):
            p, off = struct.unpack("<II", self.uc.mem_read(modules + i * 8, 8))
            if not p:
                break
            if self.string(p) == b"bayer2dnr_v23":
                offset = off
                break
        assert offset is not None
        self.module_offset = offset
        config, pp = HEAP + 0x76000, HEAP + 0x76100
        self.uc.mem_write(config, bytes(64))
        self.uc.mem_write(config + 24, struct.pack("<I", root - offset))
        self.uc.mem_write(pp, bytes(4))
        assert self.invoke("Abayer2dnr_Init_V23", [pp, config]) == 0
        context = u(pp)
        assert context == HEAP + 0x60000
        assert self.uc.mem_read(context + 0xFF8, 16) == bytes(8) + struct.pack(
            "<f", 1.0
        ) + b"\x01" + bytes(3)
        inp, out, ae, blc, result = [
            HEAP + x for x in (0x73000, 0x74000, 0x71000, 0x72000, 0x75000)
        ]
        self.uc.mem_write(inp, bytes(100))
        self.uc.mem_write(inp, struct.pack("<I", context))
        assert self.invoke("baynr-prepare", [inp]) == 0
        assert u(context + 0x58) == 3 and u(context + 0x5C) == 1
        self.uc.mem_write(out, struct.pack("<II", 0, result))
        self.uc.mem_write(result, bytes.fromhex(value.get("result", "a5" * 152)))
        self.uc.mem_write(ae, bytes(244))
        self.uc.mem_write(blc, bytes(32))
        self.uc.mem_write(inp + 24, struct.pack("<I", ae))
        self.uc.mem_write(inp + 48, struct.pack("<I", blc))
        frames = []
        for frame in value["frames"]:
            self.uc.mem_write(inp + 17, bytes([frame["gray"]]))
            self.uc.mem_write(inp + 52, struct.pack("<I", frame["bay3d"]))
            self.uc.mem_write(ae, struct.pack("<4f", frame["seconds"], *frame["gains"]))
            self.uc.mem_write(ae + 240, bytes([frame["snr"]]))
            self.uc.mem_write(blc + 24, struct.pack("<f", frame["blc"]))
            if frame["force"]:
                self.uc.mem_write(
                    context + 0x1034, struct.pack("<I", u(context + 0x1034) | 1)
                )
            assert self.invoke("baynr-frame", [inp, out], instructions=300000) == 0
            frames.append(
                dict(
                    updated=bool(self.uc.mem_read(out, 1)[0]),
                    result=self.uc.mem_read(result, 152).hex(),
                    table=self.uc.mem_read(context + 0x60, 3336).hex(),
                    selected=self.uc.mem_read(context + 0xD68, 252).hex(),
                    exposure=self.uc.mem_read(context, 88).hex(),
                    strength=self.uc.mem_read(context + 0xFF8, 16).hex(),
                    gray=bool(self.uc.mem_read(context + 0x1009, 1)[0]),
                    parameterMode=u(context + 0x100C),
                    recalculate=bool(u(context + 0x1034)),
                )
            )
        assert bytes(self.uc.mem_read(HEAP, 0x30000)) == before
        return frames


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    original = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0][
        "scene_isp32"
    ]["bayer2dnr_v23"]
    rng = random.Random(0x42415950)
    cases = []
    for seq in range(24):
        cal = copy.deepcopy(original)
        if seq % 3 == 1:
            cal["TuningPara"]["enable"] = False
        if seq % 4 == 1:
            cal["TuningPara"]["hdrdgain_ctrl_en"] = True
        frames = []
        gains = [1.0, 1.0, 1.0]
        for j in range(48):
            if j % 8 == 0:
                gains = [
                    rng.choice([1.0, 1.2, 1.22, 2.0, 4.0, 8.0]),
                    rng.choice([1.0, 2.0]),
                    rng.choice([1.0, 1.5, 2.0]),
                ]
            elif seq % 3 == 1:
                gains = [f32(gains[0] + 0.01), gains[1], gains[2]]
            f = dict(
                seconds=f32(rng.choice([0.001, 0.01, 0.1])),
                gains=gains.copy(),
                snr=j // 5 % 2,
                gray=seq % 5 == 0 and 18 <= j < 22,
                bay3d=seq % 6 == 0 and 24 <= j < 28,
                blc=[0.0, 0.5, 1.0, 2.0][seq % 4] if j < 32 else 1.0,
                force=j == 35,
            )
            if seq == 0 and j < 8:
                f.update(
                    gains=[
                        [1.0, 1.0, 1.0],
                        [1.0, 1.0, 1.0],
                        [1.2, 1.0, 1.0],
                        [1.22, 1.0, 1.0],
                        [1.22, 1.0, 1.0],
                        [1.22, 1.0, 1.0],
                        [1.22, 1.0, 1.0],
                        [1.22, 1.0, 1.0],
                    ][j],
                    snr=[0, 1, 1, 1, 0, 0, 0, 0][j],
                    blc=1.0,
                    force=j == 5,
                    gray=j == 6,
                    bay3d=False,
                    seconds=0.01,
                )
            frames.append(f)
        cases.append(dict(calibration=cal, frames=frames))
    arm = OriginalFrames()
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "baynr-frames " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    for i, (got, want) in enumerate(zip(actual, expected, strict=True)):
        for j, (g, w) in enumerate(zip(json.loads(got), want, strict=True)):
            assert g == w, (
                f"Host/native mismatch sequence {i} frame {j}: {[k for k in w if g[k] != w[k]]}"
            )
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
        sequences=len(cases),
        frames=sum(len(v["frames"]) for v in cases),
        updatedFrames=sum(f["updated"] for s in expected for f in s),
        sdkModuleOffset=hex(arm.module_offset),
        mismatches=0,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        expRuntimeSha256=hashlib.sha256(fix.RUNTIME.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        iqSha256=hashlib.sha256(iq.read_bytes()).hexdigest(),
        scope="Complete native Abayer2dnr_Init_V23, descriptor prepare and processing callbacks, native calibration lookup/merge, process, ISO selection and fixed quantization with original expf. Compare all prepared table/selected/exposure/strength/result bytes plus gray/parameter-mode/recalculate state each frame; calibration graph unchanged.",
        boundaries=[
            "Constructed raw SDK calibration, present normal AE exposure and BLC result records; native general JSON parser and C++ scheduling framework not executed.",
            "Allocation, libc strings, diagnostics are controlled boundaries; no algorithm/math stubs. Default auto/unit-strength mode, forced updates, strict ISO delta, held SNR, gray/BAY3D/BLC changes covered.",
            "No HDR callback input assembly, absent-exposure fallback, manual/UAPI strength policy or live BAYNR qualification.",
            "Physical CPU replay makes no ISP writes and loads no vendor library.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
