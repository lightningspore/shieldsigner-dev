#!/usr/bin/env python3
"""Run JSON-loaded SC3336 classifier/confidence settings against native ARM."""

import hashlib
import json
import random
import runpy
import struct
import subprocess
import sys
from pathlib import Path
from differential import BINARY, ROOT, f32
from awb_reference import RUNTIME


def main():
    manifest = json.loads(
        (ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text()
    )
    iq_path = (
        ROOT / ".tools/reverse-engineering/iqfiles" / manifest["iqFiles"][0]["name"]
    )
    iq_sha = hashlib.sha256(iq_path.read_bytes()).hexdigest()
    assert iq_sha == manifest["iqFiles"][0]["sha256"]
    runtime_sha = hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
    assert runtime_sha == manifest["gccRuntime"]["memberSha256"]
    binary_sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert binary_sha == manifest["binaries"][0]["sha256"]
    scene = json.loads(iq_path.read_bytes())["main_scene"][0]["sub_scene"][0][
        "scene_isp32"
    ]["wb_v32"]
    ext = scene["autoExtPara"]
    sgc = ext["singleColorProces"]
    grid_ref = runpy.run_path(str(Path(__file__).with_name("awb-single-color-grid.py")))
    confidence_ref = runpy.run_path(
        str(Path(__file__).with_name("awb-single-color.py"))
    )
    grid_arm = grid_ref["Original"]()
    confidence_arm = confidence_ref["Original"]()
    assert (
        hashlib.sha256(grid_ref["color_reference"].MATH.read_bytes()).hexdigest()
        == manifest["uclibcRuntime"]["memberSha256"]
    )
    bits = lambda v: struct.unpack("<I", struct.pack("<f", v))[0]
    candidates = [[c["RGain"], c["BGain"]] for c in sgc["lsUsedForEstimation"]]
    colors = [
        dict(
            index=c["index"],
            chroma=c["meanC"],
            hue=c["meanH"],
            knots=c["ct"],
            thresholds=c["disTh"],
        )
        for c in sgc["colorBlock"]
    ]
    first = ext["lineRgBg"] + [True]
    second = ext["lineRgProjCCT"] + [True]
    confidence = dict(
        brightness_knots=sgc["wgtLvX"],
        brightness_weights=sgc["wgtLvY"],
        density_knots=sgc["wgtWpNumthX"],
        density_weights=sgc["wgtWpNumthY"],
        distance_knots=sgc["wgtDisX"],
        cct_knots=sgc["wgtDisCt"],
        distance_weights=[sgc["wgtDisHCtY"], sgc["wgtDisMCtY"], sgc["wgtDisLCtY"]],
        disagreement_knots=sgc["wgtClrGradX"],
        disagreement_weights=sgc["wgtClrGradY"],
    )
    inputs = []
    expected = []
    valid = 0
    rng = random.Random(0x49515347)
    for i in range(24):
        base = [f32(rng.uniform(0.02, 0.8)) for _ in range(3)]
        grid = [
            base if i % 3 != 2 else [f32(rng.uniform(0.01, 1.2)) for _ in range(3)]
            for _ in range(225)
        ]
        v = dict(
            candidates=candidates,
            colors=colors,
            history=[j % 3 for j in range(i % 5)],
            target=sgc["illuEstListSize"],
            alpha=sgc["alpha"],
            first=first,
            second=second,
            prior=None if i % 2 else [2.0, 1.0, 1.0, 1.5],
            grid=grid,
        )
        out = grid_arm.run(v)
        if (i + 1) % 8 == 0:
            print(f"Native IQ classifier: {i + 1}/24", file=sys.stderr, flush=True)
        expected.append(out)
        valid += out["valid"]
        # Poison the manual values; only the parsed IQ object is authoritative.
        v.update(
            sgc=sgc,
            candidates=[[9.0, 9.0]],
            colors=[
                dict(
                    chroma=0.0,
                    hue=0.0,
                    knots=[0.0, 1.0, 2.0],
                    thresholds=[0.0, 0.0, 0.0],
                )
            ],
            alpha=0.0,
            target=0,
        )
        inputs.append("awb-single-color-grid " + json.dumps(v, separators=(",", ":")))
    for i in range(256):
        v = dict(
            kind="confidence",
            calibration=confidence,
            first=first,
            second=second,
            gain=[f32(rng.uniform(0.5, 3.0)), 1.0, 1.0, f32(rng.uniform(0.5, 3.0))],
            brightness=[0.0, 32.0, 128.0, 1024.0, 8192.0, 262144.0][i % 6],
            density=[0.0, 20.0, 100.0, 500.0, 1000.0, 2000.0, 3000.0][i % 7],
            distance=float((i % 13) * 300),
            disagreements=(i % 8) * 100,
        )
        expected.append(confidence_ref["native"](confidence_arm, v))
        v.update(
            sgc=sgc,
            calibration={
                k: ([[0.0] * 6] * 3 if k == "distance_weights" else [0.0] * len(values))
                for k, values in confidence.items()
            },
        )
        inputs.append("awb-single-color " + json.dumps(v, separators=(",", ":")))
    expected.append(
        dict(
            enabled=True,
            mode=0,
            colors=len(colors),
            candidates=len(candidates),
            names=[c["name"] for c in sgc["lsUsedForEstimation"]],
            indices=[c["index"] for c in sgc["colorBlock"]],
            target=sgc["illuEstListSize"],
            alpha=bits(sgc["alpha"]),
            diagnostic=sgc["illuMchPrt"],
            thresholds=[
                bits(sgc[k])
                for k in [
                    "useSgcResth",
                    "updateDpWbgnTh",
                    "updateDpWbgnTh2",
                    "updateEstWbgnTh",
                ]
            ],
        )
    )
    inputs.append("awb-sgc-parse " + json.dumps(sgc, separators=(",", ":")))
    malformed = []
    for kind in range(10):
        v = json.loads(json.dumps(sgc))
        if kind == 0:
            del v["mode"]
        elif kind == 1:
            v["mode"] = "UNKNOWN"
        elif kind == 2:
            v["colorBlock_len"] += 1
        elif kind == 3:
            v["wgtLvX"].pop()
        elif kind == 4:
            v["wgtWpNumthX"] = [6, 5, 4, 3, 2, 1]
        elif kind == 5:
            v["alpha"] = 1e100
        elif kind == 6:
            v["illuEstListSize"] = 1.5
        elif kind == 7:
            v["enable"] = 2
        elif kind == 8:
            v["lsUsedForEstimation"][0]["name"] = None
        elif kind == 9:
            v["alpha"] = 2.0
        malformed.append(v)
        inputs.append("awb-sgc-parse " + json.dumps(v, separators=(",", ":")))
    payload = "\n".join(inputs) + "\n"

    def compare(command):
        process = subprocess.run(
            command, input=payload, text=True, capture_output=True, check=True
        )
        actual = [json.loads(line) for line in process.stdout.splitlines()]
        assert len(actual) == len(expected) + len(malformed)
        for i, (a, b) in enumerate(zip(actual, expected)):
            assert a == b, (i, a, b)
        for a in actual[len(expected) :]:
            assert set(a) == {"error"} and a["error"]

    compare([str(ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture")])
    replay = "--arm" in sys.argv
    if replay:
        directory = (
            ROOT / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release"
        )
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
                f"type=bind,src={directory},dst=/bincheck,readonly",
                "alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd",
                "/bincheck/numeric-fixture",
            ]
        )
    report = dict(
        binarySha256=binary_sha,
        runtimeSha256=runtime_sha,
        iqSha256=iq_sha,
        jsonPointer="/main_scene/0/sub_scene/0/scene_isp32/wb_v32/autoExtPara/singleColorProces",
        classifierCases=24,
        cells=5400,
        validClassifications=valid,
        confidenceCases=256,
        parseSummaryChecks=1,
        malformedRejections=10,
        mismatches=0,
        arm=replay,
        mathCalls=grid_arm.math_calls,
        scope="Owned JSON single-color calibration used by complete classifier and confidence-manager comparisons; manual fixture calibration is poisoned.",
        limitations=[
            "Explicit scene selection; this loads the singleColorProces subset, not all AWB calibration or initialization.",
            "Caller-supplied line-valid flags are true; native calibrated-line construction is not tested.",
            "Synthetic grids/history/samples; no live sensor or complete IQ-initialized frame lifecycle.",
        ],
    )
    (
        ROOT / "reverse-engineering/rkaiq/awb-iq-single-color-equivalence.json"
    ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
