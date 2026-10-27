#!/usr/bin/env python3
"""Persistent full native LSC processing callback versus Rust frame owner."""

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
from differential import ROOT, BINARY, HEAP, f32, u32

reference = importlib.import_module("lsc-tables")


class OriginalFrames(reference.OriginalTables):
    def __init__(self):
        super().__init__()
        self.symbols["lsc-frame"] = self.resolve_symbol("processing", 0x1281C8)

    def run(self, value):
        cal = value["calibration"]
        self.bump = HEAP + 0x20000
        ctx, root = HEAP + 0x60000, HEAP + 0x19000
        self.uc.mem_write(ctx, bytes(0xD800))
        self.uc.mem_write(root, bytes(32))
        self.uc.mem_write(root + 12, bytes([cal["alscCoef"]["damp_enable"]]))
        self.uc.mem_write(ctx, struct.pack("<I", root))
        resolution_name = cal["common"]["resolutionAll"][0]["name"]
        for i, ill in enumerate(cal["alscCoef"]["illAll"]):
            handle, raw = HEAP + 0x2000 + i * 32, HEAP + 0x4000 + i * 256
            resolution, tables = HEAP + 0x18000 + i * 64, HEAP + 0x18400 + i * 32
            self.uc.mem_write(HEAP + 0x1000 + i * 4, struct.pack("<I", handle))
            self.uc.mem_write(handle, struct.pack("<4I", raw, resolution, 1, 0))
            self.uc.mem_write(raw, bytes(68))
            self.uc.mem_write(raw + 36, struct.pack("<2f", *ill["wbGain"]))
            n = len(ill["gains"])
            gains, vig = HEAP + 0x10000 + i * 256, HEAP + 0x11000 + i * 256
            self.uc.mem_write(raw + 52, struct.pack("<4I", gains, n, vig, n))
            self.uc.mem_write(gains, struct.pack("<" + "f" * n, *ill["gains"]))
            self.uc.mem_write(vig, struct.pack("<" + "f" * n, *ill["vig"]))
            self.uc.mem_write(resolution, bytes(48))
            self.uc.mem_write(resolution, resolution_name.encode() + b"\0")
            self.uc.mem_write(
                resolution + 40, struct.pack("<II", tables, len(ill["tableUsed"]))
            )
            for j, used in enumerate(ill["tableUsed"]):
                key = resolution_name + "_" + used["name"]
                p = next(p for p in cal["tbl"]["tableAll"] if p["name"] == key)
                address = HEAP + 0x30000 + (i * 5 + j) * 4096
                self.uc.mem_write(tables + j * 4, struct.pack("<I", address))
                self.uc.mem_write(address, bytes(100))
                self.uc.mem_write(address, p["name"].encode() + b"\0")
                self.uc.mem_write(address + 96, struct.pack("<f", p["vignetting"]))
                grids = sum(
                    [
                        p[k]["uCoeff"]
                        for k in (
                            "lsc_samples_red",
                            "lsc_samples_greenR",
                            "lsc_samples_greenB",
                            "lsc_samples_blue",
                        )
                    ],
                    [],
                )
                self.uc.mem_write(address + 100, struct.pack("<1156H", *grids))
            assert (
                self.invoke(
                    "OrderLscProfilesByVignetting", [tables, len(ill["tableUsed"])]
                )
                == 0
            )
        self.uc.mem_write(
            ctx + 0x2C,
            struct.pack("<II", HEAP + 0x1000, len(cal["alscCoef"]["illAll"])),
        )
        self.uc.mem_write(ctx + 0x54, resolution_name.encode() + b"\0")
        self.uc.mem_write(ctx + 0xC0, struct.pack("<II", ctx + 0xC0, ctx + 0xC0))
        self.uc.mem_write(ctx + 0xD78C, struct.pack("<2f", 0.2, 0.05))
        self.uc.mem_write(ctx + 0xD794, b"\x01")
        self.uc.mem_write(ctx + 0xD798, struct.pack("<3f", -1.0, -1.0, -1.0))
        self.uc.mem_write(ctx + 0xD7A4, b"\x01")
        self.uc.mem_write(ctx + 0x1CB4, struct.pack("<I", 2))
        resolution = cal["common"]["resolutionAll"][0]
        x, y = resolution["lsc_sect_size_x"], resolution["lsc_sect_size_y"]
        self.uc.mem_write(ctx + 0x1CB8, struct.pack("<32H", *x, *y))
        self.uc.mem_write(ctx + 0x1C68, struct.pack("<32H", *x, *y))
        assert self.invoke("AlscManualGrad", [ctx]) == 0
        wrapper, inp, out, result = [
            HEAP + x for x in (0xA0000, 0xA1000, 0xA2000, 0xA3000)
        ]
        self.uc.mem_write(wrapper, struct.pack("<I", ctx))
        self.uc.mem_write(inp, bytes(100))
        self.uc.mem_write(inp, struct.pack("<I", wrapper))
        self.uc.mem_write(out, struct.pack("<II", 0, result))
        self.uc.mem_write(result, bytes([0xA5]) * 2442)
        descriptor = 0x10000 + 0x1AA044
        assert u32(self.uc.mem_read(descriptor + 36, 4)) & ~1 == 0x1281C8
        frames = []
        for frame in value["frames"]:
            self.uc.mem_write(
                inp + 40, struct.pack("<4f", *frame["current"], frame["damping"])
            )
            if frame["force"]:
                self.uc.mem_write(ctx + 0xD794, b"\x01")
            if "seedFrameCount" in frame:
                self.uc.mem_write(
                    ctx + 0x1CAC, struct.pack("<I", frame["seedFrameCount"])
                )
            self.uc.mem_write(
                ctx + 0x1CB0, bytes([not cal["common"]["enable"] or frame["bypass"]])
            )
            assert self.invoke("lsc-frame", [inp, out], instructions=300000) == 0
            head = ctx + 0xC0
            history = []
            previous, node = head, u32(self.uc.mem_read(head, 4))
            while node != head:
                following, backward, index = struct.unpack(
                    "<III", self.uc.mem_read(node, 12)
                )
                assert backward == previous and len(history) < 15
                history.append(index)
                previous, node = node, following
            assert u32(self.uc.mem_read(head + 4, 4)) == previous
            frames.append(
                dict(
                    updated=bool(self.uc.mem_read(out, 1)[0]),
                    result=self.uc.mem_read(result, 2442).hex(),
                    target=self.uc.mem_read(ctx + 0x110, 2312).hex(),
                    converged=bool(self.uc.mem_read(ctx + 0xD7A5, 1)[0]),
                    inputChanged=bool(self.uc.mem_read(ctx + 0xD7A4, 1)[0]),
                    frameCount=u32(self.uc.mem_read(ctx + 0x1CAC, 4)),
                    vignetting=self.uc.mem_read(ctx + 0xBC, 4)[::-1].hex(),
                    illuminant=u32(self.uc.mem_read(ctx + 0xC8, 4)),
                    high=self.string(ctx + 0xD0).decode(),
                    low=self.string(ctx + 0xF0).decode(),
                    last=[
                        self.uc.mem_read(ctx + 0xD798 + i * 4, 4)[::-1].hex()
                        for i in range(3)
                    ],
                    history=history,
                )
            )
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
    calibration = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0][
        "scene_isp32"
    ]["lsc_v2"]
    rng = random.Random(0x4C534346)
    cases = []
    for seq in range(24):
        cal = copy.deepcopy(calibration)
        cal["alscCoef"]["damp_enable"] = seq % 4 != 0
        if seq == 22:
            cal["common"]["enable"] = 0
        frames = []
        current = [1.0, *rng.choice(cal["alscCoef"]["illAll"])["wbGain"]]
        for j in range(48):
            if j % 8 == 0:
                current = [
                    rng.choice([1.0, 1.1, 1.2, 2.0, 3.0, 8.0, 16.0]),
                    *rng.choice(cal["alscCoef"]["illAll"])["wbGain"],
                ]
            elif seq % 3 == 1:
                current = [
                    f32(current[0] + rng.choice([-0.02, 0.02, 0.001])),
                    f32(current[1] + rng.choice([-0.001, 0.001])),
                    current[2],
                ]
            force = j in (0, 25, 26) or seq % 5 == 0 and j % 7 == 0
            bypass = seq % 6 == 0 and 30 <= j < 34
            if seq % 6 == 0 and j in (30, 34):
                force = True
            frame = dict(
                current=current.copy(),
                damping=f32([0.0, 0.5, 0.9, 0.99, 1.0][seq % 5]),
                force=force,
                bypass=bypass,
            )
            if seq == 23 and j == 35:
                frame["seedFrameCount"] = 65534
            frames.append(frame)
        cases.append(dict(calibration=cal, frames=frames))
    arm = OriginalFrames()
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "lsc-frames " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    for i, (got, want) in enumerate(zip(actual, expected, strict=True)):
        got = json.loads(got)
        for j, (g, w) in enumerate(zip(got, want, strict=True)):
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
            "/shieldsigner-camera-tests/dev-0.0.34/lsc-" + uuid.uuid4().hex + ".txt"
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
        publishedFrames=sum(f["updated"] for s in expected for f in s),
        mismatches=0,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        iqSha256=hashlib.sha256(iq.read_bytes()).hexdigest(),
        scope="Complete descriptor-confirmed LSC processing callback, AlscConfig, JudgeAutoRun, AlscAutoConfig and native history/table/math loops. All 2442 published/retained result bytes, target grids, history, cached selection/vignetting/names, deadband state, convergence and frame count checked each frame.",
        boundaries=[
            "SDK graph constructed from selected one-resolution normal-case IQ; constructor/prepare/name lookup parser are not executed.",
            "No OTP, manual mode, attributes cloning, gray/HDR/multicamera; supplied force and bypass exercise automatic selected path.",
            "Allocation/string/logging boundaries and original sqrt runtime match lsc-tables oracle.",
            "CPU replay only; no ISP writes or image quality qualification.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
