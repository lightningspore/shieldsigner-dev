#!/usr/bin/env python3
"""Use an owned scene to configure complete original AWB postprocessing."""

import hashlib, json, random, runpy, struct, subprocess, sys
from pathlib import Path
from differential import ROOT, BINARY, HEAP, f32


def main():
    m = json.loads((ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text())
    iq = ROOT / ".tools/reverse-engineering/iqfiles" / m["iqFiles"][0]["name"]
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    iq_sha = hashlib.sha256(iq.read_bytes()).hexdigest()
    assert sha == m["binaries"][0]["sha256"] and iq_sha == m["iqFiles"][0]["sha256"]
    wb = json.loads(iq.read_bytes())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "wb_v32"
    ]
    ref = runpy.run_path(str(Path(__file__).with_name("awb-postprocess.py")))
    arm = ref["Original"]()
    rng = random.Random(0x53434E45)
    inputs = []
    expected = []
    coverage = {}
    for i in range(128):
        scene = json.loads(json.dumps(wb))
        e = scene["autoExtPara"]
        if i:
            e["wbGainClip"]["enable"] = bool(i % 2)
            e["wbGainDaylightClip"]["enable"] = bool(i // 2 % 2)
            e["wbGainAdjust"]["enable"] = bool(i // 4 % 2)
            e["wbGainOffset"]["enable"] = bool(i // 8 % 2)
            e["wbGainAdjust"]["ctrlDataSelt"] = (
                "AWB_CTRL_DATA_ISO" if i // 16 % 2 else "AWB_CTRL_DATA_LV"
            )
            e["wbGainAdjust"]["adjDataSelt"] = (
                "AWB_GAIN_ADJ_DATA_CT" if i // 32 % 2 else "AWB_GAIN_ADJ_DATA_GAIN"
            )
            e["wbGainOffset"]["offset"] = [
                f32(rng.uniform(-0.2, 0.2)) for _ in range(4)
            ]
            e["tolerance"]["toleranceValue"] = [0.0, 0.01, 0.05, 0.1]
            e["wbGainClip"]["cri_bound_up"] = [f32(0.1 + 0.02 * j) for j in range(6)]
            e["wbGainClip"]["cri_bound_low"] = [f32(0.3 + 0.03 * j) for j in range(6)]
        if e["wbGainAdjust"]["adjDataSelt"] == "AWB_GAIN_ADJ_DATA_CT":
            lut = e["wbGainAdjust"]["lutAll"][0]
            x = [1000.0 + 1000 * j for j in range(9)]
            y = [-1.0 + 0.2 * j for j in range(11)]
            lut.update(
                rgct_in_ds=x,
                bgcri_in_ds=y,
                rgct_lut_out=[xx for yy in y for xx in x],
                bgcri_lut_out=[yy for yy in y for xx in x],
            )
        gain = lambda: [
            f32(rng.uniform(0.7, 3.0)),
            1.0,
            1.0,
            f32(rng.uniform(0.7, 3.0)),
        ]
        brightness = [0, 256, 512, 32768, 45745, 45746, 131072, 262144][i % 8]
        # Use native interpolation for the independent reference tolerance.
        x = e["tolerance"]["lumaValue"]
        y = e["tolerance"]["toleranceValue"]
        arm.uc.mem_write(HEAP + 0x79000, struct.pack("<4f", *x))
        arm.uc.mem_write(HEAP + 0x79100, struct.pack("<4f", *y))
        arm.invoke(
            "_Z13interpolationPKfS0_ifPf",
            [HEAP + 0x79000, HEAP + 0x79100, 4, HEAP + 0x79200],
            floats=[float(brightness)],
        )
        tolerance = struct.unpack("<f", arm.uc.mem_read(HEAP + 0x79200, 4))[0]
        lut = e["wbGainAdjust"]["lutAll"][0]
        v = dict(
            candidate=gain(),
            previous=[0.0] * 4 if i % 11 == 0 else gain(),
            coefficient=[0.0, 0.5, 0.9, 1.0][i % 4],
            raw_history=[[1.0] * 4] * (i % 5),
            output_history=[gain() for _ in range(i % 4)],
            target=e["weightForNightGainCalc_len"],
            tolerance=tolerance,
            history_convergence=e["converged"]["varThforUnDamp"],
            damped_convergence=e["converged"]["varThforDamp"],
            damping_threshold=0.005,
            clip=bool(e["wbGainClip"]["enable"] or e["wbGainDaylightClip"]["enable"]),
            bounds_enabled=bool(e["wbGainClip"]["enable"]),
            daylight=bool(e["wbGainDaylightClip"]["enable"]),
            adjust=bool(e["wbGainAdjust"]["enable"]),
            offset_enabled=bool(e["wbGainOffset"]["enable"]),
            offsets=e["wbGainOffset"]["offset"],
            clipped=bool(i % 2),
            brightness=brightness,
            first=e["lineRgBg"] + [True],
            second=e["lineRgProjCCT"] + [True],
            lights=[dict(gain=gain(), probability=f32(rng.random())) for _ in range(7)],
            sample=float(i * 100),
            iso=float(50 + i * 10),
            sample_selector=int(
                e["wbGainAdjust"]["ctrlDataSelt"] == "AWB_CTRL_DATA_LV"
            ),
            temperature_mode=e["wbGainAdjust"]["adjDataSelt"] == "AWB_GAIN_ADJ_DATA_CT",
            clip_knots=e["wbGainClip"]["cct"],
            clip_lower=e["wbGainClip"]["cri_bound_low"],
            clip_upper=e["wbGainClip"]["cri_bound_up"],
            daylight_threshold=e["probCalcLv"]["outdoorLumaValThHigh"],
            daylight_minimum=e["wbGainDaylightClip"]["outdoor_cct_min"],
            lut=dict(
                sample=lut["ctlData"],
                x=lut["rgct_in_ds"],
                y=lut["bgcri_in_ds"],
                mapped_x=lut["rgct_lut_out"],
                mapped_y=lut["bgcri_lut_out"],
            ),
        )
        expected.append(arm.run(v))
        key = f"{v['bounds_enabled']}:{v['daylight']}:{v['adjust']}:{v['offset_enabled']}:{v['sample_selector']}:{v['temperature_mode']}"
        coverage[key] = coverage.get(key, 0) + 1
        v["scene_iq"] = scene
        # Keep native reference inputs separate; Rust Scene overrides duplicates.
        v.update(
            clip=False,
            adjust=False,
            offset_enabled=False,
            target=0,
            tolerance=99.0,
            history_convergence=99.0,
            damped_convergence=99.0,
        )
        inputs.append("awb-postprocess " + json.dumps(v, separators=(",", ":")))
    e = wb["autoExtPara"]
    bits = lambda n: struct.unpack("<I", struct.pack("<f", n))[0]
    expected.append(
        dict(
            lights=7,
            first=next(
                j
                for j, l in enumerate(wb["autoPara"]["lightSources"])
                if l["name"] == e["lightSourceForFirstFrame"]
            ),
            candidates=3,
            mode=0,
            optional=[False] * 4,
            temperature=False,
            luma=True,
            luts=1,
            site=[True, True],
            site_frames=3,
            site_thresholds=[bits(0.2), bits(2.0)],
            site_path=e["avaSiteRec"]["fullFileName"],
        )
    )
    inputs.append("awb-scene-parse " + json.dumps(wb, separators=(",", ":")))
    for i in range(8):
        scene = json.loads(json.dumps(wb))
        e = scene["autoExtPara"]
        a = e["wbGainAdjust"]
        if i == 0:
            a["adjDataSelt"] = "UNKNOWN"
        elif i == 1:
            a["ctrlDataSelt"] = "UNKNOWN"
        elif i == 2:
            a["lutAll"][0]["rgct_lut_out"].pop()
        elif i == 3:
            a["lutAll"][0]["rgct_in_ds"][1] = a["lutAll"][0]["rgct_in_ds"][0]
        elif i == 4:
            a["lutAll_len"] = 2
        elif i == 5:
            e["avaSiteRec"]["frameNum"] = 1.5
        elif i == 6:
            e["avaSiteRec"]["fullFileName"] = "bad\x00path"
        elif i == 7:
            e["wbGainClip"]["enable"] = 2
        inputs.append("awb-scene-parse " + json.dumps(scene, separators=(",", ":")))
    payload = "\n".join(inputs) + "\n"

    def compare(command):
        p = subprocess.run(
            command, input=payload, text=True, capture_output=True, check=True
        )
        actual = [json.loads(line) for line in p.stdout.splitlines()]
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
        sceneSummaryChecks=1,
        malformedRejections=8,
        mismatches=0,
        arm=replay,
        coverage=coverage,
        scope="Owned explicit wb_v32 scene supplies settings to complete native postprocessing through normal gain-mode return.",
        limitations=[
            "Pinned scene plus enabled optional-block variations; LUT tests use one LUT per scene.",
            "Original gain-mode incomplete-measurement prefix provides normalized candidate; complete gain strategy/frame lifecycle and persistence are not executed.",
            "All scene subsets are parsed, but this suite numerically exercises only postprocessing; hardware/live AWB remain unfinished.",
        ],
    )
    (ROOT / "reverse-engineering/rkaiq/awb-iq-scene-post-equivalence.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
