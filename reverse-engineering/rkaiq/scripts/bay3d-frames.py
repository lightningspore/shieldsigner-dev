#!/usr/bin/env python3
"""Focused complete native BAY3D constructor/controller/packing comparison."""

import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import struct
import subprocess
from differential import ROOT, BINARY, HEAP, OriginalArm, regs, u32

Base = importlib.import_module("baynr-calibration").OriginalCalibration
FLOATS = {
    "lo_filter_strength": 20,
    "hi_filter_strength": 24,
    "lo_clipwgt": 28,
    "soft_threshold_ratio": 32,
    "hi_wgt_comp": 36,
    "lo_filter_rat0": 44,
    "hi_filter_rat0": 56,
    "hi_filter_rat1": 64,
}
BYTES = {
    "hi_enable": 4,
    "lo_med_en": 5,
    "lo_gsbay_en": 6,
    "lo_gslum_en": 7,
    "hi_med_en": 8,
    "hi_gslum_en": 9,
    "wgt_use_mode": 10,
    "wgt_mge_mode": 11,
    "hi_guass": 12,
    "kl_guass": 13,
    "global_pk_en": 14,
    "hi_filter_abs_ctrl": 50,
    "hi_filter_filt_bay": 51,
    "hi_filter_filt_avg": 52,
    "hi_filter_filt_mode": 53,
    "guass_guide_coeff0": 70,
    "guass_guide_coeff1": 71,
    "guass_guide_coeff2": 72,
    "guass_guide_coeff3": 73,
}


class OriginalFrames(Base):
    def __init__(self):
        super().__init__(BINARY)
        self.stubs[self.symbols["xcam_print_log"] & ~1] = "xcam_print_log"
        self.stubs[self.symbols["bayertnr_fix_printf_V23"] & ~1] = "xcam_print_log"
        descriptor = 0x10000 + 0x1A74E8
        assert u32(self.uc.mem_read(descriptor + 36, 4)) & ~1 == 0xF5668
        assert u32(self.uc.mem_read(descriptor + 28, 4)) & ~1 == 0xF59AC
        self.symbols["bay3d-frame"] = self.resolve_symbol("processing", 0xF5668)
        self.symbols["bay3d-prepare"] = self.resolve_symbol("prepare", 0xF59AC)

    def hook(self, uc, address, size, user):
        name = self.stubs.get(address)
        if name in ("malloc", "strcmp", "strcpy", "xcam_print_log"):
            a, b = [uc.reg_read(r) for r in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1)]
            if name == "malloc":
                assert a == 0x191C
                result = HEAP + 0x60000
            elif name == "strcmp":
                result = (self.string(a) > self.string(b)) - (
                    self.string(a) < self.string(b)
                )
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
        tune = cal["TuningPara"]
        cs, ts = HEAP + 0x1000, HEAP + 0x2000
        self.uc.mem_write(
            HEAP,
            struct.pack(
                "<3IBBBBB3xII",
                0,
                cs,
                len(cal["CalibPara"]["Setting"]),
                tune["enable"],
                tune["thumbds_w"],
                tune["thumbds_h"],
                tune["trans_en"],
                tune["lo_enable"],
                ts,
                len(tune["Setting"]),
            ),
        )
        for side, sets, base, stride, key in [
            ("CalibPara", cs, HEAP + 0x3000, 324, "Calib_ISO"),
            ("TuningPara", ts, HEAP + 0x10000, 76, "Tuning_ISO"),
        ]:
            for k, s in enumerate(cal[side]["Setting"]):
                data = base + k * 0x2000
                name = HEAP + 0x20000 + (0 if side == "CalibPara" else 0x1000) + k * 128
                self.uc.mem_write(name, s["SNR_Mode"].encode() + b"\0")
                self.uc.mem_write(
                    sets + k * 16, struct.pack("<4I", name, 0, data, len(s[key]))
                )
                for j, row in enumerate(s[key]):
                    raw = bytearray(stride)
                    struct.pack_into("<f", raw, 0, row["iso"])
                    if side == "CalibPara":
                        for z, n in enumerate(
                            ("lumapoint", "sigma", "lumapoint2", "lo_sigma", "hi_sigma")
                        ):
                            struct.pack_into("<16i", raw, 4 + z * 64, *row[n])
                    else:
                        for n, p in FLOATS.items():
                            struct.pack_into("<f", raw, p, row[n])
                        for n, p in BYTES.items():
                            raw[p] = row[n]
                        for n, p in [("global_pksq", 16), ("hidif_th", 40)]:
                            struct.pack_into("<i", raw, p, row[n])
                        for n, p in [
                            ("lo_filter_thed0", 48),
                            ("hi_filter_thed0", 60),
                            ("hi_filter_thed1", 68),
                        ]:
                            struct.pack_into("<H", raw, p, row[n])
                    self.uc.mem_write(data + j * stride, bytes(raw))
        return HEAP

    def run(self, value):
        root = self.sdk_graph(value["calibration"])
        before = bytes(self.uc.mem_read(HEAP, 0x30000))
        u = lambda a: u32(self.uc.mem_read(a, 4))
        got = (u(0xF5E10) + 0xF5D4A + u(0xF5E1C)) & 0xFFFFFFFF
        self.uc.mem_write(u(got), struct.pack("<I", 32))
        lookup = (u(0xF5E20) + 0xF5DA8) & 0xFFFFFFFF
        assert u(lookup) == 32
        modules = u(lookup + 4)
        offset = None
        for k in range(100):
            name, off = struct.unpack("<II", self.uc.mem_read(modules + k * 8, 8))
            if not name:
                break
            if self.string(name) == b"bayertnr_v23":
                offset = off
                break
        assert offset is not None
        self.module_offset = offset
        config, pp = HEAP + 0x76000, HEAP + 0x76100
        self.uc.mem_write(config, bytes(64))
        self.uc.mem_write(config + 24, struct.pack("<I", root - offset))
        self.uc.mem_write(pp, bytes(4))
        assert self.invoke("Abayertnr_Init_V23", [pp, config]) == 0
        context = u(pp)
        assert context == HEAP + 0x60000
        inp, out, ae, blc, result = [
            HEAP + x for x in (0x73000, 0x74000, 0x71000, 0x72000, 0x75000)
        ]
        self.uc.mem_write(inp, bytes(100))
        self.uc.mem_write(inp, struct.pack("<I", context))
        assert self.invoke("bay3d-prepare", [inp]) == 0
        assert u(context + 0x50) == 3 and u(context + 0x54) == 1
        self.uc.mem_write(out, struct.pack("<III", 0, 0, result))
        self.uc.mem_write(result, bytes.fromhex(value.get("result", "a5" * 224)))
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
                    context + 0x1918, struct.pack("<I", u(context + 0x1918) | 1)
                )
            assert self.invoke("bay3d-frame", [inp, out], instructions=300000) == 0
            frames.append(
                dict(
                    updated=bool(self.uc.mem_read(out, 1)[0]),
                    result=self.uc.mem_read(result, 224).hex(),
                    table=self.uc.mem_read(context + 0x58, 5256).hex(),
                    selected=self.uc.mem_read(context + 0x14E0, 400).hex(),
                    exposure=self.uc.mem_read(context, 80).hex(),
                    strength=self.uc.mem_read(context + 0x18E0, 16).hex(),
                    gray=bool(self.uc.mem_read(context + 0x18F1, 1)[0]),
                    parameterMode=u(context + 0x18F4),
                    recalculate=bool(u(context + 0x1918)),
                )
            )
        assert bytes(self.uc.mem_read(HEAP, 0x30000)) == before
        return frames


class OriginalPacking(OriginalArm):
    def __init__(self):
        super().__init__(BINARY)

    def run(self, value):
        p, s = HEAP + 0x10000, HEAP + 0x20000
        raw = bytes.fromhex(value["result"])
        self.uc.mem_write(p, bytes.fromhex(value["parameters"]))
        self.uc.mem_write(s, raw)
        self.invoke(
            "_ZN5RkCam11Isp32Params26convertAiqTnrToIsp32ParamsER20isp32_isp_params_cfgR21RK_Bayertnr_Fix_V23_s",
            [HEAP, p, s],
        )
        assert bytes(self.uc.mem_read(s, 224)) == raw
        return self.uc.mem_read(p, 11145).hex()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    cal = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "bayertnr_v23"
    ]
    cases = []
    for seq in range(4):
        c = copy.deepcopy(cal)
        if seq == 1:
            c["TuningPara"]["enable"] = False
            c["TuningPara"]["lo_enable"] = False
        if seq == 2:
            c["TuningPara"]["thumbds_w"] = 4
            c["TuningPara"]["thumbds_h"] = 4
        if seq == 3:
            c["TuningPara"]["thumbds_w"] = 8
            c["TuningPara"]["thumbds_h"] = 8
        frames = []
        for j in range(12):
            frames.append(
                dict(
                    seconds=[0.003, 0.01][j % 2],
                    gains=[
                        [1.0, 1.0, 1.0],
                        [1.2, 1.0, 1.0],
                        [1.22, 1.0, 1.0],
                        [2.0, 1.0, 1.0],
                    ][j % 4],
                    snr=j // 2 % 2,
                    gray=7 <= j < 10,
                    blc=[1.0, 0.5, 2.0, 1.0][seq],
                    force=j == 10,
                )
            )
        cases.append(dict(calibration=c, frames=frames, geometry=[2304, 1296]))
    arm = OriginalFrames()
    expected = [arm.run(v) for v in cases]
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output(
        [str(binary)],
        input="".join(
            "bay3d-frames " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
        ),
        text=True,
    ).splitlines()
    for k, (got, want) in enumerate(zip(actual, expected, strict=True)):
        for j, (a, b) in enumerate(zip(json.loads(got), want, strict=True)):
            assert a == b, (
                f"Sequence{k} frame{j} differs: {[n for n in b if a[n] != b[n]]}"
            )
    rng = random.Random(37)
    pack = OriginalPacking()
    packing = [
        dict(parameters=rng.randbytes(11145).hex(), result=f["result"])
        for seq in expected
        for f in seq
    ]
    packing.extend(
        dict(parameters=rng.randbytes(11145).hex(), result=rng.randbytes(224).hex())
        for _ in range(16)
    )
    got = subprocess.check_output(
        [str(binary)],
        input="".join(
            "isp-bay3d " + json.dumps(v, separators=(",", ":")) + "\n" for v in packing
        ),
        text=True,
    ).splitlines()
    assert got == [pack.run(v) for v in packing]
    report = dict(
        passed=True,
        sequences=len(cases),
        frames=sum(map(len, expected)),
        updatedFrames=sum(f["updated"] for seq in expected for f in seq),
        packingCases=len(packing),
        sdkModuleOffset=hex(arm.module_offset),
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        scope="Complete native constructor/prepare/normal processing plus calibration/selection/fixed transfer and complete ISP32 TNR converter. Full state/result bytes, input graph and all packed parameter bytes compared.",
        limitations=[
            "Focused host ARM-instruction oracle, not physical hardware qualification.",
            "Typed SDK graph replaces JSON parsing; allocation/string/memory/diagnostic boundaries explicit.",
            "Normal present-AE path, default auto strength; HDR/manual policy outside this integration.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
