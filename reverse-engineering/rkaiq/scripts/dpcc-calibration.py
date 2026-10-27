#!/usr/bin/env python3
"""Compare JSON expert-table construction with native initialization."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import re
import struct
import subprocess
import tempfile
import uuid

from differential import OriginalArm, ROOT, BINARY, HEAP


def schemas(text):
    text = re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S)
    out = {}
    for body, name in re.findall(
        r"typedef struct \w+\s*\{(.*?)\}\s*(\w+);", text, re.S
    ):
        out[name] = re.findall(
            r"(unsigned char|bool|int|float|\w+_t)\s+(\w+)\s*(?:\[([^]]+)\])?\s*;", body
        )
    return out


def pack(schema, name, value):
    primitive = {
        "bool": ("B", 1),
        "unsigned char": ("B", 1),
        "int": ("i", 4),
        "float": ("f", 4),
    }
    out = bytearray()
    alignment = 1
    for kind, key, count in schema[name]:
        count = 13 if count == "CALIBDB_ADPCC_KNOTS_NUM" else int(count or 1)
        if kind in primitive:
            fmt, align = primitive[kind]
            data = value[key] if count != 1 else [value[key]]
            assert len(data) == count
            field = struct.pack("<" + fmt * count, *data)
        else:
            assert count == 1
            field, align = pack(schema, kind, value[key])
        out.extend(bytes((-len(out)) % align))
        out.extend(field)
        alignment = max(alignment, align)
    out.extend(bytes((-len(out)) % alignment))
    return bytes(out), alignment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    manifest = json.loads(
        (ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text()
    )
    header = ROOT / ".tools/reverse-engineering/headers/adpcc_head.h"
    entry = next(x for x in manifest["headers"] if x["name"] == header.name)
    assert hashlib.sha256(header.read_bytes()).hexdigest() == entry["sha256"]
    schema = schemas(header.read_text())
    iqpath = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    original = json.loads(iqpath.read_text())["main_scene"][0]["sub_scene"][0][
        "scene_isp32"
    ]["adpcc_calib"]["DpccTuningPara"]
    arm = OriginalArm(BINARY)
    rng = random.Random(0x44504349)
    cases = []
    expected = []

    def mutate(value):
        if isinstance(value, dict):
            return {k: mutate(v) for k, v in value.items()}
        if isinstance(value, list):
            return [rng.randrange(256) for _ in value]
        return rng.randrange(2)

    for index in range(200):
        value = copy.deepcopy(original)
        if index:
            value["Enable"] = index % 2
            value["Expert_Mode"] = mutate(value["Expert_Mode"])
            knots = []
            knot = rng.randrange(50)
            for _ in range(13):
                knot += rng.randrange(1, 10000)
                knots.append(knot)
            value["Expert_Mode"]["SetEnable"]["ISO"] = knots
        value["Fast_Mode"]["Fast_mode_en"] = 0
        expert, align = pack(
            schema, "CalibDb_Dpcc_Expert_Mode_V20_t", value["Expert_Mode"]
        )
        assert len(expert) == 1204 and align == 4
        source = bytearray(40) + expert
        source[0] = value["Enable"]
        out = HEAP + 0x10000
        arm.uc.mem_write(HEAP, bytes(source))
        arm.uc.mem_write(out, bytes(1404))
        assert (
            arm.invoke(
                "_Z34dpcc_expert_mode_basic_params_initP20Adpcc_basic_params_sP16CalibDbV2_Dpcc_s",
                [out, HEAP],
            )
            == 0
        )
        expected.append(bytes(arm.uc.mem_read(out, 1404)).hex())
        cases.append(value)
    lines = "".join(
        "dpcc-expert-init " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    assert actual == expected, next(
        (i for i, (a, b) in enumerate(zip(actual, expected)) if a != b),
        "length mismatch",
    )
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
        board = "/shieldsigner-camera-tests/dev-0.0.34/bin/numeric-fixture"
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/dpcc-init-"
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
            p = Path(temporary) / "input"
            p.write_text(lines)
            subprocess.run(
                adb + ["push", str(p), remote], check=True, capture_output=True
            )
            try:
                assert (
                    subprocess.check_output(
                        adb + ["shell", board + " < " + remote], text=True
                    ).splitlines()
                    == actual
                )
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = {
        "passed": True,
        "cases": len(cases),
        "actualProfileCases": 1,
        "tableBytesComparedPerCase": 1404,
        "mismatches": 0,
        "originalBinarySha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "iqSha256": hashlib.sha256(iqpath.read_bytes()).hexdigest(),
        "sdkHeaderSha256": entry["sha256"],
        "hostBinarySha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "physicalArmBinarySha256": board_sha,
        "hostMatchesPhysicalArm": board_sha is not None,
        "scope": "Explicit DpccTuningPara JSON through expert-table construction; independently SDK-packed input executes complete native initializer.",
        "limitations": [
            "Unused Fast-mode descriptors and preceding padding are zero-filled controlled input; native expert init does not read them.",
            "Fresh table padding starts zero on both paths.",
            "BPT/PDAF result construction, complete AdpccProcess and live camera integration remain separate.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
