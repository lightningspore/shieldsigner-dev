#!/usr/bin/env python3
"""Compare CCM static calibration fields with native ConfigHwbyCalib."""

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


class OriginalCalibration(OriginalArm):
    def run(self, value):
        source, result = HEAP, HEAP + 0x10000
        c = value["calibration"]
        luma = c["lumaCCM"]
        self.uc.mem_write(source, bytes(2164))
        self.uc.mem_write(source + 0xC, struct.pack("<3f", *luma["rgb2y_para"]))
        self.uc.mem_write(source + 0x18, bytes([luma["asym_enable"]]))
        self.uc.mem_write(source + 0x1C, bytes([luma["y_alp_sym"]["highy_adj_en"]]))
        self.uc.mem_write(
            source + 0x20, struct.pack("<f", luma["y_alp_sym"]["bound_pos_bit"])
        )
        self.uc.mem_write(
            source + 0x3CC,
            struct.pack(
                "<2f",
                luma["y_alp_asym"]["bound_pos_bit"],
                luma["y_alp_asym"]["right_pos_bit"],
            ),
        )
        self.uc.mem_write(source + 0x844, bytes(c["enhCCM"]["enh_rgb2y_para"]))
        self.uc.mem_write(result, bytes.fromhex(value["result"]))
        assert self.invoke("ConfigHwbyCalib", [source, result]) == 0
        return bytes(self.uc.mem_read(result, 156)).hex()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=200)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert 4 <= args.cases <= 4096
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    rng = random.Random(0x43434D43)
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    original = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0][
        "scene_isp32"
    ]["ccm_calib_v2"]
    cases = []
    for index in range(args.cases):
        if index == 0:
            luma = original["lumaCCM"]
            c = dict(
                lumaCCM=dict(
                    rgb2y_para=luma["rgb2y_para"],
                    asym_enable=luma["asym_enable"],
                    y_alp_sym=dict(
                        highy_adj_en=luma["y_alp_sym"]["highy_adj_en"],
                        bound_pos_bit=luma["y_alp_sym"]["bound_pos_bit"],
                    ),
                    y_alp_asym=dict(
                        bound_pos_bit=luma["y_alp_asym"]["bound_pos_bit"],
                        right_pos_bit=luma["y_alp_asym"]["right_pos_bit"],
                    ),
                ),
                enhCCM=dict(enh_rgb2y_para=original["enhCCM"]["enh_rgb2y_para"]),
            )
        else:
            c = dict(
                lumaCCM=dict(
                    rgb2y_para=[rng.uniform(0, 128) for _ in range(3)],
                    asym_enable=index % 2,
                    y_alp_sym=dict(
                        highy_adj_en=index // 2 % 2, bound_pos_bit=rng.uniform(4, 10)
                    ),
                    y_alp_asym=dict(
                        bound_pos_bit=rng.uniform(3, 11),
                        right_pos_bit=rng.uniform(3, 11),
                    ),
                ),
                enhCCM=dict(enh_rgb2y_para=[rng.randrange(256) for _ in range(3)]),
            )
        cases.append(dict(calibration=c, result=rng.randbytes(156).hex()))
    arm = OriginalCalibration(BINARY)
    expected = [arm.run(value) for value in cases]
    lines = "".join(
        "ccm-calibration " + json.dumps(value, separators=(",", ":")) + "\n"
        for value in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    assert actual == expected, "Host/native CCM mismatch"
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/ccm-" + uuid.uuid4().hex + ".txt"
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
                output = subprocess.check_output(
                    adb + ["shell", board + " < " + remote], text=True
                ).splitlines()
                assert output == actual, "Physical ARM/native CCM mismatch"
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = {
        "passed": True,
        "cases": len(cases),
        "bytesComparedPerCase": 156,
        "mismatches": 0,
        "seed": "0x43434d43",
        "originalBinarySha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "hostBinarySha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "physicalArmBinarySha256": board_sha,
        "hostMatchesPhysicalArm": board_sha is not None,
        "scope": "Complete native ConfigHwbyCalib; all 156 result bytes compared from random prior contents. Independent SDK ARM layout assertions cover source and result offsets.",
        "limitations": [
            "Native JSON parser/constructor are not executed; only consumed static IQ fields are independently SDK-packed.",
            "Physical ARM replay does not enable CCM on the camera or qualify image quality.",
        ],
    }
    report["iqSha256"] = hashlib.sha256(iq.read_bytes()).hexdigest()
    report["selectedProfileCases"] = 1
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
