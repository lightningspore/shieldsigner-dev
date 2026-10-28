#!/usr/bin/env python3
"""Full native YNR constructor, prepare and normal processing sequences."""

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
from differential import ROOT, BINARY, HEAP, regs, u32, OriginalArm

fix = importlib.import_module("baynr-quantize")
calibration = importlib.import_module("baynr-calibration")


class OriginalFrames(fix.OriginalFix, calibration.OriginalCalibration):
    def __init__(self):
        super().__init__()
        self.stubs[self.symbols["xcam_print_log"] & ~1] = "xcam_print_log"
        self.stubs[self.symbols["ynr_fix_printf_V22"] & ~1] = "ynr-print"
        descriptor = 0x10000 + 0x1A6C78
        assert u32(self.uc.mem_read(descriptor + 36, 4)) & ~1 == 0xEE5AC
        assert u32(self.uc.mem_read(descriptor + 28, 4)) & ~1 == 0xEE8F0
        self.symbols["ynr-frame"] = self.resolve_symbol("processing", 0xEE5AC)
        self.symbols["ynr-prepare"] = self.resolve_symbol("prepare", 0xEE8F0)

    def hook(self, uc, address, size, user):
        name = self.stubs.get(address)
        if name in ("malloc", "strcmp", "strcpy", "xcam_print_log", "ynr-print"):
            a, b = [uc.reg_read(r) for r in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1)]
            if name == "malloc":
                assert a == 0x169C
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

    def sdk_graph(self, cal):
        self.uc.mem_write(HEAP, bytes(0x31000))
        root, cs, ts = HEAP, HEAP + 0x1000, HEAP + 0x2000
        self.uc.mem_write(
            root,
            struct.pack(
                "<3IB3xII",
                0,
                cs,
                len(cal["CalibPara"]["Setting"]),
                cal["TuningPara"]["enable"],
                ts,
                len(cal["TuningPara"]["Setting"]),
            ),
        )
        for side, sets, base, stride, key in [
            ("CalibPara", cs, HEAP + 0x3000, 56, "Calib_ISO"),
            ("TuningPara", ts, HEAP + 0x10000, 248, "Tuning_ISO"),
        ]:
            for n, setting in enumerate(cal[side]["Setting"]):
                data = base + n * 0x2000
                name = HEAP + 0x20000 + (0 if side == "CalibPara" else 0x1000) + n * 128
                self.uc.mem_write(name, setting["SNR_Mode"].encode() + b"\0")
                self.uc.mem_write(
                    sets + n * 16, struct.pack("<4I", name, 0, data, len(setting[key]))
                )
                for i, row in enumerate(setting[key]):
                    b = bytearray(stride)
                    struct.pack_into("<f", b, 0, row["iso"])
                    if side == "CalibPara":
                        struct.pack_into(
                            "<5d2f",
                            b,
                            8,
                            *row["sigma_curve"],
                            row["ynr_lci"],
                            row["ynr_hci"],
                        )
                    else:
                        for j, k in enumerate(FLAGS):
                            b[4 + j] = row[k]
                        for j, k in enumerate(GLOBAL):
                            struct.pack_into("<f", b, 12 + j * 4, row[k])
                        for k, offset, fmt in [
                            ("lo_lumaPoint", 28, "6H"),
                            ("lo_ratio", 40, "6f"),
                            ("hi_lumaPoint", 64, "6H"),
                            ("hi_ratio", 76, "6f"),
                        ]:
                            struct.pack_into("<" + fmt, b, offset, *row["lumaPara"][k])
                        for j, k in enumerate(FILTER):
                            struct.pack_into("<f", b, 100 + j * 4, row[k])
                        for j, k in enumerate(COEFF):
                            b[172 + j] = row[k]
                        struct.pack_into("<17f", b, 180, *row["rnr_strength"])
                    self.uc.mem_write(data + i * stride, bytes(b))
        return root

    def run(self, value):
        root = self.sdk_graph(value["calibration"])
        before = bytes(self.uc.mem_read(HEAP, 0x30000))

        def u(a):
            return u32(self.uc.mem_read(a, 4))

        got = (u(0xEED60) + 0xEEC8E + u(0xEED6C)) & 0xFFFFFFFF
        self.uc.mem_write(u(got), struct.pack("<I", 32))
        lookup = (u(0xEED70) + 0xEECEC) & 0xFFFFFFFF
        assert u(lookup) == 32
        modules = u(lookup + 4)
        offset = None
        for i in range(100):
            p, off = struct.unpack("<II", self.uc.mem_read(modules + i * 8, 8))
            if not p:
                break
            if self.string(p) == b"ynr_v22":
                offset = off
                break
        assert offset is not None
        self.module_offset = offset
        config, pp = HEAP + 0x76000, HEAP + 0x76100
        self.uc.mem_write(config, bytes(64))
        self.uc.mem_write(config + 24, struct.pack("<I", root - offset))
        self.uc.mem_write(pp, bytes(4))
        assert self.invoke("Aynr_Init_V22", [pp, config]) == 0
        context = u(pp)
        assert context == HEAP + 0x60000
        assert self.uc.mem_read(context + 0x165C, 16) == bytes(8) + struct.pack(
            "<f", 1.0
        ) + b"\x01" + bytes(3)
        inp, out, ae, blc, result = [
            HEAP + x for x in (0x73000, 0x74000, 0x71000, 0x72000, 0x75000)
        ]
        self.uc.mem_write(inp, bytes(100))
        self.uc.mem_write(inp, struct.pack("<I", context))
        self.uc.mem_write(
            inp + 48, struct.pack("<II", value["geometry"][1], value["geometry"][0])
        )
        assert self.invoke("ynr-prepare", [inp]) == 0
        assert u(context + 0x58) == 3 and u(context + 0x5C) == 1
        self.uc.mem_write(out, struct.pack("<III", 0, 0, result))
        self.uc.mem_write(result, bytes.fromhex(value.get("result", "a5" * 168)))
        self.uc.mem_write(ae, bytes(244))
        self.uc.mem_write(blc, bytes(32))
        self.uc.mem_write(inp + 24, struct.pack("<I", ae))
        self.uc.mem_write(inp + 48, struct.pack("<I", blc))
        frames = []
        for frame in value["frames"]:
            self.uc.mem_write(inp + 17, bytes([frame["gray"]]))
            self.uc.mem_write(ae, struct.pack("<4f", frame["seconds"], *frame["gains"]))
            self.uc.mem_write(ae + 240, bytes([frame["snr"]]))
            self.uc.mem_write(blc + 24, struct.pack("<f", frame["blc"]))
            if frame["force"]:
                self.uc.mem_write(
                    context + 0x1698, struct.pack("<I", u(context + 0x1698) | 1)
                )
            assert self.invoke("ynr-frame", [inp, out], instructions=300000) == 0
            frames.append(
                dict(
                    updated=bool(self.uc.mem_read(out, 1)[0]),
                    result=self.uc.mem_read(result, 168).hex(),
                    table=self.uc.mem_read(context + 0x60, 4748).hex(),
                    selected=self.uc.mem_read(context + 0x12EC, 356).hex(),
                    exposure=self.uc.mem_read(context, 88).hex(),
                    strength=self.uc.mem_read(context + 0x165C, 16).hex(),
                    gray=bool(self.uc.mem_read(context + 0x166D, 1)[0]),
                    parameterMode=u(context + 0x1670),
                    recalculate=bool(u(context + 0x1698)),
                )
            )
        assert bytes(self.uc.mem_read(HEAP, 0x30000)) == before
        return frames


FLAGS = [
    "ynr_bft3x3_bypass",
    "ynr_lbft5x5_bypass",
    "ynr_lgft3x3_bypass",
    "ynr_flt1x1_bypass",
    "ynr_nlm11x11_bypass",
    "ynr_thumb_mix_cur_en",
]
GLOBAL = [
    "ynr_global_gain_alpha",
    "ynr_global_gain",
    "ynr_adjust_thresh",
    "ynr_adjust_scale",
]
FILTER = [
    "low_bf1",
    "low_bf2",
    "low_thred_adj",
    "low_peak_supress",
    "low_edge_adj_thresh",
    "low_lbf_weight_thresh",
    "low_center_weight",
    "low_dist_adj",
    "low_weight",
    "low_filt1_strength",
    "low_filt2_strength",
    "low_bi_weight",
    "hi_bf_scale",
    "hi_gain_alpha",
    "hi_center_weight",
    "hi_weight_offset",
    "hi_min_sigma",
    "hi_nr_weight",
]
COEFF = [
    "hi_filter_coeff1_1",
    "hi_filter_coeff1_2",
    "hi_filter_coeff1_3",
    "hi_filter_coeff2_1",
    "hi_filter_coeff2_2",
    "hi_filter_coeff2_3",
]


def verify_layout():
    names = [
        "ynr_uapi_head_v22.h",
        "rk_aiq_types_aynr_algo_int_v22.h",
        "rk_aiq_types_aynr_hw_v22.h",
        "ynr_head_v22.h",
    ]
    manifest = json.loads(
        (ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text()
    )
    files = {}
    hashes = {}
    for name in names:
        data = (ROOT / ".tools/reverse-engineering/headers" / name).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        assert digest == next(
            x["sha256"] for x in manifest["headers"] if x["name"] == name
        )
        files[name] = data.decode()
        hashes[name] = digest

    def decl(file, name):
        match = re.search(
            r"typedef struct " + name + r"\s*\{.*?\}\s*\w+;", files[file], re.S
        )
        assert match
        return match.group(0)

    source = "#include <stdint.h>\n#include <stdbool.h>\n#include <stddef.h>\n#define YNR_V22_ISO_CURVE_POINT_NUM 17\n#define RK_YNR_V22_MAX_ISO_NUM 13\n"
    for file, name in [
        (names[0], "RK_YNR_Params_V22_Select_s"),
        (names[0], "Aynr_ExpInfo_V22_s"),
        (names[1], "RK_YNR_Params_V22_s"),
        (names[2], "RK_YNR_Fix_V22_s"),
    ]:
        source += decl(file, name) + "\n"
    source += """
_Static_assert(sizeof(RK_YNR_Params_V22_Select_t)==356,"selected");
_Static_assert(sizeof(RK_YNR_Params_V22_t)==4748,"table");
_Static_assert(sizeof(Aynr_ExpInfo_V22_t)==88,"exposure");
_Static_assert(sizeof(RK_YNR_Fix_V22_t)==168,"fixed");
_Static_assert(offsetof(RK_YNR_Params_V22_Select_t,sigma)==44,"sigma");
_Static_assert(offsetof(RK_YNR_Params_V22_Select_t,lo_lumaPoint)==112,"low luma");
_Static_assert(offsetof(RK_YNR_Params_V22_Select_t,ynr_global_gain_alpha)==192,"global");
_Static_assert(offsetof(RK_YNR_Params_V22_Select_t,hi_filter_coeff1_1)==348,"filter coefficients");
_Static_assert(offsetof(RK_YNR_Params_V22_t,iso)==68,"ISO table");
_Static_assert(offsetof(RK_YNR_Params_V22_t,arYnrParamsISO)==120,"rows");
"""
    path = ROOT / "dist/reverse-engineering/ynr/layout.c"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source)
    subprocess.run(
        [
            "mise",
            "exec",
            "zig@0.15.2",
            "--",
            "zig",
            "cc",
            "-target",
            "arm-linux-musleabihf",
            "-c",
            str(path),
            "-o",
            str(path.with_suffix(".o")),
        ],
        check=True,
    )
    return hashes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    sdk_hashes = verify_layout()
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    cal = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "ynr_v22"
    ]
    cases = []
    for seq in range(4):
        frames = []
        for n, g in enumerate(
            [1.0, 1.0, 1.2, 1.22, 1.22, 2.0, 4.0, 4.0, 1.0, 1.0, 1.0, 2.0]
        ):
            frames.append(
                dict(
                    seconds=0.003 if n < 6 else 0.01,
                    gains=[g, 1.0, 1.0],
                    snr=(n // 3) % 2,
                    gray=n in (8, 9),
                    blc=1.0 if seq < 3 else 0.5,
                    force=n == 10,
                )
            )
        selected_cal = copy.deepcopy(cal)
        if seq == 2:
            selected_cal["TuningPara"]["enable"] = False
        cases.append(
            dict(
                calibration=selected_cal,
                geometry=[[2304, 1296], [640, 480]][seq % 2],
                frames=frames,
            )
        )
    # Walk the actual thirteen calibration rows for both sensor-noise modes.
    for snr in (0, 1):
        frames = [
            dict(
                seconds=0.003,
                gains=[float(1 << n), 1.0, 1.0],
                snr=snr,
                gray=False,
                blc=1.0,
                force=False,
            )
            for n in range(13)
        ]
        cases.append(dict(calibration=cal, geometry=[2304, 1296], frames=frames))
    arm = OriginalFrames()
    want = [arm.run(v) for v in cases]
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    lines = "".join(
        "ynr-frames " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    for seq, (got, expected) in enumerate(zip(actual, want, strict=True)):
        for n, (g, w) in enumerate(zip(json.loads(got), expected, strict=True)):
            if g != w:
                mismatch = {
                    k: (
                        [
                            i
                            for i, (a, b) in enumerate(
                                zip(bytes.fromhex(g[k]), bytes.fromhex(w[k]))
                            )
                            if a != b
                        ]
                        if isinstance(w[k], str)
                        else [g[k], w[k]]
                    )
                    for k in w
                    if g[k] != w[k]
                }
                raise AssertionError(f"sequence {seq} frame {n}: {mismatch}")
    packing = OriginalArm(BINARY)
    rng = random.Random(0x594E52)
    inputs = []
    packed = []
    for n in range(16):
        prior = rng.randbytes(11145)
        result = bytearray(rng.randbytes(168))
        result[12] = [0, 1, 2, 255][n % 4]
        packing.uc.mem_write(HEAP + 0x10000, prior)
        packing.uc.mem_write(HEAP + 0x20000, bytes(result))
        packing.invoke(
            "_ZN5RkCam11Isp32Params26convertAiqYnrToIsp32ParamsER20isp32_isp_params_cfgR16RK_YNR_Fix_V22_s",
            [HEAP, HEAP + 0x10000, HEAP + 0x20000],
        )
        packed.append(packing.uc.mem_read(HEAP + 0x10000, 11145).hex())
        inputs.append(
            "isp-ynr "
            + json.dumps(
                dict(parameters=prior.hex(), result=result.hex()), separators=(",", ":")
            )
            + "\n"
        )
    got = subprocess.check_output(
        [str(binary)], input="".join(inputs), text=True
    ).splitlines()
    assert got == packed, "Native packing mismatch"
    report = dict(
        passed=True,
        sequences=len(cases),
        frames=sum(len(v["frames"]) for v in cases),
        packingCases=16,
        sdkArmLayoutVerified=True,
        sdkHeaderSha256=sdk_hashes,
        packingBytesComparedPerCase=11145,
        updatedFrames=sum(f["updated"] for seq in want for f in seq),
        sdkModuleOffset=hex(arm.module_offset),
        scope="Complete native constructor/prepare/processing callback against focused Rust normal-path sequences plus complete native ISP32 YNR packing; no hardware claim",
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
