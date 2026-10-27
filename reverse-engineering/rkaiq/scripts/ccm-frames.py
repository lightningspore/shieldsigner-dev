#!/usr/bin/env python3
"""Verify full native CCM processing callback and publication ownership."""

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
from differential import ROOT, BINARY, HEAP
from exposure import RUNTIME

reference = importlib.import_module("ccm-tables")


initialized = importlib.import_module("ccm-initialized")


class OriginalFrames(initialized.OriginalConstructor):
    def run(self, value):
        super().run(dict(calibration=value["calibration"], frames=[]))
        context = HEAP + 0x80000
        wrapper, inp, out, result = [
            HEAP + x for x in (0xA0000, 0xA1000, 0xA2000, 0xA3000)
        ]
        self.uc.mem_write(wrapper, struct.pack("<I", context))
        self.uc.mem_write(inp, bytes(80))
        self.uc.mem_write(inp, struct.pack("<I", wrapper))
        self.uc.mem_write(out, bytes(16))
        self.uc.mem_write(out + 4, struct.pack("<I", result))
        self.uc.mem_write(result, bytes([0xA5]) * 156)
        descriptor = 0x10000 + 0x1A7FDC
        address = struct.unpack("<I", self.uc.mem_read(descriptor + 36, 4))[0]
        assert address & ~1 == 0x10D126
        self.symbols["ccm-frame"] = self.resolve_symbol("processing", 0x10D126)
        output = []
        for frame in value["frames"]:
            self.uc.mem_write(
                context + 0x55C, bytes([frame["active"], frame["attributes"]])
            )
            if frame["reconfigure"]:
                self.uc.mem_write(context + 0x55F, bytes([1]))
            self.uc.mem_write(inp + 17, bytes([frame["gray"]]))
            self.uc.mem_write(
                inp + 40,
                struct.pack(
                    "<5f3I",
                    *frame["current"],
                    frame["damping"],
                    255.0,
                    int(frame["softwareGray"]),
                    5,
                    0,
                ),
            )
            self.invoke("ccm-frame", [inp, out])
            snapshot = self.snapshot(context)
            snapshot.update(
                updated=bool(self.uc.mem_read(out, 1)[0]),
                output=bytes(self.uc.mem_read(result, 156)).hex(),
                softwareGray=bool(self.uc.mem_read(inp + 60, 1)[0]),
                informationConverged=bool(self.uc.mem_read(inp + 68, 1)[0]),
            )
            output.append(snapshot)
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
        for i, frame in enumerate(frames):
            frame["softwareGray"] = frames[i - 1]["gray"] if i else False
        cases.append(dict(calibration=c, frames=frames))
    arm = OriginalFrames(BINARY)
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "ccm-frames " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
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
            if x != y:
                for index in range(max(0, frame - 3), frame + 1):
                    print(
                        "mismatch context",
                        seq,
                        index,
                        cases[seq]["frames"][index],
                        {
                            k: (a[index][k], b[index][k])
                            for k in [
                                "alpha",
                                "converged",
                                "inputsChanged",
                                "published",
                                "updated",
                                "inputs",
                            ]
                        },
                    )
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
        scope="Full actual CCM descriptor processing callback after native AccmInit; all 156 output/result bytes, information mutations, publication flags and controller state.",
        limitations=[
            "SDK scene input and hardware-version global are controlled; native module table/lookup and full constructor execute. One allocator is modeled; native JSON parser is not executed.",
            "Symmetric, non-blended profile and default user inhibition/saturation only.",
            "Libc string/memory boundaries modeled; original uClibc floorf executes. No live ISP writes.",
        ],
    )
    flattened = [frame for sequence in expected for frame in sequence]
    report["constructorCalls"] = len(cases)
    report["updatedFrames"] = sum(v["updated"] for v in flattened)
    report["noUpdateFrames"] = sum(not v["updated"] for v in flattened)
    report["publicationClearedAfterEveryCallback"] = all(
        not v["published"] for v in flattened
    )
    report["nonconvergedFrames"] = sum(not v["converged"] for v in flattened)
    report["heldInputFrames"] = sum(not v["inputsChanged"] for v in flattened)
    report["resultBytesComparedPerFrame"] = 156
    report["stateKeysCompared"] = list(flattened[0])
    report["regression"] = {
        "sequence": 7,
        "frame": 8,
        "nativeSelectionStatus": -21,
        "beforeFix": "An unchanged clamped pair with publication already requested returned -21; Rust incorrectly continued automatic alpha/damping work.",
        "fix": "Preserve native selectCCM return status and stop that automatic pass; callback still publishes and clears its flag.",
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
