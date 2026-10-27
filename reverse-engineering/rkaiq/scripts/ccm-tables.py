#!/usr/bin/env python3
"""Check explicit CCM JSON tables and original native name resolution/sorting."""

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

runtime = importlib.import_module("ccm-runtime")
static = importlib.import_module("ccm-calibration")


def packed(values):
    return struct.pack("<" + "f" * len(values), *values).hex()


class OriginalTables(runtime.OriginalRuntime):
    def run(self, c):
        tuning = c["TuningPara"]
        matrices = tuning["matrixAll"]
        illuminants = tuning["aCcmCof"]
        source, table, matrix_base, names, refs = [
            HEAP + x for x in (0x10000, 0x20000, 0x30000, 0x40000, 0x50000)
        ]
        addresses = []
        name_addresses = {}
        for i, m in enumerate(matrices):
            n = names + i * 64
            name_addresses[m["name"]] = n
            self.uc.mem_write(n, m["name"].encode() + bytes(1))
            p = matrix_base + i * 60
            addresses.append(p)
            self.uc.mem_write(
                p,
                struct.pack(
                    "<II13f", n, 0, m["saturation"], *m["ccMatrix"], *m["ccOffsets"]
                ),
            )
        for i, ill in enumerate(illuminants):
            p = source + i * 56
            r = refs + i * 32
            pointers = [name_addresses[n] for n in ill["matrixUsed"]]
            self.uc.mem_write(r, struct.pack("<" + "I" * len(pointers), *pointers))
            self.uc.mem_write(
                p,
                struct.pack(
                    "<I3fII8f",
                    0,
                    *ill["awbGain"],
                    ill["minDist"],
                    r,
                    len(pointers),
                    *ill["gain_sat_curve"]["gains"],
                    *ill["gain_sat_curve"]["sat"],
                ),
            )
        self.uc.mem_write(table, bytes(9 * 20))
        assert (
            self.invoke(
                "pCcmMatrixAll_init",
                [source, len(illuminants), matrix_base, len(matrices)],
                stack=struct.pack("<I", table),
            )
            == 0
        )
        resolved = []
        for i, ill in enumerate(illuminants):
            profiles = []
            for j in range(len(ill["matrixUsed"])):
                address = struct.unpack(
                    "<I", self.uc.mem_read(table + i * 20 + j * 4, 4)
                )[0]
                m = matrices[addresses.index(address)]
                name = m["name"].encode()
                name = name + bytes(25 - len(name))
                profiles.append(
                    dict(
                        name=name.hex(),
                        values=bytes(self.uc.mem_read(address + 8, 52)).hex(),
                    )
                )
            p = source + i * 56
            resolved.append(
                dict(
                    values=(
                        bytes(self.uc.mem_read(p + 4, 8))
                        + bytes(self.uc.mem_read(p + 24, 32))
                    ).hex(),
                    profiles=profiles,
                )
            )
        luma = c["lumaCCM"]
        e = c["enhCCM"]
        control = c["control"]
        reference_static = static.OriginalCalibration(BINARY).run(
            dict(calibration=c, result=bytes(156).hex())
        )
        return dict(
            flags=[
                bool(control["enable"]),
                bool(tuning["damp_enable"]),
                bool(e["enh_adj_en"]),
            ],
            tolerances=packed([control["wbgain_tolerance"], control["gain_tolerance"]]),
            illuminants=resolved,
            luma=packed(
                [
                    v
                    for row in luma["y_alp_sym"]["gain_yalp_curve"]
                    for v in [row["iso"], *row["y_alpha_curve"]]
                ]
            ),
            alphaGains=packed(luma["gain_alphaScale_curve"]["gain"]),
            alphaScales=packed(luma["gain_alphaScale_curve"]["scale"]),
            enhancementGains=packed(e["enh_rat"]["gains"]),
            enhancementRatios=packed(e["enh_rat"]["enh_rat_max"]),
            staticResult=reference_static,
        )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--adb")
    args = p.parse_args()
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    original = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0][
        "scene_isp32"
    ]["ccm_calib_v2"]
    rng = random.Random(0x43434D54)
    cases = []
    for i in range(32):
        c = copy.deepcopy(original)
        if i:
            t = c["TuningPara"]
            rng.shuffle(t["matrixAll"])
            for m in t["matrixAll"]:
                m["ccMatrix"] = [rng.uniform(-4, 4) for _ in range(9)]
                m["ccOffsets"] = [rng.uniform(-100, 100) for _ in range(3)]
            for ill in t["aCcmCof"]:
                rng.shuffle(ill["matrixUsed"])
                ill["awbGain"] = [rng.uniform(0.5, 4) for _ in range(2)]
                ill["gain_sat_curve"]["sat"] = [rng.uniform(0, 100) for _ in range(4)]
            for row in c["lumaCCM"]["y_alp_sym"]["gain_yalp_curve"]:
                row["y_alpha_curve"] = [rng.randrange(1025) for _ in range(17)]
            c["lumaCCM"]["gain_alphaScale_curve"]["scale"] = [
                rng.random() for _ in range(9)
            ]
            c["enhCCM"]["enh_rat"]["enh_rat_max"] = [
                rng.uniform(0, 8) for _ in range(9)
            ]
        cases.append(c)
    arm = OriginalTables(BINARY)
    expected = [arm.run(c) for c in cases]
    lines = "".join(
        "ccm-tables " + json.dumps(c, separators=(",", ":")) + "\n" for c in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = [
        json.loads(line)
        for line in subprocess.check_output(
            [str(binary)], input=lines, text=True
        ).splitlines()
    ]
    assert actual == expected, "Loaded CCM table mismatch"
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
        board = "/shieldsigner-camera-tests/dev-0.0.34/bin/numeric-fixture"
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/ccm-tables-"
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
        cases=len(cases),
        actualProfileCases=1,
        shuffledVariedCases=31,
        illuminantsPerCase=len(original["TuningPara"]["aCcmCof"]),
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        iqSha256=hashlib.sha256(iq.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        scope="Original complete pCcmMatrixAll_init/CamCalibDbGetCcmProfileByName and ConfigHwbyCalib execute. All resolved profile names/float bits, input curve/control fields and static result bytes compared.",
        limitations=[
            "Native JSON parser/full constructor not executed; consumed ARM SDK fields packed explicitly.",
            "Curve/control input mapping checked independently from JSON; their downstream algorithms have separate native evidence.",
            "Libc string/memory routines are controlled boundaries; live CCM is not enabled.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
