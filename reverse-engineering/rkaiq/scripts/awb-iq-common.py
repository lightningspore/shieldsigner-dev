#!/usr/bin/env python3
"""Original complete JsonPara2SwParaCom compared with owned Rust IQ settings."""

import hashlib, json, random, struct, subprocess, sys
from awb_reference import OriginalAwb
from differential import ROOT, BINARY, HEAP, regs, f32

SYMBOL = "_Z18JsonPara2SwParaComPKvPK23CalibDbV2_Ccm_Para_V2_sP18awb_strategy_cfg_sP25ra_aiq_awb_remosaic_cfg_s"


class Original(OriginalAwb):
    def hook(self, uc, address, size, user):
        if self.stubs.get(address) == "malloc":
            size = uc.reg_read(regs.UC_ARM_REG_R0)
            assert 0 < size <= 255
            pointer = HEAP + 0x10000 + len(self.allocations) * 0x100
            self.allocations.append((pointer, size))
            uc.mem_write(pointer, bytes([0x7B]) * size)
            uc.reg_write(regs.UC_ARM_REG_R0, pointer)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, v):
        raw = bytearray(0x400)
        cfg = bytearray([0xA5]) * 0x600
        remosaic = bytearray([0xB6]) * 20
        # UpdateAwbCalibV2Para copies these before calling the common helper.
        cfg[0x1F8:0x208] = bytes(v["defaultNightGainWeight"])
        arrays = bytearray(0x400)
        word = lambda data, o, n: struct.pack_into("<I", data, o, n & 0xFFFFFFFF)
        fl = lambda data, o, *a: struct.pack_into("<" + "f" * len(a), data, o, *a)
        fl(raw, 0xCC, *v["defaultNightGain"])
        fl(raw, 0x2B8, *v["lineRgBg"])
        fl(raw, 0x2C4, *v["lineRgProjCCT"])
        fl(raw, 0x84, v["wbGainDaylightClip"]["outdoor_cct_min"])
        word(raw, 0x7C, v["wbGainAdjust"]["lutAll_len"])
        for key, ptr, count, offset in [
            ("cct", 0x8C, 0x90, 0),
            ("cri_bound_up", 0x94, 0x98, 0x100),
            ("cri_bound_low", 0x9C, 0xA0, 0x200),
        ]:
            a = v["wbGainClip"][key]
            word(raw, ptr, HEAP + 0x3000 + offset)
            word(raw, count, len(a))
            fl(arrays, offset, *a)
        raw[0x2D0] = v["remosaicCfg"]["enable"]
        raw[0x2D1] = v["remosaicCfg"]["applyInvWbGainEnable"]
        fl(raw, 0x2D4, *v["remosaicCfg"]["sensorWbGain"])
        weights = v["weightForNightGainCalc"]
        word(raw, 0x170, HEAP + 0x3300)
        word(raw, 0x174, len(weights))
        arrays[0x300 : 0x300 + len(weights)] = bytes(weights)
        struct.pack_into("<16I", raw, 0xDC, *v["lumaValueMatrix"])
        raw[0x11C:0x12C] = bytes(v["defaultNightGainWeight"])
        for o, key in [
            (0xA4, "lumaValThLow"),
            (0xA8, "lumaValThLow2"),
            (0xAC, "lumaValThHigh"),
            (0xB0, "lumaValThHigh2"),
        ]:
            word(raw, o, v["division"][key])
        for o, key in [(0x12C, "proDis_THH"), (0x130, "proDis_THL")]:
            fl(raw, o, v["probCalcDis"][key])
        for o, key in [(0x134, "outdoorLumaValThLow"), (0x138, "outdoorLumaValThHigh")]:
            word(raw, o, v["probCalcLv"][key])
        fl(raw, 0x140, v["probCalcWp"]["wpNumPercTh2"])
        for o, key in [
            (0x58, "dFStep"),
            (0x5C, "dFMin"),
            (0x60, "dFMax"),
            (0x68, "lvVarTh"),
        ]:
            fl(raw, o, v["dampFactor"][key])
        word(raw, 0x64, v["dampFactor"]["lvIIRsize"])
        fl(raw, 0x144, v["converged"]["varThforUnDamp"])
        fl(raw, 0x148, v["converged"]["varThforDamp"])
        raw[0x14C] = v["xyRegionStableSelection"]["enable"]
        word(raw, 0x168, v["xyRegionStableSelection"]["xyTypeListSize"])
        fl(raw, 0x16C, v["xyRegionStableSelection"]["varianceLumaTh"])
        for o, data in [(0, raw), (0x1000, cfg), (0x2000, remosaic), (0x3000, arrays)]:
            self.uc.mem_write(HEAP + o, bytes(data))
        self.allocations = []
        status = self.invoke(SYMBOL, [HEAP, 0x11223344, HEAP + 0x1000, HEAP + 0x2000])
        assert status == 0
        after = bytearray(self.uc.mem_read(HEAP + 0x1000, len(cfg)))
        rem = bytearray(self.uc.mem_read(HEAP + 0x2000, 20))
        words = lambda o, n: list(struct.unpack_from("<" + "I" * n, after, o))
        w = lambda o: words(o, 1)[0]
        lines = [
            dict(coefficients=words(o, 3), valid=bool(after[o + 12]))
            for o in (0x348, 0x358)
        ]
        clip = [
            list(
                struct.unpack(
                    "<" + "I" * w(0x370), self.uc.mem_read(w(o), w(0x370) * 4)
                )
            )
            for o in (0x374, 0x378, 0x37C)
        ]
        out = dict(
            night_gain=words(0x1D8, 4),
            lines=lines,
            daylight_min=w(0x36C),
            clip=clip,
            remosaic=[bool(rem[0]), bool(rem[1])],
            sensor_gain=list(struct.unpack_from("<4I", rem, 4)),
            weights=list(self.uc.mem_read(w(0x1EC), after[0x1E8])),
            knots=words(0x168, 16),
            percentages=list(after[0x1F8:0x208]),
            environment=words(0x1A8, 4),
            distance=words(0x1C0, 2),
            probability=words(0x1C8, 4),
            relative=w(0x1F4),
            damping=words(0x14C, 5),
            convergence=[w(0x344), w(0x340)],
            stable=bool(after[0x380]),
            target=w(0x384),
            variance=w(0x388),
            smart=words(0x4A8, 3),
            countdown=w(0x4B4),
        )
        assert w(0x164) == 16 and w(0x254) == 0x11223344
        assert after[0x148] == after[0x160] == after[0x250] == 0
        assert len(self.allocations) == 4 and [
            size for _, size in self.allocations
        ] == [len(clip[0]) * 4] * 3 + [len(weights)]
        # Only fields explicitly written by this initializer may change.
        for o, n in [
            (0x1D8, 16),
            (0x348, 13),
            (0x358, 13),
            (0x36C, 20),
            (0x380, 1),
            (0x384, 8),
            (0x1E8, 1),
            (0x1EC, 4),
            (0x168, 64),
            (0x164, 4),
            (0x1A8, 16),
            (0x1C0, 24),
            (0x1F4, 4),
            (0x14C, 20),
            (0x340, 8),
            (0x148, 1),
            (0x160, 1),
            (0x250, 1),
            (0x254, 4),
            (0x4A8, 16),
        ]:
            after[o : o + n] = cfg[o : o + n]
        assert after == cfg
        assert rem[2:4] == remosaic[2:4]
        assert (
            bytes(self.uc.mem_read(HEAP, len(raw))) == raw
            and bytes(self.uc.mem_read(HEAP + 0x3000, len(arrays))) == arrays
        )
        return out


def main():
    m = json.loads((ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text())
    iq = ROOT / ".tools/reverse-engineering/iqfiles" / m["iqFiles"][0]["name"]
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    iq_sha = hashlib.sha256(iq.read_bytes()).hexdigest()
    assert sha == m["binaries"][0]["sha256"] and iq_sha == m["iqFiles"][0]["sha256"]
    ext = json.loads(iq.read_bytes())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "wb_v32"
    ]["autoExtPara"]
    arm = Original()
    rng = random.Random(0x434F4D4D)
    cases = []
    expected = []
    for i in range(128):
        v = json.loads(json.dumps(ext))
        if i:
            v["lineRgBg"] = [f32(rng.uniform(-2, 2)) for _ in range(3)]
            v["lineRgProjCCT"] = [f32(rng.uniform(-2, 2)) for _ in range(3)]
            v["defaultNightGain"] = [f32(rng.uniform(0.1, 8)) for _ in range(4)]
            v["remosaicCfg"].update(
                enable=bool(i % 2),
                applyInvWbGainEnable=bool(i // 2 % 2),
                sensorWbGain=[f32(rng.uniform(0.1, 4)) for _ in range(4)],
            )
            v["weightForNightGainCalc"] = [i % 256] * (1 + i % 8)
            v["weightForNightGainCalc_len"] = 1 + i % 8
            v["defaultNightGainWeight"] = [(i + j) % 256 for j in range(16)]
            v["xyRegionStableSelection"].update(
                enable=bool(i % 2),
                xyTypeListSize=i,
                varianceLumaTh=f32(rng.uniform(0, 1)),
            )
            v["dampFactor"].update(
                dFStep=f32(rng.uniform(0, 0.2)),
                dFMin=0.1,
                dFMax=0.9,
                lvIIRsize=i % 16,
                lvVarTh=f32(rng.uniform(0, 1)),
            )
            n = 1 + i % 8
            v["wbGainClip"].update(
                cct=[1000.0 + 500 * j for j in range(n)],
                cct_len=n,
                cri_bound_up=[f32(0.1 + 0.01 * j) for j in range(n)],
                cri_bound_up_len=n,
                cri_bound_low=[f32(0.2 + 0.02 * j) for j in range(n)],
                cri_bound_low_len=n,
            )
            v["converged"].update(
                varThforUnDamp=f32(rng.uniform(0.001, 0.01)),
                varThforDamp=f32(rng.uniform(0.02, 0.1)),
            )
            v["wbGainDaylightClip"]["outdoor_cct_min"] = f32(rng.uniform(3000, 7000))
            v["probCalcWp"]["wpNumPercTh2"] = f32(rng.uniform(0, 1))
        cases.append(v)
        expected.append(arm.run(v))
    assert set(arm.calls) <= {"memcpy"} and not arm.runtime_calls
    inputs = ["awb-common-iq " + json.dumps(v, separators=(",", ":")) for v in cases]
    for i in range(8):
        v = json.loads(json.dumps(ext))
        if i == 0:
            v["wbGainAdjust"]["lutAll_len"] = 0
        elif i == 1:
            v["wbGainClip"]["cri_bound_up_len"] += 1
        elif i == 2:
            v["weightForNightGainCalc_len"] += 1
        elif i == 3:
            v["defaultNightGainWeight"][0] = 256
        elif i == 4:
            v["lineRgBg"].pop()
        elif i == 5:
            v["dampFactor"]["dFStep"] = 1e100
        elif i == 6:
            v["lumaValueMatrix"][1] = 0
        elif i == 7:
            v["xyRegionStableSelection"]["enable"] = 2
        inputs.append("awb-common-iq " + json.dumps(v, separators=(",", ":")))
    payload = "\n".join(inputs) + "\n"

    def compare(command):
        p = subprocess.run(
            command, input=payload, text=True, capture_output=True, check=True
        )
        actual = [json.loads(x) for x in p.stdout.splitlines()]
        assert len(actual) == len(expected) + 8
        for i, (a, b) in enumerate(zip(actual, expected)):
            assert a == b, (i, a, b)
        for a in actual[len(expected) :]:
            assert set(a) == {"error"}

    compare([str(ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture")])
    replay = "--arm" in sys.argv
    if replay:
        d = ROOT / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release"
        compare(
            [
                "docker",
                "run",
                "--rm",
                "-i",
                "--platform",
                "linux/arm/v7",
                "--network=none",
                "--mount",
                f"type=bind,src={d},dst=/bincheck,readonly",
                "alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd",
                "/bincheck/numeric-fixture",
            ]
        )
    report = dict(
        binarySha256=sha,
        iqSha256=iq_sha,
        cases=128,
        malformedRejections=8,
        mismatches=0,
        arm=replay,
        elfEntry="0xc8450",
        scope="Complete original common-strategy initializer: copied/scalar/owned tables, line-valid flags, remosaic output, initial constants and unrelated memory preservation.",
        limitations=[
            "Night-percentage bytes are supplied by the enclosing calibration update; this common helper preserves them.",
            "Successful bounded allocation is adapted; failure/partial-write behavior is not reproduced by the checked owned loader.",
            "Other full-calibration-update stages, dynamic preprocessing curves, saved-site setup, hardware configuration and live AWB remain unfinished.",
        ],
    )
    (ROOT / "reverse-engineering/rkaiq/awb-iq-common-equivalence.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
