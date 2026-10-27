#!/usr/bin/env python3
"""Native BAYNR SNR setting lookup and calibration/tuning merge."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import uuid
from differential import ROOT, BINARY, HEAP, OriginalArm, regs, f32


class OriginalCalibration(OriginalArm):
    def string(self, address):
        for n in range(65):
            if self.uc.mem_read(address + n, 1)[0] == 0:
                return bytes(self.uc.mem_read(address, n))
        raise AssertionError("Unterminated fixture string")

    def hook(self, uc, address, size, user):
        name = self.stubs.get(address)
        if name in ("strlen", "strncmp"):
            a, b, n = [
                uc.reg_read(r)
                for r in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1, regs.UC_ARM_REG_R2)
            ]
            if name == "strlen":
                result = len(self.string(a))
            else:
                left, right = self.string(a)[:n], self.string(b)[:n]
                result = (left > right) - (left < right)
            uc.reg_write(regs.UC_ARM_REG_R0, result & 0xFFFFFFFF)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def sdk_graph(self, cal):
        self.uc.mem_write(HEAP, bytes(0x31000))
        root, calsets, tunesets, table, noise, parammode, ci, ti = [
            HEAP + x
            for x in (0, 0x1000, 0x2000, 0x40000, 0x30000, 0x30080, 0x30100, 0x30104)
        ]
        self.uc.mem_write(
            root,
            struct.pack(
                "<5IBB2xII",
                0,
                calsets,
                len(cal["CalibPara"]["Setting"]),
                0,
                0,
                cal["TuningPara"]["enable"],
                cal["TuningPara"]["hdrdgain_ctrl_en"],
                tunesets,
                len(cal["TuningPara"]["Setting"]),
            ),
        )
        for side, sets, base, stride, key in [
            ("CalibPara", calsets, HEAP + 0x3000, 132, "Calib_ISO"),
            ("TuningPara", tunesets, HEAP + 0x10000, 120, "Tuning_ISO"),
        ]:
            for i, s in enumerate(cal[side]["Setting"]):
                data = base + i * 0x2000
                name = HEAP + 0x20000 + (0 if side == "CalibPara" else 0x1000) + i * 128
                self.uc.mem_write(name, s["SNR_Mode"].encode() + b"\0")
                self.uc.mem_write(
                    sets + i * 16, struct.pack("<4I", name, 0, data, len(s[key]))
                )
                for j, row in enumerate(s[key]):
                    p = data + j * stride
                    self.uc.mem_write(p, bytes(stride))
                    self.uc.mem_write(p, struct.pack("<f", row["iso"]))
                    if side == "CalibPara":
                        self.uc.mem_write(
                            p + 4, struct.pack("<32i", *row["lumapoint"], *row["sigma"])
                        )
                    else:
                        self.uc.mem_write(p + 4, bytes([row["gauss_guide"]]))
                        self.uc.mem_write(
                            p + 8,
                            struct.pack(
                                "<4f",
                                *[
                                    row[k]
                                    for k in (
                                        "filter_strength",
                                        "edgesofts",
                                        "ratio",
                                        "weight",
                                    )
                                ],
                            ),
                        )
                        self.uc.mem_write(p + 24, bytes([row["gain_bypass"]]))
                        self.uc.mem_write(
                            p + 28,
                            struct.pack(
                                "<fHHBxHH2xI2f",
                                row["gain_scale"],
                                row["pix_diff"],
                                row["diff_thld"],
                                row["trans_mode"],
                                row["trans_offset"],
                                row["itrans_offset"],
                                row["trans_datmax"],
                                row["hdr_dgain_scale_s"],
                                row["hdr_dgain_scale_m"],
                            ),
                        )
                        self.uc.mem_write(
                            p + 56,
                            struct.pack(
                                "<32H",
                                *row["gain_adj"]["gain_lumapoint"],
                                *row["gain_adj"]["gain_adj"],
                            ),
                        )
        return root

    def run(self, value):
        root = self.sdk_graph(value["calibration"])
        table, noise, parammode, ci, ti = [
            HEAP + x for x in (0x40000, 0x30000, 0x30080, 0x30100, 0x30104)
        ]
        self.uc.mem_write(table, bytes.fromhex(value["table"]))
        self.uc.mem_write(noise, value["noise"].encode() + b"\0")
        self.uc.mem_write(parammode, b"normal\0")
        before = bytes(self.uc.mem_read(HEAP, 0x30000))
        assert (
            self.invoke("bayer2dnr_get_setting_by_name_json_V23", [root, noise, ci, ti])
            == 0
        )
        indices = list(struct.unpack("<2i", self.uc.mem_read(ci, 8)))
        assert (
            self.invoke(
                "bayer2dnr_config_setting_param_json_V23",
                [table, root, parammode, noise],
            )
            == 0
        )
        assert bytes(self.uc.mem_read(HEAP, 0x30000)) == before
        return dict(table=self.uc.mem_read(table, 3336).hex(), indices=indices)


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
    cal = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "bayer2dnr_v23"
    ]
    rng = random.Random(0x42415943)
    cases = []
    for case in range(100):
        c = copy.deepcopy(cal)
        if case >= 6:
            c["TuningPara"]["enable"] = case % 2
            c["TuningPara"]["hdrdgain_ctrl_en"] = case // 2 % 2
            for s in c["CalibPara"]["Setting"]:
                for row in s["Calib_ISO"]:
                    row["lumapoint"] = [rng.randrange(-100, 65537) for _ in range(16)]
                    row["sigma"] = [rng.randrange(-100, 65537) for _ in range(16)]
            for s in c["TuningPara"]["Setting"]:
                for row in s["Tuning_ISO"]:
                    row["iso"] = f32(row["iso"] + rng.randrange(50))
                    for k in (
                        "filter_strength",
                        "edgesofts",
                        "ratio",
                        "weight",
                        "gain_scale",
                        "hdr_dgain_scale_s",
                        "hdr_dgain_scale_m",
                    ):
                        row[k] = f32(rng.uniform(-1, 16))
                    for k in ("pix_diff", "diff_thld", "trans_offset", "itrans_offset"):
                        row[k] = rng.randrange(65536)
                    row["trans_mode"] = rng.randrange(256)
                    row["trans_datmax"] = rng.randrange(0x100000000)
                    row["gauss_guide"] = bool(rng.randrange(2))
                    row["gain_bypass"] = bool(rng.randrange(2))
                    for k in ("gain_lumapoint", "gain_adj"):
                        row["gain_adj"][k] = [rng.randrange(65536) for _ in range(16)]
            if case % 3 == 0:
                c["CalibPara"]["Setting"].reverse()
            if case % 4 == 0:
                c["TuningPara"]["Setting"].reverse()
            if case % 5 == 0:
                for side, key in [
                    ("CalibPara", "Calib_ISO"),
                    ("TuningPara", "Tuning_ISO"),
                ]:
                    for s in c[side]["Setting"]:
                        s[key] = s[key][: rng.randrange(1, 14)]
                        s[key + "_len"] = len(s[key])
        if case >= 6 and case % 7 == 0:
            for side, key in [("CalibPara", "Calib_ISO"), ("TuningPara", "Tuning_ISO")]:
                for s in c[side]["Setting"]:
                    s[key].append(copy.deepcopy(s[key][-1]))
                    s[key + "_len"] = len(s[key])
        cases.append(
            dict(
                calibration=c,
                noise=["LSNR", "HSNR", "H", "L", "unknown", ""][case % 6],
                table=rng.randbytes(3336).hex(),
            )
        )
    arm = OriginalCalibration(BINARY)
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "baynr-prepare " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
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
        unalteredProfileCases=6,
        preparedTableBytesComparedPerCase=3336,
        mismatches=0,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        iqSha256=hashlib.sha256(iq.read_bytes()).hexdigest(),
        scope="Complete native bayer2dnr_config_setting_param_json_V23, get_setting_by_name and init_params. All 3336 prepared bytes and both independent setting indices; calibration SDK graph checked unchanged.",
        boundaries=[
            "Raw SDK pointer graph built from selected JSON; native JSON parser not executed. strlen/strncmp are explicit libc boundaries, no algorithm/math substitutions.",
            "Actual profile plus modified numeric fields, independent setting order, prefix/fallback/empty-name lookup, partial/capped rows and poisoned prior table. Sensor_Mode and BLC reference data not consumed by this routine.",
            "Full constructor/automatic controller and live BAYNR remain separate. Physical CPU replay makes no ISP writes.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
