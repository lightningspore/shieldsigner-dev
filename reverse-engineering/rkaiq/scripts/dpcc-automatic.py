#!/usr/bin/env python3
"""Check full fresh automatic DPCC init/process against the original ARM code."""

import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import re
import struct
import subprocess
import tempfile
import uuid

from differential import OriginalArm, ROOT, BINARY, HEAP, regs

calibration_ref = importlib.import_module("dpcc-calibration")


class OriginalAutomatic(OriginalArm):
    def __init__(self):
        super().__init__(BINARY)
        self.lookup = (
            self.resolve_symbol(
                "_ZL24calibdbV2_get_module_ptrPvP19calibdb_ctx_infos_sPKc.constprop.10",
                0x12A928,
            )
            & ~1
        )

    def hook(self, uc, address, size, user):
        if address == getattr(self, "lookup", None):
            value = HEAP + 0x20000
        elif self.stubs.get(address) == "malloc":
            assert uc.reg_read(regs.UC_ARM_REG_R0) == 0x1964
            value = HEAP + 0x40000
        elif address == (self.symbols.get("xcam_print_log", 0) & ~1):
            value = 0
        else:
            super().hook(uc, address, size, user)
            return
        uc.reg_write(regs.UC_ARM_REG_R0, value)
        uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))


def schema_full(text):
    text = re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S)
    out = {}
    for body, name in re.findall(
        r"typedef struct \w+\s*\{(.*?)\}\s*(\w+);", text, re.S
    ):
        out[name] = re.findall(
            r"(unsigned char|bool|int|float|\w+_t)\s*(\*)?\s+(\w+)\s*(?:\[([^]]+)\])?\s*;",
            body,
        )
    return out


def pack_full(schema, name, value, arm, allocator):
    primitive = {
        "bool": ("B", 1),
        "unsigned char": ("B", 1),
        "int": ("i", 4),
        "float": ("f", 4),
    }
    out = bytearray()
    alignment = 1
    for kind, pointer, key, count in schema[name]:
        count = {"CALIBDB_ADPCC_KNOTS_NUM": 13, "CALIBDB_ADPCC_PDAF_KNOTS_NUM": 16}.get(
            count, int(count or 1) if (count or "1").isdecimal() else None
        )
        assert count is not None
        if pointer:
            data = value[key]
            fmt = primitive[kind][0]
            addr = allocator[0]
            raw = struct.pack("<" + fmt * len(data), *data)
            arm.uc.mem_write(addr, raw)
            allocator[0] += len(raw) + ((-len(raw)) % 4)
            field = struct.pack("<I", addr)
            align = 4
        elif kind in primitive:
            fmt, align = primitive[kind]
            v = len(value[key[:-4]]) if key.endswith("_len") else value[key]
            data = v if count != 1 else [v]
            field = struct.pack("<" + fmt * count, *data)
        else:
            assert count == 1
            field, align = pack_full(schema, kind, value[key], arm, allocator)
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
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    header = ROOT / ".tools/reverse-engineering/headers/adpcc_head.h"
    schema = schema_full(header.read_text())
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    original = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0][
        "scene_isp32"
    ]["adpcc_calib"]["DpccTuningPara"]
    rng = random.Random(0x44504155)
    arm = OriginalAutomatic()
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
        if index >= 41:
            value["Enable"] = index % 2
            value["Expert_Mode"] = mutate(value["Expert_Mode"])
            value["Expert_Mode"]["SetEnable"]["ISO"] = [
                50 * (1 << i) for i in range(13)
            ]
            pdaf = value["Dpcc_pdaf"]
            pdaf["point_en"] = [rng.randrange(256) for _ in range(16)]
            pdaf["point_x"] = [rng.randrange(256) for _ in range(16)]
            pdaf["point_y"] = [rng.randrange(256) for _ in range(16)]
            for key in ("offsetx", "offsety", "wrapx_num", "wrapy_num"):
                pdaf[key] = rng.randint(-(1 << 31), (1 << 31) - 1)
            for key in ("wrapx", "wrapy", "forward_med"):
                pdaf[key] = rng.randrange(256)
        value["Fast_Mode"]["Fast_mode_en"] = 0
        value["Sensor_dpcc"]["sensor_dpcc_auto_en"] = 0
        value["Dpcc_pdaf"]["en"] = 0
        source, align = pack_full(
            schema, "CalibDbDpccV20_t", value, arm, [HEAP + 0x60000]
        )
        assert len(source) == 0x548 and align == 4
        arm.uc.mem_write(HEAP + 0x20000, source)
        pp = HEAP + 0x1000
        arm.uc.mem_write(pp, bytes(4))
        assert (
            arm.invoke(
                "_Z9AdpccInitPP14AdpccContext_sP21CamCalibDbV2Context_s", [pp, HEAP]
            )
            == 0
        )
        context = struct.unpack("<I", arm.uc.mem_read(pp, 4))[0]
        assert context == HEAP + 0x40000
        assert bytes(arm.uc.mem_read(context + 0x5E8, 24)) == bytes(24)
        iso = [-1, 0, 49, 50, 99, 100, 1500, 1507, 1510, 204800, 1000000][index % 11]
        if index < 41:
            grid = original["Expert_Mode"]["SetEnable"]["ISO"]
            directed = [-(1 << 31), (1 << 31) - 1] + [
                v + d for v in grid for d in (-1, 0, 1)
            ]
            iso = directed[index]
        result = rng.randbytes(192)
        out = HEAP + 0x10000
        exposure = HEAP + 0x11000
        arm.uc.mem_write(out, result)
        arm.uc.mem_write(exposure, bytes(100))
        arm.uc.mem_write(exposure + 40, struct.pack("<i", iso))
        assert (
            arm.invoke(
                "_Z12AdpccProcessP14AdpccContext_sP14AdpccExpInfo_sP17AdpccProcResult_s",
                [context, exposure, out],
            )
            == 0
        )
        expected.append(bytes(arm.uc.mem_read(out, 192)).hex())
        cases.append({"calibration": value, "iso": iso, "result": result.hex()})
    lines = "".join(
        "dpcc-auto " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
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
            "/shieldsigner-camera-tests/dev-0.0.34/dpcc-auto-"
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
        "resultBytesComparedPerCase": 192,
        "actualProfileCases": 41,
        "mismatches": 0,
        "originalBinarySha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "iqSha256": hashlib.sha256(iq.read_bytes()).hexdigest(),
        "sdkHeaderSha256": hashlib.sha256(header.read_bytes()).hexdigest(),
        "hostBinarySha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "physicalArmBinarySha256": board_sha,
        "hostMatchesPhysicalArm": board_sha is not None,
        "scope": "Complete native AdpccInit and AdpccProcess for fresh auto-expert, disabled PDAF/sensor auto; full 192-byte output including padding.",
        "boundaries": [
            "Allocator returns one controlled context; original memset/init executes.",
            "IQ module lookup returns an independently SDK-packed object; native SDK JSON parsing is not executed.",
            "Diagnostic logging is a modeled no-op.",
        ],
        "limitations": [
            "Fast/manual, enabled PDAF and sensor-side DPCC are outside this profile-bound Rust API.",
            "Outer frame/update policy and live ISP queue integration remain separate.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
