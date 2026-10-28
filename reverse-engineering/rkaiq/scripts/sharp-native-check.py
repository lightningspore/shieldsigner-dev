#!/usr/bin/env python3
"""Focused complete SHARP V33 constructor/callback/packing comparison."""

import argparse
import copy
import hashlib
import importlib
import json
import re
from pathlib import Path
import struct
import subprocess
from differential import ROOT, BINARY, HEAP, OriginalArm, regs, u32
from exposure import RUNTIME

BaseCalibration = importlib.import_module("baynr-calibration").OriginalCalibration
FIELDS = [
    "pbf_gain",
    "pbf_ratio",
    "pbf_add",
    "gaus_ratio",
    "sharp_ratio",
    "sharp_ratio_0",
    "sharp_ratio_1",
    "bf_gain",
    "bf_ratio",
    "bf_add",
    "global_gain",
    "global_gain_alpha",
    "local_gainscale",
]
CURVES = [
    ("prefilter_coeff", 264, 3),
    ("GaussianFilter_coeff", 276, 6),
    ("hfBilateralFilter_coeff", 300, 3),
    ("GaussianFilter_coeff_0", 312, 6),
    ("GaussianFilter_coeff_1", 336, 6),
]


class OriginalSharp(BaseCalibration):
    def __init__(self):
        super().__init__(BINARY)
        self.math = OriginalArm(RUNTIME, tls=True)
        self.math_calls = 0
        for name in ["xcam_print_log", "sharp_fix_printf_V33"]:
            self.stubs[self.symbols[name] & ~1] = name
        descriptor = 0x10000 + 0x1A70B0
        assert u32(self.uc.mem_read(descriptor + 28, 4)) & ~1 == 0xF1ED4
        assert u32(self.uc.mem_read(descriptor + 36, 4)) & ~1 == 0xF1B8C
        self.symbols["sharp-prepare"] = self.resolve_symbol("prepare", 0xF1ED4)
        self.symbols["sharp-process"] = self.resolve_symbol("processing", 0xF1B8C)

    def hook(self, uc, address, size, user):
        name = self.stubs.get(address)
        if name in ["pow", "log", "logf"]:
            if name == "logf":
                x = struct.unpack(
                    "<f", struct.pack("<I", uc.reg_read(regs.UC_ARM_REG_S0))
                )[0]
                self.math.invoke(name, floats=[x])
                uc.reg_write(
                    regs.UC_ARM_REG_S0, self.math.uc.reg_read(regs.UC_ARM_REG_S0)
                )
            else:
                values = [
                    struct.unpack(
                        "<d",
                        struct.pack(
                            "<Q", uc.reg_read(getattr(regs, "UC_ARM_REG_D" + str(i)))
                        ),
                    )[0]
                    for i in range(2 if name == "pow" else 1)
                ]
                self.math.invoke(name, doubles=values)
                uc.reg_write(
                    regs.UC_ARM_REG_D0, self.math.uc.reg_read(regs.UC_ARM_REG_D0)
                )
            self.math_calls += 1
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        if name in [
            "malloc",
            "strcmp",
            "strcpy",
            "xcam_print_log",
            "sharp_fix_printf_V33",
        ]:
            a, b = [uc.reg_read(r) for r in [regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1]]
            if name == "malloc":
                assert a == 0x1898
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

    def graph(self, cal):
        self.uc.mem_write(HEAP, bytes(0x31000))
        sets = HEAP + 0x1000
        tune = cal["TuningPara"]
        settings = tune["Setting"]
        self.uc.mem_write(
            HEAP,
            struct.pack(
                "<IBBBBII",
                0,
                *[
                    int(tune[k])
                    for k in [
                        "enable",
                        "sharp_ratio_seperate_en",
                        "kernel_sigma_enable",
                        "Center_Mode",
                    ]
                ],
                sets,
                len(settings),
            ),
        )
        for i, s in enumerate(settings):
            name = HEAP + 0x20000 + i * 128
            data = HEAP + 0x3000 + i * 0x4000
            self.uc.mem_write(name, s["SNR_Mode"].encode() + b"\0")
            self.uc.mem_write(
                sets + i * 16, struct.pack("<4I", name, 0, data, len(s["Tuning_ISO"]))
            )
            for j, row in enumerate(s["Tuning_ISO"]):
                b = bytearray(388)
                struct.pack_into("<fB", b, 0, row["iso"], row["exgain_bypass"])
                for k, key in enumerate(FIELDS):
                    struct.pack_into("<f", b, 8 + k * 4, row[key])
                b[60] = row["global_hf_clip_pos"]
                struct.pack_into(
                    "<fBBH",
                    b,
                    64,
                    row["noiseclip_strength"],
                    row["enhance_bit"],
                    row["noiseclip_mode"],
                    row["noise_sigma_clip"],
                )
                for key, p, n in [
                    ("gain_adj_sharp_strength", 72, 14),
                    ("dis_adj_sharp_strength", 128, 22),
                ]:
                    struct.pack_into("<" + str(n) + "f", b, p, *row[key])
                for key, p in [
                    ("luma_point", 216),
                    ("luma_sigma", 232),
                    ("hf_clip", 248),
                ]:
                    struct.pack_into("<8H", b, p, *row["luma_para"][key])
                for key, p, n in CURVES:
                    struct.pack_into("<" + str(n) + "f", b, p, *row["kernel_para"][key])
                for key, p in [
                    ("prefilter_sigma", 360),
                    ("hfBilateralFilter_sigma", 364),
                    ("GaussianFilter_sigma", 368),
                    ("GaussianFilter_sigma_0", 376),
                    ("GaussianFilter_sigma_1", 380),
                ]:
                    struct.pack_into("<f", b, p, row["kernel_sigma"][key])
                for key, p in [
                    ("GaussianFilter_radius", 372),
                    ("GaussianFilter_radius_0", 384),
                    ("GaussianFilter_radius_1", 385),
                ]:
                    b[p] = row["kernel_sigma"][key]
                self.uc.mem_write(data + j * 388, bytes(b))
        return HEAP

    def frames(self, value):
        root = self.graph(value["calibration"])
        before = bytes(self.uc.mem_read(HEAP, 0x30000))

        def u(a):
            return u32(self.uc.mem_read(a, 4))

        got = (u(0xF2330) + 0xF2266 + u(0xF233C)) & 0xFFFFFFFF
        self.uc.mem_write(u(got), struct.pack("<I", 32))
        lookup = (u(0xF2340) + 0xF22C4) & 0xFFFFFFFF
        assert u(lookup) == 32
        modules = u(lookup + 4)
        offset = None
        for i in range(100):
            p, off = struct.unpack("<II", self.uc.mem_read(modules + i * 8, 8))
            if not p:
                break
            if self.string(p) == b"sharp_v33":
                offset = off
                break
        assert offset is not None
        self.module_offset = offset
        config, pp = HEAP + 0x76000, HEAP + 0x76100
        self.uc.mem_write(config, bytes(64))
        self.uc.mem_write(config + 24, struct.pack("<I", root - offset))
        self.uc.mem_write(pp, bytes(4))
        assert self.invoke("Asharp_Init_V33", [pp, config]) == 0
        ctx = u(pp)
        assert ctx == HEAP + 0x60000
        inp, out, ae, blc, result = [
            HEAP + x for x in [0x73000, 0x74000, 0x71000, 0x72000, 0x75000]
        ]
        self.uc.mem_write(inp, bytes(100))
        self.uc.mem_write(inp, struct.pack("<I", ctx))
        self.uc.mem_write(
            inp + 48, struct.pack("<II", value["geometry"][1], value["geometry"][0])
        )
        assert self.invoke("sharp-prepare", [inp]) == 0
        self.uc.mem_write(out, struct.pack("<II", 0, result))
        self.uc.mem_write(result, bytes.fromhex(value.get("result", "a5" * 178)))
        self.uc.mem_write(ae, bytes(244))
        self.uc.mem_write(blc, bytes(32))
        self.uc.mem_write(inp + 24, struct.pack("<I", ae))
        self.uc.mem_write(inp + 48, struct.pack("<I", blc))
        frames = []
        for f in value["frames"]:
            self.uc.mem_write(inp + 17, bytes([f["gray"]]))
            self.uc.mem_write(ae, struct.pack("<4f", f["seconds"], *f["gains"]))
            self.uc.mem_write(ae + 240, bytes([f["snr"]]))
            self.uc.mem_write(blc + 24, struct.pack("<f", f["blc"]))
            if f["force"]:
                self.uc.mem_write(ctx + 0x1894, struct.pack("<I", u(ctx + 0x1894) | 1))
            self.invoke("sharp-process", [inp, out], instructions=500000)
            frames.append(
                dict(
                    updated=bool(self.uc.mem_read(out, 1)[0]),
                    result=self.uc.mem_read(result, 178).hex(),
                    table=self.uc.mem_read(ctx + 0x60, 5184).hex(),
                    selected=self.uc.mem_read(ctx + 0x14A0, 388).hex(),
                    exposure=self.uc.mem_read(ctx, 88).hex(),
                    strength=self.uc.mem_read(ctx + 0x1860, 16).hex(),
                    gray=bool(self.uc.mem_read(ctx + 0x1871, 1)[0]),
                    parameterMode=u(ctx + 0x1874),
                    recalculate=bool(u(ctx + 0x1894)),
                )
            )
        assert bytes(self.uc.mem_read(HEAP, 0x30000)) == before
        return frames

    def packed(self, result, parameters):
        self.uc.mem_write(HEAP + 0x80000, bytes.fromhex(parameters))
        self.uc.mem_write(HEAP + 0x90000, bytes.fromhex(result))
        self.invoke(
            "_ZN5RkCam11Isp32Params30convertAiqSharpenToIsp32ParamsER20isp32_isp_params_cfgR18RK_SHARP_Fix_V33_s",
            [HEAP, HEAP + 0x80000, HEAP + 0x90000],
        )
        return self.uc.mem_read(HEAP + 0x80000, 11145).hex()


def verify_layout():
    headers = ROOT / ".tools/reverse-engineering/headers"

    def record(file, name):
        text = (headers / file).read_text()
        match = re.search(
            r"typedef struct " + re.escape(name) + r"\s*\{.*?\}\s*\w+;", text, re.S
        )
        assert match, name
        return match[0]

    source = "#include <stdint.h>\n#include <stdbool.h>\n#include <stddef.h>\n#define RK_SHARP_V33_MAX_ISO_NUM 13\n"
    source += (
        record("sharp_uapi_head_v33.h", "RK_SHARP_Params_V33_Select_s")
        + "\n"
        + record("rk_aiq_types_asharp_algo_int_v33.h", "RK_SHARP_Params_V33_s")
        + "\n"
        + record("rk_aiq_types_asharp_hw_v33.h", "RK_SHARP_Fix_V33_s")
        + "\n"
    )
    for name in [
        "CalibDbV2_SharpV33_Luma_t",
        "CalibDbV2_SharpV33_kernel_s",
        "CalibDbV2_SharpV33_Ksigma_s",
        "CalibDbV2_SharpV33_T_ISO_s",
        "CalibDbV2_SharpV33_T_Set_s",
        "CalibDbV2_SharpV33_Tuning_s",
        "CalibDbV2_SharpV33_s",
    ]:
        source += record("sharp_head_v33.h", name) + "\n"
    source += """
_Static_assert(sizeof(RK_SHARP_Params_V33_Select_t)==388,"selected bytes");
_Static_assert(sizeof(RK_SHARP_Params_V33_t)==5184,"table bytes");
_Static_assert(offsetof(RK_SHARP_Params_V33_t,sharpParamsISO)==140,"table rows");
_Static_assert(sizeof(RK_SHARP_Fix_V33_t)==178,"fixed bytes");
_Static_assert(sizeof(CalibDbV2_SharpV33_T_ISO_t)==388,"JSON row bytes");
_Static_assert(sizeof(CalibDbV2_SharpV33_T_Set_t)==16,"JSON setting bytes");
_Static_assert(offsetof(RK_SHARP_Params_V33_Select_t,pbf_gain)==56,"selected pbf gain");
_Static_assert(offsetof(RK_SHARP_Params_V33_Select_t,prefilter_sigma)==264,"selected sigma");
_Static_assert(offsetof(RK_SHARP_Params_V33_Select_t,prefilter_coeff)==292,"selected kernels");
"""
    folder = ROOT / "dist/reverse-engineering"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "sharp-layout.c"
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
            str(folder / "sharp-layout.o"),
        ],
        check=True,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    assert (
        hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
        == "b62e80f7f6c3f104548c91a02429c2ca9734dada97179938240e2075778465fb"
    )
    verify_layout()
    cal = json.loads(
        (
            ROOT
            / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
        ).read_text()
    )["main_scene"][0]["sub_scene"][0]["scene_isp32"]["sharp_v33"]
    cases = []
    for case in range(4):
        c = copy.deepcopy(cal)
        c["TuningPara"]["kernel_sigma_enable"] = bool(case % 2)
        c["TuningPara"]["sharp_ratio_seperate_en"] = bool(case // 2)
        frames = []
        for i, g in enumerate(
            [1.0, 1.0, 1.2, 1.22, 1.22, 2.0, 4.0, 8.0, 16.0, 64.0, 1.0, 1.0]
        ):
            frames.append(
                dict(
                    seconds=0.003 if i % 2 else 0.01,
                    gains=[g, 1.0, 1.0],
                    blc=1.0 if i < 8 else 0.5,
                    snr=i // 3 % 2,
                    gray=i == 6,
                    force=i == 4,
                )
            )
        cases.append(
            dict(
                calibration=c,
                geometry=[2304, 1296] if case < 3 else [3840, 2160],
                frames=frames,
            )
        )
    arm = OriginalSharp()
    expected = [arm.frames(v) for v in cases]
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    lines = "".join(
        "sharp-frames " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    for i, (a, w) in enumerate(zip(actual, expected, strict=True)):
        a = json.loads(a)
        for j, (g, e) in enumerate(zip(a, w, strict=True)):
            if g != e:
                details = {
                    k: [
                        x
                        for x, (ga, ea) in enumerate(
                            zip(bytes.fromhex(g[k]), bytes.fromhex(e[k]))
                        )
                        if ga != ea
                    ][:16]
                    if isinstance(e[k], str)
                    else [g[k], e[k]]
                    for k in e
                    if g[k] != e[k]
                }
                raise AssertionError(f"sequence {i}, frame {j}: {details}")
    pack_cases = [
        dict(result=s[-1]["result"], parameters=(bytes([i]) * 11145).hex())
        for i, s in enumerate(expected)
    ]
    wanted = [arm.packed(**v) for v in pack_cases]
    lines = "".join(
        "isp-sharp " + json.dumps(v, separators=(",", ":")) + "\n" for v in pack_cases
    )
    got = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    assert got == wanted, "ISP packing mismatch"
    report = dict(
        passed=True,
        sdkLayoutArmCompiled=True,
        sequences=len(cases),
        frames=sum(map(lambda v: len(v["frames"]), cases)),
        updatedFrames=sum(f["updated"] for s in expected for f in s),
        packedCases=len(pack_cases),
        selectedBytes=388,
        tableBytes=5184,
        exposureBytes=88,
        resultBytes=178,
        packedBytes=175,
        sdkModuleOffset=hex(arm.module_offset),
        nativeMathCalls=arm.math_calls,
        runtimeSha256=hashlib.sha256(RUNTIME.read_bytes()).hexdigest(),
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        scope="Complete native constructor, prepare/processing callback, calibration, ISO selection, fixed quantization and ISP32 packing; representative normal SC3336 sequences, both kernel modes and separate-ratio modes; original uClibc log/logf/pow execute.",
        sdkHeaders=[
            dict(
                name=name,
                url="https://raw.githubusercontent.com/LuckfoxTECH/luckfox-pico/0b5c1f30ca6333b7ec5af70d26511da9ef8d39af/media/isp/release_camera_engine_rkaiq_rv1106_arm-rockchip830-linux-uclibcgnueabihf/include/rkaiq/"
                + relative,
                sha256=hashlib.sha256(
                    (ROOT / ".tools/reverse-engineering/headers" / name).read_bytes()
                ).hexdigest(),
            )
            for name, relative in [
                (
                    "rk_aiq_types_asharp_hw_v33.h",
                    "algos/asharpV33/rk_aiq_types_asharp_hw_v33.h",
                ),
                (
                    "rk_aiq_types_asharp_algo_int_v33.h",
                    "algos/asharpV33/rk_aiq_types_asharp_algo_int_v33.h",
                ),
                ("sharp_head_v33.h", "iq_parser_v2/sharp_head_v33.h"),
                ("sharp_uapi_head_v33.h", "iq_parser_v2/sharp_uapi_head_v33.h"),
            ]
        ],
        limitations=[
            "No physical ISP test here; root owns hardware integration.",
            "Typed SDK graph, allocation, libc strings/memory and diagnostics are explicit oracle boundaries.",
            "Normal input assembly only; HDR/manual modes and malformed native pointers are not qualified.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
