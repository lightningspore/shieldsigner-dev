#!/usr/bin/env python3
"""Native chroma NR SNR setting lookup and tuning table preparation."""

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
from differential import ROOT, BINARY, HEAP, f32

Base = importlib.import_module("baynr-calibration").OriginalCalibration
FIELDS = (
    "thumb_sigma",
    "thumb_bf_ratio",
    "chroma_filter_strength",
    "chroma_filter_wgt_clip",
    "anti_chroma_ghost",
    "chroma_filter_uv_gain",
    "wgt_slope",
    "gaus_ratio",
    "bf_sigmaR",
    "bf_uvgain",
    "bf_ratio",
    "hbf_wgt_clip",
    "global_alpha",
    "saturation_adj_offset",
    "saturation_adj_ratio",
    "global_gain",
    "global_gain_alpha",
    "local_gain_scale",
    "global_gain_thumb",
    "global_gain_alpha_thumb",
)
CURVES = (
    ("gain_adj_strength_ratio", 92, 13),
    ("thumb_filter_wgt_coeff", 144, 4),
    ("gaus_coeff", 160, 6),
)


class OriginalCalibration(Base):
    def sdk_graph(self, cal):
        self.uc.mem_write(HEAP, bytes(0x31000))
        root, sets = HEAP, HEAP + 0x1000
        settings = cal["TuningPara"]["Setting"]
        self.uc.mem_write(
            root,
            struct.pack("<IB3xII", 0, cal["TuningPara"]["enable"], sets, len(settings)),
        )
        for i, s in enumerate(settings):
            data, name = HEAP + 0x3000 + i * 0x2000, HEAP + 0x20000 + i * 128
            self.uc.mem_write(name, s["SNR_Mode"].encode() + b"\0")
            self.uc.mem_write(
                sets + i * 16, struct.pack("<4I", name, 0, data, len(s["Tuning_ISO"]))
            )
            for j, row in enumerate(s["Tuning_ISO"]):
                b = bytearray(184)
                struct.pack_into(
                    "<fBB", b, 0, row["iso"], row["down_scale_x"], row["down_scale_y"]
                )
                b[56] = row["bf_wgt0_sel"]
                for k, key in enumerate(FIELDS):
                    offset = 8 + k * 4 if k < 12 else 60 + (k - 12) * 4
                    struct.pack_into("<f", b, offset, row[key])
                for key, offset, n in CURVES:
                    struct.pack_into("<" + str(n) + "f", b, offset, *row[key])
                self.uc.mem_write(data + j * 184, bytes(b))
        return root

    def run(self, value):
        root = self.sdk_graph(value["calibration"])
        table, noise, mode, index = [
            HEAP + x for x in (0x40000, 0x30000, 0x30080, 0x30100)
        ]
        self.uc.mem_write(table, bytes.fromhex(value["table"]))
        self.uc.mem_write(noise, value["noise"].encode() + b"\0")
        self.uc.mem_write(mode, b"normal\0")
        before = bytes(self.uc.mem_read(HEAP, 0x30000))
        assert (
            self.invoke("cnr_get_setting_by_name_json_V30", [root, noise, index]) == 0
        )
        selected = struct.unpack("<i", self.uc.mem_read(index, 4))[0]
        self.invoke("cnr_config_setting_param_json_V30", [table, root, mode, noise])
        assert bytes(self.uc.mem_read(HEAP, 0x30000)) == before
        return dict(table=self.uc.mem_read(table, 2396).hex(), indices=selected)


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
        "cnr_v30"
    ]
    rng = random.Random(0x434E5243)
    cases = []
    for case in range(100):
        c = copy.deepcopy(cal)
        if case >= 6:
            c["TuningPara"]["enable"] = bool(case % 2)
            for s in c["TuningPara"]["Setting"]:
                for row in s["Tuning_ISO"]:
                    row["iso"] = f32(row["iso"] + rng.randrange(50))
                    row["down_scale_x"], row["down_scale_y"] = (
                        rng.randrange(256),
                        rng.randrange(256),
                    )
                    row["bf_wgt0_sel"] = bool(rng.randrange(2))
                    for key in FIELDS:
                        row[key] = f32(rng.uniform(-2, 16))
                    for key, _, n in CURVES:
                        row[key] = [f32(rng.uniform(-2, 16)) for _ in range(n)]
                if case % 5 == 0:
                    s["Tuning_ISO"] = s["Tuning_ISO"][: rng.randrange(1, 14)]
                if case % 7 == 0:
                    s["Tuning_ISO"] += [copy.deepcopy(s["Tuning_ISO"][-1])] * 2
                s["Tuning_ISO_len"] = len(s["Tuning_ISO"])
            if case % 3 == 0:
                c["TuningPara"]["Setting"].reverse()
            if case % 4 == 0:
                for s in c["TuningPara"]["Setting"]:
                    s["SNR_Mode"] += "-suffix"
        cases.append(
            dict(
                calibration=c,
                noise=["LSNR", "HSNR", "H", "L", "unknown", ""][case % 6],
                table=rng.randbytes(2396).hex(),
            )
        )
    arm = OriginalCalibration(BINARY)
    expected = [arm.run(v) for v in cases]
    lines = "".join(
        "cnr-prepare " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
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
            "/shieldsigner-camera-tests/dev-0.0.34/cnr-" + uuid.uuid4().hex + ".txt"
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
        preparedTableBytesComparedPerCase=2396,
        mismatches=0,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        iqSha256=hashlib.sha256(iq.read_bytes()).hexdigest(),
        scope="Full native cnr_get_setting_by_name_json_V30 and cnr_config_setting_param_json_V30 including complete initializer. Full prepared table, selected setting index and immutable SDK graph checked.",
        boundaries=[
            "Typed SDK JSON graph replaces JSON parsing; libc string/memory and diagnostic calls are explicit boundaries, original lookup and preparation instructions execute.",
            "Six original-profile requests plus varied settings, reordered/prefix/fallback lookup, partial/capped rows, floats, byte fields, curves and poisoned prior table bytes.",
            "Physical CPU replay loads no vendor library and performs no ISP writes. Fixed quantization, persistent controller and live CNR remain separate.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
